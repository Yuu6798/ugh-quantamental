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
| `p_weight` | `0.20` (matches `ugh_v2_alpha`) | Weight of `price_implied_score` in direction signal (new) |
| `conviction_floor` | `0.5` (matches `ugh_v2_alpha`) | Multiplier when `fire_probability == 0`; also sets the `fire_probability == 0.5` shrink. Default value reproduces the alpha variant's behavior. |

The defaults are chosen so that `ProjectionConfig()` (no-argument
construction) keeps working everywhere it is currently called — most
notably `run_projection_engine(config=None)` and
`ProjectionWorkflowRequest.config`'s `default_factory=ProjectionConfig`,
plus replay/workflow tests that omit explicit configs. Such default-
constructed configs receive **v2-alpha behavior**, which is the
conservative variant of the four. Variant builders for beta / gamma /
delta supply explicit configs (see step 5).

`u_weight`, `t_weight`, `p_weight` weight three independent directional
components. `f_weight` is no longer used in `compute_e_raw` (see §6.1);
its conviction-shaping role is taken over by `conviction_floor`.

Direction normalization is explicit in the formula: the weighted sum is
divided by `u_weight + t_weight + p_weight`. No constraint that the three
direction weights sum to any particular value.

### 5.2 Parallel variant deployment

v2 is deployed as **four parameter variants in parallel**, exposed as four
new `StrategyKind` values. Each daily run produces one forecast from each
variant against the same snapshot, enabling head-to-head comparison
unconfounded by market regime drift.

Rationale: at this stage of the project, the goal is **proof-of-concept
parameter exploration**, not picking a single conservative production
configuration. With ~16 business days per month per variant, a single
configuration would generate underpowered evidence; running four in
parallel gives 64 strategy-days/month while every variant evaluates the
same market state, making weight-effect comparisons direct.

| Variant `StrategyKind` | u_w | t_w | p_w | floor | Hypothesis tested |
|---|---|---|---|---|---|
| `ugh_v2_alpha` | 0.40 | 0.30 | 0.20 | 0.5 | Conservative: v1 weights preserved, price_implied as add-on |
| `ugh_v2_beta` | 0.20 | 0.20 | 0.40 | 0.5 | Price-heavy: prev_change is the dominant signal (April finding extrapolated) |
| `ugh_v2_gamma` | 0.40 | 0.30 | 0.20 | 0.3 | Fire-sensitive: lower floor lets fire shrink direction more aggressively |
| `ugh_v2_delta` | 0.20 | 0.30 | 0.30 | 0.5 | u-light: tests whether u_score's composite logic adds value or noise |

Total daily forecasts: 3 baselines (existing) + 4 v2 variants = **7 strategies**.

The legacy `ugh` (v1) strategy is **retired** at v2 cut-over since it has
been empirically dominated by `baseline_simple_technical` for the entire
observation period. Historical v1 records remain readable via
`theory_version=v1` for audit; new daily runs no longer emit v1.

### 5.3 `fire_probability` redefinition

v1: multiplicative (`range_exp × momentum_abs`, returns 0 in choppy)
v2: additive evidence model with neutral prior 0.5

```python
range_evidence = clamp((range_expansion - 1.0) * 2.0, -1.0, 1.0)
momentum_evidence = clamp(abs(momentum_5d) * 200.0, 0.0, 1.0)
thrust_score = 0.5 * range_evidence + 0.5 * momentum_evidence
fire_probability = clamp(0.5 + 0.5 * thrust_score, 0.0, 1.0)
```

Semantic of `fire_probability` itself: this number measures the
probability of directional thrust, with 0.5 as the no-information prior
of the **fire formula**. Above 0.5 there is positive thrust evidence
(range expansion or momentum or both); below 0.5 there is quiescence
evidence (range contraction).

Note the asymmetry between the fire formula's centered semantic and how
it is *consumed* in `compute_e_raw` under Framing A: the conviction
multiplier maps fire monotonically to `[conviction_floor, 1.0]`, not
symmetrically around fire=0.5. Therefore fire=0.5 produces a multiplier
of `floor + (1-floor)*0.5` (= 0.75 at the default floor of 0.5), which
is a 25% magnitude shrink, not "no contribution". This is intentional:
under Framing A, the absence of thrust evidence reduces our confidence
in the direction signal; we are conservative about emitting full-strength
forecasts when fire is neutral. Only fire=1.0 produces no shrink. See
§9.5 for the future Framing B alternative where fire=0.5 *does* mean
true zero contribution.

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
    if direction_weight_total == 0.0:
        # Preserve v1's zero-denominator guard. Pydantic field constraints
        # allow ge=0.0 on each weight, so a caller may legitimately set all
        # three to zero (e.g. to disable the v2 direction layer entirely
        # while keeping fire/alignment plumbing). Return 0.0 to keep the
        # bounded/no-NaN invariant.
        return 0.0
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
- **No anti-thrust bias**: `fire = 0` shrinks direction to `conviction_floor`
  fraction of full strength (default 0.5×) but never flips its sign.
