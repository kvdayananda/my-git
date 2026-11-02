"""Add timezone, auto_publish, and granular publishing stats for System B.

Revision ID: 20261101_12
Revises: 20261101_11
Create Date: 2026-11-01 21:40:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261101_12"
down_revision: Union[str, None] = "20261101_11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # automation_settings additions
    op.add_column("automation_settings", sa.Column("timezone", sa.String(length=50), nullable=False, server_default="Asia/Kolkata"))
    op.add_column("automation_settings", sa.Column("auto_publish", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("automation_settings", sa.Column("next_run_at", sa.DateTime(), nullable=True))
    op.add_column("automation_settings", sa.Column("max_retries", sa.Integer(), nullable=False, server_default="2"))

    # automation_runs additions
    op.add_column("automation_runs", sa.Column("files_created_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("automation_runs", sa.Column("files_modified_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("automation_runs", sa.Column("files_deleted_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("automation_runs", sa.Column("lines_added", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("automation_runs", sa.Column("lines_deleted", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("automation_runs", sa.Column("security_result", sa.String(length=30), nullable=False, server_default="passed"))
    op.add_column("automation_runs", sa.Column("test_result", sa.String(length=30), nullable=False, server_default="passed"))
    op.add_column("automation_runs", sa.Column("commit_message", sa.Text(), nullable=True))
    op.add_column("automation_runs", sa.Column("validation_completed_at", sa.DateTime(), nullable=True))
    op.add_column("automation_runs", sa.Column("publishing_started_at", sa.DateTime(), nullable=True))
    op.add_column("automation_runs", sa.Column("commit_created_at", sa.DateTime(), nullable=True))
    op.add_column("automation_runs", sa.Column("push_completed_at", sa.DateTime(), nullable=True))
    op.add_column("automation_runs", sa.Column("remote_sha_verified_at", sa.DateTime(), nullable=True))
    op.add_column("automation_runs", sa.Column("publishing_duration_ms", sa.Integer(), nullable=True))
    op.add_column("automation_runs", sa.Column("speed_target_met", sa.Boolean(), nullable=True))


def downgrade() -> None:
    # automation_runs rollback
    op.drop_column("automation_runs", "speed_target_met")
    op.drop_column("automation_runs", "publishing_duration_ms")
    op.drop_column("automation_runs", "remote_sha_verified_at")
    op.drop_column("automation_runs", "push_completed_at")
    op.drop_column("automation_runs", "commit_created_at")
    op.drop_column("automation_runs", "publishing_started_at")
    op.drop_column("automation_runs", "validation_completed_at")
    op.drop_column("automation_runs", "commit_message")
    op.drop_column("automation_runs", "test_result")
    op.drop_column("automation_runs", "security_result")
    op.drop_column("automation_runs", "lines_deleted")
    op.drop_column("automation_runs", "lines_added")
    op.drop_column("automation_runs", "files_deleted_count")
    op.drop_column("automation_runs", "files_modified_count")
    op.drop_column("automation_runs", "files_created_count")

    # automation_settings rollback
    op.drop_column("automation_settings", "max_retries")
    op.drop_column("automation_settings", "next_run_at")
    op.drop_column("automation_settings", "auto_publish")
    op.drop_column("automation_settings", "timezone")

