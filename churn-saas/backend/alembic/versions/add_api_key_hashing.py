"""store hashed organization API keys

Revision ID: add_api_key_hashing
Revises: add_retention_actions
Create Date: 2026-11-24 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_api_key_hashing"
down_revision: Union[str, Sequence[str], None] = "add_retention_actions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remplace la clé en clair par une empreinte SHA-256 et un préfixe visible."""
    op.add_column(
        "organizations",
        sa.Column("api_key_hash", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_organizations_api_key_hash",
        "organizations",
        ["api_key_hash"],
        unique=True,
    )
    op.add_column(
        "organizations",
        sa.Column("api_key_prefix", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "organizations",
        sa.Column(
            "api_key_created_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Les anciennes clés en clair ne sont plus valides : elles ne sont jamais
    # réaffichées et l'inscription n'en génère plus.
    op.drop_index(
        op.f("ix_organizations_api_key"), table_name="organizations"
    )
    op.drop_column("organizations", "api_key")


def downgrade() -> None:
    """Restaure l'ancienne colonne (les clés d'origine ne sont pas récupérables)."""
    op.add_column(
        "organizations",
        sa.Column("api_key", sa.String(length=64), nullable=True),
    )
    op.create_index(
        op.f("ix_organizations_api_key"),
        "organizations",
        ["api_key"],
        unique=True,
    )
    op.drop_column("organizations", "api_key_created_at")
    op.drop_column("organizations", "api_key_prefix")
    op.drop_index(
        "ix_organizations_api_key_hash", table_name="organizations"
    )
    op.drop_column("organizations", "api_key_hash")
