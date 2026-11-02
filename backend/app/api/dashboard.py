import json
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.auth import current_user
from app.core.config import get_settings
from app.db.models import (
    Analysis,
    DevelopmentTask,
    ReleaseCandidate,
    RepositoryConnection,
    TaskEvent,
    User,
)
from app.db.session import get_db
from app.schemas.dashboard import ActivityEvent, DashboardStats, SystemStatus
from app.services.sandbox_manager import docker_ready

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(user: User = Depends(current_user), db: Session = Depends(get_db)) -> DashboardStats:
    connected_repos = db.scalar(
        select(func.count(RepositoryConnection.id)).where(RepositoryConnection.user_id == user.id)
    ) or 0

    tasks_executed = db.scalar(
        select(func.count(DevelopmentTask.id)).where(DevelopmentTask.user_id == user.id)
    ) or 0

    pending_reviews = db.scalar(
        select(func.count(DevelopmentTask.id)).where(
            DevelopmentTask.user_id == user.id,
            DevelopmentTask.status == "awaiting_review",
        )
    ) or 0

    successful_releases = db.scalar(
        select(func.count(ReleaseCandidate.id)).where(
            ReleaseCandidate.user_id == user.id,
            ReleaseCandidate.status == "released",
        )
    ) or 0

    active_analyses = db.scalar(
        select(func.count(Analysis.id)).where(
            Analysis.user_id == user.id,
            Analysis.status.in_(["pending", "running"]),
        )
    ) or 0

    return DashboardStats(
        connected_repositories=connected_repos,
        tasks_executed=tasks_executed,
        pending_reviews=pending_reviews,
        successful_releases=successful_releases,
        active_analyses=active_analyses,
    )


@router.get("/activity", response_model=list[ActivityEvent])
def get_activity(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[ActivityEvent]:
    stmt = (
        select(
            TaskEvent.id,
            TaskEvent.development_task_id,
            TaskEvent.event_type,
            TaskEvent.sanitized_details,
            TaskEvent.created_at,
            RepositoryConnection.owner.label("repo_owner"),
            RepositoryConnection.name.label("repo_name"),
        )
        .join(DevelopmentTask, TaskEvent.development_task_id == DevelopmentTask.id)
        .outerjoin(RepositoryConnection, DevelopmentTask.repository_connection_id == RepositoryConnection.id)
        .where(DevelopmentTask.user_id == user.id)
        .order_by(TaskEvent.created_at.desc())
        .limit(50)
    )

    rows = db.execute(stmt).all()
    results: list[ActivityEvent] = []
    for row in rows:
        details = {}
        if row.sanitized_details:
            try:
                details = json.loads(row.sanitized_details)
            except Exception:
                details = {"raw": row.sanitized_details}

        results.append(
            ActivityEvent(
                id=row.id,
                task_id=row.development_task_id,
                event_type=row.event_type,
                details=details,
                created_at=row.created_at,
                repository_owner=row.repo_owner,
                repository_name=row.repo_name,
            )
        )
    return results


@router.get("/system", response_model=SystemStatus)
async def get_system_status() -> SystemStatus:
    settings = get_settings()
    db_url_lower = settings.database_url.lower()
    if "mysql" in db_url_lower:
        db_type = "mysql"
    elif "postgres" in db_url_lower:
        db_type = "postgresql"
    elif "sqlite" in db_url_lower:
        db_type = "sqlite"
    else:
        db_type = "database"
    has_docker = await docker_ready(settings)

    return SystemStatus(
        app_name=settings.app_name,
        app_env=settings.app_env,
        github_configured=settings.github_configured,
        openai_configured=bool(settings.openai_api_key),
        openai_model=settings.openai_model,
        sandbox_image=settings.sandbox_image,
        database_type=db_type,
        sandbox_available=has_docker,
    )

