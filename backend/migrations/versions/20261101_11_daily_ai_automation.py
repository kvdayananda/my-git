"""Add automation_settings and automation_runs tables for System B Daily AI Automation.

Revision ID: 20261101_11
Revises: 20261101_10
Create Date: 2026-11-01 07:55:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261101_11"
down_revision: Union[str, None] = "20261101_10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "automation_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("repository_connection_id", sa.Integer(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("schedule_time", sa.String(length=50), nullable=False, server_default="03:00"),
        sa.Column("focus_areas", sa.Text(), nullable=False),
        sa.Column("target_branch_prefix", sa.String(length=255), nullable=False, server_default="gitauto/daily"),
        sa.Column("auto_test", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("require_approval", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("last_run_status", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["repository_connection_id"], ["repository_connections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "repository_connection_id", name="uq_user_repo_automation"),
    )
    op.create_index("ix_automation_settings_user", "automation_settings", ["user_id"], unique=False)

    op.create_table(
        "automation_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("repository_connection_id", sa.Integer(), nullable=False),
        sa.Column("analysis_id", sa.Integer(), nullable=True),
        sa.Column("development_task_id", sa.Integer(), nullable=True),
        sa.Column("release_candidate_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("summary", sa.String(length=1000), nullable=False, server_default=""),
        sa.Column("findings_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("changes_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tests_passed", sa.Boolean(), nullable=True),
        sa.Column("target_branch", sa.String(length=255), nullable=True),
        sa.Column("commit_sha", sa.String(length=64), nullable=True),
        sa.Column("commit_url", sa.String(length=2048), nullable=True),
        sa.Column("pull_request_number", sa.Integer(), nullable=True),
        sa.Column("pull_request_url", sa.String(length=2048), nullable=True),
        sa.Column("log_output", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["development_task_id"], ["development_tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["release_candidate_id"], ["release_candidates.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["repository_connection_id"], ["repository_connections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_automation_runs_user_created", "automation_runs", ["user_id", "created_at"], unique=False)
    op.create_index("ix_automation_runs_repo_created", "automation_runs", ["repository_connection_id", "created_at"], unique=False)
    op.create_index(op.f("ix_automation_runs_status"), "automation_runs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_automation_runs_status"), table_name="automation_runs")
    op.drop_index("ix_automation_runs_repo_created", table_name="automation_runs")
    op.drop_index("ix_automation_runs_user_created", table_name="automation_runs")
    op.drop_table("automation_runs")
    op.drop_index("ix_automation_settings_user", table_name="automation_settings")
    op.drop_table("automation_settings")

