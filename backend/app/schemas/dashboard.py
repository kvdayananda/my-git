from datetime import datetime
from pydantic import BaseModel


class DashboardStats(BaseModel):
    connected_repositories: int
    tasks_executed: int
    pending_reviews: int
    successful_releases: int
    active_analyses: int


class ActivityEvent(BaseModel):
    id: int
    task_id: int
    event_type: str
    details: dict[str, object]
    created_at: datetime
    repository_name: str | None = None
    repository_owner: str | None = None


class SystemStatus(BaseModel):
    app_name: str
    app_env: str
    github_configured: bool
    openai_configured: bool
    openai_model: str
    sandbox_image: str
    database_type: str
    sandbox_available: bool

