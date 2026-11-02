import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import current_user
from app.core.config import get_settings
from app.db.base import utc_now
from app.db.models import Analysis, GitHubConnection, RepositoryConnection, User
from app.db.session import get_db
from app.schemas.analysis import AnalysisReport
from app.services.analysis import ModelReport, deterministic_report, enrich_with_openai, inspect_repository
from app.services.github.client import GitHubError
from app.services.security import decrypt_token
from app.services.github.client import GitHubClient

router = APIRouter(prefix="/analyses", tags=["analysis"])


def _connection(repository_id: int, user: User, db: Session) -> RepositoryConnection:
    connection = db.scalar(select(RepositoryConnection).where(
        RepositoryConnection.user_id == user.id,
        RepositoryConnection.github_repository_id == repository_id,
    ))
    if connection is None:
        raise HTTPException(status_code=404, detail="Connect this repository before analyzing it.")
    return connection


def _report(row: Analysis) -> AnalysisReport:
    return AnalysisReport(
        id=row.id, repository_id=row.repository_connection_id, commit_sha=row.commit_sha,
        status=row.status, project_summary=row.project_summary,
        detected_technologies=json.loads(row.detected_technologies) if row.detected_technologies else [],
        file_inventory=json.loads(row.file_inventory) if row.file_inventory else [],
        findings=json.loads(row.findings) if row.findings else [],
        recommendations=json.loads(row.recommendations) if row.recommendations else [],
        development_plan=json.loads(row.development_plan) if row.development_plan else [],
        limitations=json.loads(row.limitations) if row.limitations else [],
        model_identifier=row.model_identifier,
        token_usage=row.token_usage, created_at=row.created_at, completed_at=row.completed_at,
    )


@router.post("/repositories/{repository_id}/analyze", response_model=AnalysisReport)
async def analyze_repository(
    repository_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> AnalysisReport:
    connection = _connection(repository_id, user, db)
    github = db.scalar(select(GitHubConnection).where(GitHubConnection.user_id == user.id))
    if github is None:
        raise HTTPException(status_code=401, detail="Connect GitHub before analyzing repositories.")
    try:
        client = GitHubClient(decrypt_token(github.encrypted_access_token))
        inspection = await inspect_repository(
            client, connection.owner, connection.name, connection.default_branch, get_settings()
        )
    except (GitHubError, ValueError) as exc:
        raise HTTPException(status_code=getattr(exc, "status_code", 502), detail=str(exc)) from exc

    summary, findings, recommendations, plan = deterministic_report(inspection)
    deterministic = ModelReport(
        project_summary=summary, detected_technologies=inspection.technologies,
        findings=findings, recommendations=recommendations, development_plan=plan,
        limitations=inspection.limitations,
    )
    ai_report, token_usage = await enrich_with_openai(inspection, deterministic, get_settings())
    report = ai_report or deterministic
    limitations = sorted(set(inspection.limitations + report.limitations))
    if get_settings().openai_api_key and ai_report is None:
        limitations.append("AI enrichment was unavailable; this report contains deterministic inspection results only.")
    limitations = sorted(set(limitations))
    row = Analysis(
        user_id=user.id, repository_connection_id=connection.id, commit_sha=inspection.commit_sha,
        status="partial" if limitations else "completed", project_summary=report.project_summary,
        detected_technologies=json.dumps(report.detected_technologies or inspection.technologies),
        file_inventory=json.dumps([{"path": f.path, "size": f.size, "language": f.language} for f in inspection.files]),
        findings=json.dumps([item.model_dump() for item in report.findings]),
        recommendations=json.dumps(report.recommendations),
        development_plan=json.dumps([item.model_dump() for item in report.development_plan]),
        limitations=json.dumps(limitations), model_identifier=get_settings().openai_model if ai_report else None,
        token_usage=token_usage, completed_at=utc_now(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _report(row)


@router.post("/repositories/{repository_id}/analyze/async")
async def analyze_repository_async(
    repository_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> dict[str, object]:
    connection = _connection(repository_id, user, db)
    github = db.scalar(select(GitHubConnection).where(GitHubConnection.user_id == user.id))
    if github is None:
        raise HTTPException(status_code=401, detail="Connect GitHub before analyzing repositories.")
    try:
        client = GitHubClient(decrypt_token(github.encrypted_access_token))
        commit_sha = await client.ref(connection.owner, connection.name, connection.default_branch)
    except Exception:
        commit_sha = "unknown"

    row = Analysis(
        user_id=user.id,
        repository_connection_id=connection.id,
        commit_sha=commit_sha or "unknown",
        status="pending",
        project_summary="Analysis queued for background worker execution.",
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    try:
        from app.workers.tasks import analyze_repository_task
        job = analyze_repository_task.delay(row.id, user.id)
        return {"job_id": job.id, "analysis_id": row.id, "status": "pending"}
    except Exception as exc:
        logger.warning("Celery task queue unreachable (%s); running fallback inline analysis.", exc)
        try:
            client = GitHubClient(decrypt_token(github.encrypted_access_token))
            inspection = await inspect_repository(
                client, connection.owner, connection.name, connection.default_branch, get_settings()
            )
            summary, findings, recommendations, plan = deterministic_report(inspection)
            deterministic = ModelReport(
                project_summary=summary, detected_technologies=inspection.technologies,
                findings=findings, recommendations=recommendations, development_plan=plan,
                limitations=inspection.limitations,
            )
            ai_report, token_usage = await enrich_with_openai(inspection, deterministic, get_settings())
            report = ai_report or deterministic
            limitations = sorted(set(inspection.limitations + report.limitations))
            row.status = "partial" if limitations else "completed"
            row.project_summary = report.project_summary
            row.detected_technologies = json.dumps(report.detected_technologies or inspection.technologies)
            row.file_inventory = json.dumps([{"path": f.path, "size": f.size, "language": f.language} for f in inspection.files])
            row.findings = json.dumps([item.model_dump() for item in report.findings])
            row.recommendations = json.dumps(report.recommendations)
            row.development_plan = json.dumps([item.model_dump() for item in report.development_plan])
            row.limitations = json.dumps(limitations)
            row.model_identifier = get_settings().openai_model if ai_report else None
            row.token_usage = token_usage
            row.completed_at = utc_now()
            db.commit()
            return {"job_id": f"inline-{row.id}", "analysis_id": row.id, "status": row.status}
        except Exception as inner_exc:
            row.status = "failed"
            row.project_summary = f"Analysis failed: {inner_exc}"
            db.commit()
            raise HTTPException(status_code=502, detail=str(inner_exc)) from inner_exc


@router.get("/repositories/{repository_id}/analysis/latest", response_model=AnalysisReport)
async def latest_analysis(
    repository_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> AnalysisReport:
    connection = _connection(repository_id, user, db)
    row = db.scalar(select(Analysis).where(
        Analysis.user_id == user.id, Analysis.repository_connection_id == connection.id
    ).order_by(Analysis.created_at.desc()))
    if row is None:
        raise HTTPException(status_code=404, detail="No analysis exists for this repository.")
    return _report(row)


@router.get("/{analysis_id}", response_model=AnalysisReport)
async def get_analysis(
    analysis_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> AnalysisReport:
    row = db.scalar(select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == user.id))
    if row is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return _report(row)
