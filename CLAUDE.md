# CLAUDE.md

Guidelines for AI assistants working in this repository.

## Repository overview

`ugh-quantamental` is a minimal Python 3.11+ library implementing deterministic quantamental engines: a **projection engine** and a **state engine**. Both operate on frozen Pydantic v2 schema contracts and expose pure functions with no side effects, no I/O, and no stochastic behaviour.

The codebase is a scaffold/research tool, not a production application. Milestones 1–5 are complete.

---

## Validation commands

Always run these before considering any change done:

```bash
ruff check .   # lint
pytest -q      # tests
```

Both must pass cleanly. CI enforces the same checks on every PR and push.

---

## Project layout

```
src/ugh_quantamental/
├── __init__.py                  # package version ("0.1.0")
├── domain/                      # placeholder — business concepts (empty)
├── schemas/                     # frozen Pydantic v2 data contracts
│   ├── enums.py                 # MarketRegime, MacroCycleRegime, LifecycleState, QuestionDirection
│   ├── market_svp.py            # StateProbabilities, Phi, MarketSVP
│   ├── ssv.py                   # SSVSnapshot and its blocks (Q/F/T/P/R/X)
│   ├── omega.py                 # Omega observation-quality envelope
│   └── projection.py            # ProjectionSnapshot output contract
└── engine/
    ├── __init__.py              # re-exports all public names via __all__
    ├── projection.py            # 11 pure projection functions
    ├── projection_models.py     # QuestionFeatures, SignalFeatures, AlignmentInputs, ProjectionConfig, ProjectionEngineResult
    ├── state.py                 # 8 pure state-lifecycle functions
    └── state_models.py          # StateEventFeatures, StateConfig, StateEngineResult

tests/
├── test_import_smoke.py
├── engine/
│   ├── test_projection.py
│   ├── test_projection_models.py
│   ├── test_state.py
│   └── test_state_models.py
└── schemas/
    ├── test_market_svp.py
    ├── test_omega.py
    ├── test_projection.py
    └── test_ssv.py

docs/specs/                      # formal v1 specifications for each milestone
```

---

## Technology stack

| Tool | Purpose |
|---|---|
| Python 3.11+ | Language (f-strings, `match`, `Self`, etc. are available) |
| Pydantic v2 (`>=2,<3`) | Schema contracts — all models are `frozen=True, strict=True` |
| ruff | Linter and formatter — line length 100, target `py311` |
| pytest | Test runner — quiet mode, `src/` on `PYTHONPATH` |
| GitHub Actions | CI on PR and push to main |

No external network calls, no databases, no secrets, no environment variables.

---

## Architecture principles

### Pure functions
All engine logic is pure: same inputs always produce the same output. Functions in `engine/projection.py` and `engine/state.py` take plain Python floats/models and return computed values or Pydantic models. No globals, no mutation.

### Frozen immutable schemas
All Pydantic models use `model_config = ConfigDict(frozen=True, strict=True)`. Never attempt to mutate a schema instance; construct a new one.

### Deterministic and bounded
Both engines are explicitly deterministic (not stochastic). All intermediate values are clamped or normalised to known ranges before being written into output contracts. Validators on schema models enforce invariants (e.g. probabilities must sum to 1, dominant state must be unique).

### Strict numeric hygiene
- `ProjectionConfig` and `StateConfig` validate that all weight fields are finite.
- `StateConfig` validates that `prior_weight + evidence_weight > 0`.
- `StateConfig.temperature` must be positive.
- `StateConfig.tie_break_epsilon` has a minimum floor.
- Non-finite values in `StateEventFeatures` raise immediately.

---

## Key domain concepts

### Enumerations (`schemas/enums.py`)
- `MarketRegime` — `risk_on | neutral | risk_off`
- `MacroCycleRegime` — `expansion | slowdown | contraction | recovery | reflation | stagflation`
- `LifecycleState` — `dormant | setup | fire | expansion | exhaustion | failure` (6 canonical states)
- `QuestionDirection` — `positive | negative | neutral`

### Schema contracts
- `StateProbabilities` — 6-float simplex over `LifecycleState` (validator: sums to 1.0 ± 1e-6)
- `Phi` — lifecycle state envelope carrying `StateProbabilities` and a unique `dominant_state`
- `MarketSVP` — top-level market state vector: `regime`, `phi`, `confidence`
- `SSVSnapshot` — multi-block snapshot with Q/F/T/P/R/X blocks (questions, fundamentals, technicals, price, regime, execution)
- `Omega` — observation-quality envelope with per-block `BlockObservability` (confidence + observability)
- `ProjectionSnapshot` — output contract: `point_estimate`, `lower_bound`, `upper_bound`, `conviction`, `urgency` (validator: lower ≤ point ≤ upper)

