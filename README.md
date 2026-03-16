# ugh-quantamental

Minimal Python 3.11+ library implementing deterministic quantamental engines with persistence, workflow composition, read-only query inspection, deterministic replay, multi-run batch replay, regression suite execution, and baseline / golden snapshot management. All logic is synchronous, typed, schema-first, and connector-free.

## Features

- **Projection engine** — computes directional point estimates, conviction, urgency, and bounded projection snapshots from question/signal/alignment inputs
- **State engine** — updates lifecycle state probabilities via deterministic softmax blending over a 6-state simplex, driven by observable event features
- **Persistence scaffolding** — SQLAlchemy ORM-backed run records for projection and state runs; Alembic migration; naive-UTC `created_at` normalisation
- **Workflow layer** — synchronous composition: run engine → persist result → reload → return both (`run_projection_workflow`, `run_state_workflow`, `run_full_workflow`)
- **Query layer** — read-only inspection of persisted runs: lightweight summaries with filtering/pagination, full bundle rehydration with all typed models recovered from JSON
- **Replay layer** — deterministic single-run regression checking: reload a persisted run, rerun the engine with the original inputs, compare stored vs recomputed results field-by-field
- **Batch replay** — multi-run replay in one call: per-run isolation, aggregate mismatch / error / missing counts, optional deduplication
- **Regression suite** — named suite runner over batch replay cases: deterministic pass/fail per case, zero-run guard prevents false-positive green results
- **Baseline / golden snapshot** — persist a named suite result; compare future reruns against the pinned baseline; per-`(group, name)` case deltas with exact-match and aggregate-diff reporting
- **FX daily protocol** — frozen contracts (`ForecastRecord`, `OutcomeRecord`, `EvaluationRecord`), deterministic calendar helpers (`resolve_completed_window_ends`), deterministic ID generation, daily forecast/outcome/evaluation workflows, and GitHub Actions automation
- **Weekly FX report** — read-only `run_weekly_report` aggregates a configurable number of completed protocol windows into strategy metrics, baseline comparisons, state/GRV/mismatch summaries, and curated case examples; `WeeklyReportRequest` / `WeeklyReportResult` frozen models with JST-canonical timestamp normalization
- **Frozen schema contracts** — all data models use `ConfigDict(extra="forbid", frozen=True)`; invariants enforced at construction time
- **Pure engine functions** — same inputs always produce the same output; no globals, no mutation, no I/O

## Requirements

- Python 3.11+
- Pydantic v2 (`>=2,<3`)
- SQLAlchemy v2 (`>=2,<3`)
- Alembic (`>=1.13,<2`)

## Installation

```bash
pip install -e .
```

## Project layout

