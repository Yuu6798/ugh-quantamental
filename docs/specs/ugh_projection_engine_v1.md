# UGH Projection Engine v1 — Deterministic Milestone 4

## Why v1 introduces an explicit normalized feature contract

`SSVSnapshot` is an outward schema contract, not a full projection-theory representation. For deterministic projection math, v1 introduces a small normalized feature layer (`QuestionFeatures`, `SignalFeatures`, `AlignmentInputs`, `ProjectionConfig`) so that:

- projection functions remain pure and deterministic,
- math inputs are explicitly bounded and interpretable,
- projection logic does not overfit to accidental payload shape details,
- downstream transport remains unchanged via `ProjectionSnapshot`.

This isolates deterministic projection computation from future schema evolution while preserving v1 interoperability.

## Pure deterministic functions

All functions are side-effect free and deterministic.

1. `compute_u(question_features, signal_features, config)`
   - Computes directional utility `U` in `[-1, 1]`.
   - Uses signed question direction and strength, then adjusts with contextual F/T blend.

2. `compute_alignment(alignment_inputs, config)`
   - Computes weighted pairwise alignment in `[0, 1]`.
   - Formula: `alignment = 1 - weighted_average_gap`.

3. `compute_e_raw(u_score, signal_features, alignment, config)`
   - Computes pre-bias projection signal `E_raw` in `[-1, 1]`.
   - Weighted blend of `U`, transformed fire term (`2p_fire - 1`), and technical term, then scaled by alignment.

4. `compute_gravity_bias(signal_features, config)`
   - Computes deterministic gravity adjustment with positive contributions from `grv_lock` and `regime_fit`, negative from narrative dispersion.

5. `compute_e_star(e_raw, gravity_bias)`
   - Computes final point estimate `E* = clamp(E_raw + gravity_bias, -1, 1)`.

6. `compute_mismatch_px(e_star, signal_features)`
   - Signed price mismatch: `E* - price_implied_score`.

7. `compute_mismatch_sem(question_features, signal_features)`
   - Signed semantic mismatch: normalized question intent minus semantic anchor (`avg(fundamental, technical)`).

8. `compute_conviction(signal_features, alignment, mismatch_px, mismatch_sem)`
   - Confidence-like score in `[0, 1]` from evidence confidence and alignment, penalized by mismatch magnitude.

9. `compute_urgency(question_features, signal_features, conviction)`
   - Urgency in `[0, 1]` increasing with temporal score and fire probability, modestly with lower conviction.

10. `build_projection_snapshot(...)`
    - Converts deterministic metrics to outward `ProjectionSnapshot`.

11. `run_projection_engine(...)`
    - End-to-end deterministic composition that returns `ProjectionEngineResult` and final `ProjectionSnapshot`.

## Provisional bound-generation rule (v1)

v1 bounds are intentionally simple and symmetric around `E*`.

- `width = base + mismatch_coef * mismatch_mag + low_conf_coef * (1 - conviction) + urgency_coef * urgency`
- `mismatch_mag = 0.5 * (|mismatch_px| + |mismatch_sem|)`
- `width` is clamped to `[0, bounds_max_width]`
- `lower = E* - width`, `upper = E* + width`

Properties:
- deterministic,
- finite,
- ordered,
- confidence/mismatch/urgency sensitive.

## Intentionally deferred beyond Milestone 4

- any ML/statistical fitting or calibration,
- state-transition / temporal dynamics,
- persistence concerns,
- external connectors or data-fetch integration,
- CLI/notebook workflows,
- advanced nonlinear bound asymmetry policies.

