"""Add pull request fields to release candidates."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261031_08"
down_revision: Union[str, None] = "20261028_07"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("release_candidates", sa.Column("pull_request_number", sa.Integer(), nullable=True))
    op.add_column("release_candidates", sa.Column("pull_request_url", sa.String(2048), nullable=True))


def downgrade() -> None:
    op.drop_column("release_candidates", "pull_request_url")
    op.drop_column("release_candidates", "pull_request_number")