```
src/ugh_quantamental/
├── schemas/              # frozen Pydantic v2 data contracts
│   ├── enums.py          # MarketRegime, MacroCycleRegime, LifecycleState, QuestionDirection
│   ├── market_svp.py     # StateProbabilities, Phi, MarketSVP
│   ├── ssv.py            # SSVSnapshot and Q/F/T/P/R/X blocks
│   ├── omega.py          # Omega observation-quality envelope
│   └── projection.py     # ProjectionSnapshot output contract
├── engine/               # pure deterministic engine functions
│   ├── projection.py     # 11 pure projection functions
│   ├── projection_models.py  # QuestionFeatures, SignalFeatures, AlignmentInputs, …
│   ├── state.py          # 8 pure state-lifecycle functions
│   └── state_models.py   # StateEventFeatures, StateConfig, StateEngineResult
├── persistence/          # SQLAlchemy/Alembic run persistence
│   ├── models.py         # ProjectionRunRecord, StateRunRecord, RegressionSuiteBaselineRecord
│   ├── repositories.py   # ProjectionRunRepository, StateRunRepository, RegressionSuiteBaselineRepository
│   ├── serializers.py    # Pydantic ↔ JSON helpers
│   └── db.py             # engine/session factory helpers
├── workflows/            # synchronous workflow composition layer
│   ├── models.py          # request/response models + make_run_id
│   └── runners.py         # run_projection_workflow, run_state_workflow, run_full_workflow
├── query/                # read-only inspection layer
│   ├── models.py          # ProjectionRunQuery, StateRunQuery, *Summary, *Bundle
│   └── readers.py         # list_*_summaries, get_*_bundle
├── replay/               # deterministic replay / regression / baseline layer
│   ├── models.py          # *ReplayRequest, *ReplayComparison, *ReplayResult
│   ├── runners.py         # replay_projection_run, replay_state_run
│   ├── batch_models.py    # *BatchReplayRequest/Item/Aggregate/Result, BatchReplayStatus
│   ├── batch.py           # replay_projection_batch, replay_state_batch
│   ├── suite_models.py    # *SuiteCase, RegressionSuiteRequest/Aggregate/Result
│   ├── suites.py          # run_regression_suite
│   ├── baseline_models.py # Create/CompareRequest, RegressionSuiteBaseline, *Comparison, *Delta
│   └── baselines.py       # make_baseline_id, create/get/compare_regression_baseline
└── fx_protocol/          # FX daily prediction cycle (Phase 2, Milestones 13–17)
    ├── models.py          # ForecastRecord, OutcomeRecord, EvaluationRecord, CurrencyPair, …
    ├── ids.py             # deterministic ID generation
    ├── calendar.py        # resolve_completed_window_ends, business-day helpers
    ├── forecast_models.py # DailyForecastWorkflowRequest, DailyForecastBatch, …
    ├── outcome_models.py  # DailyOutcomeWorkflowRequest, PersistedOutcomeEvaluationBatch
    ├── data_models.py     # FxCompletedWindow, FxProtocolMarketSnapshot
    ├── automation_models.py  # FxDailyAutomationConfig, FxDailyAutomationResult
    ├── report_models.py   # WeeklyReportRequest/Result, StrategyWeeklyMetrics, …
    └── reporting.py       # run_weekly_report (read-only)

alembic/                  # Alembic migration environment
docs/specs/               # formal v1 specifications
scripts/                  # run_fx_daily_protocol.py — CLI entry point for automation
tests/                    # mirrors src layout
```

## Usage

### Projection engine

```python
from ugh_quantamental.engine import (
    run_projection_engine,
    QuestionFeatures, SignalFeatures, AlignmentInputs, ProjectionConfig,
)
from ugh_quantamental.engine.projection_models import QuestionDirectionSign

q = QuestionFeatures(
    question_direction=QuestionDirectionSign.positive,
    q_strength=0.8, s_q=0.7, temporal_score=0.6,
)
sig = SignalFeatures(
    fundamental_score=0.4, technical_score=0.2, price_implied_score=0.1,
    context_score=1.0, grv_lock=0.7, regime_fit=0.6,
    narrative_dispersion=0.2, evidence_confidence=0.8, fire_probability=0.6,
)
align = AlignmentInputs(d_qf=0.2, d_qt=0.3, d_qp=0.4, d_ft=0.2, d_fp=0.2, d_tp=0.3)

result = run_projection_engine("my-question-id", 30, q, sig, align, ProjectionConfig())
print(result.projection_snapshot.point_estimate)   # float in [-1, 1]
print(result.projection_snapshot.confidence)       # float in [0, 1]
```

### State engine

```python
from ugh_quantamental.engine import run_state_engine, StateEventFeatures, StateConfig

events = StateEventFeatures(
    catalyst_strength=0.6, follow_through=0.5, pricing_saturation=0.3,
    disconfirmation_strength=0.2, regime_shock=0.1, observation_freshness=0.9,
)
result = run_state_engine(snapshot, omega, projection_result, events, StateConfig())
print(result.updated_market_svp.phi.dominant_state)   # LifecycleState member
print(result.transition_confidence)                   # float in [0, 1]
```

### Workflow (engine + persistence in one call)

