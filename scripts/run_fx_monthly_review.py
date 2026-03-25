#!/usr/bin/env python3
"""CLI entrypoint for generating the FX Monthly Review v1.

Reads persisted CSV history, annotations, and provider health to produce
monthly review artifacts without re-running any forecast or evaluation logic.

Environment variables:
    FX_CSV_OUTPUT_DIR      Root CSV output directory (default: ./data/csv)
    FX_REVIEW_DATE         Review date in YYYYMMDD format (default: today JST)
    FX_MONTH_DAYS          Number of business days to include (default: 20)
    FX_PAIR                Currency pair (default: USDJPY)
    FX_MAX_EXAMPLES        Max representative case examples (default: 3)
    FX_INCLUDE_ANNOTATIONS Include annotation-aware metrics (default: true)
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
    month_days_str = _env("FX_MONTH_DAYS", "20")
    review_date_str = _env("FX_REVIEW_DATE", "")
    pair = _env("FX_PAIR", "USDJPY")
    max_examples_str = _env("FX_MAX_EXAMPLES", "3")
    include_annotations_str = _env("FX_INCLUDE_ANNOTATIONS", "true")

    try:
        business_day_count = int(month_days_str)
        if business_day_count < 1:
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

    if review_date_str:
        try:
            review_date_jst = datetime.strptime(review_date_str, "%Y%m%d").replace(
                hour=8, minute=0, second=0, tzinfo=_JST
            )
        except ValueError:
            _fail(f"FX_REVIEW_DATE must be YYYYMMDD, got: {review_date_str!r}")
            return
    else:
        review_date_jst = datetime.now(_JST).replace(
            hour=8, minute=0, second=0, microsecond=0
        )

    generated_at_utc = datetime.now(timezone.utc)

    if not os.path.isdir(csv_output_dir):
        _fail(f"FX_CSV_OUTPUT_DIR does not exist: {csv_output_dir}")
        return

    print("=== FX Monthly Review v1 ===")
    print(f"  csv_output_dir       : {os.path.abspath(csv_output_dir)}")
    print(f"  review_date_jst      : {review_date_jst.isoformat()}")
    print(f"  business_day_count   : {business_day_count}")
    print(f"  pair                 : {pair}")
    print(f"  max_examples         : {max_examples}")
    print(f"  include_annotations  : {include_annotations}")
    print()

    # Deferred import to keep startup fast
    from ugh_quantamental.fx_protocol.monthly_review_exports import rebuild_monthly_review

    try:
        review = rebuild_monthly_review(
            csv_output_dir,
            review_date_jst,
            pair=pair,
            business_day_count=business_day_count,
            max_examples=max_examples,
            include_annotations=include_annotations,
            generated_at_utc=generated_at_utc,
        )
    except Exception as exc:
        _fail(f"Monthly review generation failed: {exc}")
        return

    # Print summary
    cov = review.get("annotation_coverage_summary", {})
    print("=== Monthly Review v1 Summary ===")
    print(f"  requested_windows    : {review.get('requested_window_count', 0)}")
    print(f"  included_windows     : {review.get('included_window_count', 0)}")
    print(f"  missing_windows      : {review.get('missing_window_count', 0)}")
    print(f"  confirmed            : {cov.get('confirmed_count', 0)}")
    print(f"  pending              : {cov.get('pending_count', 0)}")
    print(f"  unlabeled            : {cov.get('unlabeled_count', 0)}")
    cov_rate = cov.get("annotation_coverage_rate", 0)
    print(f"  coverage_rate        : {cov_rate:.1%}")
    print(
        f"  strategy_metrics     : "
        f"{len(review.get('monthly_strategy_metrics', []))} strategies"
    )

    # Review flags
    flags = review.get("review_flags", [])
    if flags:
        print(f"\n  Review flags ({len(flags)}):")
        for f in flags:
            print(f"    - [{f.get('flag', '')}] {f.get('reason', '')}")

    # Recommendation
    rec = review.get("recommendation_summary", "")
    if rec:
        print(f"\n  Recommendation: {rec}")

    # Artifacts
    artifacts = review.get("generated_artifact_paths", [])
    if artifacts:
        print(f"\n  Generated artifacts ({len(artifacts)}):")
        for p in artifacts:
            print(f"    - {p}")

    # Provider health
    ph = review.get("provider_health_summary", {})
    if ph.get("total_runs", 0) > 0:
        print(
            f"\n  Provider health: {ph.get('success_count', 0)} success, "
            f"{ph.get('failed_count', 0)} failed, "
            f"{ph.get('fallback_adjustment_count', 0)} fallbacks, "
            f"{ph.get('lagged_snapshot_count', 0)} lagged"
        )

    print("\n[OK] Monthly review v1 generated successfully.")


if __name__ == "__main__":
    main()
