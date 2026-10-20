"""add user refresh token id

Revision ID: c3f8a1d92b10
Revises: b0b1ced4a3fd
Create Date: 2026-10-03 13:55:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3f8a1d92b10"
down_revision: Union[str, Sequence[str], None] = "b0b1ced4a3fd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("refresh_token_jti", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "refresh_token_jti")