```python
from sqlalchemy.orm import Session
from ugh_quantamental.persistence.db import create_db_engine, create_all_tables, create_session_factory
from ugh_quantamental.workflows.models import ProjectionWorkflowRequest
from ugh_quantamental.workflows.runners import run_projection_workflow

engine = create_db_engine()          # defaults to in-memory SQLite
create_all_tables(engine)
session: Session = create_session_factory(engine)()

req = ProjectionWorkflowRequest(
    projection_id="my-question-id", horizon_days=30,
    question_features=q, signal_features=sig,
    alignment_inputs=align,
)
result = run_projection_workflow(session, req)
session.commit()

print(result.engine_result.projection_snapshot.point_estimate)
print(result.persisted_run.created_at)   # naive UTC datetime
```

### Query (read-only inspection)

```python
from ugh_quantamental.query import ProjectionRunQuery
from ugh_quantamental.query.readers import list_projection_run_summaries, get_projection_run_bundle

summaries = list_projection_run_summaries(session, ProjectionRunQuery(projection_id="my-question-id"))
bundle = get_projection_run_bundle(session, run_id=summaries[0].run_id)
print(bundle.result.projection_snapshot.point_estimate)
```

### Replay (single-run regression check)

```python
from ugh_quantamental.replay import ProjectionReplayRequest
from ugh_quantamental.replay.runners import replay_projection_run

replay = replay_projection_run(session, ProjectionReplayRequest(run_id="proj-abc123"))
if replay is not None:
    print(replay.comparison.exact_match)          # True if engine output unchanged
    print(replay.comparison.point_estimate_diff)  # absolute diff (0.0 if exact match)
```

### Batch replay (multi-run regression check)

```python
from ugh_quantamental.replay import ProjectionBatchReplayRequest
from ugh_quantamental.replay.batch import replay_projection_batch

batch_req = ProjectionBatchReplayRequest(run_ids=("proj-abc123", "proj-def456"))
result = replay_projection_batch(session, batch_req)
print(result.aggregate.requested_count)   # 2
print(result.aggregate.mismatch_count)    # 0 if engine unchanged
```

### Regression suite (named pass/fail report)

```python
from ugh_quantamental.replay.suite_models import (
    RegressionSuiteRequest, ProjectionSuiteCase,
)
from ugh_quantamental.replay.suites import run_regression_suite

req = RegressionSuiteRequest(
    projection_cases=(
        ProjectionSuiteCase(name="smoke", run_ids=("proj-abc123",)),
    )
)
result = run_regression_suite(session, req)
print(result.aggregate.passed_case_count)  # 1 if exact match and at least one run
print(result.projection_cases[0].passed)   # True / False
```

### Baseline (golden snapshot create + compare)

```python
from ugh_quantamental.replay.baseline_models import (
    CreateRegressionBaselineRequest, CompareRegressionBaselineRequest,
)
from ugh_quantamental.replay.baselines import (
    create_regression_baseline, compare_regression_baseline,
)

# Pin a named baseline
bundle = create_regression_baseline(
    session,
    CreateRegressionBaselineRequest(baseline_name="v1-golden", suite_request=req),
)
session.commit()

# Compare a future rerun against the pinned baseline
result = compare_regression_baseline(
    session,
    CompareRegressionBaselineRequest(baseline_name="v1-golden"),
)
if result is not None:
    print(result.comparison.exact_match)          # True if suite result unchanged
    print(result.comparison.passed_case_count_diff)  # 0 if no change in passing cases
```

### Weekly FX report (read-only aggregation)

```python
from datetime import datetime
from zoneinfo import ZoneInfo

from ugh_quantamental.fx_protocol.models import CurrencyPair
from ugh_quantamental.fx_protocol.report_models import WeeklyReportRequest
from ugh_quantamental.fx_protocol.reporting import run_weekly_report

_JST = ZoneInfo("Asia/Tokyo")

req = WeeklyReportRequest(
    pair=CurrencyPair.USDJPY,
    report_generated_at_jst=datetime(2026, 3, 16, 10, 0, 0, tzinfo=_JST),
    business_day_count=5,   # last 5 completed protocol windows
    max_examples=3,         # up to 3 curated case examples per category
)
result = run_weekly_report(session, req)   # read-only — no writes or flushes

# Strategy-level metrics
for m in result.strategy_metrics:
    print(m.strategy_kind, m.direction_accuracy, m.mean_abs_close_error_bp)

# UGH vs baseline comparison
for c in result.baseline_comparisons:
    print(c.baseline_strategy_kind, c.direction_accuracy_delta_vs_ugh)

# Per-lifecycle-state breakdown
for s in result.state_metrics:
    print(s.dominant_state, s.forecast_count, s.direction_accuracy)

# GRV-lock fire vs non-fire split
print(result.grv_fire_summary.mean_grv_lock_fire)

# Curated case examples
for ex in result.false_positive_cases:
    print(ex.forecast_id, ex.close_error_bp, ex.conviction)
```

