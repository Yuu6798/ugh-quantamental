from pathlib import Path

STATUS = "idempotent_skip_snapshot_unavailable"


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"{path}: target count={text.count(old)}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


old_status = '        elif status in ("skipped", "skip", "idempotent_skip"):\n            skipped_count += 1\n'
new_status = (
    '        elif status in (\n'
    '            "skipped",\n'
    '            "skip",\n'
    '            "idempotent_skip",\n'
    '            "idempotent_skip_snapshot_unavailable",\n'
    '        ):\n'
    '            skipped_count += 1\n'
)
replace_once(
    "src/ugh_quantamental/fx_protocol/weekly_reports_v2.py",
    old_status,
    new_status,
)
replace_once(
    "src/ugh_quantamental/fx_protocol/monthly_review.py",
    old_status,
    new_status,
)

replace_once(
    "docs/specs/fx_observability_artifacts_v1.md",
    '| run_status | string | "ok" or "idempotent_skip" |\n',
    '| run_status | string | "ok", "idempotent_skip", or "idempotent_skip_snapshot_unavailable" (existing batch has no immutable forecast-time input snapshot; retry fails closed without synthesizing provenance) |\n',
)

test_path = Path("tests/fx_protocol/test_provider_health_status_rollups.py")
if test_path.exists():
    raise SystemExit(f"{test_path}: already exists")
test_path.write_text(
    '''"""Regression coverage for provider-health run-status classification."""\n\nfrom ugh_quantamental.fx_protocol.monthly_review import compute_provider_health_summary\nfrom ugh_quantamental.fx_protocol.weekly_reports_v2 import build_provider_health_summary\n\n\ndef test_snapshot_unavailable_retry_is_counted_as_skip_in_health_rollups() -> None:\n    rows = [\n        {\n            "provider_name": "yahoo",\n            "used_fallback_adjustment": "false",\n            "snapshot_lag_business_days": "0",\n            "run_status": "idempotent_skip_snapshot_unavailable",\n        }\n    ]\n\n    weekly = build_provider_health_summary(rows)\n    monthly = compute_provider_health_summary(rows)\n\n    for summary in (weekly, monthly):\n        assert summary["total_runs"] == 1\n        assert summary["success_count"] == 0\n        assert summary["failed_count"] == 0\n        assert summary["skipped_count"] == 1\n        assert (\n            summary["success_count"]\n            + summary["failed_count"]\n            + summary["skipped_count"]\n            == summary["total_runs"]\n        )\n''',
    encoding="utf-8",
)
