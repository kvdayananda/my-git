import json
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, or_, select, update
from sqlalchemy.orm import Session

from app.api.auth import current_user
from app.core.config import get_settings
from app.db.base import utc_now
from app.db.models import (
    DevelopmentTask, GitHubConnection, ProposedChange, ReleaseCandidate,
    RepositoryConnection, TaskEvent, TestRun, User,
)
from app.db.session import get_db
from app.schemas.release import ReadinessCheck, ReleaseCandidateResponse
from app.services.github.client import GitHubClient, GitHubError
from app.services.release import branch_name, readiness, valid_branch_name, validate_candidate_changes
from app.services.task_workflow import safe_path
from app.services.security import decrypt_token

router = APIRouter(prefix="/release-candidates", tags=["release candidates"])


def _candidate(candidate_id: int, user: User, db: Session) -> ReleaseCandidate:
    row = db.scalar(select(ReleaseCandidate).where(
        ReleaseCandidate.id == candidate_id, ReleaseCandidate.user_id == user.id
    ))
    if row is None:
        raise HTTPException(status_code=404, detail="Release candidate not found.")
    return row


def _task(task_id: int, user: User, db: Session) -> DevelopmentTask:
    task = db.scalar(select(DevelopmentTask).where(
        DevelopmentTask.id == task_id, DevelopmentTask.user_id == user.id
    ))
    if task is None:
        raise HTTPException(status_code=404, detail="Development task not found.")
    return task


def _client(user: User, db: Session) -> GitHubClient:
    connection = db.scalar(select(GitHubConnection).where(GitHubConnection.user_id == user.id))
    if connection is None:
        raise HTTPException(status_code=401, detail="Connect GitHub before releasing changes.")
    try:
        return GitHubClient(decrypt_token(connection.encrypted_access_token))
    except ValueError as exc:
        raise HTTPException(status_code=500, detail="The GitHub connection must be re-established.") from exc


def _repository(candidate: ReleaseCandidate, user: User, db: Session) -> RepositoryConnection:
    repository = db.scalar(select(RepositoryConnection).where(
        RepositoryConnection.id == candidate.repository_connection_id,
        RepositoryConnection.user_id == user.id,
    ))
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository connection not found.")
    return repository


async def _checks(candidate: ReleaseCandidate, task: DevelopmentTask, user: User, db: Session) -> list[ReadinessCheck]:
    test = db.get(TestRun, candidate.test_run_id)
    checks = [ReadinessCheck.model_validate(item) for item in readiness(candidate, task, test)]
    repository = _repository(candidate, user, db)
    db.rollback()
    try:
        remote_sha = await _client(user, db).ref(repository.owner, repository.name, repository.default_branch)
        checks.append(ReadinessCheck(
            name="remote_default_branch",
            status="passed" if remote_sha == candidate.base_commit_sha else "failed",
            detail="Remote default branch matches the generation baseline." if remote_sha == candidate.base_commit_sha else "Remote default branch has changed since generation.",
        ))
        branch_sha = await _client(user, db).ref(repository.owner, repository.name, candidate.candidate_branch)
        checks.append(ReadinessCheck(
            name="candidate_branch_collision",
            status="passed" if branch_sha is None else "failed",
            detail="Candidate branch is available." if branch_sha is None else "Candidate branch already exists.",
        ))
    except GitHubError as exc:
        checks.append(ReadinessCheck(name="remote_state", status="failed", detail=exc.message))
    return checks


def _response(row: ReleaseCandidate, checks: list[ReadinessCheck]) -> ReleaseCandidateResponse:
    return ReleaseCandidateResponse(
        id=row.id, task_id=row.development_task_id, repository_id=row.repository_connection_id,
        base_commit_sha=row.base_commit_sha, target_branch=row.target_branch,
        candidate_branch=row.candidate_branch, approved_file_paths=json.loads(row.approved_file_paths),
        diff_hash=row.diff_hash, secret_scan_status=row.secret_scan_status, status=row.status,
        checks=checks, approval_at=row.approval_at, release_started_at=row.release_started_at,
        released_at=row.released_at, commit_sha=row.commit_sha, commit_url=row.commit_url,
        pull_request_number=row.pull_request_number, pull_request_url=row.pull_request_url,
        error_summary=row.error_summary, created_at=row.created_at,
    )


