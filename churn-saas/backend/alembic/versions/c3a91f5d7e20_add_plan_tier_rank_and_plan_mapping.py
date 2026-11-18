"""add plan_tier_rank to observations and plan_mapping to organizations

Revision ID: c3a91f5d7e20
Revises: add_password_reset_tokens
Create Date: 2026-11-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3a91f5d7e20'
down_revision: Union[str, Sequence[str], None] = 'add_password_reset_tokens'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Classement des plans par organisation : {plan normalisé: rang entre 0 et 1}
    op.add_column('organizations', sa.Column('plan_mapping', sa.JSON(), nullable=True))

    # server_default : les observations déjà en base reçoivent le rang neutre (0.5, « inconnu »)
    op.add_column(
        'observations',
        sa.Column('plan_tier_rank', sa.Float(), nullable=False, server_default='0.5'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('observations', 'plan_tier_rank')
    op.drop_column('organizations', 'plan_mapping')
