from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ReadinessCheck(BaseModel):
    name: str
    status: Literal["passed", "failed", "not_run"]
    detail: str


class ReleaseCandidateResponse(BaseModel):
    id: int
    task_id: int
    repository_id: int
    base_commit_sha: str
    target_branch: str
    candidate_branch: str
    approved_file_paths: list[str]
    diff_hash: str
    secret_scan_status: str
    status: str
    checks: list[ReadinessCheck]
    approval_at: datetime | None
    release_started_at: datetime | None
    released_at: datetime | None
    commit_sha: str | None
    commit_url: str | None
    pull_request_number: int | None = None
    pull_request_url: str | None = None
    error_summary: str | None
    created_at: datetime
