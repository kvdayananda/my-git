from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class LocalProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    local_path: str = Field(..., min_length=1, max_length=2048)
    repository_connection_id: int
    target_branch: str = Field("backup/daily", min_length=1, max_length=255)
    backup_schedule: str = Field("02:00", max_length=50)
    is_active: bool = True


class LocalProjectUpdate(BaseModel):
    name: str | None = None
    target_branch: str | None = None
    backup_schedule: str | None = None
    is_active: bool | None = None


class LocalProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    repository_connection_id: int
    repository_name: str | None = None
    repository_owner: str | None = None
    name: str
    local_path: str
    target_branch: str
    backup_schedule: str
    is_active: bool
    last_backup_at: datetime | None = None
    last_backup_status: str | None = None
    created_at: datetime
    updated_at: datetime


class BackupRunRequest(BaseModel):
    dry_run: bool = False
    custom_message: str | None = None


class BackupRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    local_project_id: int
    project_name: str | None = None
    repository_connection_id: int
    target_branch: str
    commit_sha: str | None = None
    commit_url: str | None = None
    commit_message: str
    files_backed_up: list[str] = Field(default_factory=list)
    files_excluded: list[str] = Field(default_factory=list)
    status: str
    log_output: str
    error_message: str | None = None
    is_dry_run: bool
    created_at: datetime


class ScannedFileDetail(BaseModel):
    path: str
    status: str  # modified, added, deleted, untracked
    size: int
    is_secret: bool = False
    exclusion_reason: str | None = None


class BackupScanPreview(BaseModel):
    local_path: str
    target_branch: str
    safe_files: list[ScannedFileDetail]
    excluded_secrets: list[ScannedFileDetail]
    total_safe_count: int
    total_excluded_count: int

