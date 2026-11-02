"""Add repository analyses."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261028_02"
down_revision: Union[str, None] = "20261027_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "analyses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("repository_connection_id", sa.Integer(), nullable=False),
        sa.Column("commit_sha", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("project_summary", sa.Text(), nullable=False),
        sa.Column("detected_technologies", sa.Text(), nullable=False),
        sa.Column("file_inventory", sa.Text(), nullable=False),
        sa.Column("findings", sa.Text(), nullable=False),
        sa.Column("recommendations", sa.Text(), nullable=False),
        sa.Column("development_plan", sa.Text(), nullable=False),
        sa.Column("limitations", sa.Text(), nullable=False),
        sa.Column("model_identifier", sa.String(length=100)),
        sa.Column("token_usage", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["repository_connection_id"], ["repository_connections.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_analyses_user_id", "analyses", ["user_id"])
    op.create_index("ix_analyses_repository_connection_id", "analyses", ["repository_connection_id"])
    op.create_index("ix_analyses_user_repository_created", "analyses", ["user_id", "repository_connection_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_analyses_user_repository_created", table_name="analyses")
    op.drop_index("ix_analyses_repository_connection_id", table_name="analyses")
    op.drop_index("ix_analyses_user_id", table_name="analyses")
    op.drop_table("analyses")
