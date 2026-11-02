import hashlib
import json
import re
import secrets
from datetime import datetime

from app.db.models import DevelopmentTask, ProposedChange, ReleaseCandidate, TestRun
from app.services.task_workflow import safe_path, validate_change

BRANCH_NAME = re.compile(r"^gitauto/(task|daily)-[a-zA-Z0-9_\.-]+$")
HIGH_CONFIDENCE_SECRET = re.compile(
    r"(?i)(api[_-]?key|password|secret|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]"
)


def candidate_hash(changes: list[ProposedChange], base_commit_sha: str = "") -> str:
    payload = [
        {
            "path": item.file_path,
            "operation": item.operation,
            "reason": item.reason,
            "content": item.proposed_content,
        }
        for item in sorted(changes, key=lambda change: change.file_path)
    ]
    payload.insert(0, {"base_commit_sha": base_commit_sha})
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def branch_name(task_id: int) -> str:
    return f"gitauto/task-{task_id}-{secrets.token_hex(4)}"


def daily_branch_name(task_id: int) -> str:
    today_str = datetime.now().strftime("%Y-%m-%d")
    return f"gitauto/daily-{today_str}-t{task_id}"


def validate_candidate_changes(
    changes: list[ProposedChange], task: DevelopmentTask, settings: object
) -> tuple[list[str], str]:
    errors: list[str] = []
    paths: list[str] = []
    for change in changes:
        try:
            paths.append(safe_path(change.file_path))
        except ValueError as exc:
            errors.append(str(exc))
        errors.extend(validate_change(change.file_path, change.operation, change.proposed_content, settings))
        if change.operation == "delete" and not change.reason.strip():
            errors.append(f"{change.file_path}: delete requires an explicit reason")
        if HIGH_CONFIDENCE_SECRET.search(change.proposed_content):
            errors.append(f"{change.file_path}: unresolved high-confidence secret pattern")
    if not changes:
        errors.append("The task has no proposed changes.")
    if task.status not in {"awaiting_review", "approved"}:
        errors.append("The task is not ready for release review.")
    return sorted(set(errors)), candidate_hash(changes, task.base_commit_sha)


def readiness(candidate: ReleaseCandidate, task: DevelopmentTask, test: TestRun | None) -> list[dict[str, str]]:
    return [
        {"name": "authentication_and_ownership", "status": "passed", "detail": "Candidate is owned by the authenticated user."},
        {"name": "reviewed_diff", "status": "passed" if candidate.diff_hash else "failed", "detail": "A candidate diff hash is recorded."},
        {"name": "base_commit", "status": "passed" if candidate.base_commit_sha else "failed", "detail": "Generation baseline is recorded."},
        {"name": "sandbox_tests", "status": "passed" if test and test.status == "passed" else "failed", "detail": "Exact candidate changes have a persisted passing sandbox run."},
        {"name": "secret_scan", "status": "passed" if candidate.secret_scan_status == "passed" else "failed", "detail": "No unresolved high-confidence secret finding exists."},
        {"name": "explicit_approval", "status": "passed" if candidate.approval_at else "not_run", "detail": "The exact candidate must be explicitly approved."},
    ]


def valid_branch_name(name: str) -> bool:
    return bool(BRANCH_NAME.fullmatch(name))
