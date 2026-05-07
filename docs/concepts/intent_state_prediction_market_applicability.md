# Concept: Applicability of the Intent + State_A → State_B framework to FX markets

Status: **Concept / Future design** (target horizon: within 6 months from
2026-05-07; expected formalization to a spec sometime in
Q3/Q4 2026 after v2 completion)
Predecessor: requires `fx_ugh_engine_v2.md` to complete first
Source of inspiration: `Yuu6798/semantic-ci-code` repository
Owner (when active): TBD (currently a thinking artifact, not assigned)

## 1. The hypothesis being examined

The semantic-ci-code project rests on this claim, transposed:

> If we **define and extract** an Intent declaration, a State_A (baseline),
> and a State_B (observed), then **difference detection** and **prediction
> verification** become mechanical operations.

The semantic-ci-code instantiation:
- Intent = `target.yaml` declared by the human author
- State_A = baseline RPE (Resolved Program Entity)
- State_B = observed RPE after candidate code is applied
- Expected = compiled from Intent + change_kind templates
- Verdict = `pass` / `repair` / `fail` based on constraint evaluation
- Determinism guaranteed via hash trail over inputs and extractor versions

This document examines: **does the same framework apply to financial
markets, and where does it break?**

## 2. Why ask this question now

`ugh-quantamental` is already a partial implementation of this framework
without naming it as such:

| Framework concept | Existing UGH analog |
|---|---|
| State_A | `FxProtocolMarketSnapshot` at t-1 |
| State_B | `FxOutcomeRecord` at t |
| Intent | (implicit in `ForecastRecord`) — direction + magnitude prediction |
| Expected | `ForecastRecord.expected_close_change_bp` + `forecast_direction` |
| Verdict | `EvaluationRecord` with binary direction_hit / range_hit / state_proxy_hit |
| Determinism | `theory_version`, `engine_version`, `protocol_version` already on records |
| Hash trail | Partial: snapshot_ref + version stamps; no bit-equal verification yet |

What's **missing** vs the semantic-ci framework:
1. Explicit declarative Intent (no `forecast.yaml`)
2. Constraint kinds (state / delta / repair) — UGH does only state
3. `change_kind` template expansion (no regime → constraint set mapping)
4. `unknown_policy` decoupling (UGH hardcodes behavior in `conviction_floor`)
5. 3-tier Verdict (UGH has binary hit/miss only)
6. Repair hint generation (UGH has no closed feedback loop)
7. Evidence chain on individual forecast components (only theory_version stamp)

Adding these would test whether richer structure in the forecasting layer
changes what we can learn from each day's run.

## 3. Decomposition of the hypothesis

The hypothesis has two independently testable claims:

### Claim A: Difference detection

> Given State_A and State_B as structured entities, the diff between them
> can be extracted mechanically.

For markets: yes, trivially. Snapshot at t-1 vs t-1+1 day yields
`close_change_bp`, `range_delta`, `regime_shift_indicator`, etc. This is
already done.

### Claim B: Prediction verification

> Given State_A and Intent, an Expected State_B can be compiled, and
> Observed State_B can be checked against Expected via constraint
> evaluation.

For markets: partially. The compilation of Expected from Intent is
exactly what the UGH engine does. What's missing is the **explicit
constraint declaration** and **structured verdict generation**.

## 4. What applies to markets (hold)

These framework elements transfer cleanly:

