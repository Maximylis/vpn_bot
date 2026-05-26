"""fix auto renew tariff column

Revision ID: bb5d01ecf4d3
Revises: bcdea7f8f1b9
Create Date: 2026-05-26 20:56:12.001365

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb5d01ecf4d3'
down_revision: Union[str, Sequence[str], None] = 'bcdea7f8f1b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "subscriptions",
        sa.Column(
            "auto_renew_tariff",
            sa.String(length=50),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("subscriptions", "auto_renew_tariff")
