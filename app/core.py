"""TaskPulse Core Engine."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional


@dataclass
class Job:
    id: str
    name: str
    priority: int = 1
    max_retries: int = 3
    retries_left: int = 3
    status: str = "queued"
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class JobQueue:
    def __init__(self) -> None:
        self.jobs: list[Job] = []

    def enqueue(self, job: Job) -> None:
        self.jobs.append(job)
        self.jobs.sort(key=lambda j: j.priority, reverse=True)

    def pop_next(self) -> Optional[Job]:
        for j in self.jobs:
            if j.status == "queued":
                j.status = "running"
                return j
        return None

    def complete_job(self, job_id: str) -> None:
        for j in self.jobs:
            if j.id == job_id:
                j.status = "succeeded"

    def fail_job(self, job_id: str, error: str) -> None:
        for j in self.jobs:
            if j.id == job_id:
                j.retries_left -= 1
                j.error = error
                if j.retries_left > 0:
                    j.status = "queued"
                else:
                    j.status = "failed"
