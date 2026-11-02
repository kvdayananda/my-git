"""Create users, GitHub connections, and repository connections."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261027_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("github_id", sa.Integer(), nullable=False),
        sa.Column("github_login", sa.String(length=255), nullable=False),
        sa.Column("github_name", sa.String(length=255)),
        sa.Column("github_email", sa.String(length=320)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("github_id"),
    )
    op.create_index("ix_users_github_id", "users", ["github_id"], unique=False)
    op.create_index("ix_users_github_login", "users", ["github_login"], unique=False)
    op.create_table(
        "github_connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("encrypted_access_token", sa.Text(), nullable=False),
        sa.Column("scope", sa.String(length=1000)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "repository_connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("github_repository_id", sa.Integer(), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("default_branch", sa.String(length=255), nullable=False),
        sa.Column("visibility", sa.String(length=50), nullable=False),
        sa.Column("language", sa.String(length=100)),
        sa.Column("html_url", sa.String(length=2048), nullable=False),
        sa.Column("can_push", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "github_repository_id", name="uq_user_github_repository"),
    )
    op.create_index("ix_repository_connections_user_id", "repository_connections", ["user_id"], unique=False)
    op.create_index("ix_repository_owner_name", "repository_connections", ["owner", "name"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_repository_owner_name", table_name="repository_connections")
    op.drop_index("ix_repository_connections_user_id", table_name="repository_connections")
    op.drop_table("repository_connections")
    op.drop_table("github_connections")
    op.drop_index("ix_users_github_login", table_name="users")
    op.drop_index("ix_users_github_id", table_name="users")
    op.drop_table("users")
