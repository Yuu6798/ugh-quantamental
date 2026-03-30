"""Rebuild analytics and weekly artifacts from persisted CSV history.

This module re-derives all annotation analytics and weekly v2 artifacts
from the ``history/`` directory and ``annotations/`` files.  No forecast
engine is re-executed — everything is reconstructed from persisted records.

Importable without SQLAlchemy.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from ugh_quantamental.fx_protocol.analytics_annotations import (
    build_labeled_observations,
    build_slice_scoreboard,
    build_tag_scoreboard,
    generate_manual_annotation_template,
)
from ugh_quantamental.fx_protocol.weekly_report_exports import (
    export_weekly_report_artifacts,
)
from ugh_quantamental.fx_protocol.weekly_reports_v2 import run_weekly_report_v2

logger = logging.getLogger(__name__)


def rebuild_annotation_analytics(
    csv_output_dir: str,
    *,
    generated_at_utc: datetime | None = None,
    ai_annotations: dict[str, dict[str, str]] | None = None,
) -> dict[str, str | None]:
    """Rebuild all annotation analytics from history and annotation files.

    Does NOT re-run forecasting or outcome evaluation.  Only re-derives:
    - labeled_observations.csv
    - slice_scoreboard.csv
    - tag_scoreboard.csv
    - manual_annotations.template.csv

    Parameters
    ----------
    ai_annotations:
        Optional dict keyed by forecast_id with AI annotation fields.
        When provided, AI annotations become the primary source for labels.

    Returns a dict of artifact keys to absolute paths (or None on failure).
    """
    if generated_at_utc is None:
        generated_at_utc = datetime.now(timezone.utc)

    result: dict[str, str | None] = {
        "manual_annotation_template_path": None,
        "labeled_observations_path": None,
        "slice_scoreboard_path": None,
        "tag_scoreboard_path": None,
    }

    # Step 1: Ensure manual annotation template exists
    try:
        result["manual_annotation_template_path"] = generate_manual_annotation_template(
            csv_output_dir
        )
    except Exception:
        logger.warning("Manual annotation template rebuild failed.", exc_info=True)

    # Step 1b: Generate AI annotations if not provided externally.
    # Uses the deterministic adapter to ensure AI-first analysis is active
    # in the default rebuild path (CLI, GitHub Actions).
    if ai_annotations is None:
        try:
            from ugh_quantamental.fx_protocol.ai_annotations import (
                ai_batch_to_lookup,
                run_ai_annotation_pass,
            )
            # Build a quick observation list from history for the adapter
            _history = os.path.join(os.path.abspath(csv_output_dir), "history")
            if os.path.isdir(_history):
                _obs_for_ai = _collect_eval_rows_for_ai(_history)
                if _obs_for_ai:
                    _batch = run_ai_annotation_pass(
                        _obs_for_ai, generated_at_utc=generated_at_utc,
                    )
                    if _batch:
                        ai_annotations = ai_batch_to_lookup(_batch)
        except Exception:
            logger.warning("Default AI annotation pass failed (non-fatal).", exc_info=True)

    # Step 2: Rebuild labeled observations (must run before scoreboards)
    try:
        result["labeled_observations_path"] = build_labeled_observations(
            csv_output_dir, generated_at_utc, ai_annotations=ai_annotations
        )
    except Exception:
        logger.warning("Labeled observations rebuild failed.", exc_info=True)

    # Step 3: Rebuild slice scoreboard
    try:
        result["slice_scoreboard_path"] = build_slice_scoreboard(
            csv_output_dir, generated_at_utc
        )
    except Exception:
        logger.warning("Slice scoreboard rebuild failed.", exc_info=True)

    # Step 4: Rebuild tag scoreboard
    try:
        result["tag_scoreboard_path"] = build_tag_scoreboard(
            csv_output_dir, generated_at_utc
        )
    except Exception:
        logger.warning("Tag scoreboard rebuild failed.", exc_info=True)

    return result


def rebuild_weekly_report(
    csv_output_dir: str,
    report_date_jst: datetime,
    *,
    business_day_count: int = 5,
    generated_at_utc: datetime | None = None,
    ai_annotations: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Rebuild weekly v2 report and export artifacts.

    Steps:
    1. Rebuild annotation analytics (labeled observations, scoreboards).
    2. Generate the v2 weekly report from rebuilt data.
    3. Export artifacts (JSON, MD, CSV) to dated and latest directories.

    Does NOT re-run forecast engine.

    Returns the v2 report dict with ``generated_artifact_paths`` populated.
    """
    if generated_at_utc is None:
        generated_at_utc = datetime.now(timezone.utc)

    # Step 0: Remove stale labeled_observations.csv so that if rebuild fails,
    # run_weekly_report_v2 cannot silently use outdated data.
    stale_obs = os.path.join(
        os.path.abspath(csv_output_dir), "analytics", "labeled_observations.csv"
    )
    if os.path.isfile(stale_obs):
        os.remove(stale_obs)

    # Step 1: Rebuild analytics first
    analytics_result = rebuild_annotation_analytics(
        csv_output_dir, generated_at_utc=generated_at_utc,
        ai_annotations=ai_annotations,
    )

    # Guard: if labeled observations were not regenerated, raise to prevent
    # silently publishing an empty or stale weekly report.
    if analytics_result.get("labeled_observations_path") is None:
        raise RuntimeError(
            "labeled_observations rebuild produced no output; "
            "cannot generate weekly report without fresh observation data. "
            "Check that history/ contains forecast and evaluation CSVs."
        )

    # Step 2: Generate v2 report
    report = run_weekly_report_v2(
        csv_output_dir,
        report_date_jst,
        business_day_count=business_day_count,
        generated_at_utc=generated_at_utc,
    )

    # Step 3: Export artifacts
    if report_date_jst.tzinfo is not None:
        from zoneinfo import ZoneInfo

        _JST = ZoneInfo("Asia/Tokyo")
        dt = report_date_jst.astimezone(_JST)
    else:
        dt = report_date_jst
    date_str = dt.strftime("%Y%m%d")
    export_weekly_report_artifacts(report, csv_output_dir, date_str)

    return report


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _collect_eval_rows_for_ai(history_dir: str) -> list[dict[str, str]]:
    """Collect evaluated forecast rows from history for the AI annotation adapter.

    Uses cross-batch join: evaluations live in the *next* day's batch,
    so we build a global forecast_id → evaluation index first, then
    iterate over forecasts and merge matched evaluations.
    """
    import csv as _csv

    # Pass 1: global evaluation index across all batches
    global_evals: dict[str, dict[str, str]] = {}
    for date_dir in sorted(os.listdir(history_dir)):
        date_path = os.path.join(history_dir, date_dir)
        if not os.path.isdir(date_path):
            continue
        for batch_dir in sorted(os.listdir(date_path)):
            eval_csv = os.path.join(date_path, batch_dir, "evaluation.csv")
            if not os.path.isfile(eval_csv):
                continue
            with open(eval_csv, newline="", encoding="utf-8") as fh:
                for r in _csv.DictReader(fh):
                    fid = r.get("forecast_id", "")
                    if fid:
                        global_evals[fid] = r

    # Pass 2: iterate forecasts, merge with global evaluation index
    rows: list[dict[str, str]] = []
    for date_dir in sorted(os.listdir(history_dir)):
        date_path = os.path.join(history_dir, date_dir)
        if not os.path.isdir(date_path):
            continue
        for batch_dir in sorted(os.listdir(date_path)):
            forecast_csv = os.path.join(date_path, batch_dir, "forecast.csv")
            if not os.path.isfile(forecast_csv):
                continue
            with open(forecast_csv, newline="", encoding="utf-8") as fh:
                for fc in _csv.DictReader(fh):
                    fid = fc.get("forecast_id", "")
                    if not fid:
                        continue
                    ev = global_evals.get(fid)
                    if not ev:
                        continue
                    merged = dict(fc)
                    merged.update(ev)
                    rows.append(merged)
    return rows