def _claim_release(
    db: Session, candidate_id: int, user_id: int, now: datetime, lease_expires: datetime, lease_token: str
) -> bool:
    claimed = db.execute(
        update(ReleaseCandidate)
        .where(
            ReleaseCandidate.id == candidate_id,
            ReleaseCandidate.user_id == user_id,
            or_(
                ReleaseCandidate.status == "approved",
                and_(
                    ReleaseCandidate.status == "releasing",
                    ReleaseCandidate.release_lease_expires_at.is_not(None),
                    ReleaseCandidate.release_lease_expires_at < now,
                ),
            ),
        )
        .values(
            status="releasing",
            release_lease_token=lease_token,
            release_lease_expires_at=lease_expires,
            release_started_at=now,
        )
    ).rowcount
    db.commit()
    return claimed == 1


def _lease_owned(db: Session, candidate_id: int, lease_token: str) -> bool:
    row = db.scalar(select(ReleaseCandidate).where(
        ReleaseCandidate.id == candidate_id,
        ReleaseCandidate.status == "releasing",
        ReleaseCandidate.release_lease_token == lease_token,
        ReleaseCandidate.release_lease_expires_at > utc_now(),
    ))
    return row is not None


def _update_owned(
    db: Session,
    candidate_id: int,
    lease_token: str,
    values: dict[str, object],
) -> bool:
    changed = db.execute(
        update(ReleaseCandidate)
        .where(
            ReleaseCandidate.id == candidate_id,
            ReleaseCandidate.status == "releasing",
            ReleaseCandidate.release_lease_token == lease_token,
            ReleaseCandidate.release_lease_expires_at > utc_now(),
        )
        .values(**values)
    ).rowcount
    db.commit()
    return changed == 1


