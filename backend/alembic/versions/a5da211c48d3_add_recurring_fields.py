"""add recurring fields

Revision ID: a5da211c48d3
Revises: 5fa8c1333462
Create Date: 2026-05-26 19:34:59.649028

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5da211c48d3'
down_revision: Union[str, Sequence[str], None] = 'a539237410d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "subscriptions",
        sa.Column(
            "auto_renew",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.add_column(
        "subscriptions",
        sa.Column(
            "payment_method_id",
            sa.String(length=255),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("subscriptions", "payment_method_id")
    op.drop_column("subscriptions", "auto_renew")