## Development

```bash
ruff check .   # lint
pytest -q      # tests
```

Both must pass cleanly. CI enforces the same checks on every PR and push.

## Specification documents

Formal v1 specs live in `docs/specs/`:

| File | Covers |
|---|---|
| `ugh_market_ssv_v1.md` | Enum taxonomy and schema contracts (Milestones 1–3) |
| `ugh_projection_engine_v1.md` | Projection engine math and API (Milestone 4) |
| `ugh_state_engine_v1.md` | State lifecycle update functions and API (Milestone 5) |
| `ugh_persistence_v1.md` | Persistence scaffolding policy and schema (Milestone 6) |
| `ugh_workflow_v1.md` | Workflow composition layer and import policy (Milestone 7) |
| `ugh_query_v1.md` | Read-only query layer: summaries, filtering, bundle rehydration (Milestone 8) |
| `ugh_replay_v1.md` | Deterministic replay / regression layer and comparison policy (Milestone 9) |
| `ugh_batch_replay_v1.md` | Batch replay / experiment runner (Milestone 10) |
| `ugh_regression_suite_v1.md` | Regression suite runner and pass/fail policy (Milestone 11) |
| `ugh_baseline_v1.md` | Baseline / golden snapshot management and comparison policy (Milestone 12) |
| `fx_daily_protocol_v1.md` | FX daily protocol contracts, calendar helpers, and ID generation (Milestone 13) |
| `fx_daily_forecast_workflow_v1.md` | Daily forecast workflow: UGH + 3 baselines, idempotency (Milestone 14) |
| `fx_daily_outcome_evaluation_workflow_v1.md` | Daily outcome/evaluation workflow (Milestone 15) |
| `fx_daily_automation_v1.md` | GitHub Actions automation and durable SQLite data branch (Milestone 16) |
| `fx_weekly_report_v1.md` | Read-only weekly report: window selection, metrics, baseline comparison, case examples (Milestone 17) |

## FX Daily Protocol automation (Milestone 16)

A GitHub Actions workflow runs the FX daily protocol automatically every business
day at **08:00 JST** (23:00 UTC the previous day, Mon–Fri).

### How it works

1. The workflow checks out the code branch and a separate `fx-daily-data` branch
   (created automatically on first run).
2. Alembic migrations are applied to a SQLite database file in `fx-daily-data`.
3. `scripts/run_fx_daily_protocol.py` fetches USDJPY market data, creates the
   daily forecast batch (UGH + 3 baselines), and — when the prior window is
   available — records the outcome and per-forecast evaluations.
4. If any data changed, the SQLite file is committed and pushed back to the
   `fx-daily-data` branch only (never to `main`).

### Data source

USDJPY market data is fetched from the **Yahoo Finance chart API** — a public,
unauthenticated HTTPS endpoint.  No API key, no GitHub Secrets, and no private
endpoint configuration is required to run the automation.

If you have a private data feed, set `FX_DATA_URL` as a repository secret; the
script will use your endpoint instead of Yahoo Finance.

### Environment variables / secrets

No secrets are required for default operation.

| Variable | Where | Description |
|---|---|---|
| `FX_DATA_URL` | GitHub Secret (optional) | Override with a private endpoint; default uses Yahoo Finance |
| `FX_DATA_AUTH_TOKEN` | GitHub Secret (optional) | Bearer token for custom endpoint only |
| `FX_DATA_BRANCH` | GitHub Variable | Data branch name (default: `fx-daily-data`) |
| `FX_SQLITE_FILENAME` | GitHub Variable | SQLite filename (default: `fx_protocol.db`) |
| `FX_THEORY_VERSION` | GitHub Variable | UGH theory version (default: `v1`) |
| `FX_ENGINE_VERSION` | GitHub Variable | UGH engine version (default: `v1`) |
| `FX_SCHEMA_VERSION` | GitHub Variable | Schema version (default: `v1`) |
| `FX_PROTOCOL_VERSION` | GitHub Variable | Protocol version (default: `v1`) |

