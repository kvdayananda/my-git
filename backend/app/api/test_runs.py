import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import current_user
from app.core.config import get_settings
from app.db.base import utc_now
from app.db.models import DevelopmentTask, ProposedChange, TestRun, User
from app.services.release import candidate_hash
from app.db.session import get_db
from app.schemas.test_run import TestProfile, TestRunResponse
from app.services.sandbox_manager import SandboxUnavailable, run_in_sandbox
from app.services.sandbox_policy import available_profiles

router = APIRouter(prefix="", tags=["test runs"])
_running_tasks: set[int] = set()
_secret_log = re.compile(r"(?i)(api[_-]?key|password|secret|token)\s*[:=]\s*\S+")


def _task(task_id: int, user: User, db: Session) -> DevelopmentTask:
    task = db.scalar(select(DevelopmentTask).where(DevelopmentTask.id == task_id, DevelopmentTask.user_id == user.id))
    if task is None:
        raise HTTPException(status_code=404, detail="Development task not found.")
    return task


def _sanitize(value: str, limit: int) -> str:
    return _secret_log.sub(r"\1=[REDACTED]", value[:limit])


def _response(run: TestRun) -> TestRunResponse:
    return TestRunResponse(
        id=run.id, task_id=run.development_task_id, base_commit_sha=run.base_commit_sha,
        candidate_hash=run.candidate_hash,
        execution_profile=run.execution_profile, command_classification=run.command_classification,
        status=run.status, exit_code=run.exit_code, started_at=run.started_at, ended_at=run.ended_at,
        duration_ms=run.duration_ms, timed_out=run.timed_out, resource_violation=run.resource_violation,
        stdout=run.stdout, stderr=run.stderr, summary=run.summary, error_details=run.error_details,
        created_at=run.created_at,
    )


@router.get("/development-tasks/{task_id}/tests/profiles", response_model=list[TestProfile])
async def test_profiles(task_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[TestProfile]:
    task = _task(task_id, user, db)
    return [TestProfile.model_validate(profile) for profile in available_profiles(Path(task.workspace_path), get_settings())]


@router.post("/development-tasks/{task_id}/tests", response_model=TestRunResponse, status_code=201)
async def run_tests(task_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> TestRunResponse:
    task = _task(task_id, user, db)
    if task.status not in {"awaiting_review", "approved"}:
        raise HTTPException(status_code=409, detail="Tests require generated changes awaiting review or approval.")
    if task_id in _running_tasks:
        raise HTTPException(status_code=409, detail="A test run is already active for this task.")
    _running_tasks.add(task_id)
    run = TestRun(
        user_id=user.id, development_task_id=task.id, base_commit_sha=task.base_commit_sha,
        candidate_hash=candidate_hash(
            db.scalars(select(ProposedChange).where(
                ProposedChange.development_task_id == task.id
            )).all(),
            task.base_commit_sha,
        ),
        execution_profile="python-pytest", command_classification="pytest", status="preparing",
        timed_out=False, stdout="", stderr="", summary="", created_at=utc_now(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    try:
        profile = available_profiles(Path(task.workspace_path), get_settings())[0]
        if not profile["available"]:
            run.status = "unavailable"
            run.error_details = str(profile["reason"])
            run.summary = "Sandbox execution is unavailable."
        else:
            run.status = "running"
            db.commit()
            result = await run_in_sandbox(Path(task.workspace_path), "python-pytest", get_settings())
            run.status = str(result["status"])
            run.exit_code = result["exit_code"]  # type: ignore[assignment]
            run.started_at = result["started_at"]  # type: ignore[assignment]
            run.ended_at = result["ended_at"]  # type: ignore[assignment]
            run.duration_ms = result["duration_ms"]  # type: ignore[assignment]
            run.timed_out = bool(result["timed_out"])
            run.stdout = _sanitize(str(result["stdout"]), get_settings().sandbox_output_limit_bytes)
            run.stderr = _sanitize(str(result["stderr"]), get_settings().sandbox_output_limit_bytes)
            run.summary = str(result["summary"])
    except SandboxUnavailable as exc:
        run.status = "unavailable"
        run.error_details = str(exc)
        run.summary = "Sandbox execution is unavailable."
    except (OSError, ValueError) as exc:
        run.status = "infrastructure_error"
        run.error_details = str(exc)
        run.summary = "Sandbox infrastructure failed."
    finally:
        db.commit()
        db.refresh(run)
        _running_tasks.discard(task_id)
    return _response(run)


@router.post("/development-tasks/{task_id}/tests/async", status_code=201)
async def run_tests_async(task_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    task = _task(task_id, user, db)
    if task.status not in {"awaiting_review", "approved"}:
        raise HTTPException(status_code=409, detail="Tests require generated changes awaiting review or approval.")
    if task_id in _running_tasks:
        raise HTTPException(status_code=409, detail="A test run is already active for this task.")

    run = TestRun(
        user_id=user.id, development_task_id=task.id, base_commit_sha=task.base_commit_sha,
        candidate_hash=candidate_hash(
            db.scalars(select(ProposedChange).where(
                ProposedChange.development_task_id == task.id
            )).all(),
            task.base_commit_sha,
        ),
        execution_profile="python-pytest", command_classification="pytest", status="queued",
        timed_out=False, stdout="", stderr="", summary="", created_at=utc_now(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    from app.workers.tasks import run_sandbox_test_task
    job = run_sandbox_test_task.delay(run.id, user.id)
    return {"job_id": job.id, "test_run_id": run.id, "status": "queued"}


@router.get("/development-tasks/{task_id}/tests/latest", response_model=TestRunResponse)
async def latest_test(task_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> TestRunResponse:
    _task(task_id, user, db)
    run = db.scalar(select(TestRun).where(
        TestRun.development_task_id == task_id, TestRun.user_id == user.id
    ).order_by(TestRun.created_at.desc()))
    if run is None:
        raise HTTPException(status_code=404, detail="No test run exists for this task.")
    return _response(run)


@router.get("/test-runs/{test_run_id}", response_model=TestRunResponse)
async def get_test_run(test_run_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> TestRunResponse:
    run = db.scalar(select(TestRun).where(TestRun.id == test_run_id, TestRun.user_id == user.id))
    if run is None:
        raise HTTPException(status_code=404, detail="Test run not found.")
    return _response(run)


@router.post("/test-runs/{test_run_id}/cancel", response_model=TestRunResponse)
async def cancel_test_run(test_run_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> TestRunResponse:
    run = db.scalar(select(TestRun).where(TestRun.id == test_run_id, TestRun.user_id == user.id))
    if run is None:
        raise HTTPException(status_code=404, detail="Test run not found.")
    if run.status not in {"queued", "preparing", "running"}:
        raise HTTPException(status_code=409, detail="This test run is no longer active.")
    raise HTTPException(
        status_code=409,
        detail="Cancellation is unavailable until the sandbox process handle is available.",
    )
