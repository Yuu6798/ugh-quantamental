"""Tests for analytics_annotations.py — annotation + analytics layer."""

from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from ugh_quantamental.fx_protocol.analytics_annotations import (
    AI_ANNOTATION_FIELDNAMES,
    LABELED_OBSERVATION_FIELDNAMES,
    MANUAL_ANNOTATION_FIELDNAMES,
    SLICE_SCOREBOARD_FIELDNAMES,
    TAG_SCOREBOARD_FIELDNAMES,
    _build_event_tag_fields,
    _derive_auto_event_tags,
    _is_last_business_day_of_month,
    build_labeled_observations,
    build_slice_scoreboard,
    build_tag_scoreboard,
    generate_ai_annotations,
    generate_manual_annotation_template,
    load_manual_annotations,
    run_annotation_analytics,
)
from ugh_quantamental.fx_protocol.csv_exports import (
    EVALUATION_FIELDNAMES,
    FORECAST_FIELDNAMES,
    OUTCOME_FIELDNAMES,
)

_JST = ZoneInfo("Asia/Tokyo")
_UTC = timezone.utc
_NOW = datetime(2026, 3, 16, 6, 0, 0, tzinfo=_UTC)
_AS_OF = datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST)


# ---------------------------------------------------------------------------
# Helpers: create minimal history CSVs
# ---------------------------------------------------------------------------