### Running locally

```bash
# No secrets needed — Yahoo Finance is used by default.
export FX_DATA_DIR="./data"
python scripts/run_fx_daily_protocol.py

# Optional: use a custom private endpoint instead.
export FX_DATA_URL="https://your-data-endpoint/usdjpy"
python scripts/run_fx_daily_protocol.py
```

### Durable storage

All forecast, outcome, and evaluation records are stored in a SQLite database
file committed to the `fx-daily-data` branch.  This branch is isolated from
the code branch; data commits do not trigger CI.

### What is still out of scope (v1)

- Monthly reporting (next milestone)
- Multi-pair support beyond USDJPY
- Intraday or high-frequency data
- External broker integration
- Async execution

## Out of scope

The following are intentionally not implemented:

- ML fitting, calibration, or learned weight matrices
- Stochastic/probabilistic filtering (particle filters, Kalman, etc.)
- REST/gRPC service layer
- Async execution or background jobs
- Intra-day or high-frequency signal handling
- Monthly reporting (next milestone)

## PR review auto-fix bot (same PR branch)

### Purpose
- Automatically handle only **clear/mechanical** PR review findings (diff comments and review body comments) and keep fixes inside the **same PR head branch**.
- Push is allowed only after validations succeed; no child PR workflow is used.

### Non-goals
- Large design refactors, API contract changes, abstract feedback interpretation, or risky multi-file transformations.

### Why GitHub Actions (not GitHub App)
- This repository already uses GitHub Actions CI and has no webhook server runtime.
- The MVP can stay lightweight and repo-local by adding one workflow + Python module.
- Triggering on review events and pushing to the PR head branch is directly supported.

### Setup
1. Ensure workflow `.github/workflows/review-autofix.yml` is enabled.
2. Keep workflow permissions minimal (`contents: write`, `pull-requests: write`).
3. Configure repository variables as needed (see env example below).

### Required events
- `pull_request_review_comment` (`created`, `edited`)
- `pull_request_review` (`submitted`, `edited`)

### Local run
```bash
export GITHUB_EVENT_PATH=/path/to/event.json
export GITHUB_EVENT_NAME=pull_request_review_comment
export BOT_MODE=detect_only
python -m ugh_quantamental.review_autofix.bot
```

### Environment example
```bash
BOT_MODE=detect_only
TARGET_REVIEWERS=
DRY_RUN=true
ALLOW_PUSH_ON_FORK=false
VALIDATION_FORMAT_COMMANDS=
VALIDATION_LINT_COMMANDS="ruff check ."
VALIDATION_TYPECHECK_COMMANDS=
VALIDATION_TEST_COMMANDS="pytest -q"
REPLY_ON_SUCCESS=true
REPLY_ON_FAILURE=true
AUTO_RESOLVE=false
LOG_LEVEL=INFO
```

### Operation modes
- `detect_only` (Phase 1)
- `propose_only` (Phase 2)
- `apply_and_push` (Phase 3)
- `apply_push_and_resolve` (Phase 4; resolve is flag-gated)

### same-repo PR vs fork PR
- same-repo PR: can apply, validate, and push to the same PR head branch.
- fork PR: defaults to no push (`ALLOW_PUSH_ON_FORK=false`), handled as propose-only/dry-run.

### Safety notes
- Do not execute arbitrary commands from review text.
- Keep changes minimal and directly linked to the matched rule.
- Never push when validation fails.
- Do not log secrets.

### Known constraints
- Rule set is intentionally narrow for MVP; unmatched/ambiguous comments are skipped.
- Review-body automation requires enough location hints (e.g., `file: path/to/file.py`).
- Duplicate prevention uses a state key (`review_comment_id + head_sha` or `review_id + head_sha`).
