"""add retention status, customer owner and customer actions

Revision ID: add_retention_actions
Revises: add_user_invitations
Create Date: 2026-11-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_retention_actions"
down_revision: Union[str, Sequence[str], None] = "add_user_invitations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Ajoute le suivi de rétention et le journal des actions."""
    op.add_column(
        "customers",
        sa.Column(
            "retention_status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'none'"),
        ),
    )
    op.add_column(
        "customers",
        sa.Column("owner_user_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_customers_owner_user_id_users",
        "customers",
        "users",
        ["owner_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_customers_owner_user_id", "customers", ["owner_user_id"]
    )

    op.create_table(
        "customer_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("action_type", sa.String(length=20), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'todo'"),
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
            ["customer_id"],
            ["customers.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_customer_actions_customer_id",
        "customer_actions",
        ["customer_id"],
    )
    op.create_index(
        "ix_customer_actions_created_by_user_id",
        "customer_actions",
        ["created_by_user_id"],
    )


def downgrade() -> None:
    """Retire le journal et les colonnes de rétention."""
    op.drop_index(
        "ix_customer_actions_created_by_user_id", table_name="customer_actions"
    )
    op.drop_index(
        "ix_customer_actions_customer_id", table_name="customer_actions"
    )
    op.drop_table("customer_actions")
    op.drop_index("ix_customers_owner_user_id", table_name="customers")
    op.drop_constraint(
        "fk_customers_owner_user_id_users", "customers", type_="foreignkey"
    )
    op.drop_column("customers", "owner_user_id")
    op.drop_column("customers", "retention_status")
