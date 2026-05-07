# FX UGH Engine v2 — Data-driven projection redesign

Spec version: v2 (supersedes v1 projection logic; engine internals are mutable
per the determinism-only invariant in CLAUDE.md)
Status: Draft
Owner: `src/ugh_quantamental/engine/projection.py`,
       `src/ugh_quantamental/engine/projection_models.py`,
       `src/ugh_quantamental/fx_protocol/market_ugh_builder.py`
Predecessor: v1 was constructed before any operational data existed.

## 1. Background

The v1 engine was designed before any UGH forecast logs existed. It was a
mental construction. Now we have one month (March 20 – April 24, 2026) of
operational forecast / outcome / evaluation data to inform a redesign.

The CLAUDE.md invariants that must be preserved are:
- **Determinism**: same inputs → same outputs
- **Pure functions**: no side effects, no globals, no I/O
- **Bounded values**: explicit clamping, no NaN/inf
- **Frozen schemas**: existing Pydantic models stay `frozen=True`

The internal math, coefficients, and pipeline structure of the engine
are **explicitly mutable** based on observed performance.

## 2. Observed facts (April 2026)

From `csv/analytics/monthly/202605/monthly_review.md` (16 business days,
review date 2026-05-01) and weekly reports for 4/6 onwards:

### 2.1 What works

| Component | Metric | April result |
|---|---|---|
| `engine/state.py` (state engine) | `state_proxy_hit_rate` | **100% (16/16)** |
| Volatility band derivation (`_build_range_from_baseline_context`) | `range_hit_rate` | **75–80%** |
| Provider / data layer | success / fallback / lag | 17 success / 0 fallback / 0 lag |

### 2.2 What does not work

