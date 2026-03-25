#!/usr/bin/env python3
"""CLI entrypoint for rebuilding FX analytics from persisted history.

Rebuilds annotation analytics (labeled observations, scoreboards) and
optionally the weekly v2 report from the CSV history directory.
No forecast or evaluation logic is re-executed.

Environment variables:
    FX_CSV_OUTPUT_DIR  Root CSV output directory (default: ./data/csv)
    FX_REPORT_DATE     If set (YYYYMMDD), also rebuild weekly report for this date
    FX_WEEK_DAYS       Number of business days for weekly report (default: 5)
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
    report_date_str = _env("FX_REPORT_DATE", "")
    week_days_str = _env("FX_WEEK_DAYS", "5")

    if not os.path.isdir(csv_output_dir):
        _fail(f"FX_CSV_OUTPUT_DIR does not exist: {csv_output_dir}")
        return

    generated_at_utc = datetime.now(timezone.utc)

    print("=== FX Analytics Rebuild ===")
    print(f"  csv_output_dir : {os.path.abspath(csv_output_dir)}")
    print()

    # Deferred import
    from ugh_quantamental.fx_protocol.analytics_rebuild import (
        rebuild_annotation_analytics,
        rebuild_weekly_report,
    )

    # Step 1: Rebuild annotation analytics
    print("[1/2] Rebuilding annotation analytics...")
    try:
        analytics_result = rebuild_annotation_analytics(
            csv_output_dir, generated_at_utc=generated_at_utc
        )
        for key, path in analytics_result.items():
            status = path if path else "(skipped)"
            print(f"  {key}: {status}")
    except Exception as exc:
        _fail(f"Analytics rebuild failed: {exc}")
        return

    # Step 2: Optionally rebuild weekly report
    if report_date_str:
        try:
            business_day_count = int(week_days_str)
            if business_day_count < 1:
                raise ValueError
        except ValueError:
            _fail(f"FX_WEEK_DAYS must be a positive integer, got: {week_days_str!r}")
            return

        try:
            report_date_jst = datetime.strptime(report_date_str, "%Y%m%d").replace(
                hour=8, minute=0, second=0, tzinfo=_JST
            )
        except ValueError:
            _fail(f"FX_REPORT_DATE must be YYYYMMDD, got: {report_date_str!r}")
            return

        print(f"\n[2/2] Rebuilding weekly report for {report_date_str}...")
        try:
            report = rebuild_weekly_report(
                csv_output_dir,
                report_date_jst,
                business_day_count=business_day_count,
                generated_at_utc=generated_at_utc,
            )
            artifacts = report.get("generated_artifact_paths", [])
            print(f"  observations: {report.get('observation_count', 0)}")
            for p in artifacts:
                print(f"  artifact: {p}")
        except Exception as exc:
            _fail(f"Weekly report rebuild failed: {exc}")
            return
    else:
        print("\n[2/2] Skipping weekly report (set FX_REPORT_DATE=YYYYMMDD to enable).")

    print("\n[OK] Analytics rebuild completed successfully.")


if __name__ == "__main__":
    main()
