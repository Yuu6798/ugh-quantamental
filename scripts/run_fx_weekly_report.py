#!/usr/bin/env python3
"""CLI entrypoint for generating the FX Weekly Report v2.

Reads persisted CSV history and annotations to produce weekly v2 artifacts
without re-running any forecast or evaluation logic.

Environment variables:
    FX_CSV_OUTPUT_DIR  Root CSV output directory (default: ./data/csv)
    FX_REPORT_DATE     Report date in YYYYMMDD format (default: today JST)
    FX_WEEK_DAYS       Number of business days to include (default: 5)
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

_JST = ZoneInfo("Asia/Tokyo")


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _fail(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    csv_output_dir = _env("FX_CSV_OUTPUT_DIR", "./data/csv")
    week_days_str = _env("FX_WEEK_DAYS", "5")
    report_date_str = _env("FX_REPORT_DATE", "")

    try:
        business_day_count = int(week_days_str)
        if business_day_count < 1:
            raise ValueError
    except ValueError:
        _fail(f"FX_WEEK_DAYS must be a positive integer, got: {week_days_str!r}")
        return  # unreachable, for type checker

    if report_date_str:
        try:
            report_date_jst = datetime.strptime(report_date_str, "%Y%m%d").replace(
                hour=8, minute=0, second=0, tzinfo=_JST
            )
        except ValueError:
            _fail(f"FX_REPORT_DATE must be YYYYMMDD, got: {report_date_str!r}")
            return
    else:
        report_date_jst = datetime.now(_JST).replace(
            hour=8, minute=0, second=0, microsecond=0
        )

    generated_at_utc = datetime.now(timezone.utc)

    if not os.path.isdir(csv_output_dir):
        _fail(f"FX_CSV_OUTPUT_DIR does not exist: {csv_output_dir}")
        return

    print("=== FX Weekly Report v2 ===")
    print(f"  csv_output_dir     : {os.path.abspath(csv_output_dir)}")
    print(f"  report_date_jst    : {report_date_jst.isoformat()}")
    print(f"  business_day_count : {business_day_count}")
    print()

    # Deferred import to keep startup fast
    from ugh_quantamental.fx_protocol.analytics_rebuild import rebuild_weekly_report

    try:
        report = rebuild_weekly_report(
            csv_output_dir,
            report_date_jst,
            business_day_count=business_day_count,
            generated_at_utc=generated_at_utc,
        )
    except Exception as exc:
        _fail(f"Weekly report generation failed: {exc}")
        return

    # Print summary
    cov = report.get("annotation_coverage", {})
    print("=== Weekly Report v2 Summary ===")
    print(f"  observations       : {report.get('observation_count', 0)}")
    print(f"  confirmed          : {cov.get('confirmed_annotation_count', 0)}")
    print(f"  pending            : {cov.get('pending_annotation_count', 0)}")
    print(f"  unlabeled          : {cov.get('unlabeled_count', 0)}")
    print(f"  coverage_rate      : {cov.get('annotation_coverage_rate', 0):.1%}")
    print(f"  strategy_metrics   : {len(report.get('strategy_metrics', []))} strategies")
    print(f"  slice_metrics      : {len(report.get('slice_metrics', []))} slices")

    artifacts = report.get("generated_artifact_paths", [])
    if artifacts:
        print("\n  Generated artifacts:")
        for p in artifacts:
            print(f"    - {p}")

    ph = report.get("provider_health_summary", {})
    if ph.get("total_runs", 0) > 0:
        print(f"\n  Provider health: {ph.get('success_count', 0)} success, "
              f"{ph.get('failed_count', 0)} failed, "
              f"{ph.get('fallback_adjustment_count', 0)} fallbacks")

    print("\n[OK] Weekly report v2 generated successfully.")


if __name__ == "__main__":
    main()