- **Conservative dampening at neutral fire**: `fire = 0.5` produces
  `multiplier = floor + (1−floor)*0.5` = 0.75 at default floor — a 25%
  magnitude shrink, not zero contribution. This is by design under
  Framing A; see §5.3 and §9.5.
- **Full strength only at maximal fire**: only `fire = 1.0` produces
  multiplier 1.0 (no shrink).
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
| 1 | Bump **both** `FX_THEORY_VERSION` and `FX_ENGINE_VERSION` from `v1` to `v2` in `.github/workflows/fx-daily-protocol.yml`, `.github/workflows/fx-analysis-pipeline.yml`, and the manual-run defaults in `scripts/run_fx_daily_protocol.py` (lines 57–58). Both bumps are required: `theory_version` reflects the UGH theory generation, and `engine_version` reflects the projection engine implementation — and v2 changes the engine math (`compute_e_raw`, `fire_probability`). Leaving `engine_version=v1` on v2 records would falsely claim v1 engine semantics, breaking audit and replay. Records persist both fields in `forecast_record.{theory_version,engine_version}` for stratification. |
| 2 | Implement v2 `compute_e_raw` in `engine/projection.py` and v2 `fire_probability` in `fx_protocol/market_ugh_builder.py`. |
| 3 | Add `p_weight` (default `0.20`) and `conviction_floor` (default `0.5`) fields to `ProjectionConfig` in `engine/projection_models.py`. Defaults are the alpha-variant values, chosen so existing `ProjectionConfig()` callers (including `run_projection_engine(config=None)`, `ProjectionWorkflowRequest.config`'s `default_factory`, and replay/workflow tests that omit configs) continue to function and receive v2-alpha behavior. Variant builders for beta/gamma/delta in step 5 supply explicit configs. |
| 4 | Add four enum values to `StrategyKind`: `ugh_v2_alpha`, `ugh_v2_beta`, `ugh_v2_gamma`, `ugh_v2_delta`. Retire `ugh` from new daily emission (keep enum for historical record loading). |
| 4b | **Migrate all UGH-classification sites to recognize the v2 variants as UGH-class strategies.** The current code hardcodes `StrategyKind.ugh` in many places that gate UGH-specific behavior; without this migration, v2 variants will fail validation, lose their range/state diagnostics, and be excluded from analytics. Introduce a helper `is_ugh_kind(k: StrategyKind) -> bool` returning True for `ugh` (legacy) and all `ugh_v2_*`, and apply it to **all** of the following call sites (verified via grep on the v1 codebase, May 2026): `models.py` `ForecastRecord` UGH-required-field validator (lines ~374-382), `models.py` `EvaluationRecord` `range_hit`/`state_proxy_hit` requirement (lines ~633-658), `outcomes.py` `evaluate_forecast_outcome` UGH-only diagnostics (lines ~221, ~342), `forecasting.py:104` (`input_snapshot_ref` population), `reporting.py:41` (`_ALL_STRATEGY_KINDS` constant), `reporting.py:279,510,515` (UGH-row filters), `observability.py:285,296` (scoreboard UGH filter), `monthly_review.py:240` (monthly UGH metric extraction), `monthly_governance.py:135` (governance filter), `analytics_annotations.py:185` (AI annotation UGH eval extraction). Without this expansion, H4 (state proxy / range hit) and the per-variant lenses in §9.5 will be empty or silently misclassified. |
| 5 | In `forecasting.py`, replace `build_ugh_forecast` with four variant builders (or one parameterized builder) that emit four `ForecastRecord`s per snapshot, each with its variant's `ProjectionConfig`. |
| 6 | Update existing engine tests (`tests/engine/test_projection.py`) with new golden values; add tests per §8. |
| 7 | Update analytics (weekly / monthly aggregations) to handle the expanded `StrategyKind` set without crashing — most queries iterate over distinct kinds and should require no change. Verify slice metric output dimensions don't break weekly_report.md formatting. |
| 7.5 | **Prerequisite check**: confirm weekly/monthly aggregation already stratifies by `theory_version` (and ideally also `engine_version`, since both bump in step 1) when computing per-strategy metrics, OR add the stratification filter before any v2 record is emitted. Without this, the first v1↔v2 boundary week will produce mixed metrics that are difficult to interpret. |
| 8 | Land before next Monday's automated weekly cron so 5/11 → 5/29 data accumulates under v2. |
| 9 | After 10+ business days under v2, re-run monthly review and check H1–H5 across all four variants. |

Historical `v1` records remain untouched (read-only replay invariant).
However, the **current** weekly and monthly aggregation implementations
do **not** stratify by `theory_version`: weekly reports load all rows
without a version filter and monthly review groups by `strategy_kind`
only. Step 7.5 is therefore not optional. Without it, the v1↔v2
boundary will silently mix records under shared `strategy_kind` values —
particularly the baseline strategies, which keep their identifiers
across the version boundary — producing per-strategy metrics that span
both theory versions and are not interpretable as either pure-v1 or
pure-v2. The v1/v2 boundary becomes auditable in CSV **only after**
step 7.5's stratification has been added (or formally verified to
already exist in code paths not yet inspected).

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

