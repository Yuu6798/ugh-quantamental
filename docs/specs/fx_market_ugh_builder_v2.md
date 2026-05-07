# FX Market UGH Builder v2 — Fire-probability robustness in choppy regimes

Spec version: v2 (extends v1 in `fx_daily_automation_v1.md` §"Market-derived UGH builder")
Status: Draft
Owner: `src/ugh_quantamental/fx_protocol/market_ugh_builder.py`
Related fix (already merged): `forecasting.py` UGH magnitude unit scaling (PR #87)

## 1. Motivation

The April 2026 monthly review (`csv/analytics/monthly/202605/monthly_review.md`,
review date 2026-05-01, 16 included business days) flagged
`inspect_direction_logic`:

| Strategy | Dir Hit Rate | vs UGH (Δ pp) |
|---|---|---|
| **ugh** | **31.2%** | — |
| baseline_simple_technical | 43.8% | +12.5 |
| baseline_prev_day_direction | 43.8% | +12.5 |
| baseline_random_walk | 0.0% | -31.2 |

Within the 16 observations, 11 are AI-classified as choppy and UGH hits
direction in **0 of 11** (binomial p ≈ 0.0005 against a 50:50 prior).
This is the structural anti-pattern that v2 targets.

The v1 `fire_probability` formula multiplicatively requires both range
expansion AND momentum, so when momentum is near zero (the definition of
choppy) the fire probability collapses to 0. In the projection engine,
`fire_component = fire_probability × 2 − 1`, so `fire = 0` actively pushes
`e_raw` toward `−f_weight = −0.30` regardless of direction sign — i.e. the
engine is biased anti-thrust when it should be neutral.

## 2. Scope

This spec covers **only** the `derive_signal_features` `fire_probability`
calculation in `market_ugh_builder.py:255-256` and the supporting intermediate
statistics. All other v1 derivations are unchanged:

- `derive_question_features` (no change)
- `derive_alignment_inputs` (no change)
- `derive_state_event_features` (no change)
- All `compute_snapshot_statistics` outputs other than the new ones below

The engine (`projection.py`, `state.py`) is **not modified**. Only the
application-layer feature builder changes.

## 3. v1 baseline (current behavior)

```python
# market_ugh_builder.py:255-256 (v1)
momentum_abs = abs(stats["momentum_5d"]) * 100
fire_probability = _clamp(range_exp * _clamp(momentum_abs, 0.0, 1.0), 0.0, 1.0)
```

Where:
- `range_exp = recent_mean_range_5 / trailing_mean_range_20` (typically [0.5, 2.0])
- `momentum_5d = (SMA5 − SMA20) / SMA20` (typically [-0.01, +0.01])
- `momentum_abs × 100` maps a 1% SMA gap to 1.0

### Failure mode

For any window where `momentum_abs < 0.01` (i.e. SMA5 within 0.01% of SMA20),
`fire_probability ≈ 0` regardless of range_exp. This describes essentially
every choppy regime.

`fire_component` then evaluates to ≈ −1, which contributes
`f_weight × −1 = −0.30` to the `e_raw` numerator (out of denominator
`u_weight + f_weight + t_weight = 1.0`). The result is a structural −0.30
floor on `e_raw` for choppy regimes, dwarfing any directional signal from
`u_score` or `technical_score`.

## 4. v2 design

### 4.1 Semantic refinement

`fire_probability` is redefined to mean **"probability of directional thrust,
with 0.5 as the neutral prior"**. This is consistent with how the projection
engine already consumes it (`fire_component = 2p − 1` is symmetric around 0.5)
but makes the no-information default explicit.

| `fire_probability` | `fire_component` | Engine interpretation |
|---|---|---|
| 1.0 | +1.0 | Strong thrust expected (full push toward direction) |
| 0.5 | 0.0 | No information (no contribution to `e_raw`) |
| 0.0 | −1.0 | Strong anti-thrust expected (full mean-reversion bias) |

### 4.2 Formula

```python
# v2 fire_probability — additive evidence model centered on neutral 0.5

# Range evidence: signed ratio deviation, mapped from typical band [0.5, 1.5]
# to [-1, 1]. Excess expansion → positive; contraction → negative.
range_evidence = _clamp((stats["range_expansion"] - 1.0) * 2.0, -1.0, 1.0)

# Momentum evidence: always non-negative; doubles v1 sensitivity
# (5 bp SMA gap → 0.1 evidence; 50 bp → 1.0).
momentum_evidence = _clamp(abs(stats["momentum_5d"]) * 200.0, 0.0, 1.0)

# Combined thrust score in [-0.5, 1.0]. Weights are tunable but
# default to equal contribution from range and momentum.
thrust_score = 0.5 * range_evidence + 0.5 * momentum_evidence

# Re-center on neutral prior 0.5; map thrust_score in [-0.5, 1.0]
# to fire_probability in [0.25, 1.0]. The half-open lower bound is
# intentional: anti-thrust evidence (range contraction with no momentum)
# is rare and physiologically asymmetric — quiet markets are not actively
# anti-thrust, just absent.
fire_probability = _clamp(0.5 + 0.5 * thrust_score, 0.0, 1.0)
```

### 4.3 Worked examples

| Scenario | range_exp | momentum_5d | range_ev | mom_ev | thrust | **fire_v2** | fire_v1 |
|---|---|---|---|---|---|---|---|
| Trending high-vol | 1.4 | +0.008 | +0.80 | 1.00 | +0.90 | **0.95** | 1.00 |
| Trending normal | 1.0 | +0.005 | 0.00 | 1.00 | +0.50 | **0.75** | 1.00 |
| **Choppy normal** | 1.0 | 0.000 | 0.00 | 0.00 | 0.00 | **0.50** | **0.00** |
| **Choppy expanding** | 1.3 | 0.000 | +0.60 | 0.00 | +0.30 | **0.65** | **0.00** |
| Quiet contraction | 0.7 | 0.000 | −0.60 | 0.00 | −0.30 | **0.35** | 0.00 |
| Volatile but flat | 1.5 | +0.001 | +1.00 | 0.20 | +0.60 | **0.80** | 0.30 |

The bolded choppy rows show the structural fix: choppy normal goes from
fire=0 (engine pushes e_raw down by 0.30) to fire=0.5 (neutral, zero
contribution). Choppy expanding now correctly produces a moderate thrust
signal.

## 5. Determinism and boundary contract

- All inputs (`range_expansion`, `momentum_5d`) are existing v1 statistics.
  No new statistics required.
- All operations are pure float arithmetic with explicit clamping. Same
  snapshot → same `fire_probability`, identical to v1.
- Output stays in `[0.0, 1.0]` (Pydantic `SignalFeatures.fire_probability`
  field bound preserved).
- No engine schema changes; the bounded contract with `projection.py` is
  unchanged.

## 6. Backward compatibility

This is a **breaking semantic change** to historical UGH forecasts:
- Forecasts produced under v1 (all data through PR #87) used the multiplicative
  formula. Their `fire_probability` values are persisted in
  `forecasts/USDJPY_*.csv`.
- Going forward, new daily runs will produce v2 values. Historical CSVs are
  immutable per the architecture invariant ("read-only replay" / "no
  destructive rebuild").
- Weekly / monthly reports computed from a mix of v1 and v2 data are still
  consistent at the observation level (each row's metrics use the
  `expected_close_change_bp` / `forecast_direction` recorded at the time).
- A `theory_version` bump from `v1` to `v2` is recommended (workflow env
  var `FX_THEORY_VERSION`) to make the boundary auditable in records.

## 7. Test plan

### 7.1 Unit tests (`tests/fx_protocol/test_market_ugh_builder.py`)

Add the following parametrized cases. All must pass deterministically.

| Test name | range_exp | momentum_5d | Expected fire_probability |
|---|---|---|---|
| `test_fire_neutral_when_no_signal` | 1.0 | 0.0 | 0.5 (exact) |
| `test_fire_increases_with_momentum` | 1.0 | 0.005 | > 0.5 |
| `test_fire_increases_with_range_expansion` | 1.4 | 0.0 | > 0.5 |
| `test_fire_decreases_with_range_contraction` | 0.6 | 0.0 | < 0.5 |
| `test_fire_saturates_at_max_thrust` | 2.0 | 0.02 | 1.0 (clamped) |
| `test_fire_clamped_at_lower_bound` | 0.0 | 0.0 | within [0, 0.5] |
| `test_fire_symmetric_in_momentum_sign` | 1.0 | ±0.005 | identical |
| `test_fire_independent_of_direction` | varies | varies | only abs(momentum) matters |

### 7.2 Integration tests

- `test_build_ugh_request_choppy_market_yields_neutral_fire`: synthetic
  snapshot with 20 windows of zero net change but non-zero ranges →
  asserts `fire_probability ∈ [0.4, 0.6]`.
- `test_build_ugh_request_directional_market_yields_high_fire`: synthetic
  snapshot with monotonic close progression → asserts
  `fire_probability > 0.7`.

### 7.3 Regression tests

- Existing `test_market_ugh_builder.py` cases that assert specific
  `fire_probability` values **will fail** under v2 and must be updated.
  Snapshot golden values regenerated with v2 outputs documented in commit
  message.
- `pytest -q` and `ruff check .` must remain clean.

## 8. Acceptance criteria

1. `derive_signal_features` produces v2 `fire_probability` per §4.2 formula.
2. All v2 unit tests in §7.1 pass.
3. No engine code changed (`engine/projection.py`, `engine/state.py` byte-identical).
4. Existing UGH forecast records are unchanged (read-only).
5. CLAUDE.md invariants preserved: deterministic, frozen, bounded, naive-UTC, flush-only, read-only replay.
6. After the v2 build is deployed and ≥10 business days of new data accumulate, a re-run of the monthly review must show:
   - UGH choppy `dir_rate` strictly greater than 0% (i.e. v2 escapes the
     binomial-significant 0/N anti-pattern)
   - `inspect_direction_logic` flag delta improved (UGH-vs-best-baseline gap < 10 pp), OR
   - if the flag persists, the regime-conditional metrics show non-trivial
     differentiation from random_walk baseline (`mean_close_error_bp` no
     longer tracking baseline_random_walk to within 0.5 bp)

If criterion 6 is not met after 10 business days, escalate to Phase 3
(regime-aware switching, originally Option C in the modification plan).

## 9. Out of scope

The following are tracked for future spec work but are **not** in v2:

- **Regime-aware mean-reversion fallback** (originally Option C). v2 will
  show whether the additive formula alone restores choppy hit rate above
  random; if it doesn't, switching logic becomes the next milestone.
- **Conviction factor empirical tuning** (`forecasting.py` `0.5 + 0.5*conviction`).
  v2 changes upstream of conviction; tuning the multiplier requires v2 data
  first.
- **`event_tags` annotation pipeline**. Slice analysis blind spot but not a
  forecast quality issue.
- **`ProjectionConfig.bp_scale`** (engine contract change). The application
  layer fix in PR #87 is sufficient for unit scaling; engine contract
  changes are deferred indefinitely.

## 10. Migration

1. Land this spec.
2. Implement v2 formula in `market_ugh_builder.py` with the new tests.
3. Update existing affected tests with new golden values.
4. Bump `FX_THEORY_VERSION` from `v1` to `v2` in workflow env defaults
   (`.github/workflows/fx-daily-protocol.yml`, `fx-analysis-pipeline.yml`).
5. Document the boundary in commit message and PR description.
6. Monitor the next two weekly reports for the criterion-6 metrics.
