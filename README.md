# ugh-quantamental

Minimal Python 3.11+ library implementing deterministic quantamental engines: a **projection engine** and a **state engine**. Both operate on frozen Pydantic v2 schema contracts and expose pure functions with no side effects, no I/O, and no stochastic behaviour.

## Features

- **Projection engine** — computes directional point estimates, conviction, urgency, and bounded projection snapshots from question/signal/alignment inputs
- **State engine** — updates lifecycle state probabilities via deterministic softmax blending over a 6-state simplex, driven by observable event features
- **Frozen schema contracts** — all data models use `ConfigDict(extra="forbid", frozen=True)`; validated invariants enforced at construction time
- **Pure functions** — same inputs always produce the same output; no globals, no mutation, no I/O

## Requirements

- Python 3.11+
- Pydantic v2 (`>=2,<3`)

## Installation

```bash
pip install -e .
```

## Project layout

```
src/ugh_quantamental/
├── schemas/
│   ├── enums.py            # MarketRegime, MacroCycleRegime, LifecycleState, QuestionDirection
│   ├── market_svp.py       # StateProbabilities, Phi, MarketSVP
│   ├── ssv.py              # SSVSnapshot and Q/F/T/P/R/X blocks
│   ├── omega.py            # Omega observation-quality envelope
│   └── projection.py       # ProjectionSnapshot output contract
└── engine/
    ├── projection.py        # 11 pure projection functions
    ├── projection_models.py # QuestionFeatures, SignalFeatures, AlignmentInputs, ProjectionConfig, ProjectionEngineResult
    ├── state.py             # 8 pure state-lifecycle functions
    └── state_models.py      # StateEventFeatures, StateConfig, StateEngineResult
```

## Usage

### Projection engine

```python
from ugh_quantamental.engine import (
    run_projection_engine,
    QuestionFeatures,
    SignalFeatures,
    AlignmentInputs,
    ProjectionConfig,
)
from ugh_quantamental.schemas.enums import QuestionDirection

q = QuestionFeatures(direction=QuestionDirection.positive, strength=0.8, weight=1.0)
sig = SignalFeatures(
    momentum=0.6, carry=0.3, value=0.2,
    px_z=0.5, sem_z=0.4,
    model_confidence=0.75, data_quality=0.9,
)
align = AlignmentInputs(
    momentum_carry=0.7, momentum_value=0.5, carry_value=0.6,
    question_momentum=0.8, question_carry=0.6, question_value=0.5,
)
cfg = ProjectionConfig()

result = run_projection_engine("my-question-id", 30, q, sig, align, cfg)
print(result.projection_snapshot.point_estimate)   # float in [-1, 1]
print(result.projection_snapshot.confidence)       # float in [0, 1]
```

### State engine

```python
from ugh_quantamental.engine import (
    run_state_engine,
    StateEventFeatures,
    StateConfig,
)

features = StateEventFeatures(
    momentum_score=0.6,
    breakout_score=0.4,
    volume_confirm=0.7,
    exhaustion_score=0.1,
    failure_score=0.05,
    time_in_state=3.0,
)
result = run_state_engine(snapshot, omega, projection_result, features, StateConfig())
print(result.updated_market_svp.phi.dominant_state)  # LifecycleState member
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

## Out of scope

The following are intentionally not implemented:

- ML fitting, calibration, or learned weight matrices
- Stochastic/probabilistic filtering (particle filters, Kalman, etc.)
- Persistence, serialisation, or database connectors
- External data connectors or API clients