### 9.1 Philosophy

v2's purpose is **knowledge accumulation**. Every observable outcome must
produce a documented learning that informs the next milestone. There is no
"failure state" in this framework — only different routes through a
pre-cataloged decision tree. A variant that scores 0/N choppy hits is not
a failure; it is data point that constrains the design space. The only
true failure mode is **inconclusive data** (insufficient signal to
distinguish outcomes), which is itself a known risk handled in §9.4.

### 9.2 Ship criteria (operational gate before merge)

v2 ships into production once:
1. All test plan items in §8 pass for every variant.
2. `ruff check .` and `pytest -q` clean.
3. Engine runs deterministically: same snapshot → same forecast batch for
   each variant; variant outputs differ only by their config.
4. `theory_version` is correctly recorded as `v2` on new forecasts;
   `strategy_kind` correctly records `ugh_v2_alpha`/`beta`/`gamma`/`delta`.
5. All four variants produce a forecast on every daily run; no variant
   silently skips.
6. Migration step 7.5 (theory_version stratification in aggregations) is
   verified as already-present or has been added.

These are operational, not empirical. They gate the merge but say nothing
about the variants' real-world performance.

### 9.3 Knowledge criteria (the actual goal)

After ≥ 10 May 2026 business days under v2, the data must locate the
outcome unambiguously in **one cell** of the dispersion matrix below, and
the corresponding next-step decision must be recorded as a follow-up
spec. This recording is what makes v2 a success — not whether any
particular variant "won".

### 9.4 Variant dispersion → learning matrix

Read this as: "if reality looks like row X, what we learned is column Y,
and the documented next step is column Z." H1 here is simplified to
**choppy `direction_hit_count ≥ 1`** for each variant (no statistical
test required at this sample size; the binary "did we escape 0/N" is what
matters at this stage).

| Observed pattern | What we learned | Documented next step |
|---|---|---|
| All 4 variants pass H1 | The structural changes (no anti-thrust bias + price_implied invested) were the dominant lever. Weight choices were second-order at this resolution. | v3: promote `fire` to Framing B (it has discriminative room). Drop the worst-performing two variants; iterate weights on the remaining two with finer grid. |
| **Only `beta` passes H1** | `price_implied_score` is the dominant signal; v1 was systematically discarding the best information. | v3: rebuild around prev_change as the primary input; explore explicit mean_reversion factor; consider whether u_score adds anything. |
| Only `gamma` passes H1 | Fire's signal is real and lowering the floor below 0.5 unlocks it. The conservative floor was masking real conviction information. | v3: promote `fire` to Framing B; redesign the fire formula to carry directional content (continuation vs reversion evidence). |
| Only `delta` passes H1 | `u_score`'s composite logic is degrading direction prediction; demoting it (and adding price_implied) is what works. | v3: simplify or remove `compute_u`; keep technical + price_implied; reconsider what `u` was meant to capture. |
| Only `alpha` passes H1 | Conservative invest of price_implied with v1-equivalent weights is the recipe. Aggressive parameter shifts overcorrect. | v3: alpha as default; iterate one parameter at a time on smaller deltas. |
| **`alpha + gamma` pass (same direction weights, different floor) but `beta + delta` fail** | Direction weights matter more than the conviction floor. The (0.40, 0.30, 0.20) ratio is doing useful work; floor is a finer knob. | v3: hold direction weights at (0.40, 0.30, 0.20); iterate `conviction_floor` on a finer grid (0.3, 0.4, 0.5, 0.6, 0.7). |
| **`beta + delta` pass (high p_weight) but `alpha + gamma` fail (low p_weight)** | `p_weight` is the binding lever; more weight on `price_implied_score` improves direction. | v3: hold floor at 0.5; iterate `p_weight` on a finer grid (0.20, 0.30, 0.40, 0.50, 0.60). |
| **No variant passes H1** (all 0/N choppy) | The projection-direction layer needs deeper redesign than the v2 changes provided. The anti-thrust bias removal alone is insufficient. | Phase 3: regime-aware switching with a separate model for choppy markets. v2 variants retire; their data documents what didn't work. |
| H1 results are **mixed without a clean pattern** (e.g. alpha + delta pass, beta + gamma fail) | At this sample size, multiple parameter changes interact in ways that the 4-variant grid can't disambiguate. | Run v2 unchanged for one additional month to gather more data, then re-evaluate. If still ambiguous, design v2.1 with a 2-variant orthogonal comparison instead. |
| H4 violated (state or range engine regressed) by any variant | A shared engine component was inadvertently changed. | Hotfix: revert the regression; do not advance to v3 until restored. v2 results from regressed runs are quarantined. |

