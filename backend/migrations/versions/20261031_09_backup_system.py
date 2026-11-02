"""Add local projects and backup records tables for System A Daily Backup.

Revision ID: 20261031_09
Revises: 20261031_08
Create Date: 2026-10-31 21:30:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261031_09"
down_revision: Union[str, None] = "20261031_08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "local_projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("repository_connection_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("local_path", sa.String(length=2048), nullable=False),
        sa.Column("target_branch", sa.String(length=255), nullable=False, server_default="backup/daily"),
        sa.Column("backup_schedule", sa.String(length=50), nullable=False, server_default="02:00"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("last_backup_at", sa.DateTime(), nullable=True),
        sa.Column("last_backup_status", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["repository_connection_id"], ["repository_connections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_local_projects_user_created", "local_projects", ["user_id", "created_at"])
    op.create_index("ix_local_projects_user_id", "local_projects", ["user_id"])
    op.create_index("ix_local_projects_repository_connection_id", "local_projects", ["repository_connection_id"])

    op.create_table(
        "backup_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("local_project_id", sa.Integer(), nullable=False),
        sa.Column("repository_connection_id", sa.Integer(), nullable=False),
        sa.Column("target_branch", sa.String(length=255), nullable=False),
        sa.Column("commit_sha", sa.String(length=64), nullable=True),
        sa.Column("commit_url", sa.String(length=2048), nullable=True),
        sa.Column("commit_message", sa.Text(), nullable=False),
        sa.Column("files_backed_up", sa.Text(), nullable=False),
        sa.Column("files_excluded", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("log_output", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("is_dry_run", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["local_project_id"], ["local_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["repository_connection_id"], ["repository_connections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_backup_records_user_created", "backup_records", ["user_id", "created_at"])
    op.create_index("ix_backup_records_project_created", "backup_records", ["local_project_id", "created_at"])
    op.create_index("ix_backup_records_status", "backup_records", ["status"])


def downgrade() -> None:
    op.drop_index("ix_backup_records_status", table_name="backup_records")
    op.drop_index("ix_backup_records_project_created", table_name="backup_records")
    op.drop_index("ix_backup_records_user_created", table_name="backup_records")
    op.drop_table("backup_records")

    op.drop_index("ix_local_projects_repository_connection_id", table_name="local_projects")
    op.drop_index("ix_local_projects_user_id", table_name="local_projects")
    op.drop_index("ix_local_projects_user_created", table_name="local_projects")
    op.drop_table("local_projects")

