"""initial persistence tables

Revision ID: 0001_initial_persistence
Revises:
Create Date: 2026-03-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_persistence"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projection_runs",
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("projection_id", sa.String(length=128), nullable=False),
        sa.Column("question_features_json", sa.JSON(), nullable=False),
        sa.Column("signal_features_json", sa.JSON(), nullable=False),
        sa.Column("alignment_inputs_json", sa.JSON(), nullable=False),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("run_id"),
    )
    op.create_index("ix_projection_runs_projection_id", "projection_runs", ["projection_id"])

    op.create_table(
        "state_runs",
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("snapshot_id", sa.String(length=128), nullable=False),
        sa.Column("omega_id", sa.String(length=128), nullable=False),
        sa.Column("projection_id", sa.String(length=128), nullable=True),
        sa.Column("dominant_state", sa.String(length=32), nullable=False),
        sa.Column("transition_confidence", sa.Float(), nullable=False),
        sa.Column("snapshot_json", sa.JSON(), nullable=False),
        sa.Column("omega_json", sa.JSON(), nullable=False),
        sa.Column("projection_result_json", sa.JSON(), nullable=False),
        sa.Column("event_features_json", sa.JSON(), nullable=False),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("run_id"),
    )
    op.create_index("ix_state_runs_snapshot_id", "state_runs", ["snapshot_id"])
    op.create_index("ix_state_runs_omega_id", "state_runs", ["omega_id"])
    op.create_index("ix_state_runs_projection_id", "state_runs", ["projection_id"])
    op.create_index("ix_state_runs_dominant_state", "state_runs", ["dominant_state"])


def downgrade() -> None:
    op.drop_index("ix_state_runs_dominant_state", table_name="state_runs")
    op.drop_index("ix_state_runs_projection_id", table_name="state_runs")
    op.drop_index("ix_state_runs_omega_id", table_name="state_runs")
    op.drop_index("ix_state_runs_snapshot_id", table_name="state_runs")
    op.drop_table("state_runs")

    op.drop_index("ix_projection_runs_projection_id", table_name="projection_runs")
    op.drop_table("projection_runs")