### 9.5 Per-variant lens reporting

Regardless of which row is realized, the May review must report the
following five lenses for each variant. These are not pass/fail criteria;
they are the data points feeding the matrix.

| Lens | Metric |
|---|---|
| Choppy direction | `dir_hit_count`, `dir_rate` on choppy-labeled observations |
| Trending direction | `dir_hit_count`, `dir_rate` on trending-labeled observations |
| Overall direction | `dir_hit_count`, `dir_rate` on all observations |
| Magnitude calibration | `mean_close_error_bp` and its delta vs `baseline_random_walk` |
| Conviction distribution | `fire_probability` distribution stats (mean, std, frac at 0.5 ± 0.05) |

The conviction distribution lens is what tells us whether `fire` carries
discriminative power (Framing B feasibility check). If most v2 days have
fire ≈ 0.5, the additive formula is producing constant noise; if fire is
spread across [0, 1], it is encoding something.

### 9.6 Closure

v2 closes successfully when:
1. The May data unambiguously selects one row of the matrix.
2. A follow-up spec for the documented next step is started.
3. Variant-level reports for all five lenses are persisted in
   `csv/analytics/monthly/202606/`.

If §9.6 condition 1 cannot be met (mixed pattern row), the spec extends
itself: another month of identical-config running is automatic, no spec
revision required. Inconclusive data is a known and handled risk, not a
failure.

## 9.5. Design choice: fire as conviction multiplier (Framing A) vs directional confirmer (Framing B)

v2 adopts **Framing A**: `fire_probability` enters `compute_e_raw` as a
conviction multiplier in `[conviction_floor, 1.0]` (default `[0.5, 1.0]`).
Fire never flips the direction signal — values below 0.5 only shrink it.

The conceptually richer alternative is **Framing B**: fire as a
directional confirmer with multiplier `2*fire − 1` in `[-1, +1]`, where
`fire = 0.5` produces `e_raw = 0` (flat, equivalent to random-walk
baseline), `fire > 0.5` amplifies direction in the same sign, and
`fire < 0.5` actively reverses it.

Framing B requires fire to **measure something with intrinsic
directional meaning** — i.e. fire's value distribution must encode
"continuation evidence" vs "reversal evidence". The current v2 fire
formula (range_evidence + |momentum_evidence|) does not: |momentum| is
non-negative by construction and range contraction is "quiescence", not
"reversal". So Framing B with the current fire formula would assign
physical meaning where none exists, producing arbitrary direction flips
in low-signal markets.

**v2 holds at Framing A** while May 2026 data is collected. If the fire
distribution observed in production clusters tightly near 0.5 with low
discriminative power, that signals the next milestone: redesign fire
itself to carry directional content (e.g., explicit mean-reversion
evidence from extreme prev_close_change magnitudes, or u_score versus
realized momentum disagreement) and promote fire to Framing B. This is
the eventual target — fire should be a quantity whose value *means*
something specific — but premature promotion is rejected.

## 10. Out of scope (deferred)

- **Coefficient empirical fitting**. With ~30 observations split across
  4 strategies and multiple regimes, statistical fitting is underpowered.
  Defaults are chosen by structural reasoning; tuning awaits ≥3 months
  of v2 data.
- **Regime-aware switching**. If H1 fails, switching becomes the next
  spec. Until then, v2 is regime-blind by design.
- **`gravity_bias` redesign**. The bias term is small in magnitude relative
  to the −0.30 anti-thrust floor and is not the primary fault.
- **Mean-reversion explicit factor**. v2 defaults to **continuation**
  (positive `p_weight = 0.20`) because the April-month evidence is that
  `baseline_prev_day_direction` (a continuation strategy) achieves
  43.8% dir hit on the same observations where UGH achieves 31.2% — i.e.
  same-direction extrapolation from prev_change is the empirically
  stronger choice with current data. If H2 fails on May data
  (UGH choppy dir_rate remains well below `baseline_prev_day_direction`
  choppy dir_rate), the next iteration negates `p_weight` to test
  reversion. An explicit `mean_reversion_score` factor that combines
  prev_change magnitude with regime-conditional reversal probability is
  reserved for Phase 3.
- **State-engine direction extraction**. The state engine returns lifecycle
  state (setup/fire/exhaustion) which is direction-agnostic. Extracting
  direction from state transitions is non-trivial and deferred.
