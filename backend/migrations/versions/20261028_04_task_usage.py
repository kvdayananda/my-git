"""Track task generation token usage."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261028_04"
down_revision: Union[str, None] = "20261028_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("development_tasks", sa.Column("token_usage", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("development_tasks", "token_usage")
