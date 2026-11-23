"""Add the subscription plan column to existing organizations.

Revision ID: 002_organization_plan
Revises: 001_initial
Create Date: 2026-11-23

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "002_organization_plan"
down_revision: Union[str, Sequence[str], None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("organizations")}
    if "plan" not in columns:
        op.add_column(
            "organizations",
            sa.Column("plan", sa.String(length=40), nullable=False, server_default="free"),
        )


def downgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("organizations")}
    if "plan" in columns:
        op.drop_column("organizations", "plan")
