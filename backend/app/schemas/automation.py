from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AutomationSettingCreate(BaseModel):
    repository_connection_id: int
    is_enabled: bool = True
    schedule_time: str = Field("20:00", max_length=50)
    timezone: str = Field("Asia/Kolkata", max_length=50)
    auto_publish: bool = False
    focus_areas: list[str] = Field(
        default_factory=lambda: ["bug_detection", "documentation", "test_generation", "code_improvements"]
    )
    target_branch_prefix: str = Field("gitauto/daily", max_length=255)
    auto_test: bool = True


class AutomationSettingUpdate(BaseModel):
    is_enabled: bool | None = None
    schedule_time: str | None = None
    timezone: str | None = None
    auto_publish: bool | None = None
    focus_areas: list[str] | None = None
    target_branch_prefix: str | None = None
    auto_test: bool | None = None


class AutomationSettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    repository_connection_id: int
    repository_name: str | None = None
    repository_owner: str | None = None
    default_branch: str | None = None
    is_enabled: bool
    schedule_time: str
    timezone: str
    auto_publish: bool
    next_run_at: datetime | None = None
    max_retries: int
    focus_areas: list[str]
    target_branch_prefix: str
    auto_test: bool
    require_approval: bool
    last_run_at: datetime | None = None
    last_run_status: str | None = None
    created_at: datetime
    updated_at: datetime


class AutomationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    repository_connection_id: int
    repository_name: str | None = None
    analysis_id: int | None = None
    development_task_id: int | None = None
    release_candidate_id: int | None = None
    status: str
    summary: str
    findings_count: int
    changes_count: int
    files_created_count: int = 0
    files_modified_count: int = 0
    files_deleted_count: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    security_result: str = "passed"
    test_result: str = "passed"
    commit_message: str | None = None
    tests_passed: bool | None = None
    target_branch: str | None = None
    commit_sha: str | None = None
    commit_url: str | None = None
    pull_request_number: int | None = None
    pull_request_url: str | None = None
    validation_completed_at: datetime | None = None
    publishing_started_at: datetime | None = None
    commit_created_at: datetime | None = None
    push_completed_at: datetime | None = None
    remote_sha_verified_at: datetime | None = None
    publishing_duration_ms: int | None = None
    speed_target_met: bool | None = None
    log_output: str
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class AutomationTriggerRequest(BaseModel):
    focus_area: str | None = None

