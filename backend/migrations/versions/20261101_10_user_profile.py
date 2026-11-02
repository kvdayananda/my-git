"""Add user profile settings, avatars, timezone, and notification preferences.

Revision ID: 20261101_10
Revises: 20261031_09
Create Date: 2026-11-01 07:30:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261101_10"
down_revision: Union[str, None] = "20261031_09"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("github_avatar_url", sa.String(length=2048), nullable=True))
    op.add_column("users", sa.Column("custom_display_name", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(length=2048), nullable=True))
    op.add_column("users", sa.Column("timezone", sa.String(length=100), server_default="UTC", nullable=False))
    op.add_column("users", sa.Column("notification_preferences", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "notification_preferences")
    op.drop_column("users", "timezone")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "custom_display_name")
    op.drop_column("users", "github_avatar_url")

