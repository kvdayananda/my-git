"""Add development task workflow tables."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261028_03"
down_revision: Union[str, None] = "20261028_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "development_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("repository_connection_id", sa.Integer(), nullable=False),
        sa.Column("base_commit_sha", sa.String(64), nullable=False),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("workspace_path", sa.String(2048), nullable=False),
        sa.Column("plan", sa.Text(), nullable=False),
        sa.Column("validation_results", sa.Text(), nullable=False),
        sa.Column("test_results", sa.Text(), nullable=False),
        sa.Column("error_summary", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["repository_connection_id"], ["repository_connections.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_development_tasks_user_id", "development_tasks", ["user_id"])
    op.create_index("ix_development_tasks_repository_connection_id", "development_tasks", ["repository_connection_id"])
    op.create_index("ix_development_tasks_status", "development_tasks", ["status"])
    op.create_index("ix_development_tasks_user_created", "development_tasks", ["user_id", "created_at"])
    op.create_index("ix_development_tasks_repository", "development_tasks", ["repository_connection_id", "created_at"])
    op.create_table(
        "proposed_changes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("development_task_id", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(2048), nullable=False),
        sa.Column("operation", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("proposed_content", sa.Text(), nullable=False),
        sa.Column("validation_status", sa.String(30), nullable=False),
        sa.Column("review_status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["development_task_id"], ["development_tasks.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_proposed_changes_development_task_id", "proposed_changes", ["development_task_id"])
    op.create_table(
        "task_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("development_task_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("sanitized_details", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["development_task_id"], ["development_tasks.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_task_events_development_task_id", "task_events", ["development_task_id"])
    op.create_index("ix_task_events_task_created", "task_events", ["development_task_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_task_events_task_created", table_name="task_events")
    op.drop_index("ix_task_events_development_task_id", table_name="task_events")
    op.drop_table("task_events")
    op.drop_index("ix_proposed_changes_development_task_id", table_name="proposed_changes")
    op.drop_table("proposed_changes")
    for name in ("ix_development_tasks_repository", "ix_development_tasks_user_created", "ix_development_tasks_status", "ix_development_tasks_repository_connection_id", "ix_development_tasks_user_id"):
        op.drop_index(name, table_name="development_tasks")
    op.drop_table("development_tasks")