def _write_csv(path: str, fieldnames: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _make_forecast_row(
    as_of_jst: str = "2026-03-13T08:00:00+09:00",
    forecast_id: str = "fc-001",
    batch_id: str = "batch-001",
    strategy: str = "ugh",
    direction: str = "up",
    change_bp: str = "10.0",
) -> dict[str, str]:
    return {
        "forecast_id": forecast_id,
        "forecast_batch_id": batch_id,
        "pair": "USDJPY",
        "strategy_kind": strategy,
        "as_of_jst": as_of_jst,
        "window_end_jst": "2026-03-16T08:00:00+09:00",
        "forecast_direction": direction,
        "expected_close_change_bp": change_bp,
        "expected_range_low": "149.0",
        "expected_range_high": "150.0",
        "primary_question": "",
        "dominant_state": "setup",
        "prob_dormant": "0.1",
        "prob_setup": "0.5",
        "prob_fire": "0.15",
        "prob_expansion": "0.1",
        "prob_exhaustion": "0.1",
        "prob_failure": "0.05",
        "q_dir": "positive",
        "q_strength": "0.5",
        "s_q": "0.5",
        "temporal_score": "0.5",
        "grv_raw": "0.5",
        "grv_lock": "0.5",
        "alignment": "0.5",
        "e_star": "10.0",
        "mismatch_px": "0.1",
        "mismatch_sem": "0.1",
        "conviction": "0.5",
        "urgency": "0.5",
        "disconfirmer_rule_count": "0",
        "theory_version": "v1",
        "engine_version": "v1",
        "schema_version": "v1",
        "protocol_version": "v1",
        "market_data_vendor": "test",
        "market_data_feed_name": "test",
        "market_data_price_type": "mid",
        "market_data_resolution": "1d",
        "market_data_timezone": "Asia/Tokyo",
    }


def _make_outcome_row(
    direction: str = "up",
    change_bp: str = "12.5",
) -> dict[str, str]:
    return {
        "outcome_id": "out-001",
        "pair": "USDJPY",
        "window_start_jst": "2026-03-13T08:00:00+09:00",
        "window_end_jst": "2026-03-16T08:00:00+09:00",
        "realized_open": "149.5",
        "realized_high": "150.2",
        "realized_low": "149.1",
        "realized_close": "149.7",
        "realized_direction": direction,
        "realized_close_change_bp": change_bp,
        "realized_range_price": "1.1",
        "event_happened": "True",
        "event_tags": "fomc|cpi_us",
        "schema_version": "v1",
        "protocol_version": "v1",
        "market_data_vendor": "test",
        "market_data_feed_name": "test",
        "market_data_price_type": "mid",
        "market_data_resolution": "1d",
        "market_data_timezone": "Asia/Tokyo",
    }


def _make_eval_row(
    forecast_id: str = "fc-001",
    strategy: str = "ugh",
    direction_hit: str = "True",
    range_hit: str = "True",
    state_proxy_hit: str = "True",
    close_error_bp: str = "2.5",
    magnitude_error_bp: str = "2.5",
) -> dict[str, str]:
    return {
        "evaluation_id": f"eval-{forecast_id}",
        "forecast_id": forecast_id,
        "outcome_id": "out-001",
        "pair": "USDJPY",
        "strategy_kind": strategy,
        "direction_hit": direction_hit,
        "range_hit": range_hit,
        "close_error_bp": close_error_bp,
        "magnitude_error_bp": magnitude_error_bp,
        "state_proxy_hit": state_proxy_hit,
        "mismatch_change_bp": "2.5",
        "realized_state_proxy": "setup",
        "actual_state_change": "False",
        "disconfirmers_hit": "",
        "disconfirmer_explained": "",
        "evaluated_at_utc": "2026-03-16T06:00:00+00:00",
        "theory_version": "v1",
        "engine_version": "v1",
        "schema_version": "v1",
        "protocol_version": "v1",
    }


def _setup_history(tmpdir: str, date_str: str = "20260313", batch_id: str = "batch-001") -> str:
    """Create a minimal history directory with forecast, outcome, evaluation CSVs."""
    batch_path = os.path.join(tmpdir, "history", date_str, batch_id)
    os.makedirs(batch_path, exist_ok=True)

    forecasts = [
        _make_forecast_row(strategy="ugh", forecast_id="fc-001"),
        _make_forecast_row(strategy="baseline_random_walk", forecast_id="fc-002",
                           direction="flat", change_bp="0.0"),
    ]
    _write_csv(
        os.path.join(batch_path, "forecast.csv"),
        FORECAST_FIELDNAMES,
        forecasts,
    )
    _write_csv(
        os.path.join(batch_path, "outcome.csv"),
        OUTCOME_FIELDNAMES,
        [_make_outcome_row()],
    )
    evals = [
        _make_eval_row(forecast_id="fc-001", strategy="ugh"),
        _make_eval_row(
            forecast_id="fc-002", strategy="baseline_random_walk",
            range_hit="", state_proxy_hit="",
        ),
    ]
    _write_csv(
        os.path.join(batch_path, "evaluation.csv"),
        EVALUATION_FIELDNAMES,
        evals,
    )
    return tmpdir


# ---------------------------------------------------------------------------
# Test: AI annotation generation
# ---------------------------------------------------------------------------


class TestGenerateAiAnnotations:
    def test_generates_file(self, tmp_path: str) -> None:
        tmpdir = str(tmp_path)
        _setup_history(tmpdir)
        path = generate_ai_annotations(tmpdir, _AS_OF, _NOW)
        assert path is not None
        assert os.path.isfile(path)
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        assert len(rows) >= 1
        row = rows[-1]
        assert row["as_of_jst"] == _AS_OF.isoformat()
        for col in AI_ANNOTATION_FIELDNAMES:
            assert col in row

    def test_no_history_still_succeeds(self, tmp_path: str) -> None:
        """AI annotation generation should not crash with empty history."""
        tmpdir = str(tmp_path)
        path = generate_ai_annotations(tmpdir, _AS_OF, _NOW)
        assert path is not None
        assert os.path.isfile(path)

    def test_idempotent_rerun(self, tmp_path: str) -> None:
        """Rerunning for the same as_of_jst should not duplicate rows."""
        tmpdir = str(tmp_path)
        _setup_history(tmpdir)
        generate_ai_annotations(tmpdir, _AS_OF, _NOW)
        generate_ai_annotations(tmpdir, _AS_OF, _NOW)
        path = os.path.join(tmpdir, "annotations", "ai_annotation_suggestions.csv")
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        as_of_values = [r["as_of_jst"] for r in rows]
        assert as_of_values.count(_AS_OF.isoformat()) == 1


# ---------------------------------------------------------------------------
# Test: Manual annotation template
# ---------------------------------------------------------------------------


class TestManualAnnotationTemplate:
    def test_generates_template(self, tmp_path: str) -> None:
        tmpdir = str(tmp_path)
        path = generate_manual_annotation_template(tmpdir)
        assert os.path.isfile(path)
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        assert len(rows) == 1
        for col in MANUAL_ANNOTATION_FIELDNAMES:
            assert col in rows[0]
        assert rows[0]["annotation_status"] == "pending"


# ---------------------------------------------------------------------------
# Test: Manual annotation loading
# ---------------------------------------------------------------------------


class TestLoadManualAnnotations:
    def test_missing_file_returns_empty(self, tmp_path: str) -> None:
        result = load_manual_annotations(str(tmp_path))
        assert result == {}

    def test_loads_confirmed(self, tmp_path: str) -> None:
        tmpdir = str(tmp_path)
        ann_dir = os.path.join(tmpdir, "annotations")
        os.makedirs(ann_dir, exist_ok=True)
        _write_csv(
            os.path.join(ann_dir, "manual_annotations.csv"),
            MANUAL_ANNOTATION_FIELDNAMES,
            [{
                "as_of_jst": "2026-03-13T08:00:00+09:00",
                "regime_label": "trending",
                "event_tags": "fomc",
                "volatility_label": "high",
                "intervention_risk": "low",
                "notes": "test",
                "annotation_status": "confirmed",
            }],
        )
        result = load_manual_annotations(tmpdir)
        assert "2026-03-13T08:00:00+09:00" in result
        assert result["2026-03-13T08:00:00+09:00"]["regime_label"] == "trending"
        assert result["2026-03-13T08:00:00+09:00"]["annotation_status"] == "confirmed"

    def test_pending_status(self, tmp_path: str) -> None:
        tmpdir = str(tmp_path)
        ann_dir = os.path.join(tmpdir, "annotations")
        os.makedirs(ann_dir, exist_ok=True)
        _write_csv(
            os.path.join(ann_dir, "manual_annotations.csv"),
            MANUAL_ANNOTATION_FIELDNAMES,
            [{
                "as_of_jst": "2026-03-13T08:00:00+09:00",
                "regime_label": "mixed",
                "event_tags": "",
                "volatility_label": "normal",
                "intervention_risk": "low",
                "notes": "",
                "annotation_status": "pending",
            }],
        )
        result = load_manual_annotations(tmpdir)
        assert result["2026-03-13T08:00:00+09:00"]["annotation_status"] == "pending"

    def test_utf8_bom_handled(self, tmp_path: str) -> None:
        """CSV saved with UTF-8 BOM (e.g. Excel) should still be loaded correctly."""
        tmpdir = str(tmp_path)
        ann_dir = os.path.join(tmpdir, "annotations")
        os.makedirs(ann_dir, exist_ok=True)
        path = os.path.join(ann_dir, "manual_annotations.csv")
        # Write with BOM prefix
        with open(path, "w", encoding="utf-8-sig", newline="") as fh:
            import csv as _csv
            writer = _csv.DictWriter(fh, fieldnames=list(MANUAL_ANNOTATION_FIELDNAMES))
            writer.writeheader()
            writer.writerow({
                "as_of_jst": "2026-03-13T08:00:00+09:00",
                "regime_label": "trending",
                "event_tags": "fomc",
                "volatility_label": "high",
                "intervention_risk": "low",
                "notes": "bom test",
                "annotation_status": "confirmed",
            })
        result = load_manual_annotations(tmpdir)
        assert "2026-03-13T08:00:00+09:00" in result
        assert result["2026-03-13T08:00:00+09:00"]["regime_label"] == "trending"


# ---------------------------------------------------------------------------
# Test: Labeled observations
# ---------------------------------------------------------------------------


class TestLabeledObservations:
    def test_generates_without_annotations(self, tmp_path: str) -> None:
        """labeled_observations.csv should be generated even without manual annotations."""
        tmpdir = str(tmp_path)
        _setup_history(tmpdir)
        path = build_labeled_observations(tmpdir, _NOW)
        assert path is not None
        assert os.path.isfile(path)
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 2  # ugh + baseline
        for col in LABELED_OBSERVATION_FIELDNAMES:
            assert col in rows[0]
        # Without annotations, annotation columns should be empty
        assert rows[0]["regime_label"] == ""
        assert rows[0]["annotation_status"] == ""

    def test_joins_confirmed_annotations(self, tmp_path: str) -> None:
        tmpdir = str(tmp_path)
        _setup_history(tmpdir)
        # Write manual annotation
        ann_dir = os.path.join(tmpdir, "annotations")
        os.makedirs(ann_dir, exist_ok=True)
        _write_csv(
            os.path.join(ann_dir, "manual_annotations.csv"),
            MANUAL_ANNOTATION_FIELDNAMES,
            [{
                "as_of_jst": "2026-03-13T08:00:00+09:00",
                "regime_label": "trending",
                "event_tags": "fomc",
                "volatility_label": "high",
                "intervention_risk": "medium",
                "notes": "confirmed test",
                "annotation_status": "confirmed",
            }],
        )
        path = build_labeled_observations(tmpdir, _NOW)
        assert path is not None
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 2
        for row in rows:
            assert row["regime_label"] == "trending"
            assert row["annotation_status"] == "confirmed"
            assert row["intervention_risk"] == "medium"

    def test_cross_batch_evaluation_join(self, tmp_path: str) -> None:
        """Evaluations in a later batch that reference an earlier batch's forecast_ids
        must be joined correctly (production layout: evaluation.csv in day N+1 batch
        evaluates day N forecasts)."""
        tmpdir = str(tmp_path)
        # Day 1 batch: forecasts only (no evaluation yet)
        day1_batch = os.path.join(tmpdir, "history", "20260313", "batch-day1")
        os.makedirs(day1_batch, exist_ok=True)
        forecasts_day1 = [
            _make_forecast_row(
                as_of_jst="2026-03-13T08:00:00+09:00",
                strategy="ugh", forecast_id="fc-day1-ugh", batch_id="batch-day1",
            ),
        ]
        _write_csv(
            os.path.join(day1_batch, "forecast.csv"), FORECAST_FIELDNAMES, forecasts_day1
        )

        # Day 2 batch: forecast for day 2 + evaluation of day 1's forecast
        day2_batch = os.path.join(tmpdir, "history", "20260314", "batch-day2")
        os.makedirs(day2_batch, exist_ok=True)
        forecasts_day2 = [
            _make_forecast_row(
                as_of_jst="2026-03-14T08:00:00+09:00",
                strategy="ugh", forecast_id="fc-day2-ugh", batch_id="batch-day2",
            ),
        ]
        _write_csv(
            os.path.join(day2_batch, "forecast.csv"), FORECAST_FIELDNAMES, forecasts_day2
        )
        _write_csv(
            os.path.join(day2_batch, "outcome.csv"), OUTCOME_FIELDNAMES, [_make_outcome_row()]
        )
        evals_day2 = [
            _make_eval_row(forecast_id="fc-day1-ugh", strategy="ugh", direction_hit="True"),
        ]
        _write_csv(
            os.path.join(day2_batch, "evaluation.csv"), EVALUATION_FIELDNAMES, evals_day2
        )

        path = build_labeled_observations(tmpdir, _NOW)
        assert path is not None
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        # Day 2's forecast has no evaluation yet → excluded.
        # Only day 1's forecast (evaluated in day 2's batch) should appear.
        assert len(rows) == 1
        day1_row = rows[0]
        assert day1_row["as_of_jst"] == "2026-03-13T08:00:00+09:00"
        # Day 1's forecast should have evaluation data from day 2's batch
        assert day1_row["direction_hit"] == "True"
        assert day1_row["close_error_bp"] == "2.5"

    def test_no_history_returns_none(self, tmp_path: str) -> None:
        result = build_labeled_observations(str(tmp_path), _NOW)
        assert result is None

    def test_ai_annotation_columns_in_labeled(self, tmp_path: str) -> None:
        """AI annotation columns should be present in labeled_observations.csv."""
        tmpdir = str(tmp_path)
        _setup_history(tmpdir)
        path = build_labeled_observations(tmpdir, _NOW)
        assert path is not None
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            headers = reader.fieldnames or []
        assert "ai_regime_label" in headers
        assert "ai_annotation_status" in headers
        assert "annotation_source" in headers


# ---------------------------------------------------------------------------
# Test: Slice scoreboard
# ---------------------------------------------------------------------------


class TestSliceScoreboard:
    def test_generates_from_labeled_observations(self, tmp_path: str) -> None:
        tmpdir = str(tmp_path)
        _setup_history(tmpdir)
        build_labeled_observations(tmpdir, _NOW)
        path = build_slice_scoreboard(tmpdir, _NOW)
        assert path is not None
        assert os.path.isfile(path)
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) >= 1
        for col in SLICE_SCOREBOARD_FIELDNAMES:
            assert col in rows[0]

    def test_confirmed_uses_labels(self, tmp_path: str) -> None:
        tmpdir = str(tmp_path)
        _setup_history(tmpdir)
        ann_dir = os.path.join(tmpdir, "annotations")
        os.makedirs(ann_dir, exist_ok=True)
        _write_csv(
            os.path.join(ann_dir, "manual_annotations.csv"),
            MANUAL_ANNOTATION_FIELDNAMES,
            [{
                "as_of_jst": "2026-03-13T08:00:00+09:00",
                "regime_label": "trending",
                "event_tags": "fomc",
                "volatility_label": "high",
                "intervention_risk": "low",
                "notes": "",
                "annotation_status": "confirmed",
            }],
        )
        build_labeled_observations(tmpdir, _NOW)
        path = build_slice_scoreboard(tmpdir, _NOW)
        assert path is not None
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        # Should have rows with regime_label=trending
        labeled = [r for r in rows if r["regime_label"] == "trending"]
        assert len(labeled) >= 1

    def test_unlabeled_has_empty_labels(self, tmp_path: str) -> None:
        tmpdir = str(tmp_path)
        _setup_history(tmpdir)
        build_labeled_observations(tmpdir, _NOW)
        path = build_slice_scoreboard(tmpdir, _NOW)
        assert path is not None
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        # Without annotations, all should be unlabeled (empty labels)
        for row in rows:
            assert row["regime_label"] == ""

    def test_case_insensitive_confirmed(self, tmp_path: str) -> None:
        """'Confirmed' and ' confirmed ' should be treated as confirmed."""
        tmpdir = str(tmp_path)
        _setup_history(tmpdir)
        ann_dir = os.path.join(tmpdir, "annotations")
        os.makedirs(ann_dir, exist_ok=True)
        _write_csv(
            os.path.join(ann_dir, "manual_annotations.csv"),
            MANUAL_ANNOTATION_FIELDNAMES,
            [{
                "as_of_jst": "2026-03-13T08:00:00+09:00",
                "regime_label": "choppy",
                "event_tags": "fomc",
                "volatility_label": "low",
                "intervention_risk": "high",
                "notes": "",
                "annotation_status": " Confirmed ",
            }],
        )
        build_labeled_observations(tmpdir, _NOW)
        path = build_slice_scoreboard(tmpdir, _NOW)
        assert path is not None
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        labeled = [r for r in rows if r["regime_label"] == "choppy"]
        assert len(labeled) >= 1

    def test_no_observations_returns_none(self, tmp_path: str) -> None:
        result = build_slice_scoreboard(str(tmp_path), _NOW)
        assert result is None


