# UGH State Engine v1 — Deterministic Milestone 5

## Why deterministic evidence in v1

v1 keeps the lifecycle update layer explicit, pure, and reviewable. Instead of full stochastic filtering, it uses deterministic bounded heuristics so the transition from prior `phi` to updated `phi` is explainable, reproducible, and contract-safe for downstream consumers.

This keeps Milestone 5 aligned with current schema/projection contracts while deferring calibration-heavy methods.

## Inputs consumed

The v1 state engine consumes:

- `SSVSnapshot`
  - prior lifecycle envelope: `snapshot.phi`
  - lifecycle context blocks (question/factor/timing/price/regime)
- `Omega`
  - market regime source via `omega.market_svp.regime`
  - block confidence and observability for deterministic quality scoring
- `ProjectionEngineResult`
  - deterministic forward metrics: `e_star`, `conviction`, `urgency`, mismatch terms
- `StateEventFeatures`
  - normalized event signals for catalyst/follow-through/saturation/disconfirmation/regime shock/freshness

## Pure functions

1. `compute_block_quality(omega, event_features)`
   - Computes a `[0,1]` quality score from per-block confidence × observability, blended with observation freshness.

2. `compute_state_evidence(snapshot, projection_result, event_features, config)`
   - Produces raw evidence scores for the six lifecycle states:
     - `dormant`: rises when conviction, urgency, catalyst, and follow-through are all weak.
     - `setup`: rises on positive signal with low saturation and still pre-fire conditions.
     - `fire`: rises from a weighted evidence sum
       (`0.35*catalyst + 0.35*prior.fire + 0.15*urgency + 0.15*follow_through`)
       and a catalyst floor (`catalyst_floor_coef * catalyst`), then uses the
       larger of the two bounded values. The floor lets strong-catalyst days
       fire without relying on `prior.fire` history, closing the round-4
       multiplicative-gate loophole.
     - `expansion`: rises with strong `e_star`, conviction, follow-through, and prior fire/expansion lean.
     - `exhaustion`: rises when signal stays positive but pricing saturation is high and mismatch shrinks.
     - `failure`: rises when `e_star` is negative and/or disconfirmation is
       elevated. As of **v2.4** a lone `regime_shock` is damped: it contributes
       only `regime_shock_failure_floor * regime_shock` to the failure evidence
       when uncorroborated, ramping to its full value as `negative_e` /
       `disconfirmation` corroborate it. This stops a single same-snapshot shock
       spike from flipping the state to `failure` while keeping `negative_e` and
       `disconfirmation` as full-strength single-signal triggers (see Changelog).

3. `normalize_state_probabilities(scores, config)`
   - Applies temperature softmax to map any finite score vector to a valid `StateProbabilities` simplex.
   - Default evidence-layer `softmax_temperature` is `0.5` to sharpen raw state evidence before prior blending.
   - Rejects non-finite scaled values, and config constrains temperature away from unsafe near-zero values (`softmax_temperature >= 1e-8`).

4. `blend_with_prior(prior_probabilities, evidence_scores, config)`
   - Blends prior probabilities with normalized evidence via deterministic coefficients.

5. `resolve_dominant_state(probabilities, prior_dominant_state)`
   - Selects unique dominant lifecycle state with deterministic prior-first tie resolution.

6. `build_phi(probabilities, prior_dominant_state, config)`
   - Builds schema-valid `Phi`; if tied, injects tiny epsilon to chosen winner and renormalizes.

7. `build_market_svp(snapshot, omega, updated_phi, block_quality, transition_confidence, config)`
   - Preserves top-level market regime, replaces `phi`, and recomputes confidence deterministically.

8. `run_state_engine(snapshot, omega, projection_result, event_features, config)`
   - End-to-end deterministic composition; returns `StateEngineResult`.

## Prior blending rule

Given prior distribution `P_prior` and normalized evidence distribution `P_evidence`:

- normalize blending weights from `StateConfig` (`prior_weight`, `evidence_weight`)
- blending is defined only when `prior_weight + evidence_weight > 0`
- compute statewise blended score:

`P_blended[s] = prior_w * P_prior[s] + evidence_w * P_evidence[s]`

- apply a second, final softmax over the blended non-negative vector using
  `final_softmax_temperature` (default `0.12`) to widen the winner margin at
  the actual `dominant_state` decision layer.
- if the blended vector has no positive mass, fall back to a uniform
  distribution.

The two temperatures are intentionally independent: `softmax_temperature=0.5`
sharpens the evidence side before prior blending, while
`final_softmax_temperature=0.12` sharpens only the final state-probability
distribution. This preserves the default `0.55/0.45` prior/evidence blend
needed to keep `fire` reachable while reducing knife-edge final-state ties.

## Tie-break rule

`Phi` requires a unique dominant state.

- Step 1: find tied max-probability states.
- Step 2: if prior dominant state is among tied states, choose it.
- Step 3: otherwise choose the first state in fixed order:
  `dormant -> setup -> fire -> expansion -> exhaustion -> failure`.
- Step 4: add tiny configured epsilon to chosen state and renormalize.

`tie_break_epsilon` is constrained in config to a minimum-safe positive value (`>= 1e-8`) so tie resolution remains compatible with `Phi` dominant-state validation.

This keeps tie handling deterministic and minimal.

## Intentionally deferred

Still out-of-scope in v1:

- stochastic/HMM/Bayesian filtering
- learned transition matrices or ML calibration
- persistence/connectors/CLI orchestration
- online parameter fitting
- external data retrieval

## Changelog

### v2.4 — failure hysteresis (FX-STATE-HYSTERESIS, engine_review_2026_06 ★2)

Single same-snapshot `regime_shock` spikes (e.g. the trading day after a sharp
move) previously fired the `failure` state on their own because the failure
evidence was the raw `max(negative_e, disconfirmation, regime_shock)`. That
distorted the lifecycle-state label, `state_proxy`, and regime/state-stratified
analysis even when the forecast was correct (the state is a parallel label, not
a forecast-direction input — `forecasting.py` derives direction from
`e_star × conviction`, so this is a labelling/analysis cleanup, not a
direction-prediction change).

v2.4 damps the shock term in `compute_state_evidence`:

```
shock_corroboration = max(negative_e, disconfirmation)
damped_regime_shock = regime_shock * (
    regime_shock_failure_floor + (1 - regime_shock_failure_floor) * shock_corroboration
)
failure = failure_weight * clamp(max(negative_e, disconfirmation, damped_regime_shock))
```

`regime_shock_failure_floor` (new `StateConfig` field, default `0.4`) caps the
standalone contribution of an uncorroborated shock; `negative_e` and
`disconfirmation` remain full-strength single-signal triggers. The damping is
same-snapshot only — no prior-day state is required, so no workflow/plumbing
change is needed. `engine_version` bumps `v2.3 → v2.4` (synced across
`automation_models.py`, `fx-daily-protocol.yml`, and
`scripts/run_fx_daily_protocol.py`).
