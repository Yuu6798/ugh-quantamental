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
     - `fire`: rises with strong catalyst + high prior fire + urgency + follow-through.
     - `expansion`: rises with strong `e_star`, conviction, follow-through, and prior fire/expansion lean.
     - `exhaustion`: rises when signal stays positive but pricing saturation is high and mismatch shrinks.
     - `failure`: rises when `e_star` is negative and/or disconfirmation/regime shock is elevated.

3. `normalize_state_probabilities(scores, config)`
   - Applies temperature softmax to map any finite score vector to a valid `StateProbabilities` simplex.

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
- compute statewise blended score:

`P_blended[s] = prior_w * P_prior[s] + evidence_w * P_evidence[s]`

- renormalize the blended non-negative vector to sum to `1.0` for a stable valid output distribution.

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
