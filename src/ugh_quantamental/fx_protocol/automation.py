"""FX Daily Automation orchestration (v1).

Implements ``run_fx_daily_protocol_once``, which drives the full daily
forecast and outcome/evaluation cycle for USDJPY.

SQLAlchemy is required at call time; the module itself is importable without it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from ugh_quantamental.fx_protocol.automation_models import (
    FxDailyAutomationConfig,
    FxDailyAutomationResult,
)
from ugh_quantamental.fx_protocol.calendar import (
    current_as_of_jst,
    is_protocol_business_day,
    prev_as_of_jst,
)
from ugh_quantamental.fx_protocol.data_sources import FxMarketDataProvider
from ugh_quantamental.fx_protocol.ids import make_forecast_batch_id
from ugh_quantamental.fx_protocol.request_builders import (
    build_daily_forecast_request,
    build_daily_outcome_request,
    previous_window_matches,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _make_default_ugh_request(snapshot_ref: str):  # type: ignore[return]
    """Build a minimal placeholder UGH ``FullWorkflowRequest`` for automation runs.

    In a research/scaffold context the UGH engine inputs are not derived from
    market data.  This function provides stable, non-random defaults so that the
    automation pipeline produces deterministic records without requiring external
    UGH input calibration at this milestone.

    Callers that have real UGH inputs should construct the ``FullWorkflowRequest``
    themselves and pass it to ``build_daily_forecast_request`` directly.
    """
    from ugh_quantamental.engine.projection_models import (
        AlignmentInputs,
        QuestionDirectionSign,
        QuestionFeatures,
        SignalFeatures,
    )
    from ugh_quantamental.engine.state_models import StateEventFeatures
    from ugh_quantamental.schemas.enums import LifecycleState, MacroCycleRegime, MarketRegime
    from ugh_quantamental.schemas.market_svp import MarketSVP, Phi, StateProbabilities
    from ugh_quantamental.schemas.omega import BlockObservability, EvidenceLineageRecord, Omega
    from ugh_quantamental.schemas.ssv import (
        FBlock,
        PBlock,
        QBlock,
        QuestionLedger,
        QuestionRecord,
        RBlock,
        SSVSnapshot,
        TBlock,
        XBlock,
    )
    from ugh_quantamental.workflows.models import (
        FullWorkflowRequest,
        FullWorkflowStateRequest,
        ProjectionWorkflowRequest,
    )

    probs = StateProbabilities(
        dormant=0.10,
        setup=0.50,
        fire=0.15,
        expansion=0.10,
        exhaustion=0.10,
        failure=0.05,
    )
    phi = Phi(dominant_state=LifecycleState.setup, probabilities=probs)
    market_svp = MarketSVP(
        as_of="2020-01-01T00:00:00Z",
        regime=MarketRegime.neutral,
        phi=phi,
        confidence=0.5,
    )
    question_record = QuestionRecord(
        question_id=snapshot_ref,
        direction="positive",
        score=0.5,
        weight=1.0,
    )
    question_ledger = QuestionLedger(
        as_of="2020-01-01",
        coverage_ratio=1.0,
        questions=(question_record,),
    )
    block_obs = BlockObservability(q=0.8, f=0.8, t=0.8, p=0.8, r=0.8, x=0.8)
    omega = Omega(
        omega_id=f"omega-{snapshot_ref}",
        market_svp=market_svp,
        question_ledger=question_ledger,
        evidence_lineage=(
            EvidenceLineageRecord(
                source_id="auto",
                observed_at="2020-01-01T00:00:00Z",
                source_type="internal",
            ),
        ),
        block_confidence=block_obs,
        block_observability=block_obs,
        confidence=0.8,
    )
    snapshot = SSVSnapshot(
        snapshot_id=snapshot_ref,
        q=QBlock(ledger=question_ledger),
        f=FBlock(factor_count=3, aggregate_signal=0.1),
        t=TBlock(timestamp="2020-01-01T00:00:00Z", lookback_days=20),
        p=PBlock(implied_move_30d=0.02, implied_volatility=0.1, skew_25d=0.0),
        phi=phi,
        r=RBlock(
            market_regime=MarketRegime.neutral,
            macro_cycle_regime=MacroCycleRegime.expansion,
            conviction=0.5,
        ),
        x=XBlock(tags=("auto",)),
    )
    return FullWorkflowRequest(
        projection=ProjectionWorkflowRequest(
            projection_id=snapshot_ref,
            horizon_days=1,
            question_features=QuestionFeatures(
                question_direction=QuestionDirectionSign.positive,
                q_strength=0.5,
                s_q=0.5,
                temporal_score=0.5,
            ),
            signal_features=SignalFeatures(
                fundamental_score=0.2,
                technical_score=0.2,
                price_implied_score=0.2,
                context_score=1.0,
                grv_lock=0.5,
                regime_fit=0.5,
                narrative_dispersion=0.3,
                evidence_confidence=0.8,
                fire_probability=0.4,
            ),
            alignment_inputs=AlignmentInputs(
                d_qf=0.1,
                d_qt=0.1,
                d_qp=0.1,
                d_ft=0.1,
                d_fp=0.1,
                d_tp=0.1,
            ),
        ),
        state=FullWorkflowStateRequest(
            snapshot=snapshot,
            omega=omega,
            event_features=StateEventFeatures(
                catalyst_strength=0.5,
                follow_through=0.5,
                pricing_saturation=0.3,
                disconfirmation_strength=0.2,
                regime_shock=0.1,
                observation_freshness=0.8,
            ),
        ),
    )


def run_fx_daily_protocol_once(
    config: FxDailyAutomationConfig,
    provider: FxMarketDataProvider,
    session: "Session",
) -> FxDailyAutomationResult:
    """Execute one full daily FX protocol run.

    Steps
    -----
    1. Determine canonical ``as_of_jst`` (08:00 JST today or previous business day).
    2. Fetch one USDJPY snapshot from the provider.
    3. If ``config.run_forecast_generation``: build and run the forecast workflow
       (idempotent — rerunning the same window returns the existing batch).
    4. If ``config.run_outcome_evaluation`` and the newest completed window matches
       the immediately-previous protocol window: build and run the outcome/evaluation
       workflow (idempotent).
    5. Return a typed ``FxDailyAutomationResult``.

    Parameters
    ----------
    config:
        Automation configuration.
    provider:
        Market data provider to fetch the USDJPY snapshot from.
    session:
        Active SQLAlchemy session.  The caller owns the transaction; this
        function flushes but does not commit.

    Returns
    -------
    FxDailyAutomationResult
        Summary of what was created or already existed.
    """
    # Deferred to avoid transitive SQLAlchemy import at module load time.
    from ugh_quantamental.fx_protocol.forecasting import run_daily_forecast_workflow
    from ugh_quantamental.fx_protocol.outcomes import run_daily_outcome_evaluation_workflow

    # --- Step 1: canonical as_of_jst ---
    now_utc = datetime.now(timezone.utc)
    as_of_jst = current_as_of_jst(now_utc)
    if not is_protocol_business_day(as_of_jst):
        raise ValueError(
            f"Today ({as_of_jst.date()} JST) is not a protocol business day. "
            "Run on Mon–Fri only."
        )

    # --- Step 2: fetch snapshot ---
    snapshot = provider.fetch_snapshot(as_of_jst)

    # Freshness guard: the newest completed window must close at exactly as_of_jst.
    # A lagging or cached provider would return a window_end_jst in the past,
    # causing today's forecast batch to be built from stale history.  Once
    # persisted it would be treated as idempotent-complete by later reruns,
    # permanently blocking regeneration with correct data.
    #
    # Exception: Yahoo Finance FX daily bars are typically published on the next
    # calendar day, so a lag of exactly 1 protocol business day is acceptable.
    # When this occurs, as_of_jst is adjusted to newest_end and the snapshot is
    # re-fetched so that snapshot.as_of_jst and all derived batch IDs are
    # consistent with the actual data available.
    if not snapshot.completed_windows:
        raise ValueError("Provider returned a snapshot with no completed windows.")
    newest_end = snapshot.completed_windows[-1].window_end_jst
    if newest_end != as_of_jst:
        if newest_end == prev_as_of_jst(as_of_jst):
            print(
                f"[WARN] Provider data is 1 business day behind "
                f"(newest window ends {newest_end.isoformat()}); "
                f"adjusting as_of_jst from {as_of_jst.isoformat()} "
                f"to {newest_end.isoformat()}.",
                flush=True,
            )
            as_of_jst = newest_end
            snapshot = provider.fetch_snapshot(as_of_jst)
            if not snapshot.completed_windows:
                raise ValueError("Provider returned a snapshot with no completed windows.")
            newest_end = snapshot.completed_windows[-1].window_end_jst
            if newest_end != as_of_jst:
                raise ValueError(
                    f"Stale snapshot after 1-day fallback: newest completed window ends at "
                    f"{newest_end.isoformat()} but as_of_jst is {as_of_jst.isoformat()}. "
                    "Provider data may be lagging or cached."
                )
        else:
            raise ValueError(
                f"Stale snapshot: newest completed window ends at {newest_end.isoformat()} "
                f"but as_of_jst is {as_of_jst.isoformat()}. "
                "Provider data may be lagging or cached."
            )

    # --- Step 3: forecast generation ---
    forecast_batch_id: str | None = None
    forecast_created = False

    if config.run_forecast_generation:
        ugh_request = _make_default_ugh_request(config.input_snapshot_ref)
        forecast_request = build_daily_forecast_request(
            snapshot,
            ugh_request=ugh_request,
            input_snapshot_ref=config.input_snapshot_ref,
            theory_version=config.theory_version,
            engine_version=config.engine_version,
            schema_version=config.schema_version,
            protocol_version=config.protocol_version,
        )
        # Check idempotency: compute what the batch ID would be.
        expected_batch_id = make_forecast_batch_id(
            config.pair, as_of_jst, config.protocol_version
        )
        from ugh_quantamental.persistence.repositories import FxForecastRepository

        existing = FxForecastRepository.load_fx_forecast_batch(session, expected_batch_id)
        if existing is not None and len(existing.forecasts) == 4:
            # Complete batch already exists — idempotent skip.
            forecast_batch_id = existing.forecast_batch_id
            forecast_created = False
        else:
            # Either no batch or a partial batch: delegate to the workflow which
            # enforces completeness and raises on partial-batch corruption.
            result = run_daily_forecast_workflow(session, forecast_request)
            forecast_batch_id = result.forecast_batch_id
            forecast_created = True

    # --- Step 4: outcome/evaluation ---
    outcome_id: str | None = None
    outcome_recorded = False
    evaluation_count = 0

    # For outcome evaluation we additionally require that the prior-day forecast
    # batch exists and is complete.  On a fresh or backfilled database the batch
    # may be absent; proceeding without it would let run_daily_outcome_evaluation_workflow
    # raise ValueError inside the transaction, rolling back the newly-created
    # today's forecast batch.
    _prior_batch_ready = False
    if config.run_outcome_evaluation and previous_window_matches(snapshot):
        from ugh_quantamental.persistence.repositories import FxForecastRepository as _FxFR

        prior_as_of = snapshot.completed_windows[-1].window_start_jst
        prior_batch_id = make_forecast_batch_id(config.pair, prior_as_of, config.protocol_version)
        prior_batch = _FxFR.load_fx_forecast_batch(session, prior_batch_id)
        _prior_batch_ready = prior_batch is not None and len(prior_batch.forecasts) == 4

    if _prior_batch_ready:
        outcome_request = build_daily_outcome_request(
            snapshot,
            schema_version=config.schema_version,
            protocol_version=config.protocol_version,
        )
        outcome_result = run_daily_outcome_evaluation_workflow(session, outcome_request)
        outcome_id = outcome_result.outcome.outcome_id
        evaluation_count = len(outcome_result.evaluations)

        # Both workflows are idempotent; any completion here counts as "recorded".
        outcome_recorded = True

    # --- Step 5: CSV exports ---
    forecast_csv_path: str | None = None
    outcome_csv_path: str | None = None
    evaluation_csv_path: str | None = None

    if config.write_csv_exports and forecast_batch_id is not None:
        from ugh_quantamental.fx_protocol.csv_exports import (
            export_daily_evaluation_csv,
            export_daily_forecast_csv,
            export_daily_outcome_csv,
        )
        from ugh_quantamental.persistence.repositories import (
            FxForecastRepository,
            FxOutcomeEvaluationRepository,
        )

        batch = FxForecastRepository.load_fx_forecast_batch(session, forecast_batch_id)
        if batch is not None and batch.forecasts:
            forecast_csv_path = export_daily_forecast_csv(
                batch.forecasts,
                as_of_jst,
                config.pair.value,
                config.csv_output_dir,
            )

        if outcome_id is not None:
            outcome_rec = FxOutcomeEvaluationRepository.load_fx_outcome_record(
                session, outcome_id
            )
            outcome_csv_path = export_daily_outcome_csv(
                outcome_rec,
                as_of_jst,
                config.pair.value,
                config.csv_output_dir,
            )
            eval_batch = FxOutcomeEvaluationRepository.load_fx_evaluation_batch(
                session, outcome_id
            )
            evaluation_csv_path = export_daily_evaluation_csv(
                eval_batch,
                as_of_jst,
                config.pair.value,
                config.csv_output_dir,
            )

    # --- Step 6: publish to latest/ + history/ layout and write manifest ---
    manifest_path: str | None = None

    if config.write_csv_exports and forecast_csv_path is not None:
        from ugh_quantamental.fx_protocol.csv_exports import (
            publish_csv_to_layout,
            write_latest_manifest,
        )

        date_str = as_of_jst.strftime("%Y%m%d")
        layout = publish_csv_to_layout(
            config.csv_output_dir,
            date_str,
            forecast_batch_id,  # type: ignore[arg-type]  # not None when forecast_csv_path set
            forecast_csv_path,
            outcome_csv_path,
            evaluation_csv_path,
        )
        manifest_data: dict[str, object] = {
            "as_of_jst": as_of_jst.isoformat(),
            "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "forecast_batch_id": forecast_batch_id,
            "outcome_id": outcome_id,
            "evaluation_count": evaluation_count,
            "forecast_csv_path": layout["latest_forecast"],
            "outcome_csv_path": layout["latest_outcome"],
            "evaluation_csv_path": layout["latest_evaluation"],
            "protocol_version": config.protocol_version,
            "theory_version": config.theory_version,
            "engine_version": config.engine_version,
            "schema_version": config.schema_version,
        }
        manifest_path = write_latest_manifest(config.csv_output_dir, manifest_data)

    return FxDailyAutomationResult(
        as_of_jst=as_of_jst,
        forecast_batch_id=forecast_batch_id,
        outcome_id=outcome_id,
        forecast_created=forecast_created,
        outcome_recorded=outcome_recorded,
        evaluation_count=evaluation_count,
        data_commit_created=False,  # set by the script after git operations
        forecast_csv_path=forecast_csv_path,
        outcome_csv_path=outcome_csv_path,
        evaluation_csv_path=evaluation_csv_path,
        manifest_path=manifest_path,
    )
