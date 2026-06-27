"""End-to-end tests for FX-ANNOT-LIVE: the live annotation wiring.

These guard the root cause behind "weekly 28/28 unannotated": the daily live
path (``run_annotation_analytics``) must wire deterministic AI + OHLC fallback
labels into ``labeled_observations.csv`` so that effective coverage is > 0 and
the downstream weekly / monthly slices actually populate (rather than
collapsing to ``label=all`` / empty). No API key, network, or randomness.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime, timezone

from zoneinfo import ZoneInfo

from ugh_quantamental.fx_protocol.analytics_annotations import run_annotation_analytics
from ugh_quantamental.fx_protocol.analytics_rebuild import rebuild_weekly_report
from ugh_quantamental.fx_protocol.annotation_sources import build_annotation_source_summary
from ugh_quantamental.fx_protocol.labeled_observations import (
    _resolve_annotation_status,
    build_labeled_observations,
)
from ugh_quantamental.fx_protocol.monthly_review import compute_monthly_regime_metrics
from ugh_quantamental.fx_protocol.weekly_report_exports import (
    export_weekly_ai_annotation_summary_csv,
    export_weekly_annotation_coverage_csv,
)
from ugh_quantamental.fx_protocol.weekly_reports_v2 import (
    build_annotation_field_coverage,
    build_slice_metrics,
)

_JST = ZoneInfo("Asia/Tokyo")
_UTC = timezone.utc
_NOW = datetime(2026, 3, 27, 6, 0, 0, tzinfo=_UTC)

_FORECAST_FIELDNAMES = [
    "forecast_id", "forecast_batch_id", "pair", "strategy_kind", "as_of_jst",
    "window_end_jst", "forecast_direction", "expected_close_change_bp",
]
_EVAL_FIELDNAMES = [
    "evaluation_id", "forecast_id", "outcome_id", "pair", "strategy_kind",
    "direction_hit", "range_hit", "close_error_bp", "magnitude_error_bp",
    "state_proxy_hit",
]
_OUTCOME_FIELDNAMES = [
    "outcome_id", "pair", "window_start_jst", "window_end_jst",
    "realized_open", "realized_high", "realized_low", "realized_close",
    "realized_direction", "realized_close_change_bp", "event_tags",
]


def _write_csv(path: str, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_day(
    tmpdir: str,
    *,
    date_str: str,
    as_of: str,
    day_index: int,
    high: float = 150.6,
    low: float = 149.6,
) -> None:
    """Write one business day's forecast/eval/outcome for a single UGH forecast.

    Steadily rising close (consistent positive change) so the OHLC fallback
    classifies the series as trending.
    """
    batch_dir = os.path.join(tmpdir, "history", date_str, "batch_001")
    fid = f"fc_{day_index:03d}"
    oid = f"oc_{day_index:03d}"
    open_px = 150.0 + day_index * 0.2
    close_px = open_px + 0.15

    _write_csv(os.path.join(batch_dir, "forecast.csv"), [{
        "forecast_id": fid,
        "forecast_batch_id": "batch_001",
        "pair": "USDJPY",
        "strategy_kind": "ugh",
        "as_of_jst": as_of,
        "forecast_direction": "up",
        "expected_close_change_bp": "10.0",
    }], _FORECAST_FIELDNAMES)

    _write_csv(os.path.join(batch_dir, "evaluation.csv"), [{
        "evaluation_id": f"ev_{day_index:03d}",
        "forecast_id": fid,
        "outcome_id": oid,
        "pair": "USDJPY",
        "strategy_kind": "ugh",
        "direction_hit": "True",
        "range_hit": "True",
        "close_error_bp": "5.0",
        "magnitude_error_bp": "3.0",
        "state_proxy_hit": "",
    }], _EVAL_FIELDNAMES)

    _write_csv(os.path.join(batch_dir, "outcome.csv"), [{
        "outcome_id": oid,
        "pair": "USDJPY",
        "window_start_jst": as_of,
        "window_end_jst": as_of,
        "realized_open": f"{open_px:.2f}",
        "realized_high": f"{high + day_index * 0.2:.2f}",
        "realized_low": f"{low + day_index * 0.2:.2f}",
        "realized_close": f"{close_px:.2f}",
        "realized_direction": "up",
        "realized_close_change_bp": "12.0",
        "event_tags": "",
    }], _OUTCOME_FIELDNAMES)


def _setup_history(tmpdir: str, days: int = 6) -> str:
    for i in range(days):
        date_str = f"202603{16 + i:02d}"
        as_of = f"2026-03-{16 + i:02d}T08:00:00+09:00"
        _write_day(tmpdir, date_str=date_str, as_of=as_of, day_index=i)
    return os.path.join(tmpdir, "analytics", "labeled_observations.csv")


def _read_rows(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class TestDailyLivePath:
    def test_daily_path_populates_effective_coverage(self, tmp_path) -> None:
        tmpdir = str(tmp_path)
        obs_path = _setup_history(tmpdir)

        result = run_annotation_analytics(
            tmpdir, datetime(2026, 3, 21, 8, 0, 0, tzinfo=_JST), generated_at_utc=_NOW
        )
        assert result["labeled_observations_path"] is not None
        rows = _read_rows(obs_path)
        assert rows

        # Effective coverage > 0: every row carries a market-derived regime
        # and volatility label, a non-none source, and confirmed status.
        assert all(r["regime_label"] for r in rows)
        assert all(r["volatility_label"] for r in rows)
        assert all(r["annotation_source"] != "none" for r in rows)
        assert all(r["annotation_status"] == "confirmed" for r in rows)
        # No leakage vocabulary: regime is from the shared axis only.
        assert all(r["regime_label"] in ("trending", "choppy") for r in rows)
        assert all(r["volatility_label"] in ("low", "normal", "high") for r in rows)

    def test_weekly_slice_not_collapsed_to_all(self, tmp_path) -> None:
        tmpdir = str(tmp_path)
        obs_path = _setup_history(tmpdir)
        run_annotation_analytics(
            tmpdir, datetime(2026, 3, 21, 8, 0, 0, tzinfo=_JST), generated_at_utc=_NOW
        )
        rows = _read_rows(obs_path)

        slices = build_slice_metrics(rows)
        regime_slices = [s for s in slices if s.get("slice_dimension") == "regime_label"]
        assert regime_slices
        labels = {s["label"] for s in regime_slices}
        # Annotated rows must produce real labels, not the unannotated "all".
        assert labels & {"trending", "choppy"}
        assert labels != {"all"}

    def test_monthly_regime_slice_non_empty(self, tmp_path) -> None:
        tmpdir = str(tmp_path)
        obs_path = _setup_history(tmpdir)
        run_annotation_analytics(
            tmpdir, datetime(2026, 3, 21, 8, 0, 0, tzinfo=_JST), generated_at_utc=_NOW
        )
        rows = _read_rows(obs_path)

        regime_metrics = compute_monthly_regime_metrics(rows)
        labels = {m["regime_label"] for m in regime_metrics}
        # The confirmed market-derived rows populate a real regime bucket,
        # not only the "unlabeled" catch-all.
        assert labels - {"unlabeled"}


class TestWeeklyRebuildPath:
    def test_rebuild_weekly_report_populates_labels(self, tmp_path) -> None:
        tmpdir = str(tmp_path)
        obs_path = _setup_history(tmpdir)
        rebuild_weekly_report(
            tmpdir,
            datetime(2026, 3, 21, 8, 0, 0, tzinfo=_JST),
            generated_at_utc=_NOW,
        )
        rows = _read_rows(obs_path)
        assert rows
        assert all(r["annotation_source"] != "none" for r in rows)
        assert all(r["regime_label"] in ("trending", "choppy") for r in rows)


class TestFallbackPrecedence:
    def test_fallback_does_not_override_higher_sources(self, tmp_path) -> None:
        """AI / manual labels win; fallback only fills what they leave empty."""
        tmpdir = str(tmp_path)
        obs_path = _setup_history(tmpdir, days=3)

        ai = {"fc_001": {"ai_regime_label": "choppy"}}
        fallback = {
            "fc_001": {"regime_label": "trending", "volatility_label": "high"},
            "fc_002": {"regime_label": "trending", "volatility_label": "low"},
        }
        build_labeled_observations(
            tmpdir, _NOW, ai_annotations=ai, fallback_annotations=fallback
        )
        # labeled_observations rows carry as_of_jst (not forecast_id); fc_001
        # is day index 1 (2026-03-17), fc_002 is day index 2 (2026-03-18).
        rows = {r["as_of_jst"][:10]: r for r in _read_rows(obs_path)}
        fc1 = rows["2026-03-17"]
        fc2 = rows["2026-03-18"]

        # fc_001: AI regime wins, fallback volatility fills the empty field.
        assert fc1["regime_label"] == "choppy"
        assert fc1["annotation_source"] == "ai"
        assert fc1["volatility_label"] == "high"
        # fc_002: no AI -> fallback supplies both labels (lowest tier).
        assert fc2["regime_label"] == "trending"
        assert fc2["annotation_source"] == "ohlc_fallback"
        assert fc2["annotation_status"] == "confirmed"

    def test_no_annotations_leaves_rows_unannotated(self, tmp_path) -> None:
        tmpdir = str(tmp_path)
        obs_path = _setup_history(tmpdir, days=3)
        build_labeled_observations(tmpdir, _NOW)
        rows = _read_rows(obs_path)
        assert all(r["annotation_source"] == "none" for r in rows)
        assert all(not r["regime_label"] for r in rows)

    def test_pending_manual_not_promoted_by_fallback(self, tmp_path) -> None:
        """A pending manual annotation must stay pending even when a fallback
        label is available (manual outranks fallback; regression for
        PR #116 review)."""
        tmpdir = str(tmp_path)
        obs_path = _setup_history(tmpdir, days=3)
        # Manual annotation for 2026-03-17 (fc_001), pending, regime only.
        _write_csv(
            os.path.join(tmpdir, "annotations", "manual_annotations.csv"),
            [{
                "as_of_jst": "2026-03-17T08:00:00+09:00",
                "regime_label": "choppy",
                "event_tags": "",
                "volatility_label": "",
                "intervention_risk": "",
                "notes": "",
                "annotation_status": "pending",
            }],
            ["as_of_jst", "regime_label", "event_tags", "volatility_label",
             "intervention_risk", "notes", "annotation_status"],
        )
        fallback = {"fc_001": {"regime_label": "trending", "volatility_label": "high"}}
        build_labeled_observations(tmpdir, _NOW, fallback_annotations=fallback)
        row = {r["as_of_jst"][:10]: r for r in _read_rows(obs_path)}["2026-03-17"]

        assert row["regime_label"] == "choppy"  # manual wins over fallback
        assert row["annotation_source"] == "manual_compat"
        assert row["annotation_status"] == "pending"  # NOT promoted to confirmed


class TestResolveAnnotationStatus:
    def test_ai_label_confirmed(self) -> None:
        assert _resolve_annotation_status({"ai", "none"}, "") == "confirmed"

    def test_fallback_with_auto_tag_stays_confirmed(self) -> None:
        # Auto event tags must NOT strip confirmation off a fallback-labeled row.
        assert _resolve_annotation_status({"ohlc_fallback", "none"}, "") == "confirmed"

    def test_pending_manual_label_not_promoted(self) -> None:
        assert _resolve_annotation_status({"manual_compat", "ohlc_fallback"}, "pending") == "pending"

    def test_confirmed_manual_label_kept(self) -> None:
        assert _resolve_annotation_status({"manual_compat", "none"}, "confirmed") == "confirmed"

    def test_no_label_carries_manual_status(self) -> None:
        assert _resolve_annotation_status({"none"}, "") == ""


class TestFallbackConfirmationWithAutoTags:
    def test_month_end_fallback_row_is_confirmed(self, tmp_path) -> None:
        """A fallback-labeled row that also has a month_end calendar auto tag
        must still be annotation_status=confirmed (regression for PR #116)."""
        tmpdir = str(tmp_path)
        # 2026-03-31 is the last business day of March -> month_end auto tag.
        _write_day(
            tmpdir, date_str="20260331",
            as_of="2026-03-31T08:00:00+09:00", day_index=1,
        )
        obs_path = os.path.join(tmpdir, "analytics", "labeled_observations.csv")
        fallback = {"fc_001": {"regime_label": "trending", "volatility_label": "low"}}
        build_labeled_observations(tmpdir, _NOW, fallback_annotations=fallback)
        row = _read_rows(obs_path)[0]

        assert "month_end" in row["event_tags"]          # auto tag present
        assert row["annotation_source"] == "auto_only"   # auto wins source
        assert row["regime_label"] == "trending"         # fallback label kept
        assert row["annotation_status"] == "confirmed"   # still confirmed


class TestSourceSummaryCountsFallback:
    def test_fallback_rows_counted_and_buckets_sum(self) -> None:
        observations = [
            {"annotation_source": "ohlc_fallback"},
            {"annotation_source": "ohlc_fallback"},
            {"annotation_source": "ai"},
            {"annotation_source": "none"},
        ]
        summary = build_annotation_source_summary(observations)
        assert summary["fallback_annotated_count"] == 2
        assert summary["ai_annotated_count"] == 1
        assert summary["unannotated_count"] == 1
        bucket_sum = (
            summary["ai_annotated_count"]
            + summary["auto_annotated_count"]
            + summary["manual_annotated_count"]
            + summary["fallback_annotated_count"]
            + summary["unannotated_count"]
        )
        assert bucket_sum == summary["total_observations"] == 4


class TestFieldCoverageAttribution:
    def test_fallback_not_counted_as_manual(self) -> None:
        """Fallback-won regime/volatility must report as fallback, not manual."""
        observations = [
            {  # fallback won regime + volatility (ai empty)
                "ai_regime_label": "", "regime_label": "trending",
                "fallback_regime_label": "trending",
                "ai_volatility_label": "", "volatility_label": "low",
                "fallback_volatility_label": "low",
            },
            {  # manual won regime (ai empty, no fallback column)
                "ai_regime_label": "", "regime_label": "choppy",
                "fallback_regime_label": "",
            },
        ]
        cov = build_annotation_field_coverage(observations)
        assert cov["regime_label"]["fallback_populated_count"] == 1
        assert cov["regime_label"]["manual_populated_count"] == 1  # only the manual row
        assert cov["volatility_label"]["fallback_populated_count"] == 1
        assert cov["volatility_label"]["manual_populated_count"] == 0


class TestWeeklyExportsThreadFallback:
    def test_summary_csv_includes_fallback(self, tmp_path) -> None:
        report = {
            "annotation_source_summary": {
                "total_observations": 3, "ai_annotated_count": 0,
                "auto_annotated_count": 0, "manual_annotated_count": 0,
                "fallback_annotated_count": 3, "unannotated_count": 0,
                "evidence_ref_count": 0,
            },
        }
        path = export_weekly_ai_annotation_summary_csv(report, str(tmp_path))
        metrics = {r["metric"]: r["value"] for r in _read_rows(path)}
        assert metrics["fallback_annotated_count"] == "3"

    def test_coverage_csv_includes_fallback_columns(self, tmp_path) -> None:
        report = {
            "annotation_field_coverage": {
                "regime_label": {
                    "total_observations": 2, "fallback_populated_count": 2,
                    "fallback_populated_rate": 1.0, "manual_populated_count": 0,
                    "effective_populated_count": 2,
                },
            },
        }
        path = export_weekly_annotation_coverage_csv(report, str(tmp_path))
        rows = {r["field"]: r for r in _read_rows(path)}
        assert rows["regime_label"]["fallback_populated_count"] == "2"