### Projection engine (`engine/projection.py`)
End-to-end entry point: `run_projection_engine(q, sig, align, cfg)` → `ProjectionEngineResult`.

Individual pure functions in computation order:
1. `compute_u(q, cfg)` — directional utility ∈ [−1, 1]
2. `compute_alignment(align, cfg)` — weighted pairwise alignment ∈ [0, 1]
3. `compute_e_raw(u, sig, cfg)` — pre-bias signal ∈ [−1, 1]
4. `compute_gravity_bias(sig, cfg)` — deterministic gravity adjustment
5. `compute_e_star(e_raw, gravity, cfg)` — final point estimate ∈ [−1, 1]
6. `compute_mismatch_px(e_star, sig)` — signed price mismatch
7. `compute_mismatch_sem(e_star, sig)` — signed semantic mismatch
8. `compute_conviction(e_star, align_score, sig)` — confidence-like score ∈ [0, 1]
9. `compute_urgency(sig, cfg)` — urgency ∈ [0, 1]
10. `build_projection_snapshot(...)` — assembles `ProjectionSnapshot`
11. `run_projection_engine(...)` — composes all of the above

### State engine (`engine/state.py`)
End-to-end entry point: `run_state_engine(features, prior_svp, omega, cfg)` → `StateEngineResult`.

Individual pure functions:
1. `compute_block_quality(omega, cfg)` — quality scalar from Omega and freshness
2. `compute_state_evidence(features, cfg)` — raw evidence for all 6 states
3. `normalize_state_probabilities(evidence, cfg)` — temperature softmax → valid simplex
4. `blend_with_prior(prior, new_probs, cfg)` — deterministic weighted blend
5. `resolve_dominant_state(probs)` — unique dominant state (prior-first tie-break)
6. `build_phi(probs, prior_phi, cfg)` — schema-valid `Phi` (epsilon injection for ties)
7. `build_market_svp(prior_svp, phi, cfg)` — preserves `regime`, replaces `phi`, recomputes `confidence`
8. `run_state_engine(...)` — composes all of the above

---

## Development conventions

### Code style
- Line length: 100 characters (ruff enforces this)
- Python 3.11+ syntax only
- Type annotations on all function signatures
- Docstrings on public functions and classes
- No bare `except`; be explicit about exception types

### Adding new schemas
1. Define the model in `src/ugh_quantamental/schemas/` with `frozen=True, strict=True`
2. Add field validators using `@field_validator` or `@model_validator` as needed
3. Export from `schemas/__init__.py` if the module adds one
4. Add a corresponding test file in `tests/schemas/`

### Adding new engine functions
1. Add the pure function to the appropriate `engine/*.py` module
2. Add it to `engine/__init__.py` `__all__`
3. All inputs must be normalised/bounded before use
4. Return typed output (Pydantic model or plain scalar)
5. Add tests in the corresponding `tests/engine/` file

### Tests
- Do not modify existing tests unless explicitly required by the task
- New tests should follow the existing pattern: parametrised where multiple cases exist, single-case functions for edge/boundary conditions
- No network calls, no file I/O, no randomness in tests
- Test filenames mirror source filenames (`engine/state.py` → `tests/engine/test_state.py`)

### Commits and PRs
- Do not commit, push, or open a PR unless explicitly asked
- Keep diffs tightly scoped to the requested task
- Use `/plan` for non-trivial work before starting

---

## Specification documents

Formal v1 specs live in `docs/specs/` and are the authoritative definition of each milestone:

| File | Covers |
|---|---|
| `ugh_market_ssv_v1.md` | Enum taxonomy and schema contracts (Milestones 1–3) |
| `ugh_projection_engine_v1.md` | Projection engine math and API (Milestone 4) |
| `ugh_state_engine_v1.md` | State lifecycle update functions and API (Milestone 5) |

When implementing a new milestone, read the corresponding spec first. The spec defines the required function signatures, invariants, and deferred scope.

---

## What is intentionally out of scope (deferred)

Per the v1 specs, the following are **not** implemented and should not be added without a new milestone spec:

- ML fitting, calibration, or learned weight matrices
- Stochastic/probabilistic filtering (e.g. particle filters, Kalman)
- Persistence, serialisation, or database connectors
- External data connectors or API clients
- Advanced asymmetric projection bounds
- Intra-day or high-frequency signal handling
