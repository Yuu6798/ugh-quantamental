"""add fx forecast records table

Revision ID: 0003_add_fx_forecast_records
Revises: 0002_add_regression_suite_baselines
Create Date: 2026-03-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_add_fx_forecast_records"
down_revision = "0002_add_regression_suite_baselines"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fx_forecast_records",
        sa.Column("forecast_id", sa.String(length=128), nullable=False),
        sa.Column("forecast_batch_id", sa.String(length=128), nullable=False),
        sa.Column("pair", sa.String(length=16), nullable=False),
        sa.Column("strategy_kind", sa.String(length=64), nullable=False),
        sa.Column("as_of_jst", sa.DateTime(timezone=False), nullable=False),
        sa.Column("window_end_jst", sa.DateTime(timezone=False), nullable=False),
        sa.Column("protocol_version", sa.String(length=32), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("forecast_id"),
    )
    op.create_index(
        "ix_fx_forecast_records_forecast_batch_id",
        "fx_forecast_records",
        ["forecast_batch_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_fx_forecast_records_forecast_batch_id",
        table_name="fx_forecast_records",
    )
    op.drop_table("fx_forecast_records")
