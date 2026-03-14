"""add fx outcome and evaluation records tables

Revision ID: 0004_add_fx_outcome_and_evaluation_records
Revises: 0003_add_fx_forecast_records
Create Date: 2026-03-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_add_fx_outcome_and_evaluation_records"
down_revision = "0003_add_fx_forecast_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fx_outcome_records",
        sa.Column("outcome_id", sa.String(length=128), nullable=False),
        sa.Column("pair", sa.String(length=16), nullable=False),
        sa.Column("window_start_jst", sa.DateTime(timezone=False), nullable=False),
        sa.Column("window_end_jst", sa.DateTime(timezone=False), nullable=False),
        sa.Column("protocol_version", sa.String(length=32), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("outcome_id"),
    )

    op.create_table(
        "fx_evaluation_records",
        sa.Column("evaluation_id", sa.String(length=512), nullable=False),
        sa.Column("forecast_id", sa.String(length=128), nullable=False),
        sa.Column("outcome_id", sa.String(length=128), nullable=False),
        sa.Column("pair", sa.String(length=16), nullable=False),
        sa.Column("strategy_kind", sa.String(length=64), nullable=False),
        sa.Column("window_start_jst", sa.DateTime(timezone=False), nullable=False),
        sa.Column("window_end_jst", sa.DateTime(timezone=False), nullable=False),
        sa.Column("protocol_version", sa.String(length=32), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("evaluation_id"),
    )
    op.create_index(
        "ix_fx_evaluation_records_forecast_id",
        "fx_evaluation_records",
        ["forecast_id"],
    )
    op.create_index(
        "ix_fx_evaluation_records_outcome_id",
        "fx_evaluation_records",
        ["outcome_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_fx_evaluation_records_outcome_id",
        table_name="fx_evaluation_records",
    )
    op.drop_index(
        "ix_fx_evaluation_records_forecast_id",
        table_name="fx_evaluation_records",
    )
    op.drop_table("fx_evaluation_records")
    op.drop_table("fx_outcome_records")