| Observation | Strength | Implication |
|---|---|---|
| UGH `direction_hit_rate` overall | 31.2% (5/16) | Below baseline_simple_technical (43.8%) |
| UGH `direction_hit_rate` choppy regime | **0/11** (p ≈ 0.0005 vs 50:50 prior) | Systematic anti-pattern, not noise |
| UGH `mean_close_error_bp` | 19.2 bp, identical to baseline_random_walk to within 0.5 bp | Magnitude signal is noise (now partially fixed by PR #87 unit scaling) |
| `inspect_direction_logic` flag | fired in monthly review | UGH-vs-best-baseline gap > 10 pp |

### 2.3 Smoking-gun structural finding

**`price_implied_score` is computed in `derive_signal_features` but never
consumed by `compute_e_raw`.**

`compute_e_raw` (v1, `projection.py:71-88`) uses only:
- `u_score`
- `fire_probability` (via `fire_component = 2p − 1`)
- `technical_score`

It ignores: `price_implied_score`, `fundamental_score`, `regime_fit`,
`narrative_dispersion`, `evidence_confidence`. Several of these are computed
specifically as projection inputs but the projection function never reads
them.

`price_implied_score` is the bp-normalized prev close change
(`prev_close_change_bp / trailing_mean_abs_change_bp`, clamped to [-1, +1]).
It is precisely the signal that powers `baseline_prev_day_direction`, which
beats UGH by 12.5 pp on April data. **UGH is leaving usable directional
information on the table.**

## 3. Structural diagnosis (why v1 fails in choppy)

In choppy regimes (momentum_5d ≈ 0, spot ≈ sma20):

| v1 component | Value | Contribution to e_raw |
|---|---|---|
| `u_score` | ≈ 0 (all directional inputs collapse) | 0 |
| `fire_probability` | ≈ 0 (multiplicative, requires both range_exp and momentum) | `f_weight × (0 × 2 − 1) = −0.30` |
| `technical_score` | ≈ 0 (momentum × 100 → 0) | 0 |
| **e_raw (pre-alignment)** | | **≈ −0.30** |

The result: e_raw is systematically pushed to −0.30 regardless of any
directional context. After gravity_bias and clamping, e_star is most often a
small negative number → forecast direction = DOWN. Choppy days that closed
UP are missed; choppy days that closed DOWN are matched only by accident of
sign. The 0/11 hit rate is the empirical fingerprint of this structural
DOWN bias.

## 4. Hypotheses for May 2026 verification

These are the propositions v2 makes that May data will confirm or reject.

| ID | Hypothesis | Measurable in May | Failure → action |
|---|---|---|---|
| H1 | Removing the `fire = 0` anti-thrust bias eliminates the systematic 0/N choppy direction-miss pattern. | UGH choppy `dir_rate > 0%`; binomial test against 50:50 no longer rejects in either tail. | Phase 3: regime-aware switching. |
| H2 | Adding `price_implied_score` to `compute_e_raw` lifts UGH choppy `dir_rate` toward `baseline_prev_day_direction` parity. | UGH choppy `dir_rate ≥ baseline_prev_day_direction choppy dir_rate − 15 pp`. | Drop p_weight, try mean-reversion factor. |
| H3 | Fire-as-conviction-amplifier preserves trending performance. | UGH trending `dir_rate ≥ baseline_simple_technical trending dir_rate − 10 pp`. | Re-tune u_weight / t_weight ratio. |
| H4 | The state engine and volatility band remain unchanged-good. | `state_proxy_hit_rate ≥ 95%`, `range_hit_rate ≥ 70%`. | Engine regression; revert state-related changes. |
| H5 | UGH magnitude is no longer indistinguishable from random_walk. | `mean_close_error_bp` differs from baseline_random_walk by ≥ 1.0 bp in either direction in any weekly report. | conviction-multiplier tuning. |

These five hypotheses define the v2 success contract. Each is independently
falsifiable.

## 5. New factors and inputs

No new schema fields are introduced. v2 reuses existing `SignalFeatures`
fields that v1 computed but did not consume.

### 5.1 `ProjectionConfig` additions

| Field | Default | Purpose |
|---|---|---|
| `p_weight` | `0.20` | Weight of `price_implied_score` in direction signal (new) |
| `conviction_floor` | `0.5` | Minimum conviction multiplier when `fire_probability == 0` (new) |

`u_weight` (default 0.40), `f_weight` (0.30), `t_weight` (0.30) are
**re-roled**: `f_weight` no longer multiplies a directional component;
instead it scales the conviction band width (see §6.1). `u_weight` and
`t_weight` continue to weight directional components, with `p_weight`
joining them.

Default sum is `u_weight + t_weight + p_weight = 0.80`; normalization is
explicit in the formula below.

### 5.2 `fire_probability` redefinition

v1: multiplicative (`range_exp × momentum_abs`, returns 0 in choppy)
v2: additive evidence model with neutral prior 0.5

```python
range_evidence = clamp((range_expansion - 1.0) * 2.0, -1.0, 1.0)
momentum_evidence = clamp(abs(momentum_5d) * 200.0, 0.0, 1.0)
thrust_score = 0.5 * range_evidence + 0.5 * momentum_evidence
fire_probability = clamp(0.5 + 0.5 * thrust_score, 0.0, 1.0)
```

Semantic: `fire_probability` measures the probability of directional thrust
with 0.5 as the no-information prior. `0.5 → no contribution to e_raw`,
`> 0.5 → boost direction signal`, `< 0.5 → shrink direction signal`.

## 6. Revised engine math

### 6.1 `compute_e_raw` v2

```python
def compute_e_raw(u_score, signal_features, alignment, config):
    """v2: direction signal × conviction multiplier × alignment.

    Direction signal is a weighted sum of three independent directional
    inputs (u, technical, price-implied). Conviction multiplier is derived
    from fire_probability and shrinks (never inverts) the direction signal.
    """
    direction_weight_total = config.u_weight + config.t_weight + config.p_weight
    direction_signal = (
        config.u_weight * u_score
        + config.t_weight * signal_features.technical_score
        + config.p_weight * signal_features.price_implied_score
    ) / direction_weight_total

    # fire_probability ∈ [0, 1]; conviction_multiplier ∈ [conviction_floor, 1.0]
    conviction_multiplier = config.conviction_floor + (1.0 - config.conviction_floor) * signal_features.fire_probability

    return _clamp(direction_signal * conviction_multiplier * alignment, -1.0, 1.0)
```

Key properties:
- **No anti-thrust bias**: `fire = 0` shrinks direction by `conviction_floor`
  (default 0.5×) but never flips its sign.
- **No-direction → no-output**: if all three direction inputs are 0,
  e_raw = 0 regardless of fire.
- **All directional inputs are independent**: `price_implied_score` enters
  e_raw directly, no longer trapped in mismatch_px.

### 6.2 `compute_u` (unchanged)

The directional utility function works correctly for trending markets and
collapses gracefully to 0 in choppy. v2 preserves it byte-identical.

### 6.3 `compute_gravity_bias` (unchanged)

Gravity bias is small in magnitude and does not contribute to the structural
choppy bias. Left unchanged for v2; coefficient tuning is deferred to a
later data-driven pass.

### 6.4 Other functions

`compute_alignment`, `compute_e_star`, `compute_mismatch_*`,
`compute_conviction`, `compute_urgency`, `build_projection_snapshot`,
`run_projection_engine` are unchanged in structure. Only `compute_e_raw`
is replaced.

## 7. Migration

| Step | Action |
|---|---|
| 1 | Bump `FX_THEORY_VERSION` from `v1` to `v2` in `.github/workflows/fx-daily-protocol.yml` and `fx-analysis-pipeline.yml`. Records persist version in `forecast_record.theory_version` for audit. |
| 2 | Implement v2 in `engine/projection.py` and `fx_protocol/market_ugh_builder.py`. |
| 3 | Update `engine/projection_models.py` to add `p_weight` and `conviction_floor` fields with defaults. |
| 4 | Update existing engine tests (`tests/engine/test_projection.py`) with new golden values; add tests per §8. |
| 5 | Land before next Monday's automated weekly cron so 5/11 → 5/29 data accumulates under v2. |
| 6 | After 10+ business days under v2, re-run monthly review and check H1–H5. |

Historical `v1` records remain untouched (read-only replay invariant).
Weekly / monthly reports stratify by `theory_version` if present; the v1/v2
boundary becomes auditable in CSV.

## 8. Test plan

### 8.1 New unit tests

Engine (`tests/engine/test_projection.py`):

| Test | Inputs | Expected |
|---|---|---|
| `test_e_raw_zero_when_all_directional_inputs_zero` | u=0, technical=0, price_implied=0, any fire | e_raw == 0.0 |
| `test_fire_zero_shrinks_but_does_not_flip` | u=+0.5, technical=+0.5, price_implied=+0.5, fire=0 | e_raw > 0, magnitude shrunk to 50% of fire=1 case |
| `test_fire_one_maximizes_signal` | direction inputs +0.5, fire=1.0 | e_raw matches direction_signal × alignment exactly |
| `test_price_implied_alone_drives_direction` | u=0, technical=0, price_implied=+1.0, fire=1.0 | e_raw = +0.20 / 0.80 × 1.0 × alignment = +0.25 × alignment |
| `test_no_anti_thrust_bias_in_choppy` | all directional inputs 0, fire ∈ {0, 0.5, 1} | e_raw == 0.0 in all cases |

Builder (`tests/fx_protocol/test_market_ugh_builder.py`):

| Test | Snapshot | Expected |
|---|---|---|
| `test_fire_neutral_when_no_signal` | range_exp=1.0, momentum=0 | fire == 0.5 (exact) |
| `test_fire_increases_with_momentum` | range_exp=1.0, momentum=+0.005 | fire > 0.5 |
| `test_fire_decreases_with_range_contraction` | range_exp=0.6, momentum=0 | fire < 0.5 |
| `test_fire_clamped_to_unit_interval` | extreme inputs | fire ∈ [0, 1] |
| `test_fire_symmetric_in_momentum_sign` | momentum=±0.005 | identical fire |

### 8.2 Updated existing tests

Existing engine tests with hard-coded e_raw / e_star values must be
regenerated. Test name convention: prefix with `v2_` if behavior changed,
or update inline if invariant.

### 8.3 Integration tests

| Test | Description |
|---|---|
| `test_full_workflow_choppy_snapshot_neutral_e_star` | Synthetic 20-window snapshot with zero net change, finite ranges → e_star ∈ [-0.05, +0.05] |
| `test_full_workflow_directional_snapshot_correct_sign` | Monotonic up-trend snapshot → e_star > +0.30, direction = UP |
| `test_full_workflow_prev_change_picks_up_choppy` | Choppy snapshot with strong recent close change → e_raw inherits price_implied_score sign |

## 9. Acceptance criteria

v2 ships once:
1. All test plan items in §8 pass.
2. `ruff check .` and `pytest -q` clean.
3. Engine runs deterministically (same snapshot → same forecast batch).
4. `theory_version` is correctly recorded on new forecasts.

v2 is **validated** once May 2026 data shows:
1. **H1 met**: UGH choppy dir_rate > 0% in May labeled_observations.
2. **H4 met**: state_proxy_hit_rate ≥ 95%, range_hit_rate ≥ 70%.
3. At least one of {H2, H3, H5} met.

v2 is **invalidated** (escalate to Phase 3) if:
- H1 not met after 10 May business days, OR
- H4 violated (state / range engine regressed).

## 10. Out of scope (deferred)

- **Coefficient empirical fitting**. With ~30 observations split across
  4 strategies and multiple regimes, statistical fitting is underpowered.
  Defaults are chosen by structural reasoning; tuning awaits ≥3 months
  of v2 data.
- **Regime-aware switching**. If H1 fails, switching becomes the next
  spec. Until then, v2 is regime-blind by design.
- **`gravity_bias` redesign**. The bias term is small in magnitude relative
  to the −0.30 anti-thrust floor and is not the primary fault.
- **Mean-reversion explicit factor**. v2 captures mean-reversion implicitly
  via `price_implied_score` sign (when prev change was extreme, score is
  saturated; this can act as continuation OR reversion depending on weight).
  An explicit `mean_reversion_score` is reserved for Phase 3.
- **State-engine direction extraction**. The state engine returns lifecycle
  state (setup/fire/exhaustion) which is direction-agnostic. Extracting
  direction from state transitions is non-trivial and deferred.
