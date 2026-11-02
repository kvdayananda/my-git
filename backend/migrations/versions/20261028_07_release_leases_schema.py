"""Align indexes and add durable release leases."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261028_07"
down_revision: Union[str, None] = "20261028_06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("release_candidates", sa.Column("release_lease_token", sa.String(64), nullable=True))
    op.add_column("release_candidates", sa.Column("release_lease_expires_at", sa.DateTime(), nullable=True))
    op.drop_index("ix_users_github_id", table_name="users")


def downgrade() -> None:
    op.create_index("ix_users_github_id", "users", ["github_id"], unique=False)
    op.drop_column("release_candidates", "release_lease_expires_at")
    op.drop_column("release_candidates", "release_lease_token")
