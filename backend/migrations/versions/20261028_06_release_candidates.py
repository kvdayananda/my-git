"""Add immutable release candidates and test candidate hashes."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261028_06"
down_revision: Union[str, None] = "20261028_05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("test_runs", sa.Column("candidate_hash", sa.String(64), nullable=False, server_default=""))
    op.create_table(
        "release_candidates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("repository_connection_id", sa.Integer(), nullable=False),
        sa.Column("development_task_id", sa.Integer(), nullable=False),
        sa.Column("test_run_id", sa.Integer(), nullable=False),
        sa.Column("base_commit_sha", sa.String(64), nullable=False),
        sa.Column("target_branch", sa.String(255), nullable=False),
        sa.Column("candidate_branch", sa.String(255), nullable=False),
        sa.Column("approved_file_paths", sa.Text(), nullable=False),
        sa.Column("diff_hash", sa.String(64), nullable=False),
        sa.Column("secret_scan_status", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("approval_at", sa.DateTime()),
        sa.Column("approved_by", sa.Integer()),
        sa.Column("release_started_at", sa.DateTime()),
        sa.Column("released_at", sa.DateTime()),
        sa.Column("commit_sha", sa.String(64)),
        sa.Column("commit_url", sa.String(2048)),
        sa.Column("error_summary", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["repository_connection_id"], ["repository_connections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["development_task_id"], ["development_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["test_run_id"], ["test_runs.id"]),
        sa.UniqueConstraint("development_task_id", "diff_hash", name="uq_release_task_diff"),
        sa.UniqueConstraint("candidate_branch"),
    )
    op.create_index("ix_release_candidates_user_id", "release_candidates", ["user_id"])
    op.create_index("ix_release_candidates_repository_connection_id", "release_candidates", ["repository_connection_id"])
    op.create_index("ix_release_candidates_development_task_id", "release_candidates", ["development_task_id"])
    op.create_index("ix_release_candidates_test_run_id", "release_candidates", ["test_run_id"])
    op.create_index("ix_release_candidates_status", "release_candidates", ["status"])
    op.create_index("ix_release_candidates_user_created", "release_candidates", ["user_id", "created_at"])


def downgrade() -> None:
    for name in (
        "ix_release_candidates_user_created", "ix_release_candidates_status",
        "ix_release_candidates_test_run_id", "ix_release_candidates_development_task_id",
        "ix_release_candidates_repository_connection_id", "ix_release_candidates_user_id",
    ):
        op.drop_index(name, table_name="release_candidates")
    op.drop_table("release_candidates")
    op.drop_column("test_runs", "candidate_hash")