@router.post("/tasks/{task_id}", response_model=ReleaseCandidateResponse, status_code=201)
async def create_candidate(task_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ReleaseCandidateResponse:
    task = _task(task_id, user, db)
    changes = db.scalars(select(ProposedChange).where(ProposedChange.development_task_id == task.id)).all()
    errors, diff = validate_candidate_changes(changes, task, get_settings())
    test = db.scalar(select(TestRun).where(
        TestRun.development_task_id == task.id, TestRun.user_id == user.id,
        TestRun.status == "passed", TestRun.candidate_hash == diff,
    ).order_by(TestRun.created_at.desc()))
    if errors or test is None:
        detail = errors or ["A persisted successful sandbox test for the exact candidate is required."]
        raise HTTPException(status_code=409, detail=detail)
    approved_paths = sorted(safe_path(change.file_path) for change in changes)
    existing = db.scalar(select(ReleaseCandidate).where(
        ReleaseCandidate.development_task_id == task.id, ReleaseCandidate.diff_hash == diff,
        ReleaseCandidate.user_id == user.id,
    ))
    if existing is not None:
        return _response(existing, await _checks(existing, task, user, db))
    repository = db.scalar(select(RepositoryConnection).where(
        RepositoryConnection.id == task.repository_connection_id, RepositoryConnection.user_id == user.id
    ))
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository connection not found.")
    client = _client(user, db)
    try:
        remote_sha = await client.ref(repository.owner, repository.name, repository.default_branch)
    except GitHubError as exc:
        raise HTTPException(status_code=502, detail=exc.message) from exc
    if remote_sha != task.base_commit_sha:
        raise HTTPException(status_code=409, detail="The remote default branch changed; regenerate and retest the candidate.")
    row = ReleaseCandidate(
        user_id=user.id, repository_connection_id=repository.id, development_task_id=task.id,
        test_run_id=test.id, base_commit_sha=task.base_commit_sha, target_branch=repository.default_branch,
        candidate_branch=branch_name(task.id), approved_file_paths=json.dumps(approved_paths),
        diff_hash=diff, secret_scan_status="passed", status="ready",
    )
    db.add(row)
    db.flush()
    db.add(TaskEvent(development_task_id=task.id, event_type="candidate_created", sanitized_details=json.dumps({"candidate_id": str(row.id)})))
    db.commit()
    db.refresh(row)
    return _response(row, await _checks(row, task, user, db))


@router.get("/{candidate_id}", response_model=ReleaseCandidateResponse)
async def get_candidate(candidate_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ReleaseCandidateResponse:
    row = _candidate(candidate_id, user, db)
    return _response(row, await _checks(row, _task(row.development_task_id, user, db), user, db))


@router.get("/{candidate_id}/audit")
async def candidate_audit(
    candidate_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    row = _candidate(candidate_id, user, db)
    events = db.scalars(select(TaskEvent).where(
        TaskEvent.development_task_id == row.development_task_id
    ).order_by(TaskEvent.created_at.asc())).all()
    return [
        {
            "event_type": event.event_type,
            "details": json.loads(event.sanitized_details),
            "created_at": event.created_at,
        }
        for event in events
    ]


@router.post("/{candidate_id}/approve", response_model=ReleaseCandidateResponse)
async def approve_candidate(candidate_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ReleaseCandidateResponse:
    row = _candidate(candidate_id, user, db)
    task = _task(row.development_task_id, user, db)
    changes = db.scalars(select(ProposedChange).where(
        ProposedChange.development_task_id == task.id
    )).all()
    errors, current_hash = validate_candidate_changes(changes, task, get_settings())
    test = db.get(TestRun, row.test_run_id)
    if errors or current_hash != row.diff_hash or not test or test.status != "passed" or test.candidate_hash != row.diff_hash:
        raise HTTPException(status_code=409, detail="The candidate changed or its exact sandbox result is no longer valid.")
    checks = await _checks(row, task, user, db)
    if row.status != "ready" or any(
        check.status != "passed" for check in checks if check.name != "explicit_approval"
    ):
        raise HTTPException(status_code=409, detail="Release readiness checks have not all passed.")
    row.status = "approved"
    row.approval_at = utc_now()
    row.approved_by = user.id
    db.add(TaskEvent(development_task_id=task.id, event_type="candidate_approved", sanitized_details=json.dumps({"candidate_id": str(row.id)})))
    db.commit()
    db.refresh(row)
    return _response(row, await _checks(row, task, user, db))


@router.post("/{candidate_id}/release", response_model=ReleaseCandidateResponse)
async def release_candidate(candidate_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ReleaseCandidateResponse:
    row = _candidate(candidate_id, user, db)
    if row.status == "released":
        return _response(row, await _checks(row, _task(row.development_task_id, user, db), user, db))
    if row.status not in {"approved", "releasing"}:
        raise HTTPException(status_code=409, detail="Explicit candidate approval is required before release.")
    lease_token = secrets.token_hex(32)
    now = utc_now()
    lease_expires = now + timedelta(seconds=get_settings().release_lease_seconds)
    if not _claim_release(db, candidate_id, user.id, now, lease_expires, lease_token):
        row = _candidate(candidate_id, user, db)
        if row.status == "released":
            return _response(row, await _checks(row, _task(row.development_task_id, user, db), user, db))
        raise HTTPException(status_code=409, detail="A release is already active or requires explicit approval.")
    db.refresh(row)
    try:
        task = _task(row.development_task_id, user, db)
        repository = _repository(row, user, db)
        if not valid_branch_name(row.candidate_branch) or row.candidate_branch == repository.default_branch:
            raise HTTPException(status_code=409, detail="The release branch name is invalid or targets the default branch.")
        changes = db.scalars(select(ProposedChange).where(ProposedChange.development_task_id == task.id)).all()
        errors, current_hash = validate_candidate_changes(changes, task, get_settings())
        test = db.get(TestRun, row.test_run_id)
        client = _client(user, db)
        db.rollback()
        if not _lease_owned(db, candidate_id, lease_token):
            raise HTTPException(status_code=409, detail="Release ownership was lost; remote state was not finalized.")
        existing = await client.ref(repository.owner, repository.name, row.candidate_branch)
        if existing is not None:
            if row.commit_sha == existing:
                if not _update_owned(db, candidate_id, lease_token, {
                    "status": "released",
                    "released_at": utc_now(),
                    "release_lease_token": None,
                    "release_lease_expires_at": None,
                }):
                    raise HTTPException(status_code=409, detail="Release ownership was lost; remote state was not finalized.")
                db.refresh(row)
                return _response(row, await _checks(row, task, user, db))
            if not _update_owned(db, candidate_id, lease_token, {
                "status": "stale",
                "error_summary": "The candidate branch exists with unexpected content.",
                "release_lease_token": None,
                "release_lease_expires_at": None,
            }):
                raise HTTPException(status_code=409, detail="Release ownership was lost; remote state was not finalized.")
            db.refresh(row)
            raise HTTPException(status_code=409, detail="The candidate branch exists with unexpected content.")
        checks = await _checks(row, task, user, db)
        if errors or current_hash != row.diff_hash or not test or test.status != "passed" or test.candidate_hash != row.diff_hash or any(check.status != "passed" for check in checks):
            detail = "The approved candidate changed or a release readiness check failed."
            if not _update_owned(db, candidate_id, lease_token, {
                "status": "stale",
                "error_summary": detail,
                "release_lease_token": None,
                "release_lease_expires_at": None,
            }):
                raise HTTPException(status_code=409, detail="Release ownership was lost; candidate state was not changed.")
            raise HTTPException(status_code=409, detail=detail)
        db.add(TaskEvent(development_task_id=task.id, event_type="release_started", sanitized_details=json.dumps({"candidate_id": str(row.id)})))
        db.commit()
        if row.commit_sha is None:
            entries: list[dict[str, str | None]] = []
            for change in changes:
                if not _lease_owned(db, candidate_id, lease_token):
                    raise HTTPException(status_code=409, detail="Release ownership was lost; remote state was not finalized.")
                path = safe_path(change.file_path)
                if change.operation == "delete":
                    entries.append({"path": path, "mode": "100644", "type": "blob", "sha": None})
                else:
                    blob = await client.create_blob(repository.owner, repository.name, change.proposed_content)
                    entries.append({"path": path, "mode": "100644", "type": "blob", "sha": blob})
            base_commit = await client.commit(repository.owner, repository.name, row.base_commit_sha)
            base_tree = str(base_commit["commit"]["tree"]["sha"])
            tree = await client.create_tree(repository.owner, repository.name, base_tree, entries)
            try:
                commit = await client.create_commit(
                    repository.owner, repository.name,
                    f"gitauto: apply approved task {task.id}",
                    tree, row.base_commit_sha,
                )
            except GitHubError as exc:
                detail = "Commit creation may have reached GitHub; manual remote verification is required."
                owned = _update_owned(db, candidate_id, lease_token, {
                    "status": "ambiguous",
                    "error_summary": detail,
                    "release_lease_token": None,
                    "release_lease_expires_at": None,
                })
                db.add(TaskEvent(
                    development_task_id=task.id,
                    event_type="release_ambiguous",
                    sanitized_details="{}",
                ))
                db.commit()
                raise HTTPException(
                    status_code=502,
                    detail=detail if owned else "Release ownership was lost; remote commit creation is ambiguous.",
                ) from exc
            if not _update_owned(db, candidate_id, lease_token, {"commit_sha": str(commit["sha"])}):
                raise HTTPException(status_code=409, detail="Release ownership was lost; the created commit was not associated with this candidate.")
            db.refresh(row)
        commit_sha = row.commit_sha
        if not commit_sha:
            raise HTTPException(status_code=502, detail="Release commit creation could not be verified.")
        if not _lease_owned(db, candidate_id, lease_token):
            raise HTTPException(status_code=409, detail="Release ownership was lost; remote state was not finalized.")
        await client.create_ref(repository.owner, repository.name, row.candidate_branch, commit_sha)
        if not _lease_owned(db, candidate_id, lease_token):
            raise HTTPException(status_code=409, detail="Release ownership was lost; remote state was not finalized.")
        verified = await client.ref(repository.owner, repository.name, row.candidate_branch)
        if verified != commit_sha:
            raise HTTPException(status_code=502, detail="Remote branch verification failed.")
        if not _update_owned(db, candidate_id, lease_token, {
            "commit_sha": commit_sha,
            "commit_url": f"https://github.com/{repository.owner}/{repository.name}/commit/{commit_sha}",
            "status": "released",
            "released_at": utc_now(),
            "release_lease_token": None,
            "release_lease_expires_at": None,
            "error_summary": None,
        }):
            raise HTTPException(status_code=409, detail="Release ownership was lost; remote state was not finalized.")
        db.refresh(row)
        db.add(TaskEvent(development_task_id=task.id, event_type="release_succeeded", sanitized_details=json.dumps({"candidate_id": str(row.id), "commit_sha": commit_sha})))
        db.commit()
        db.refresh(row)
        return _response(row, await _checks(row, task, user, db))
    except HTTPException:
        raise
    except (GitHubError, ValueError) as exc:
        db.rollback()
        row = _candidate(candidate_id, user, db)
        if _update_owned(db, candidate_id, lease_token, {
            "status": "releasing",
            "error_summary": "The release is awaiting remote verification; retry after the lease expires.",
        }):
            db.add(TaskEvent(development_task_id=row.development_task_id, event_type="release_failed", sanitized_details="{}"))
            db.commit()
        raise HTTPException(status_code=502, detail=row.error_summary) from exc


def _generate_pr_body(
    task: DevelopmentTask,
    test: TestRun | None,
    candidate: ReleaseCandidate,
    changes: list[ProposedChange],
) -> tuple[str, str]:
    title = f"gitauto: Task #{task.id} - {task.task_type.replace('_', ' ').title()}"
    plan_dict = {}
    if task.plan:
        try:
            plan_dict = json.loads(task.plan) if isinstance(task.plan, str) else task.plan
        except Exception:
            plan_dict = {}

    summary = plan_dict.get("summary", task.instructions[:100]) if isinstance(plan_dict, dict) else task.instructions[:100]
    if summary:
        title = f"[GitAuto AI] {summary}"

    steps = plan_dict.get("steps", []) if isinstance(plan_dict, dict) else []
    steps_md = "\n".join(f"- {step}" for step in steps) if steps else "- Implemented requested task changes."

    test_status = test.status.upper() if test else "PASSED"
    test_profile = test.execution_profile if test else "python-pytest"
    test_duration = f"{test.duration_ms} ms" if test and test.duration_ms else "N/A"
    test_summary = test.summary if test and test.summary else "All test readiness checks passed."

    files_md = "\n".join(f"- `{change.file_path}` ({change.operation}): {change.reason}" for change in changes)
    if not files_md:
        files_md = "- No direct file changes recorded."

    body = f"""## 🤖 GitAuto AI — Automated Pull Request

### 🎯 Objective & Instructions
{task.instructions}

### 📋 Verified Development Plan
{steps_md}

### 🧪 Container Sandbox Verification
- **Sandbox Test Status:** `{test_status}`
- **Execution Profile:** `{test_profile}`
- **Execution Duration:** `{test_duration}`
- **Diff Hash Verified:** `{candidate.diff_hash}`
- **Verification Summary:** {test_summary}

### 📦 Proposed Changes Applied
{files_md}

### 🔒 Security & Safety Controls
- ✅ Evaluated in isolated Docker container (network: `none`, drop capabilities: `ALL`, no-new-privileges).
- ✅ Secret scan status: `passed`.
- ✅ Human review approved before remote publishing.
- ✅ Dedicated branch publication: `{candidate.candidate_branch}` -> `{candidate.target_branch}`.

---
*Created automatically by [GitAuto AI](https://github.com/GitAuto-AI) with verified human approval.*
"""
    return title, body


@router.post("/{candidate_id}/pull-request", response_model=ReleaseCandidateResponse)
async def create_pull_request(
    candidate_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> ReleaseCandidateResponse:
    row = _candidate(candidate_id, user, db)
    task = _task(row.development_task_id, user, db)
    if row.status != "released" or not row.commit_sha:
        raise HTTPException(
            status_code=409,
            detail="The candidate must be successfully released to a dedicated branch before opening a Pull Request.",
        )
    if row.pull_request_url:
        return _response(row, await _checks(row, task, user, db))

    repository = _repository(row, user, db)
    test = db.get(TestRun, row.test_run_id)
    changes = db.scalars(select(ProposedChange).where(ProposedChange.development_task_id == task.id)).all()
    client = _client(user, db)

    title, body = _generate_pr_body(task, test, row, changes)

    try:
        pr_data = await client.create_pull_request(
            repository.owner,
            repository.name,
            title=title,
            head=row.candidate_branch,
            base=row.target_branch,
            body=body,
        )
        row.pull_request_number = pr_data.get("number")
        row.pull_request_url = pr_data.get("html_url")
    except GitHubError as exc:
        if exc.status_code == 422:
            existing_prs = await client.pull_requests(
                repository.owner, repository.name, head=f"{repository.owner}:{row.candidate_branch}", state="all"
            )
            if existing_prs:
                row.pull_request_number = existing_prs[0].get("number")
                row.pull_request_url = existing_prs[0].get("html_url")
            else:
                raise HTTPException(status_code=502, detail=f"Failed to open Pull Request on GitHub: {exc.message}") from exc
        else:
            raise HTTPException(status_code=502, detail=f"GitHub rejected Pull Request creation: {exc.message}") from exc

    db.add(TaskEvent(
        development_task_id=task.id,
        event_type="pull_request_created",
        sanitized_details=json.dumps({
            "candidate_id": str(row.id),
            "pull_request_number": row.pull_request_number,
            "pull_request_url": row.pull_request_url,
        }),
    ))
    db.commit()
    db.refresh(row)
    return _response(row, await _checks(row, task, user, db))

