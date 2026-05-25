"""add trial notification fields

Revision ID: a539237410d5
Revises: 5fa8c1333462
Create Date: 2026-05-26 00:00:51.759800

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a539237410d5'
down_revision: Union[str, Sequence[str], None] = '5fa8c1333462'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "subscriptions",
        sa.Column(
            "is_trial",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.add_column(
        "subscriptions",
        sa.Column(
            "trial_penultimate_day_notified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.add_column(
        "subscriptions",
        sa.Column(
            "trial_lastday_notified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("subscriptions", "trial_lastday_notified")
    op.drop_column("subscriptions", "trial_penultimate_day_notified")
    op.drop_column("subscriptions", "is_trial")
