from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_user_invitations"
down_revision: Union[str, Sequence[str], None] = "c3a91f5d7e20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_invitations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("invited_by_user_id", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["invited_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        "ix_user_invitations_organization_id",
        "user_invitations",
        ["organization_id"],
    )
    op.create_index(
        "ix_user_invitations_email",
        "user_invitations",
        ["email"],
    )
    op.create_index(
        "ix_user_invitations_token_hash",
        "user_invitations",
        ["token_hash"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_invitations_token_hash", table_name="user_invitations"
    )
    op.drop_index("ix_user_invitations_email", table_name="user_invitations")
    op.drop_index(
        "ix_user_invitations_organization_id", table_name="user_invitations"
    )
    op.drop_table("user_invitations")
