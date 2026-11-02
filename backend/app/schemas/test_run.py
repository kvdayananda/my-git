from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class TestRunResponse(BaseModel):
    id: int
    task_id: int
    base_commit_sha: str
    candidate_hash: str
    execution_profile: str
    command_classification: str
    status: Literal[
        "queued", "preparing", "running", "passed", "failed", "timed_out",
        "cancelled", "unavailable", "rejected", "infrastructure_error",
    ]
    exit_code: int | None
    started_at: datetime | None
    ended_at: datetime | None
    duration_ms: int | None
    timed_out: bool
    resource_violation: str | None
    stdout: str
    stderr: str
    summary: str
    error_details: str | None
    created_at: datetime


class TestProfile(BaseModel):
    name: str
    command_classification: str
    available: bool
    reason: str
