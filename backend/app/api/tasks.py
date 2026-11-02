import json
import os
import secrets
import difflib
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import current_user
from app.core.config import get_settings
from app.db.base import utc_now
from app.db.models import Analysis, DevelopmentTask, ProposedChange, RepositoryConnection, TaskEvent, User, GitHubConnection
from app.db.session import get_db
from app.schemas.task import Plan, RevisionRequest, TaskCreate, TaskResponse
from app.services.code_generation import GenerationError, apply_changes, generate_changes
from app.services.task_workflow import validate_change, validate_plan_paths
from app.services.github.client import GitHubClient, GitHubError
from app.services.security import decrypt_token

router = APIRouter(prefix="/development-tasks", tags=["development tasks"])
_generation_locks: set[int] = set()


def _task(task_id: int, user: User, db: Session) -> DevelopmentTask:
    task = db.scalar(select(DevelopmentTask).where(DevelopmentTask.id == task_id, DevelopmentTask.user_id == user.id))
    if task is None:
        raise HTTPException(status_code=404, detail="Development task not found.")
    return task


def _response(task: DevelopmentTask, db: Session) -> TaskResponse:
    plan = Plan.model_validate_json(task.plan) if task.plan != "{}" else None
    changes = db.scalars(select(ProposedChange).where(ProposedChange.development_task_id == task.id)).all()
    return TaskResponse(
        id=task.id, repository_id=task.repository_connection_id, base_commit_sha=task.base_commit_sha,
        task_type=task.task_type, instructions=task.instructions, status=task.status, plan=plan,
        validation_results=json.loads(task.validation_results), test_results=json.loads(task.test_results),
        token_usage=task.token_usage,
        error_summary=task.error_summary, changes=changes, created_at=task.created_at,
        completed_at=task.completed_at,
    )


def _event(task: DevelopmentTask, event_type: str, db: Session, details: dict[str, str] | None = None) -> None:
    db.add(TaskEvent(development_task_id=task.id, event_type=event_type, sanitized_details=json.dumps(details or {})))


