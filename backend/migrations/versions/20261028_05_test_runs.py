"""Add sandbox test runs."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261028_05"
down_revision: Union[str, None] = "20261028_04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "test_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("development_task_id", sa.Integer(), nullable=False),
        sa.Column("base_commit_sha", sa.String(64), nullable=False),
        sa.Column("execution_profile", sa.String(50), nullable=False),
        sa.Column("command_classification", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("exit_code", sa.Integer()),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("ended_at", sa.DateTime()),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column("timed_out", sa.Boolean(), nullable=False),
        sa.Column("resource_violation", sa.String(255)),
        sa.Column("stdout", sa.Text(), nullable=False),
        sa.Column("stderr", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("error_details", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["development_task_id"], ["development_tasks.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_test_runs_user_id", "test_runs", ["user_id"])
    op.create_index("ix_test_runs_development_task_id", "test_runs", ["development_task_id"])
    op.create_index("ix_test_runs_status", "test_runs", ["status"])
    op.create_index("ix_test_runs_task_created", "test_runs", ["development_task_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_test_runs_task_created", table_name="test_runs")
    op.drop_index("ix_test_runs_status", table_name="test_runs")
    op.drop_index("ix_test_runs_development_task_id", table_name="test_runs")
    op.drop_index("ix_test_runs_user_id", table_name="test_runs")
    op.drop_table("test_runs")