# ---------------------------------------------------------------------------
# Test: Tag scoreboard
# ---------------------------------------------------------------------------


class TestTagScoreboard:
    def test_expands_multiple_tags(self, tmp_path: str) -> None:
        """Each pipe-delimited tag should produce a separate aggregation entry."""
        tmpdir = str(tmp_path)
        _setup_history(tmpdir)
        ann_dir = os.path.join(tmpdir, "annotations")
        os.makedirs(ann_dir, exist_ok=True)
        _write_csv(
            os.path.join(ann_dir, "manual_annotations.csv"),
            MANUAL_ANNOTATION_FIELDNAMES,
            [{
                "as_of_jst": "2026-03-13T08:00:00+09:00",
                "regime_label": "trending",
                "event_tags": "fomc|cpi_us",
                "volatility_label": "high",
                "intervention_risk": "low",
                "notes": "",
                "annotation_status": "confirmed",
            }],
        )
        build_labeled_observations(tmpdir, _NOW)
        path = build_tag_scoreboard(tmpdir, _NOW)
        assert path is not None
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        tags = {r["event_tag"] for r in rows}
        assert "fomc" in tags
        assert "cpi_us" in tags
        for col in TAG_SCOREBOARD_FIELDNAMES:
            assert col in rows[0]

    def test_pending_excluded_from_tag_scoreboard(self, tmp_path: str) -> None:
        """Pending annotations must not contribute to tag scoreboard."""
        tmpdir = str(tmp_path)
        _setup_history(tmpdir)
        ann_dir = os.path.join(tmpdir, "annotations")
        os.makedirs(ann_dir, exist_ok=True)
        _write_csv(
            os.path.join(ann_dir, "manual_annotations.csv"),
            MANUAL_ANNOTATION_FIELDNAMES,
            [{
                "as_of_jst": "2026-03-13T08:00:00+09:00",
                "regime_label": "choppy",
                "event_tags": "boj|nfp_us",
                "volatility_label": "high",
                "intervention_risk": "high",
                "notes": "",
                "annotation_status": "pending",
            }],
        )
        build_labeled_observations(tmpdir, _NOW)
        result = build_tag_scoreboard(tmpdir, _NOW)
        # Pending rows should be excluded → no confirmed tags → None
        assert result is None

    def test_no_tags_returns_none(self, tmp_path: str) -> None:
        """If no rows have event_tags, tag_scoreboard should return None."""
        tmpdir = str(tmp_path)
        # Create history without event tags
        batch_path = os.path.join(tmpdir, "history", "20260313", "batch-001")
        os.makedirs(batch_path, exist_ok=True)
        fc = _make_forecast_row()
        _write_csv(os.path.join(batch_path, "forecast.csv"), FORECAST_FIELDNAMES, [fc])
        outcome = _make_outcome_row()
        outcome["event_tags"] = ""
        outcome["event_happened"] = "False"
        _write_csv(os.path.join(batch_path, "outcome.csv"), OUTCOME_FIELDNAMES, [outcome])
        ev = _make_eval_row()
        _write_csv(os.path.join(batch_path, "evaluation.csv"), EVALUATION_FIELDNAMES, [ev])

        build_labeled_observations(tmpdir, _NOW)
        result = build_tag_scoreboard(tmpdir, _NOW)
        # No event_tags → no tag rows → None
        assert result is None


