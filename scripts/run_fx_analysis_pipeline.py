#!/usr/bin/env python3
"""CLI entrypoint for the FX Analysis Pipeline.

Chains weekly aggregation → monthly review → governance output generation
as a single pipeline. This script replaces the separate weekly and monthly
CLI scripts when run as part of the analysis pipeline.

Modes:
    weekly  — Generate weekly report only (default on non-monthly runs)
    monthly — Generate all weekly reports for the month → monthly review → governance

Environment variables:
    FX_CSV_OUTPUT_DIR       Root CSV output directory (default: ./data/csv)
    FX_PIPELINE_MODE        Pipeline mode: "weekly" or "monthly" (default: auto-detect)
    FX_REPORT_DATE          Report date in YYYYMMDD format (default: today JST)
    FX_WEEK_DAYS            Business days per week (default: 5)
    FX_MONTH_DAYS           Business days per month (default: 20)
    FX_PAIR                 Currency pair (default: USDJPY)
    FX_MAX_EXAMPLES         Max representative case examples (default: 3)
    FX_INCLUDE_ANNOTATIONS  Include annotation-aware metrics (default: true)
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

_JST = ZoneInfo("Asia/Tokyo")


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _fail(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def _resolve_weekly_dates_in_month(
    review_date_jst: datetime,
    business_day_count: int,
    week_days: int,
) -> list[datetime]:
    """Resolve weekly report dates that cover the monthly window.

    Returns a list of report dates (each representing one week's end)
    that collectively cover the month's business days.
    """
    # Walk backwards from review_date to find the month window
    dates: list[datetime] = []
    candidate = review_date_jst.replace(
        hour=0, minute=0, second=0, microsecond=0
    ) - timedelta(days=1)
    while len(dates) < business_day_count:
        if candidate.isoweekday() in range(1, 6):
            dates.append(candidate)
        candidate -= timedelta(days=1)

    dates.reverse()

    # Group into weeks and create report dates (day after each week's last day)
    weekly_report_dates: list[datetime] = []
    for i in range(0, len(dates), week_days):
        week_end_idx = min(i + week_days - 1, len(dates) - 1)
        # Report date is the day after the week's last business day
        report_date = dates[week_end_idx] + timedelta(days=1)
        # Skip to next Monday if report_date is a weekend
        while report_date.isoweekday() > 5:
            report_date += timedelta(days=1)
        weekly_report_dates.append(
            report_date.replace(hour=8, minute=0, second=0, microsecond=0, tzinfo=_JST)
        )

    return weekly_report_dates


def run_weekly_pipeline(
    csv_output_dir: str,
    report_date_jst: datetime,
    week_days: int,
    generated_at_utc: datetime,
) -> dict:
    """Run the weekly report pipeline step."""
    from ugh_quantamental.fx_protocol.analytics_rebuild import rebuild_weekly_report

    print(f"  [weekly] Generating report for {report_date_jst.strftime('%Y-%m-%d')}...")
    return rebuild_weekly_report(
        csv_output_dir,
        report_date_jst,
        business_day_count=week_days,
        generated_at_utc=generated_at_utc,
    )


def run_monthly_pipeline(
    csv_output_dir: str,
    review_date_jst: datetime,
    pair: str,
    month_days: int,
    week_days: int,
    max_examples: int,
    include_annotations: bool,
    generated_at_utc: datetime,
) -> None:
    """Run the full monthly pipeline: weekly reports → monthly review → governance."""
    import json

    from ugh_quantamental.fx_protocol.monthly_governance import run_monthly_governance
    from ugh_quantamental.fx_protocol.monthly_governance_exports import (
        export_governance_artifacts,
    )
    from ugh_quantamental.fx_protocol.monthly_review_exports import rebuild_monthly_review

    # Step 1: Generate weekly reports for each week in the month
    print("\n=== Step 1: Weekly Reports ===")
    weekly_report_dates = _resolve_weekly_dates_in_month(
        review_date_jst, month_days, week_days
    )
    print(f"  Generating {len(weekly_report_dates)} weekly reports...")

    weekly_failures: list[str] = []
    for wdate in weekly_report_dates:
        try:
            run_weekly_pipeline(csv_output_dir, wdate, week_days, generated_at_utc)
        except Exception as exc:
            msg = f"Weekly report for {wdate.strftime('%Y-%m-%d')} failed: {exc}"
            print(f"  [ERROR] {msg}")
            weekly_failures.append(msg)

    if weekly_failures:
        raise RuntimeError(
            f"{len(weekly_failures)} weekly report(s) failed — "
            f"aborting monthly pipeline to prevent incomplete governance outputs. "
            f"Failures: {'; '.join(weekly_failures)}"
        )

    # Step 2: Monthly review
    print("\n=== Step 2: Monthly Review ===")
    review = rebuild_monthly_review(
        csv_output_dir,
        review_date_jst,
        pair=pair,
        business_day_count=month_days,
        max_examples=max_examples,
        include_annotations=include_annotations,
        generated_at_utc=generated_at_utc,
    )
    print(f"  Monthly review generated: {review.get('included_window_count', 0)} windows")

    # Step 3: Load weekly report artifacts for governance
    print("\n=== Step 3: Governance Outputs ===")
    base = os.path.abspath(csv_output_dir)
    weekly_dir = os.path.join(base, "analytics", "weekly")
    weekly_reports: list[dict] = []
    if os.path.isdir(weekly_dir):
        for entry in sorted(os.listdir(weekly_dir)):
            if entry == "latest":
                continue
            report_json = os.path.join(weekly_dir, entry, "weekly_report.json")
            if os.path.isfile(report_json):
                try:
                    with open(report_json, encoding="utf-8") as fh:
                        weekly_reports.append(json.load(fh))
                except (json.JSONDecodeError, OSError) as exc:
                    print(f"  [WARN] Failed to load {report_json}: {exc}")

    # Filter weekly reports to the monthly window and deduplicate by week_window
    from ugh_quantamental.fx_protocol.report_window import resolve_business_day_window

    month_start, month_end = resolve_business_day_window(review_date_jst, month_days)
    seen_windows: set[tuple[str, str]] = set()
    relevant_reports: list[dict] = []
    for wr in weekly_reports:
        ww = wr.get("week_window", {})
        w_start = ww.get("start", "")
        w_end = ww.get("end", "")
        if not w_start or not w_end:
            continue
        # Include if the weekly window overlaps with the monthly window
        if w_end >= month_start and w_start <= month_end:
            window_key = (w_start, w_end)
            if window_key not in seen_windows:
                seen_windows.add(window_key)
                relevant_reports.append(wr)

    # Sort chronologically by week start
    relevant_reports.sort(key=lambda r: r.get("week_window", {}).get("start", ""))
    print(f"  Found {len(relevant_reports)} weekly reports for this month")

    # Step 4: Generate governance outputs
    governance = run_monthly_governance(review, relevant_reports)

    # Use review_month from governance decision log so that the artifact directory
    # matches the reviewed data window (e.g. 202603), not the run date (e.g. 202604).
    dl = governance.get("monthly_decision_log", {})
    month_str = dl.get("review_month", "")
    if not month_str:
        # Fallback: derive from review_date_jst
        if review_date_jst.tzinfo is not None:
            rg_jst = review_date_jst.astimezone(_JST)
        else:
            rg_jst = review_date_jst.replace(tzinfo=_JST)
        month_str = rg_jst.strftime("%Y%m")

    # Export governance artifacts
    paths = export_governance_artifacts(governance, csv_output_dir, month_str)

    # Print governance summary
    print("\n=== Governance Summary ===")
    print(f"  Overall judgment     : {governance['overall_judgment']}")
    dl = governance.get("monthly_decision_log", {})
    flags = dl.get("key_flags", [])
    if flags:
        print(f"  Key flags            : {', '.join(flags)}")
    candidates = governance.get("change_candidate_list", [])
    if candidates:
        print(f"  Change candidates    : {len(candidates)}")
        for cc in candidates:
            print(f"    - [{cc['candidate_id']}] {cc['category']}: {cc['rationale'][:60]}...")
    vr = governance.get("version_decision_record", {})
    print(f"  Version update       : {vr.get('update_performed', False)}")
    print(f"\n  Generated governance artifacts ({len(paths)}):")
    for key, path in paths.items():
        print(f"    - {path}")

    print(f"\n  Recommendation: {dl.get('final_recommendation', 'N/A')}")


def main() -> None:
    csv_output_dir = _env("FX_CSV_OUTPUT_DIR", "./data/csv")
    pipeline_mode = _env("FX_PIPELINE_MODE", "")
    report_date_str = _env("FX_REPORT_DATE", "")
    week_days_str = _env("FX_WEEK_DAYS", "5")
    month_days_str = _env("FX_MONTH_DAYS", "20")
    pair = _env("FX_PAIR", "USDJPY")
    max_examples_str = _env("FX_MAX_EXAMPLES", "3")
    include_annotations_str = _env("FX_INCLUDE_ANNOTATIONS", "true")

    try:
        week_days = int(week_days_str)
        if week_days < 1:
            raise ValueError
    except ValueError:
        _fail(f"FX_WEEK_DAYS must be a positive integer, got: {week_days_str!r}")
        return

    try:
        month_days = int(month_days_str)
        if month_days < 1:
            raise ValueError
    except ValueError:
        _fail(f"FX_MONTH_DAYS must be a positive integer, got: {month_days_str!r}")
        return

    try:
        max_examples = int(max_examples_str)
        if max_examples < 1:
            raise ValueError
    except ValueError:
        _fail(f"FX_MAX_EXAMPLES must be a positive integer, got: {max_examples_str!r}")
        return

    include_annotations = include_annotations_str.lower() in ("true", "1", "yes")

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

    # Auto-detect mode if not specified
    if not pipeline_mode:
        # Monthly on 1st of month, weekly otherwise
        if report_date_jst.day == 1:
            pipeline_mode = "monthly"
        else:
            pipeline_mode = "weekly"

    if pipeline_mode not in ("weekly", "monthly"):
        _fail(f"FX_PIPELINE_MODE must be 'weekly' or 'monthly', got: {pipeline_mode!r}")
        return

    print("=== FX Analysis Pipeline ===")
    print(f"  mode               : {pipeline_mode}")
    print(f"  csv_output_dir     : {os.path.abspath(csv_output_dir)}")
    print(f"  report_date_jst    : {report_date_jst.isoformat()}")
    print(f"  week_days          : {week_days}")
    if pipeline_mode == "monthly":
        print(f"  month_days         : {month_days}")
        print(f"  pair               : {pair}")
        print(f"  max_examples       : {max_examples}")
        print(f"  include_annotations: {include_annotations}")

    if pipeline_mode == "weekly":
        try:
            report = run_weekly_pipeline(
                csv_output_dir, report_date_jst, week_days, generated_at_utc
            )
        except Exception as exc:
            _fail(f"Weekly pipeline failed: {exc}")
            return

        cov = report.get("annotation_coverage", {})
        print("\n=== Weekly Pipeline Summary ===")
        print(f"  observations       : {report.get('observation_count', 0)}")
        print(f"  coverage_rate      : {cov.get('annotation_coverage_rate', 0):.1%}")
        print("\n[OK] Weekly pipeline completed successfully.")

    elif pipeline_mode == "monthly":
        try:
            run_monthly_pipeline(
                csv_output_dir,
                report_date_jst,
                pair=pair,
                month_days=month_days,
                week_days=week_days,
                max_examples=max_examples,
                include_annotations=include_annotations,
                generated_at_utc=generated_at_utc,
            )
        except Exception as exc:
            _fail(f"Monthly pipeline failed: {exc}")
            return

        print("\n[OK] Monthly pipeline completed successfully.")


if __name__ == "__main__":
    main()
