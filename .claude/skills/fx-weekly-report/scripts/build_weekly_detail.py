#!/usr/bin/env python3
"""Build the daily forecast-vs-actual detail for one FX weekly report.

Read-only helper for the ``fx-weekly-report`` skill. Reads persisted CSV
artifacts from a checkout of the ``fx-daily-data`` branch and prints:

- per-day forecast vs realized outcome per strategy (direction / range /
  state-correctness / close error),
- the UGH alpha state & conviction trajectory,
- per-day AI annotation labels (regime / volatility / intervention / tags),
- failure_reason annotations,
- the carry-over evaluation of the previous week's Friday forecast.

Usage:
    python build_weekly_detail.py --csv-dir <data-checkout>/csv --week-start YYYYMMDD

``--week-start`` is the Monday of the target week. The previous Friday
(week_start - 3 days) is included automatically as the carry-over row.
Never writes anything.
"""

from __future__ import annotations

import argparse
import csv
import glob
import os
import re
import sys
from datetime import datetime, timedelta

STRATEGIES = [
    "baseline_prev_day_direction",
    "baseline_random_walk",
    "baseline_simple_technical",
    "ugh_v2_alpha",
    "ugh_v2_beta",
    "ugh_v2_gamma",
    "ugh_v2_delta",
]


def _load_forecasts(base: str, dates: list[str]) -> dict[tuple[str, str], dict]:
    # Key by the forecast's own as_of date, not the directory date: outcome
    # catch-up republishes a recovered window's forecast.csv under the
    # window's END-date directory, and keying by directory would present the
    # 8/27 batch as an "8/28 forecast" (observed 2026-09-05).
    fc: dict[tuple[str, str], dict] = {}
    wanted = set(dates)
    for d in dates:
        for f in glob.glob(f"{base}/history/{d}/*/forecast.csv"):
            with open(f, newline="") as fh:
                for r in csv.DictReader(fh):
                    as_of = r.get("as_of_jst", "")[:10].replace("-", "") or d
                    if as_of in wanted:
                        fc.setdefault((as_of, r["strategy_kind"]), r)
    return fc


def _load_outcomes(base: str) -> dict[str, dict]:
    oc: dict[str, dict] = {}
    for f in glob.glob(f"{base}/outcomes/*_outcome.csv"):
        with open(f, newline="") as fh:
            for r in csv.DictReader(fh):
                oc[r["window_start_jst"][:10].replace("-", "")] = r
    return oc


def _load_evaluations(base: str) -> dict[tuple[str, str], dict]:
    ev: dict[tuple[str, str], dict] = {}
    for f in glob.glob(f"{base}/evaluations/*_evaluation.csv"):
        with open(f, newline="") as fh:
            for r in csv.DictReader(fh):
                m = re.search(r"fc_[A-Z]+_(\d{8})T", r["forecast_id"])
                if m:
                    ev[(m.group(1), r["strategy_kind"])] = r
    return ev


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv-dir", required=True, help="csv/ root of the fx-daily-data checkout")
    ap.add_argument("--week-start", required=True, help="Monday of the target week, YYYYMMDD")
    args = ap.parse_args()

    base = args.csv_dir.rstrip("/")
    if not os.path.isdir(base):
        print(f"[ERROR] csv dir not found: {base}", file=sys.stderr)
        sys.exit(1)

    monday = datetime.strptime(args.week_start, "%Y%m%d")
    if monday.weekday() != 0:
        print(f"[WARN] {args.week_start} is not a Monday (weekday={monday.weekday()})",
              file=sys.stderr)
    prev_friday = monday - timedelta(days=3)
    week = [monday + timedelta(days=i) for i in range(5)]
    dates = [prev_friday.strftime("%Y%m%d")] + [d.strftime("%Y%m%d") for d in week]

    fc = _load_forecasts(base, dates)
    oc = _load_outcomes(base)
    ev = _load_evaluations(base)

    for d in dates:
        tag = " (carry-over)" if d == dates[0] else ""
        o = oc.get(d)
        header = f"--- {d}{tag} ---"
        if o:
            print(f"{header} realized {o['realized_open']}->{o['realized_close']} "
                  f"({float(o['realized_close_change_bp']):+.1f}bp, {o['realized_direction']}) "
                  f"range {o['realized_low']}-{o['realized_high']}")
        else:
            print(f"{header} (outcome pending)")
        for s in STRATEGIES:
            f = fc.get((d, s))
            e = ev.get((d, s))
            if not f:
                continue
            hit = ("HIT" if e["direction_hit"] == "True" else "miss") if e else "pending"
            rng = (e["range_hit"] or "-") if e else "-"
            stc = (e.get("state_correctness_hit", "") or "-") if e else "-"
            err = f"{float(e['close_error_bp']):.1f}bp" if e else ""
            print(f"  {s:32s} {f['forecast_direction']:5s} "
                  f"exp{float(f['expected_close_change_bp'] or 0):+6.1f} "
                  f"{hit:7s} rng:{rng:5s} stC:{stc:5s} {err}")
        print()

    print("=== UGH alpha state/conviction ===")
    for d in dates:
        f = fc.get((d, "ugh_v2_alpha"))
        if f:
            rng = (f"range {float(f['expected_range_low']):.2f}-"
                   f"{float(f['expected_range_high']):.2f}") if f["expected_range_low"] else ""
            print(f"{d} state: {f['dominant_state']} conv: {f['conviction'][:5]} "
                  f"dir: {f['forecast_direction']} {rng}")

    labeled = f"{base}/analytics/labeled_observations.csv"
    if os.path.isfile(labeled):
        print()
        with open(labeled, newline="") as fh:
            rows = [r for r in csv.DictReader(fh)
                    if r["as_of_jst"][:10].replace("-", "") in dates]
        seen: set[str] = set()
        for r in rows:
            day = r["as_of_jst"][:10]
            if day in seen:
                continue
            seen.add(day)
            print(f"{day} | regime: {r['regime_label']} | vol: {r['volatility_label']} "
                  f"| interv: {r['intervention_risk']} | tags: {r['effective_event_tags'] or '-'}")
        for r in rows:
            if r["ai_failure_reason"]:
                print(f"failure: {r['as_of_jst'][:10]} {r['strategy_kind']} "
                      f"{r['ai_failure_reason']}")


if __name__ == "__main__":
    main()