# ---------------------------------------------------------------------------
# Test: Orchestrator
# ---------------------------------------------------------------------------


class TestRunAnnotationAnalytics:
    def test_all_artifacts_generated(self, tmp_path: str) -> None:
        tmpdir = str(tmp_path)
        _setup_history(tmpdir)
        result = run_annotation_analytics(tmpdir, _AS_OF, _NOW)
        assert result["ai_annotation_suggestions_path"] is not None
        assert result["manual_annotation_template_path"] is not None
        assert result["labeled_observations_path"] is not None
        assert result["slice_scoreboard_path"] is not None
        # tag_scoreboard depends on event_tags in labeled_observations

    def test_empty_dir_does_not_crash(self, tmp_path: str) -> None:
        """Run on an empty directory should not raise."""
        result = run_annotation_analytics(str(tmp_path), _AS_OF, _NOW)
        assert isinstance(result, dict)
        # AI annotations and template should still be generated
        assert result["ai_annotation_suggestions_path"] is not None
        assert result["manual_annotation_template_path"] is not None

    def test_existing_predictions_unchanged(self, tmp_path: str) -> None:
        """The annotation layer must not modify any existing history CSVs."""
        tmpdir = str(tmp_path)
        _setup_history(tmpdir)

        # Read original CSVs
        batch_path = os.path.join(tmpdir, "history", "20260313", "batch-001")
        original_forecast = _read_file(os.path.join(batch_path, "forecast.csv"))
        original_outcome = _read_file(os.path.join(batch_path, "outcome.csv"))
        original_eval = _read_file(os.path.join(batch_path, "evaluation.csv"))

        run_annotation_analytics(tmpdir, _AS_OF, _NOW)

        # Verify originals are untouched
        assert _read_file(os.path.join(batch_path, "forecast.csv")) == original_forecast
        assert _read_file(os.path.join(batch_path, "outcome.csv")) == original_outcome
        assert _read_file(os.path.join(batch_path, "evaluation.csv")) == original_eval


