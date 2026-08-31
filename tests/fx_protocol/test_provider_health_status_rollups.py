"""Regression coverage for provider-health run-status classification."""

from ugh_quantamental.fx_protocol.monthly_review import compute_provider_health_summary
from ugh_quantamental.fx_protocol.weekly_reports_v2 import build_provider_health_summary


def test_snapshot_unavailable_retry_is_counted_as_skip_in_health_rollups() -> None:
    rows = [
        {
            "provider_name": "yahoo",
            "used_fallback_adjustment": "false",
            "snapshot_lag_business_days": "0",
            "run_status": "idempotent_skip_snapshot_unavailable",
        }
    ]

    weekly = build_provider_health_summary(rows)
    monthly = compute_provider_health_summary(rows)

    for summary in (weekly, monthly):
        assert summary["total_runs"] == 1
        assert summary["success_count"] == 0
        assert summary["failed_count"] == 0
        assert summary["skipped_count"] == 1
        assert (
            summary["success_count"]
            + summary["failed_count"]
            + summary["skipped_count"]
            == summary["total_runs"]
        )