@router.post("/repositories/{repository_id}", response_model=TaskResponse, status_code=201)
async def create_task(repository_id: int, payload: TaskCreate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> TaskResponse:
    repository = db.scalar(select(RepositoryConnection).where(
        RepositoryConnection.user_id == user.id, RepositoryConnection.github_repository_id == repository_id
    ))
    if repository is None:
        raise HTTPException(status_code=404, detail="Connect this repository before creating a task.")
    analysis = db.scalar(select(Analysis).where(
        Analysis.user_id == user.id, Analysis.repository_connection_id == repository.id
    ).order_by(Analysis.created_at.desc()))
    if analysis is None:
        raise HTTPException(status_code=409, detail="Run a repository analysis before creating a development task.")
    root = Path(get_settings().workspace_root).resolve() / str(user.id) / secrets.token_hex(16)
    root.mkdir(parents=True, exist_ok=False)
    task = DevelopmentTask(
        user_id=user.id, repository_connection_id=repository.id, base_commit_sha=analysis.commit_sha,
        task_type=payload.task_type, instructions=payload.instructions, status="planning",
        workspace_path=os.fspath(root), plan="{}", validation_results="[]", test_results="[]",
    )
    db.add(task)
    db.flush()
    _event(task, "created", db)
    db.commit()
    db.refresh(task)
    return _response(task, db)


@router.get("", response_model=list[TaskResponse])
async def list_tasks(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[TaskResponse]:
    return [_response(task, db) for task in db.scalars(
        select(DevelopmentTask).where(DevelopmentTask.user_id == user.id).order_by(DevelopmentTask.created_at.desc())
    ).all()]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> TaskResponse:
    return _response(_task(task_id, user, db), db)


@router.post("/{task_id}/plan", response_model=TaskResponse)
async def create_plan(task_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> TaskResponse:
    task = _task(task_id, user, db)
    if task.status not in {"planning", "revision_requested"}:
        raise HTTPException(status_code=409, detail="This task cannot be planned in its current state.")
    plan = Plan(
        summary=f"Plan for {task.task_type.replace('_', ' ')}",
        objective=task.instructions,
        files_to_create=[], files_to_modify=[], steps=["Review relevant files", "Implement the approved change", "Run safe validation"],
        expected_behavior="The requested behavior is implemented without unrelated repository changes.",
        acceptance_criteria=["Only approved files are changed", "Validation reports no prohibited content."],
        testing_strategy="Run project-specific tests only after sandbox infrastructure is configured.",
        risks=["No code generation is performed until the plan is explicitly approved."],
    )
    errors = validate_plan_paths(plan.model_dump(), get_settings())
    if errors:
        task.status = "failed"
        task.error_summary = "; ".join(errors)
    else:
        task.plan = plan.model_dump_json()
        task.status = "awaiting_plan_approval"
        _event(task, "plan_created", db)
    db.commit()
    return _response(task, db)


@router.post("/{task_id}/plan/approve", response_model=TaskResponse)
async def approve_plan(task_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> TaskResponse:
    task = _task(task_id, user, db)
    if task.status != "awaiting_plan_approval":
        raise HTTPException(status_code=409, detail="Only plans awaiting approval can be approved.")
    task.status = "generating"
    _event(task, "plan_approved", db)
    db.commit()
    return _response(task, db)


@router.post("/{task_id}/generate", response_model=TaskResponse)
async def generate_task(task_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> TaskResponse:
    task = _task(task_id, user, db)
    if task.status != "generating":
        raise HTTPException(status_code=409, detail="Approve the plan before generation.")
    if task_id in _generation_locks:
        raise HTTPException(status_code=409, detail="Generation is already active for this task.")
    _generation_locks.add(task_id)
    repository = db.get(RepositoryConnection, task.repository_connection_id)
    github = db.scalar(select(GitHubConnection).where(GitHubConnection.user_id == user.id))
    try:
        if repository is None or github is None:
            task.status = "failed"
            task.error_summary = "The repository authorization context is unavailable."
            _event(task, "generation_failed", db)
            db.commit()
            return _response(task, db)
        try:
            plan = Plan.model_validate_json(task.plan)
            client = GitHubClient(decrypt_token(github.encrypted_access_token))
            generated, token_usage = await generate_changes(
                client=client,
                owner=repository.owner,
                name=repository.name,
                commit_sha=task.base_commit_sha,
                workspace=Path(task.workspace_path).resolve(),
                plan=plan,
                instructions=task.instructions,
                settings=get_settings(),
            )
            apply_changes(Path(task.workspace_path).resolve(), generated, get_settings())
            for change in generated.changes:
                db.add(ProposedChange(
                    development_task_id=task.id,
                    file_path=change.file_path,
                    operation=change.operation,
                    reason=change.reason,
                    proposed_content=change.proposed_content,
                    validation_status="passed",
                    review_status="pending",
                ))
            task.token_usage = token_usage
            task.status = "awaiting_review"
            task.validation_results = json.dumps([{"status": "passed", "detail": "Structured changes and protected-path checks passed."}])
            task.test_results = json.dumps([{"status": "not_run", "detail": "Tests are not run by the API process."}])
            task.error_summary = None
            _event(task, "generation_succeeded", db, {"changes": str(len(generated.changes))})
        except (GenerationError, GitHubError, ValueError) as exc:
            db.rollback()
            task = _task(task_id, user, db)
            task.status = "failed"
            task.error_summary = str(exc)
            task.test_results = json.dumps([{"status": "not_run", "detail": "Generation failed before tests could run."}])
            _event(task, "generation_failed", db)
        db.commit()
        db.refresh(task)
        return _response(task, db)
    finally:
        _generation_locks.discard(task_id)


@router.post("/{task_id}/generate/async")
async def generate_task_async(task_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    task = _task(task_id, user, db)
    if task.status != "generating":
        raise HTTPException(status_code=409, detail="Approve the plan before generation.")
    
    from app.workers.tasks import generate_code_task
    job = generate_code_task.delay(task.id, user.id)
    return {"job_id": job.id, "task_id": task.id, "status": "queued"}


@router.get("/{task_id}/changes", response_model=list[dict[str, object]])
async def task_changes(task_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[dict[str, object]]:
    task = _task(task_id, user, db)
    return [
        {
            "id": change.id, "file_path": change.file_path, "operation": change.operation,
            "reason": change.reason, "validation_status": change.validation_status,
            "review_status": change.review_status,
        }
        for change in db.scalars(select(ProposedChange).where(ProposedChange.development_task_id == task.id)).all()
    ]


@router.get("/{task_id}/diff")
async def task_diff(task_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    task = _task(task_id, user, db)
    changes = db.scalars(select(ProposedChange).where(ProposedChange.development_task_id == task.id)).all()
    chunks: list[str] = []
    for change in changes:
        original = [] if change.operation == "create" else ["[original content unavailable]\n"]
        proposed = change.proposed_content.splitlines(keepends=True)
        chunks.extend(difflib.unified_diff(
            original, proposed, fromfile=f"a/{change.file_path}", tofile=f"b/{change.file_path}"
        ))
    return {"task_id": str(task.id), "base_commit_sha": task.base_commit_sha, "diff": "".join(chunks)}


@router.post("/{task_id}/review/{decision}", response_model=TaskResponse)
async def review_task(task_id: int, decision: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> TaskResponse:
    task = _task(task_id, user, db)
    if decision not in {"approve", "reject"} or task.status != "awaiting_review":
        raise HTTPException(status_code=409, detail="This task is not ready for review.")
    task.status = "approved" if decision == "approve" else "rejected"
    task.completed_at = utc_now()
    _event(task, f"review_{decision}", db)
    db.commit()
    return _response(task, db)


@router.post("/{task_id}/revision", response_model=TaskResponse)
async def request_revision(task_id: int, payload: RevisionRequest, user: User = Depends(current_user), db: Session = Depends(get_db)) -> TaskResponse:
    task = _task(task_id, user, db)
    if task.status != "awaiting_review":
        raise HTTPException(status_code=409, detail="Only tasks awaiting review can be revised.")
    task.instructions = payload.instructions
    task.status = "revision_requested"
    _event(task, "revision_requested", db)
    db.commit()
    return _response(task, db)


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(task_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> TaskResponse:
    task = _task(task_id, user, db)
    if task.status in {"approved", "rejected", "cancelled", "failed"}:
        raise HTTPException(status_code=409, detail="This task cannot be cancelled.")
    task.status = "cancelled"
    task.completed_at = utc_now()
    _event(task, "cancelled", db)
    db.commit()
    return _response(task, db)