def _read_file(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# Test: Auto event-tag derivation
# ---------------------------------------------------------------------------


class TestIsLastBusinessDayOfMonth:
    def test_last_weekday_friday(self) -> None:
        # 2026-01-30 is a Friday, last business day of Jan 2026
        assert _is_last_business_day_of_month(datetime(2026, 1, 30))

    def test_last_weekday_not_last_day(self) -> None:
        # 2026-01-31 is a Saturday — last business day is 30th
        assert not _is_last_business_day_of_month(datetime(2026, 1, 31))
        assert not _is_last_business_day_of_month(datetime(2026, 1, 29))

    def test_march_end_quarter(self) -> None:
        # 2026-03-31 is a Tuesday — last business day
        assert _is_last_business_day_of_month(datetime(2026, 3, 31))

    def test_mid_month(self) -> None:
        assert not _is_last_business_day_of_month(datetime(2026, 3, 15))


class TestDeriveAutoEventTags:
    def test_outcome_tags_included(self) -> None:
        outcome = {"event_tags": "fomc|cpi_us"}
        tags = _derive_auto_event_tags("2026-03-18T08:00:00+09:00", outcome)
        assert "fomc" in tags
        assert "cpi_us" in tags

    def test_month_end_tag(self) -> None:
        # 2026-03-31 is last business day of March (quarter end too)
        tags = _derive_auto_event_tags("2026-03-31T08:00:00+09:00", None)
        assert "month_end" in tags
        assert "quarter_end" in tags

    def test_month_end_non_quarter(self) -> None:
        # 2026-01-30 is last business day of Jan (not quarter end)
        tags = _derive_auto_event_tags("2026-01-30T08:00:00+09:00", None)
        assert "month_end" in tags
        assert "quarter_end" not in tags

    def test_no_tags(self) -> None:
        tags = _derive_auto_event_tags("2026-03-18T08:00:00+09:00", None)
        assert tags == []

    def test_outcome_empty_tags(self) -> None:
        tags = _derive_auto_event_tags("2026-03-18T08:00:00+09:00", {"event_tags": ""})
        assert tags == []

    def test_deduplication_and_sort(self) -> None:
        outcome = {"event_tags": "fomc|boj|fomc"}
        tags = _derive_auto_event_tags("2026-03-18T08:00:00+09:00", outcome)
        assert tags == ["boj", "fomc"]  # sorted and deduplicated


class TestBuildEventTagFields:
    def test_manual_only(self) -> None:
        m, a, e, src = _build_event_tag_fields("fomc|cpi_us", [])
        assert m == "cpi_us|fomc"  # sorted
        assert a == ""
        assert e == "cpi_us|fomc"
        assert src == "manual"

    def test_auto_only(self) -> None:
        m, a, e, src = _build_event_tag_fields("", ["month_end"])
        assert m == ""
        assert a == "month_end"
        assert e == "month_end"
        assert src == "auto"

    def test_mixed(self) -> None:
        m, a, e, src = _build_event_tag_fields("fomc", ["month_end"])
        assert "fomc" in e
        assert "month_end" in e
        assert src == "mixed"

    def test_none(self) -> None:
        m, a, e, src = _build_event_tag_fields("", [])
        assert m == ""
        assert a == ""
        assert e == ""
        assert src == "none"

    def test_overlapping_manual_auto(self) -> None:
        """When manual tags are a subset of auto tags, source is still 'manual'."""
        m, a, e, src = _build_event_tag_fields("fomc", ["fomc"])
        assert e == "fomc"
        assert src == "manual"


# ---------------------------------------------------------------------------
# Test: Labeled observation event-tag provenance
# ---------------------------------------------------------------------------


class TestLabeledObservationEventTagProvenance:
    def test_auto_event_tags_from_outcome(self, tmp_path: str) -> None:
        """Auto event tags should be derived from outcome event_tags."""
        tmpdir = str(tmp_path)
        _setup_history(tmpdir)  # outcome has event_tags="fomc|cpi_us"
        path = build_labeled_observations(tmpdir, _NOW)
        assert path is not None
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        for row in rows:
            assert "fomc" in row.get("auto_event_tags", "")
            assert "cpi_us" in row.get("auto_event_tags", "")
            assert row["event_tag_source"] == "auto_only"
            assert row["effective_event_tags"] == row["event_tags"]

    def test_manual_event_tags_from_annotations(self, tmp_path: str) -> None:
        """Manual event tags should come from annotation file."""
        tmpdir = str(tmp_path)
        _setup_history(tmpdir)
        ann_dir = os.path.join(tmpdir, "annotations")
        os.makedirs(ann_dir, exist_ok=True)
        _write_csv(
            os.path.join(ann_dir, "manual_annotations.csv"),
            MANUAL_ANNOTATION_FIELDNAMES,
            [{
                "as_of_jst": "2026-03-13T08:00:00+09:00",
                "regime_label": "trending",
                "event_tags": "boj",
                "volatility_label": "high",
                "intervention_risk": "low",
                "notes": "",
                "annotation_status": "confirmed",
            }],
        )
        path = build_labeled_observations(tmpdir, _NOW)
        assert path is not None
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        for row in rows:
            assert "boj" in row["manual_event_tags"]
            # Auto tags should also have outcome tags
            assert "fomc" in row["auto_event_tags"]
            # With AI-first precedence (no AI tags here), auto takes priority
            # over manual. Effective contains auto tags.
            assert "fomc" in row["effective_event_tags"]
            assert row["event_tag_source"] == "auto_only"

    def test_no_event_tags(self, tmp_path: str) -> None:
        """When no tags exist at all, source should be 'none'."""
        tmpdir = str(tmp_path)
        batch_path = os.path.join(tmpdir, "history", "20260313", "batch-001")
        os.makedirs(batch_path, exist_ok=True)
        fc = _make_forecast_row()
        _write_csv(os.path.join(batch_path, "forecast.csv"), FORECAST_FIELDNAMES, [fc])
        outcome = _make_outcome_row()
        outcome["event_tags"] = ""
        outcome["event_happened"] = "False"
        _write_csv(os.path.join(batch_path, "outcome.csv"), OUTCOME_FIELDNAMES, [outcome])
        ev = _make_eval_row()
        _write_csv(os.path.join(batch_path, "evaluation.csv"), EVALUATION_FIELDNAMES, [ev])

        path = build_labeled_observations(tmpdir, _NOW)
        assert path is not None
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        for row in rows:
            assert row["annotation_source"] == "none"
            assert row["effective_event_tags"] == ""
