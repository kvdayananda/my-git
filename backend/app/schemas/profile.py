from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class NotificationPreferences(BaseModel):
    email_on_backup: bool = True
    email_on_failure: bool = True
    email_on_pr: bool = True
    browser_notifications: bool = True


class GitHubProfileDetails(BaseModel):
    connected: bool
    github_id: int | None = None
    login: str | None = None
    name: str | None = None
    email: str | None = None
    avatar_url: str | None = None
    html_url: str | None = None
    public_repos: int | None = None
    followers: int | None = None
    following: int | None = None
    github_created_at: str | None = None


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    github_id: int
    github_login: str
    github_name: str | None = None
    github_email: str | None = None
    custom_display_name: str | None = None
    display_name: str
    avatar_url: str | None = None
    github_avatar_url: str | None = None
    github_profile_url: str
    timezone: str
    notification_preferences: NotificationPreferences
    created_at: datetime
    updated_at: datetime
    github_connected: bool
    connected_repositories_count: int
    local_projects_count: int
    automation_active: bool
    github_profile: GitHubProfileDetails | None = None


class ProfileUpdateRequest(BaseModel):
    custom_display_name: str | None = Field(None, max_length=255)
    timezone: str | None = Field(None, max_length=100)
    notification_preferences: NotificationPreferences | None = None


class RecentBackupActivity(BaseModel):
    id: int
    project_name: str
    status: str
    commit_sha: str | None = None
    commit_url: str | None = None
    is_dry_run: bool
    created_at: datetime


class RecentTaskActivity(BaseModel):
    id: int
    repository_name: str
    task_type: str
    status: str
    created_at: datetime


class ProfileSummaryDashboard(BaseModel):
    user_id: int
    display_name: str
    github_login: str
    github_connected: bool
    avatar_url: str | None = None
    timezone: str
    connected_repositories_count: int
    local_projects_count: int
    automation_active: bool
    active_backups_count: int
    last_backup_at: datetime | None = None
    last_backup_status: str | None = None
    recent_backups: list[RecentBackupActivity] = []
    recent_tasks: list[RecentTaskActivity] = []

