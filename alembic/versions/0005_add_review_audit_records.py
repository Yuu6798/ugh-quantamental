"""add review audit runs table

Revision ID: 0005_add_review_audit_records
Revises: 0004_add_fx_outcome_and_evaluation_records
Create Date: 2026-03-15
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_add_review_audit_records"
down_revision = "0004_add_fx_outcome_and_evaluation_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "review_audit_runs",
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("audit_id", sa.String(length=128), nullable=False),
        sa.Column("pr_number", sa.Integer(), nullable=False),
        sa.Column("reviewer_login", sa.String(length=128), nullable=True),
        sa.Column("verdict", sa.String(length=32), nullable=False),
        sa.Column("extractor_version", sa.String(length=32), nullable=False),
        sa.Column("feature_spec_version", sa.String(length=32), nullable=False),
        sa.Column("review_context_json", sa.JSON(), nullable=False),
        sa.Column("observation_json", sa.JSON(), nullable=False),
        sa.Column("intent_features_json", sa.JSON(), nullable=False),
        sa.Column("action_features_json", sa.JSON(), nullable=True),
        sa.Column("engine_result_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("run_id"),
    )
    op.create_index(
        "ix_review_audit_runs_audit_id",
        "review_audit_runs",
        ["audit_id"],
        unique=False,
    )
    op.create_index(
        "ix_review_audit_runs_pr_number",
        "review_audit_runs",
        ["pr_number"],
        unique=False,
    )
    op.create_index(
        "ix_review_audit_runs_verdict",
        "review_audit_runs",
        ["verdict"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_review_audit_runs_verdict", table_name="review_audit_runs")
    op.drop_index("ix_review_audit_runs_pr_number", table_name="review_audit_runs")
    op.drop_index("ix_review_audit_runs_audit_id", table_name="review_audit_runs")
    op.drop_table("review_audit_runs")