| Element | Market mapping | Notes |
|---|---|---|
| Structured State extraction | Snapshot statistics module already exists | `compute_snapshot_statistics` is the analog of `griffe`/`mypy` for code |
| Three constraint kinds | `state` (today's vol bound), `delta` (regime shift), `repair` (next-day adjustment hint) | UGH currently only emits state-level checks |
| `unknown_policy` per constraint | When fire_probability ≈ 0.5 or momentum ambiguous, declare per-signal fallback | Generalizes v2's single `conviction_floor` |
| Evidence chain | `snapshot_ref` + extractor (statistic) + version → result | Audit trail for each constraint result |
| Hash trail / determinism | Engine is already pure; bit-equal verification is feasible | Add as a CI test |
| 3-tier Verdict (`pass`/`repair`/`fail`) | Replace binary direction_hit with verdict + hint | More information than current binary |

## 5. Where the framework breaks (limits)

These are the structural reasons the framework cannot be applied verbatim.
Each is documented because it constrains the experimental design.

### Break 1: Intent has no authority

In code, the author **declares** Intent and bears responsibility for it.
If observed code deviates, the code is wrong (or the author was wrong).

In markets, **no actor declares Intent**. UGH's forecast IS the Intent,
which means the predictor and the truth source are the same agent
self-evaluating. The "objective verdict" property of semantic-ci is lost.

Implication: the experimental analog must explicitly mark Intent as
"hypothesis under test", not "specification to enforce".

### Break 2: Repair is asymmetric and delayed

In code, `repair` regenerates the candidate code in the same PR cycle —
LLM gets feedback, retries.

In markets, repair cannot regenerate the market. It can only update the
**model** for tomorrow's forecast. The feedback loop is one-day delayed,
and the loss accrued today is permanent.

Implication: repair-hint generation is still useful as a model-tuning
signal, but cannot recover the day's forecast loss. Verdict→repair
transitions are slower than in code CI.

### Break 3: No semantic extractor, only statistical extractor

In code, `griffe` extracts the public API as a deterministic structure.
In markets, statistics extract observed behavior, but the underlying
"semantics" (why the market moved) are not recoverable from any
extractor — there is no analog of `mypy` for market intent.

Implication: market state is a thinner structure than code state. The
constraints that can be evaluated are statistical predicates, not
semantic ones (e.g., "type contract preserved" has no analog).

### Break 4: Reproducibility breaks at the data layer

Same code → same RPE: deterministic. Same snapshot → same forecast:
deterministic. But the **next** day's market is non-deterministic. The
extractor and engine are reproducible; reality is not.

Implication: hash trail and bit-equal checks apply to model outputs,
not to truth. This is fine but should be stated explicitly to avoid
implying market predictability.

### Break 5: change_kind is normative; regime is descriptive

`feature` `bugfix` `refactor` are normative — they say what the author
**ought** to be doing. `trending` `choppy` are descriptive — they
characterize what the market **happens** to be doing.

Implication: regime-templated default constraints are weaker than
change_kind templates. They can encode "typical behavior in this regime"
but not "required behavior". This shifts violations from "specification
breach" to "atypicality observed", which is a subtler but valid signal.

## 6. Proposed experimental design (Phase 4)

The experiment to verify how far the framework applies:

### 6.1 Add a `forecast_intent.yaml` declaration to each daily run

Co-emitted with the existing `ForecastRecord`, capturing:
- Declared intent (predict close direction and magnitude)
- Auto-derived `regime_kind` from snapshot
- Constraint set expanded from a `regime_kind` template
- Per-constraint `unknown_policy`

Example skeleton:

```yaml
intent: "Predict USDJPY 1-day close direction and magnitude"
forecast_id: <existing>
as_of_jst: <existing>
regime_kind: choppy
intent_confidence: 0.55
constraints:
  - id: direction_aligns_with_momentum
    kind: state
    target: forecast.direction
    operator: equals_sign
    expected: derive_from(momentum_5d)
    severity: soft
    unknown_policy: warn
  - id: magnitude_within_vol_band
    kind: delta
    target: forecast.expected_close_change_bp
    operator: within_range
    expected: [-trailing_mean_abs, +trailing_mean_abs]
    severity: hard
    unknown_policy: fail
  - id: state_compatible_with_regime
    kind: state
    target: forecast.dominant_state
    operator: included_in
    expected: regime_compatible_states[regime_kind]
    severity: hard
    unknown_policy: warn
```

### 6.2 Generate per-forecast Verdict on outcome day

Co-emitted with `EvaluationRecord`, capturing:
- Per-constraint result (`satisfied` / `violated` / `unknown`)
- Verdict roll-up (`pass` / `repair` / `fail`)
- Repair hints when constraints suggest specific adjustments

### 6.3 Run for one calendar month in parallel with v2 variants

Each daily run produces:
- 4 v2 forecast records (existing in v2 spec)
- 4 corresponding `forecast_intent.yaml` declarations
- 4 corresponding `verdict.yaml` evaluations after outcome

### 6.4 Analyze verdict distribution

After the month:
- What fraction of forecasts get `pass` / `repair` / `fail`?
- Which constraints are most frequently violated?
- Do repair hints, applied to the next day's forecast, improve dir_rate?
- Does `unknown_policy = fail` constraint tripping correlate with bad
  outcomes (= a useful early-warning signal)?

## 7. What the experiment can and cannot verify

### Can verify
- Whether structured Intent declaration is mechanically feasible for
  daily forecasts
- Whether 3-tier Verdict carries more information than binary hit/miss
  in retrospective analysis
- Whether repair hints have any signal in next-day improvement (closed
  loop test)
- Which constraint operators are useful in the market domain
- Whether `unknown_policy` per-constraint declaration is more useful
  than v2's global `conviction_floor`

### Cannot verify
- Whether markets "ought to" follow Intent — they do not
- Why a particular forecast failed (no semantic extractor)
- Whether the framework prevents losses (it can document them; it
  cannot reverse them)

## 8. Pre-conditions for activating this concept

This concept is dormant until:

1. v2 ships and one calendar month of v2 data has been collected.
2. The variant dispersion learning matrix (v2 §9.4) lands on a defined
   row, producing a v3 next-step decision.
3. The v3 next step is implemented and at least one further month of
   v3 data exists.

Only after step 3 does enough operational ground exist to test whether
Intent declaration adds learning beyond what v2/v3 already provide.

## 9. Decision points if this concept is activated

When the time comes (anticipated 2026-Q3 or Q4):

| Question | Decision criterion |
|---|---|
| Do we add `forecast_intent.yaml` as new artifact? | If verdict distribution analysis from a 1-month pilot shows ≥ 2 distinct verdict modes (not just "all pass" or "all fail"), proceed. |
| Do we replace `conviction_floor` with per-constraint `unknown_policy`? | If at least one constraint shows that a different unknown_policy than v2's default produces meaningfully different outcomes. |
| Do we add repair hint feedback loop? | If applying repair hints to next-day's variant config produces measurably better results than not applying them. |
| Do we promote constraint-based evaluation to the primary metric? | Only if the binary hit/miss metric is shown to obscure information that constraint evaluation surfaces. |

## 10. Out of scope (now and possibly forever)

These are explicitly **not** what this concept is testing:

- A trading system. Verdict→action mapping (pass→trade, fail→don't)
  is not part of this framework. The framework is for forecast quality
  observation, not execution.
- A claim that markets follow Intent. They do not.
- A replacement for the engine. The engine produces the forecast that
  becomes Intent's content. Engine and Intent declaration are layers.
- An LLM-as-judge service. Verdict is computed deterministically from
  declared constraints, not from any model's opinion.

## 11. Open questions to resolve before activating

1. Does the constraint operator set need market-specific extensions?
   (E.g., `bp_within`, `regime_consistent_with`, etc.)
2. How do `regime_kind` templates get authored — by humans (like
   change_kind) or auto-derived (which loses normativity)?
3. Should the Verdict influence forecast persistence — e.g., quarantine
   `fail` verdicts from scoreboards?
4. What's the relationship between `unknown_policy: fail` here and the
   existing `FX_LAST_RETRY` hard-fail behavior?

These do not need resolution until activation.

---

This document is a thinking artifact. It does not commit code, schema, or
workflow changes. It records the structural analysis of why and how the
semantic-ci-code framework would or would not apply, so that when the v2
data and decisions are in, this analysis is ready to use.
