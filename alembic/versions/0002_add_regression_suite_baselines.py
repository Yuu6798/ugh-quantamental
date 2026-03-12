"""add regression suite baselines table

Revision ID: 0002_add_regression_suite_baselines
Revises: 0001_initial_persistence
Create Date: 2026-03-12
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_add_regression_suite_baselines"
down_revision = "0001_initial_persistence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "regression_suite_baselines",
        sa.Column("baseline_id", sa.String(length=64), nullable=False),
        sa.Column("baseline_name", sa.String(length=256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("suite_request_json", sa.JSON(), nullable=False),
        sa.Column("suite_result_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("baseline_id"),
        sa.UniqueConstraint("baseline_name"),
    )
    op.create_index(
        "ix_regression_suite_baselines_baseline_name",
        "regression_suite_baselines",
        ["baseline_name"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_regression_suite_baselines_baseline_name",
        table_name="regression_suite_baselines",
    )
    op.drop_table("regression_suite_baselines")
