import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import current_user
from app.db.models import (
    AutomationRun,
    AutomationSetting,
    RepositoryConnection,
    User,
)
from app.db.session import get_db
from app.schemas.automation import (
    AutomationRunResponse,
    AutomationSettingCreate,
    AutomationSettingResponse,
    AutomationSettingUpdate,
    AutomationTriggerRequest,
)
from app.services.automation.engine import (
    approve_and_publish_automation_run,
    execute_daily_ai_automation,
)
from app.services.automation.scheduler import compute_next_run
from app.services.github.client import GitHubError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/automation", tags=["automation"])


def _setting_response(s: AutomationSetting, repo: RepositoryConnection | None = None) -> AutomationSettingResponse:
    try:
        areas = json.loads(s.focus_areas) if s.focus_areas else []
    except Exception:
        areas = ["code_improvements"]
    return AutomationSettingResponse(
        id=s.id,
        user_id=s.user_id,
        repository_connection_id=s.repository_connection_id,
        repository_name=repo.name if repo else None,
        repository_owner=repo.owner if repo else None,
        default_branch=repo.default_branch if repo else None,
        is_enabled=s.is_enabled,
        schedule_time=s.schedule_time,
        timezone=s.timezone or "Asia/Kolkata",
        auto_publish=bool(s.auto_publish),
        next_run_at=s.next_run_at,
        max_retries=s.max_retries or 2,
        focus_areas=areas,
        target_branch_prefix=s.target_branch_prefix,
        auto_test=s.auto_test,
        require_approval=s.require_approval,
        last_run_at=s.last_run_at,
        last_run_status=s.last_run_status,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


def _run_response(r: AutomationRun, repo: RepositoryConnection | None = None) -> AutomationRunResponse:
    return AutomationRunResponse(
        id=r.id,
        user_id=r.user_id,
        repository_connection_id=r.repository_connection_id,
        repository_name=f"{repo.owner}/{repo.name}" if repo else None,
        analysis_id=r.analysis_id,
        development_task_id=r.development_task_id,
        release_candidate_id=r.release_candidate_id,
        status=r.status,
        summary=r.summary,
        findings_count=r.findings_count,
        changes_count=r.changes_count,
        files_created_count=r.files_created_count or 0,
        files_modified_count=r.files_modified_count or 0,
        files_deleted_count=r.files_deleted_count or 0,
        lines_added=r.lines_added or 0,
        lines_deleted=r.lines_deleted or 0,
        security_result=r.security_result or "passed",
        test_result=r.test_result or "passed",
        commit_message=r.commit_message,
        tests_passed=r.tests_passed,
        target_branch=r.target_branch,
        commit_sha=r.commit_sha,
        commit_url=r.commit_url,
        pull_request_number=r.pull_request_number,
        pull_request_url=r.pull_request_url,
        validation_completed_at=r.validation_completed_at,
        publishing_started_at=r.publishing_started_at,
        commit_created_at=r.commit_created_at,
        push_completed_at=r.push_completed_at,
        remote_sha_verified_at=r.remote_sha_verified_at,
        publishing_duration_ms=r.publishing_duration_ms,
        speed_target_met=r.speed_target_met,
        log_output=r.log_output,
        error_message=r.error_message,
        created_at=r.created_at,
        completed_at=r.completed_at,
    )


@router.get("/settings", response_model=list[AutomationSettingResponse])
async def list_automation_settings(
    user: User = Depends(current_user), db: Session = Depends(get_db)
) -> list[AutomationSettingResponse]:
    """List System B daily automation settings across user's connected repositories."""
    settings = db.scalars(
        select(AutomationSetting).where(AutomationSetting.user_id == user.id)
    ).all()
    results: list[AutomationSettingResponse] = []
    for s in settings:
        repo = db.get(RepositoryConnection, s.repository_connection_id)
        results.append(_setting_response(s, repo))
    return results


@router.post("/settings", response_model=AutomationSettingResponse, status_code=201)
async def create_or_update_setting(
    payload: AutomationSettingCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> AutomationSettingResponse:
    """Configure or enable System B daily automation for a repository."""
    repo = db.scalar(
        select(RepositoryConnection).where(
            (
                (RepositoryConnection.id == payload.repository_connection_id)
                | (RepositoryConnection.github_repository_id == payload.repository_connection_id)
            ),
            RepositoryConnection.user_id == user.id,
        )
    )
    if not repo:
        raise HTTPException(status_code=404, detail="Connected repository not found.")

    setting = db.scalar(
        select(AutomationSetting).where(
            AutomationSetting.user_id == user.id,
            AutomationSetting.repository_connection_id == repo.id,
        )
    )
    if not setting:
        tz = payload.timezone.strip() if payload.timezone else "Asia/Kolkata"
        sched = payload.schedule_time.strip() if payload.schedule_time else "20:00"
        setting = AutomationSetting(
            user_id=user.id,
            repository_connection_id=repo.id,
            is_enabled=payload.is_enabled,
            schedule_time=sched,
            timezone=tz,
            auto_publish=payload.auto_publish,
            next_run_at=compute_next_run(sched, tz),
            focus_areas=json.dumps(payload.focus_areas),
            target_branch_prefix=payload.target_branch_prefix.strip(),
            auto_test=payload.auto_test,
            require_approval=True,  # Safety rule: human approval always required
        )
        db.add(setting)
    else:
        setting.is_enabled = payload.is_enabled
        if payload.schedule_time:
            setting.schedule_time = payload.schedule_time.strip()
        if payload.timezone:
            setting.timezone = payload.timezone.strip()
        if payload.auto_publish is not None:
            setting.auto_publish = payload.auto_publish
        setting.next_run_at = compute_next_run(setting.schedule_time, setting.timezone)
        setting.focus_areas = json.dumps(payload.focus_areas)
        setting.target_branch_prefix = payload.target_branch_prefix.strip()
        setting.auto_test = payload.auto_test

    db.commit()
    db.refresh(setting)
    return _setting_response(setting, repo)


@router.patch("/settings/{setting_id}", response_model=AutomationSettingResponse)
async def update_automation_setting(
    setting_id: int,
    payload: AutomationSettingUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> AutomationSettingResponse:
    """Update automation settings (schedule, enabled toggle, focus areas)."""
    setting = db.get(AutomationSetting, setting_id)
    if not setting or setting.user_id != user.id:
        raise HTTPException(status_code=404, detail="Automation setting not found.")

    if payload.is_enabled is not None:
        setting.is_enabled = payload.is_enabled
    if payload.schedule_time is not None:
        setting.schedule_time = payload.schedule_time.strip()
    if payload.timezone is not None:
        setting.timezone = payload.timezone.strip()
    if payload.auto_publish is not None:
        setting.auto_publish = payload.auto_publish
    if payload.schedule_time is not None or payload.timezone is not None:
        setting.next_run_at = compute_next_run(setting.schedule_time, setting.timezone)
    if payload.focus_areas is not None:
        setting.focus_areas = json.dumps(payload.focus_areas)
    if payload.target_branch_prefix is not None:
        setting.target_branch_prefix = payload.target_branch_prefix.strip()
    if payload.auto_test is not None:
        setting.auto_test = payload.auto_test

    db.commit()
    db.refresh(setting)
    repo = db.get(RepositoryConnection, setting.repository_connection_id)
    return _setting_response(setting, repo)


@router.post("/settings/{setting_id}/toggle", response_model=AutomationSettingResponse)
async def toggle_automation_setting(
    setting_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> AutomationSettingResponse:
    """Quickly toggle System B daily automation on or off."""
    setting = db.get(AutomationSetting, setting_id)
    if not setting or setting.user_id != user.id:
        raise HTTPException(status_code=404, detail="Automation setting not found.")

    setting.is_enabled = not setting.is_enabled
    db.commit()
    db.refresh(setting)
    repo = db.get(RepositoryConnection, setting.repository_connection_id)
    return _setting_response(setting, repo)


@router.post("/settings/{setting_id}/run", response_model=AutomationRunResponse)
async def trigger_automation_by_setting(
    setting_id: int,
    payload: AutomationTriggerRequest = AutomationTriggerRequest(),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> AutomationRunResponse:
    """Manually trigger System B Daily Automation for an automation setting."""
    setting = db.get(AutomationSetting, setting_id)
    if not setting or setting.user_id != user.id:
        raise HTTPException(status_code=404, detail="Automation setting not found.")

    repo = db.get(RepositoryConnection, setting.repository_connection_id)
    if not repo or repo.user_id != user.id:
        raise HTTPException(status_code=404, detail="Connected repository not found.")

    try:
        run = await execute_daily_ai_automation(
            repo=repo,
            user=user,
            db=db,
            setting=setting,
            focus_override=payload.focus_area,
        )
        return _run_response(run, repo)
    except Exception as exc:
        logger.exception("Daily AI Automation execution failed")
        raise HTTPException(status_code=500, detail=f"Automation execution failed: {str(exc)}") from exc


@router.post("/run/{repository_id}", response_model=AutomationRunResponse)
async def trigger_automation_now(
    repository_id: int,
    payload: AutomationTriggerRequest = AutomationTriggerRequest(),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> AutomationRunResponse:
    """Manually trigger System B Daily Automation for a repository."""
    repo = db.scalar(
        select(RepositoryConnection).where(
            (
                (RepositoryConnection.id == repository_id)
                | (RepositoryConnection.github_repository_id == repository_id)
            ),
            RepositoryConnection.user_id == user.id,
        )
    )
    if not repo:
        raise HTTPException(status_code=404, detail="Connected repository not found.")

    setting = db.scalar(
        select(AutomationSetting).where(
            AutomationSetting.user_id == user.id,
            AutomationSetting.repository_connection_id == repo.id,
        )
    )

    try:
        run = await execute_daily_ai_automation(
            repo=repo,
            user=user,
            db=db,
            setting=setting,
            focus_override=payload.focus_area,
        )
        return _run_response(run, repo)
    except Exception as exc:
        logger.exception("Daily AI Automation execution failed")
        raise HTTPException(status_code=500, detail=f"Automation execution failed: {str(exc)}") from exc


@router.get("/runs", response_model=list[AutomationRunResponse])
async def list_automation_runs(
    repository_id: int | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> list[AutomationRunResponse]:
    """List historical System B automation runs."""
    query = select(AutomationRun).where(AutomationRun.user_id == user.id)
    if repository_id:
        query = query.where(AutomationRun.repository_connection_id == repository_id)
    runs = db.scalars(query.order_by(AutomationRun.created_at.desc()).limit(limit)).all()
    results: list[AutomationRunResponse] = []
    for r in runs:
        repo = db.get(RepositoryConnection, r.repository_connection_id)
        results.append(_run_response(r, repo))
    return results


@router.get("/runs/{run_id}", response_model=AutomationRunResponse)
async def get_automation_run(
    run_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> AutomationRunResponse:
    """Get full details and logs of an automation run."""
    run = db.get(AutomationRun, run_id)
    if not run or run.user_id != user.id:
        raise HTTPException(status_code=404, detail="Automation run not found.")
    repo = db.get(RepositoryConnection, run.repository_connection_id)
    return _run_response(run, repo)


@router.post("/runs/{run_id}/approve-publish", response_model=AutomationRunResponse)
@router.post("/runs/{run_id}/approve-and-publish", response_model=AutomationRunResponse)
async def approve_and_publish(
    run_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> AutomationRunResponse:
    """Human approval: publish approved candidate commit to dedicated branch and open GitHub PR."""
    run = db.get(AutomationRun, run_id)
    if not run or run.user_id != user.id:
        raise HTTPException(status_code=404, detail="Automation run not found.")

    try:
        updated_run = await approve_and_publish_automation_run(run_id=run.id, user=user, db=db)
        repo = db.get(RepositoryConnection, updated_run.repository_connection_id)
        return _run_response(updated_run, repo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except GitHubError as exc:
        logger.warning("GitHub error during PR publishing: %s", exc.message)
        raise HTTPException(status_code=exc.status_code, detail=f"GitHub publishing failed: {exc.message}") from exc
    except Exception as exc:
        logger.exception("Error during PR publishing")
        raise HTTPException(status_code=502, detail=f"GitHub publishing failed: {str(exc)}") from exc

