from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, ConfigDict


class RunSummary(BaseModel):
    id: int
    repository_id: int
    repository_name: str
    status: str
    commit_sha: str | None = None
    commit_url: str | None = None
    pull_request_number: int | None = None
    pull_request_url: str | None = None
    commit_message: str | None = None
    lines_added: int = 0
    lines_deleted: int = 0
    files_created_count: int = 0
    files_modified_count: int = 0
    files_deleted_count: int = 0
    speed_target_met: bool | None = None
    publishing_duration_ms: int | None = None
    created_at: datetime
    completed_at: datetime | None = None


class DailyAnalyticsResponse(BaseModel):
    date: str
    runs_count: int
    successful_runs: int
    failed_runs: int
    commits_count: int
    prs_count: int
    lines_added: int
    lines_deleted: int
    files_created_count: int
    files_modified_count: int
    files_deleted_count: int
    speed_target_met_count: int
    avg_publishing_duration_ms: int | None = None
    runs: list[RunSummary] = []


class DayData(BaseModel):
    date: str
    day_name: str
    runs: int
    commits: int
    prs: int
    lines_added: int
    lines_deleted: int


class WeeklyAnalyticsResponse(BaseModel):
    start_date: str
    end_date: str
    total_runs: int
    total_commits: int
    total_prs: int
    total_lines_added: int
    total_lines_deleted: int
    daily_breakdown: list[DayData] = []


class RepoStats(BaseModel):
    repository_id: int
    repository_name: str
    runs: int
    commits: int
    prs: int
    lines_added: int
    lines_deleted: int


class MonthlyAnalyticsResponse(BaseModel):
    year: int
    month: int
    total_runs: int
    total_commits: int
    total_prs: int
    total_lines_added: int
    total_lines_deleted: int
    active_repositories_count: int
    repository_breakdown: list[RepoStats] = []
    daily_breakdown: list[DayData] = []


class LifetimeAnalyticsResponse(BaseModel):
    total_automated_repositories: int
    total_runs: int
    total_successful_runs: int
    total_failed_runs: int
    total_commits: int
    total_prs: int
    total_lines_added: int
    total_lines_deleted: int
    total_lines_changed: int
    success_rate_percent: float
    speed_target_met_count: int
    speed_compliance_percent: float
    avg_publishing_duration_ms: int | None = None
    first_run_date: datetime | None = None
    latest_run_date: datetime | None = None
    repository_breakdown: list[RepoStats] = []

