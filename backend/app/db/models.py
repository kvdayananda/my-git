from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utc_now


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    github_id: Mapped[int] = mapped_column(Integer, unique=True)
    github_login: Mapped[str] = mapped_column(String(255), index=True)
    github_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    github_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    github_avatar_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    custom_display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    timezone: Mapped[str] = mapped_column(String(100), default="UTC")
    notification_preferences: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)
    github_connection: Mapped["GitHubConnection | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    repositories: Mapped[list["RepositoryConnection"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    local_projects: Mapped[list["LocalProject"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class GitHubConnection(Base):
    __tablename__ = "github_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    encrypted_access_token: Mapped[str] = mapped_column(Text)
    scope: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)
    user: Mapped[User] = relationship(back_populates="github_connection")


class RepositoryConnection(Base):
    __tablename__ = "repository_connections"
    __table_args__ = (
        UniqueConstraint("user_id", "github_repository_id", name="uq_user_github_repository"),
        Index("ix_repository_owner_name", "owner", "name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    github_repository_id: Mapped[int] = mapped_column(Integer)
    owner: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_branch: Mapped[str] = mapped_column(String(255))
    visibility: Mapped[str] = mapped_column(String(50))
    language: Mapped[str | None] = mapped_column(String(100), nullable=True)
    html_url: Mapped[str] = mapped_column(String(2048))
    can_push: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)
    user: Mapped[User] = relationship(back_populates="repositories")

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"


class Analysis(Base):
    __tablename__ = "analyses"
    __table_args__ = (
        Index("ix_analyses_user_repository_created", "user_id", "repository_connection_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    repository_connection_id: Mapped[int] = mapped_column(
        ForeignKey("repository_connections.id", ondelete="CASCADE"), index=True
    )
    commit_sha: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(30))
    project_summary: Mapped[str] = mapped_column(Text, default="")
    detected_technologies: Mapped[str] = mapped_column(Text, default="[]")
    file_inventory: Mapped[str] = mapped_column(Text, default="[]")
    findings: Mapped[str] = mapped_column(Text, default="[]")
    recommendations: Mapped[str] = mapped_column(Text, default="[]")
    development_plan: Mapped[str] = mapped_column(Text, default="[]")
    limitations: Mapped[str] = mapped_column(Text, default="[]")
    model_identifier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    token_usage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class DevelopmentTask(Base):
    __tablename__ = "development_tasks"
    __table_args__ = (
        Index("ix_development_tasks_user_created", "user_id", "created_at"),
        Index("ix_development_tasks_repository", "repository_connection_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    repository_connection_id: Mapped[int] = mapped_column(
        ForeignKey("repository_connections.id", ondelete="CASCADE"), index=True
    )
    base_commit_sha: Mapped[str] = mapped_column(String(64))
    task_type: Mapped[str] = mapped_column(String(50))
    instructions: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), index=True)
    workspace_path: Mapped[str] = mapped_column(String(2048))
    plan: Mapped[str] = mapped_column(Text, default="{}")
    validation_results: Mapped[str] = mapped_column(Text, default="[]")
    test_results: Mapped[str] = mapped_column(Text, default="[]")
    token_usage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ProposedChange(Base):
    __tablename__ = "proposed_changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    development_task_id: Mapped[int] = mapped_column(
        ForeignKey("development_tasks.id", ondelete="CASCADE"), index=True
    )
    file_path: Mapped[str] = mapped_column(String(2048))
    operation: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(Text)
    proposed_content: Mapped[str] = mapped_column(Text)
    validation_status: Mapped[str] = mapped_column(String(30), default="not_run")
    review_status: Mapped[str] = mapped_column(String(30), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class TaskEvent(Base):
    __tablename__ = "task_events"
    __table_args__ = (Index("ix_task_events_task_created", "development_task_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    development_task_id: Mapped[int] = mapped_column(
        ForeignKey("development_tasks.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(50))
    sanitized_details: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class TestRun(Base):
    __test__ = False
    __tablename__ = "test_runs"
    __table_args__ = (Index("ix_test_runs_task_created", "development_task_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    development_task_id: Mapped[int] = mapped_column(
        ForeignKey("development_tasks.id", ondelete="CASCADE"), index=True
    )
    base_commit_sha: Mapped[str] = mapped_column(String(64))
    candidate_hash: Mapped[str] = mapped_column(String(64), default="")
    execution_profile: Mapped[str] = mapped_column(String(50))
    command_classification: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), index=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timed_out: Mapped[bool] = mapped_column(Boolean, default=False)
    resource_violation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stdout: Mapped[str] = mapped_column(Text, default="")
    stderr: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class ReleaseCandidate(Base):
    __tablename__ = "release_candidates"
    __table_args__ = (
        UniqueConstraint("development_task_id", "diff_hash", name="uq_release_task_diff"),
        Index("ix_release_candidates_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    repository_connection_id: Mapped[int] = mapped_column(
        ForeignKey("repository_connections.id", ondelete="CASCADE"), index=True
    )
    development_task_id: Mapped[int] = mapped_column(
        ForeignKey("development_tasks.id", ondelete="CASCADE"), index=True
    )
    test_run_id: Mapped[int] = mapped_column(ForeignKey("test_runs.id"), index=True)
    base_commit_sha: Mapped[str] = mapped_column(String(64))
    target_branch: Mapped[str] = mapped_column(String(255))
    candidate_branch: Mapped[str] = mapped_column(String(255), unique=True)
    approved_file_paths: Mapped[str] = mapped_column(Text)
    diff_hash: Mapped[str] = mapped_column(String(64))
    secret_scan_status: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), index=True)
    approval_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    release_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    release_lease_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    release_lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    commit_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    pull_request_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pull_request_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class LocalProject(Base):
    __tablename__ = "local_projects"
    __table_args__ = (
        Index("ix_local_projects_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    repository_connection_id: Mapped[int] = mapped_column(
        ForeignKey("repository_connections.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    local_path: Mapped[str] = mapped_column(String(2048))
    target_branch: Mapped[str] = mapped_column(String(255), default="backup/daily")
    backup_schedule: Mapped[str] = mapped_column(String(50), default="02:00")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_backup_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_backup_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    user: Mapped["User"] = relationship(back_populates="local_projects")
    repository_connection: Mapped["RepositoryConnection"] = relationship()
    backup_records: Mapped[list["BackupRecord"]] = relationship(
        back_populates="local_project", cascade="all, delete-orphan"
    )


class BackupRecord(Base):
    __tablename__ = "backup_records"
    __table_args__ = (
        Index("ix_backup_records_user_created", "user_id", "created_at"),
        Index("ix_backup_records_project_created", "local_project_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    local_project_id: Mapped[int] = mapped_column(
        ForeignKey("local_projects.id", ondelete="CASCADE"), index=True
    )
    repository_connection_id: Mapped[int] = mapped_column(
        ForeignKey("repository_connections.id", ondelete="CASCADE"), index=True
    )
    target_branch: Mapped[str] = mapped_column(String(255))
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    commit_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    commit_message: Mapped[str] = mapped_column(Text)
    files_backed_up: Mapped[str] = mapped_column(Text, default="[]")
    files_excluded: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(String(50), index=True)
    log_output: Mapped[str] = mapped_column(Text, default="")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_dry_run: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    local_project: Mapped["LocalProject"] = relationship(back_populates="backup_records")
    repository_connection: Mapped["RepositoryConnection"] = relationship()


class AutomationSetting(Base):
    __tablename__ = "automation_settings"
    __table_args__ = (
        UniqueConstraint("user_id", "repository_connection_id", name="uq_user_repo_automation"),
        Index("ix_automation_settings_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    repository_connection_id: Mapped[int] = mapped_column(
        ForeignKey("repository_connections.id", ondelete="CASCADE"), index=True
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    schedule_time: Mapped[str] = mapped_column(String(50), default="20:00")
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata")
    auto_publish: Mapped[bool] = mapped_column(Boolean, default=False)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    max_retries: Mapped[int] = mapped_column(Integer, default=2)
    focus_areas: Mapped[str] = mapped_column(
        Text, default='["bug_detection","documentation","test_generation","code_improvements"]'
    )
    target_branch_prefix: Mapped[str] = mapped_column(String(255), default="gitauto/daily")
    auto_test: Mapped[bool] = mapped_column(Boolean, default=True)
    require_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_run_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    user: Mapped["User"] = relationship()
    repository: Mapped["RepositoryConnection"] = relationship()


class AutomationRun(Base):
    __tablename__ = "automation_runs"
    __table_args__ = (
        Index("ix_automation_runs_user_created", "user_id", "created_at"),
        Index("ix_automation_runs_repo_created", "repository_connection_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    repository_connection_id: Mapped[int] = mapped_column(
        ForeignKey("repository_connections.id", ondelete="CASCADE"), index=True
    )
    analysis_id: Mapped[int | None] = mapped_column(ForeignKey("analyses.id", ondelete="SET NULL"), nullable=True)
    development_task_id: Mapped[int | None] = mapped_column(
        ForeignKey("development_tasks.id", ondelete="SET NULL"), nullable=True
    )
    release_candidate_id: Mapped[int | None] = mapped_column(
        ForeignKey("release_candidates.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), index=True)
    summary: Mapped[str] = mapped_column(String(1000), default="")
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    changes_count: Mapped[int] = mapped_column(Integer, default=0)
    files_created_count: Mapped[int] = mapped_column(Integer, default=0)
    files_modified_count: Mapped[int] = mapped_column(Integer, default=0)
    files_deleted_count: Mapped[int] = mapped_column(Integer, default=0)
    lines_added: Mapped[int] = mapped_column(Integer, default=0)
    lines_deleted: Mapped[int] = mapped_column(Integer, default=0)
    security_result: Mapped[str] = mapped_column(String(30), default="passed")
    test_result: Mapped[str] = mapped_column(String(30), default="passed")
    commit_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    tests_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    target_branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    commit_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    pull_request_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pull_request_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    validation_completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    publishing_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    commit_created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    push_completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    remote_sha_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    publishing_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    speed_target_met: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    log_output: Mapped[str] = mapped_column(Text, default="")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship()
    repository: Mapped["RepositoryConnection"] = relationship()
