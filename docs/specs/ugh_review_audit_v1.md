# UGH Review Audit Engine v1 — PR Review Semantic Audit

## Why this layer exists

The `review_autofix` bot classifies and applies mechanical PR review fixes. It
records what it fixed, but not whether the fix was semantically aligned with
the reviewer's intent.

The review audit engine adds a deterministic audit layer that computes:

- **PoR** (Probability of Relevance) — how well the bot can address the
  reviewer's intent, given the clarity, locality, and mechanicalness of the
  review comment.
- **ΔE** (semantic divergence) — how much the applied fix deviated from that
  intent, measured as a distance between intent and action feature vectors.
- a **verdict** categorising the outcome as `aligned | marginal | misaligned |
  insufficient_data`.

This layer follows the same `engine → persist → replay` pattern as the
projection and state engines. v1 integrates with the review_autofix bot in
**shadow mode only** — results are stored and logged, but never used to block
pushes or trigger enforcement.

---

## Three-layer extraction boundary

Raw review text is never passed into the engine. A deterministic extraction
pipeline converts raw observations into bounded, typed features before the
engine is called:

```
ReviewContext           raw GitHub event data (frozen dataclass)
    │
    ▼  extract_review_observation()       rule-based, deterministic
ReviewObservation       symbolic intermediate: bool / enum / int counts
    │
    ▼  extract_review_intent_features()   normalization to [0, 1]
ReviewIntentFeatures    bounded floats consumed by the engine
    │
    ▼  run_review_audit_engine()
ReviewAuditSnapshot / ReviewAuditEngineResult
```

This separation ensures:

- the engine remains pure, connector-free, and fully reproducible,
- extractor rule changes are tracked independently from engine changes,
- raw text is preserved in persistence as an audit trail but never modifies
  engine computation.

---

## Inputs consumed

### `ReviewIntentFeatures` (required — pre-action)

| Field | Range | Meaning |
|---|---|---|
| `intent_clarity` | [0, 1] | How clearly the reviewer specified what to fix |
| `locality_strength` | [0, 1] | How tightly scoped the fix target is |
| `mechanicalness` | [0, 1] | How mechanical / automation-safe the fix is |
| `scope_boundness` | [0, 1] | Whether the reviewer explicitly constrained fix scope |
| `semantic_change_risk` | [0, 1] | Estimated risk of unintended behavioural change |
| `validation_intensity` | [0, 1] | Implied level of validation the fix requires |

### `FixActionFeatures | None` (optional — post-action only)

| Field | Range / Type | Meaning |
|---|---|---|
| `changed` | bool | Whether the executor produced any change |
| `validation_ok` | bool | Whether validation passed |
| `lines_changed` | int ≥ 0 | Raw lines changed |
| `files_changed` | int ≥ 0 | Raw files changed |
| `target_file_match` | [0, 1] | Fix touched the file the reviewer referenced |
| `line_anchor_touched` | [0, 1] | Fix touched the line / hunk the reviewer referenced |
| `diff_hunk_overlap` | [0, 1] | Overlap between applied diff and reviewer diff hunk |
| `scope_ratio` | [0, 1] | Fix scope relative to intent (0 = tight, 1 = broad) |
| `validation_scope_executed` | [0, 1] | Breadth of validation actually run |
| `behavior_preservation_proxy` | [0, 1] | Estimated probability existing behaviour was preserved |
| `execution_status` | str | `"succeeded" \| "no_op" \| "failed" \| "timeout" \| "skipped"` |

`FixActionFeatures` is `None` in detect_only / propose_only modes, or when the
audit runs before code execution.

### `ReviewAuditConfig`

| Field | Default | Constraint |
|---|---|---|
| `w_clarity` | 0.30 | > 0.0 |
| `w_locality` | 0.25 | > 0.0 |
| `w_mechanical` | 0.20 | > 0.0 |
| `w_scope` | 0.25 | > 0.0 |
| `extractor_version` | `"v1"` | str |
| `feature_spec_version` | `"v1"` | str |

The four weights are not required to sum to exactly 1.0; `compute_por`
normalises by their total internally.

---

## ReviewObservation — semantic field definitions

`ReviewObservation` is the symbolic intermediate layer produced by
`extract_review_observation`. It is stored in `observation_json` for extractor
replay. It is **never** passed into the engine.

| Field | Type | Extraction rule |
|---|---|---|
| `has_path_hint` | bool | `context.path is not None` |
| `has_line_anchor` | bool | `context.line is not None or context.start_line is not None` |
| `has_diff_hunk` | bool | `context.diff_hunk is not None` |
| `priority` | `"P0" \| "P1" \| "P2" \| "P3"` | `extract_priority(context.body)` |
| `mechanical_keyword_hits` | int ≥ 0 | count of `_AUTO_KEYWORDS` tokens in `context.body` |
| `skip_keyword_hits` | int ≥ 0 | count of `_SKIP_KEYWORDS` tokens in `context.body` |
| `behavior_preservation_signal` | bool | body contains any of: `"preserve"`, `"behavior"`, `"existing"`, `"既存"` |
| `scope_limit_signal` | bool | body contains any of: `"minimal"`, `"only"`, `"scope"`, `"最小"`, `"のみ"` |
| `ambiguity_signal_count` | int ≥ 0 | count of `"should"`, `"consider"`, `"提案"` in body |
| `target_file_present` | bool | `context.path is not None` |
| `review_kind` | `"diff_comment" \| "review_body"` | `"diff_comment"` if `context.diff_hunk` else `"review_body"` |

All token-match operations are case-insensitive. Keyword lists (`_AUTO_KEYWORDS`,
`_SKIP_KEYWORDS`) are sourced from `classifier.py` to stay consistent with the
existing classification layer.

---

## ReviewIntentFeatures — normalization rules

`extract_review_intent_features(obs: ReviewObservation) -> ReviewIntentFeatures`

Each feature is computed deterministically from `ReviewObservation` fields and
clamped to `[0, 1]` before being written into the model.

### `intent_clarity`

Priority contributes a base score: `P0 → 1.0, P1 → 0.75, P2 → 0.5, P3 → 0.25`.

```
priority_score = {P0: 1.0, P1: 0.75, P2: 0.5, P3: 0.25}[priority]
clarity_raw = 0.35 * priority_score
            + 0.25 * float(has_path_hint)
            + 0.25 * float(has_line_anchor)
            + 0.15 * float(has_diff_hunk)
intent_clarity = clamp(clarity_raw, 0.0, 1.0)
```

### `locality_strength`

```
locality_raw = 0.55 * float(has_line_anchor)
             + 0.45 * float(has_diff_hunk)
locality_strength = clamp(locality_raw, 0.0, 1.0)
```

### `mechanicalness`

```
mech_raw = min(1.0, mechanical_keyword_hits / 3.0)
         - 0.15 * min(1.0, skip_keyword_hits / 2.0)
mechanicalness = clamp(mech_raw, 0.0, 1.0)
```

### `semantic_change_risk`

```
ambiguity_factor = min(1.0, ambiguity_signal_count / 3.0)
risk_raw = 0.5 * ambiguity_factor
         + 0.3 * float(behavior_preservation_signal)
         + 0.2 * min(1.0, skip_keyword_hits / 2.0)
semantic_change_risk = clamp(risk_raw, 0.0, 1.0)
```

### `scope_boundness`

```
scope_raw = 0.6 * float(scope_limit_signal)
          - 0.4 * semantic_change_risk
scope_boundness = clamp(scope_raw, 0.0, 1.0)
```

### `validation_intensity`

```
validation_raw = 0.4 * (1.0 - mechanicalness)
              + 0.6 * semantic_change_risk
validation_intensity = clamp(validation_raw, 0.0, 1.0)
```

---

## Pure deterministic functions

All functions are side-effect free and deterministic. No raw text enters any
function.

### 1. `compute_por(intent, config) -> float`

PoR measures the probability that the bot can perform a semantically relevant
fix, integrating clarity, locality, mechanicalness, and scope-boundness.

```
w_total = w_clarity + w_locality + w_mechanical + w_scope
por = (  w_clarity    * intent.intent_clarity
       + w_locality   * intent.locality_strength
       + w_mechanical * intent.mechanicalness
       + w_scope      * intent.scope_boundness
     ) / w_total

por = clamp(por, 0.0, 1.0)
```

### 2. `compute_delta_e(intent, action, config) -> float | None`

ΔE measures semantic divergence between what the reviewer intended and what the
bot actually applied.

**If `action is None`: return `None`.** Absence of action data is not the same
as zero divergence; returning `None` is distinct from returning `0.0`.

```
intent_vector = [
    intent.locality_strength,
    intent.mechanicalness,
    intent.scope_boundness,
    intent.validation_intensity,
]

action_vector = [
    action.target_file_match,
    action.diff_hunk_overlap,
    1.0 - min(1.0, action.scope_ratio),   # inverted: lower scope_ratio = tighter = more aligned
    action.validation_scope_executed,
]

weights = [0.25, 0.25, 0.25, 0.25]   # uniform in v1

delta_e = clamp(
    sum(w * abs(iv - av) for w, iv, av in zip(weights, intent_vector, action_vector)),
    0.0, 1.0,
)
```

### 3. `compute_mismatch_score(por, delta_e) -> float | None`

```
if delta_e is None:
    return None
return clamp(0.5 * (1.0 - por) + 0.5 * delta_e, 0.0, 1.0)
```

### 4. `compute_verdict(por, delta_e, action) -> str`

Rules are evaluated top-to-bottom; first matching rule wins.

| Condition | Verdict |
|---|---|
| `action is None` | `"insufficient_data"` |
| `por >= 0.7 and delta_e <= 0.2` | `"aligned"` |
| `por < 0.4 or delta_e > 0.6` | `"misaligned"` |
| otherwise | `"marginal"` |

### 5. `build_audit_snapshot(audit_id, por, delta_e, mismatch_score, verdict) -> ReviewAuditSnapshot`

Assembles the output contract. All scalar fields are clamped to their declared
bounds before construction. `delta_e` and `mismatch_score` may be `None`.

### 6. `run_review_audit_engine(audit_id, intent, action, config) -> ReviewAuditEngineResult`

End-to-end composition:

```
por            = compute_por(intent, config)
delta_e        = compute_delta_e(intent, action, config)
mismatch_score = compute_mismatch_score(por, delta_e)
verdict        = compute_verdict(por, delta_e, action)
snapshot       = build_audit_snapshot(audit_id, por, delta_e, mismatch_score, verdict)
return ReviewAuditEngineResult(
    audit_snapshot = snapshot,
    intent_features = intent,
    action_features = action,
    config = config,
)
```

---

## action is None policy

When `FixActionFeatures` is absent:

- `delta_e = None` — not `0.0`; absence of action data is not the same as zero
  divergence, and `0.0` would misrepresent a fully-aligned fix.
- `mismatch_score = None` — derived from `delta_e`, inherits `None`.
- `verdict = "insufficient_data"`.

This occurs in detect_only and propose_only bot modes, and in any pre-action
audit invocation before code execution completes.

---

## Shadow mode policy

v1 is **non-enforcing shadow audit only**.

| Bot mode | Audit phase | `FixActionFeatures` | Possible verdicts |
|---|---|---|---|
| `detect_only` | pre-action only | `None` | `"insufficient_data"` only |
| `propose_only` | pre-action only | `None` | `"insufficient_data"` only |
| `apply_and_push` | pre-action + post-action | present | all four |
| `apply_push_and_resolve` | pre-action + post-action | present | all four |

In all modes:

- `push_head_branch()` is never conditional on the audit verdict.
- The verdict is written to persistence and emitted to the log only.
- No enforcement, blocking, or user-visible reply is triggered by the verdict.

The purpose of v1 shadow integration is **measurement, storage, and replay** —
not enforcement. Enforcement is explicitly deferred.

---

## Persistence boundary

The review audit run record stores the following JSON columns:

| Column | Content | Purpose |
|---|---|---|
| `review_context_json` | Serialised `ReviewContext` dataclass | Audit trail; source for extractor replay |
| `observation_json` | `ReviewObservation` | Extractor replay comparison target |
| `intent_features_json` | `ReviewIntentFeatures` | Engine replay input |
| `action_features_json` | `FixActionFeatures` or `null` | Engine replay input |
| `engine_result_json` | `ReviewAuditEngineResult` | Stored output |
| `extractor_version` | e.g. `"v1"` | Tracks which rule set produced the observation |
| `feature_spec_version` | e.g. `"v1"` | Tracks which normalization formula set was used |

`ReviewContext` is a **frozen dataclass**, not a Pydantic `BaseModel`. The
serialization boundary uses dedicated helpers distinct from `dump_model_json` /
`load_model_json`:

```python
dump_review_context_json(context: ReviewContext) -> dict
load_review_context_json(payload: dict) -> ReviewContext
```

Raw text fields in `review_context_json` (e.g. `body`, `diff_hunk`) are
preserved verbatim for audit trail purposes. They are not re-fed into the
engine during replay or any other operation.

---

## Replay policy

Replay is split into two independent operations to isolate sources of drift.

### Engine replay

Re-runs the engine from stored `intent_features_json` and `action_features_json`.

```
run_id
    ▼
get_review_audit_run_bundle(session, run_id)
    ├── None  →  return None
    ▼
run_review_audit_engine(
    audit_id = bundle.audit_id,
    intent   = bundle.intent_features,    recovered from DB
    action   = bundle.action_features,    recovered from DB (may be None)
    config   = bundle.engine_result.config,
)
    ▼
ReviewAuditReplayComparison(
    exact_match, por_diff, delta_e_diff, mismatch_score_diff, verdict_match
)
```

Detects: engine code changes that produce different outputs from identical typed
inputs.

### Extractor replay

Re-runs the extractor from stored `review_context_json`.

```
run_id
    ▼
get_review_audit_run_bundle(session, run_id)
    ├── None  →  return None
    ▼
load_review_context_json(bundle.review_context_json)
    ▼
extract_review_observation(context)
extract_review_intent_features(observation)
    ▼
ReviewAuditExtractorReplayComparison(
    observation_match, intent_features_match, per-field observation diffs
)
```

Detects: extractor rule changes that shift feature values for identical raw
inputs.

Both replay operations are **read-only** — no writes, flushes, or commits.

---

## extractor_version / feature_spec_version policy

- `extractor_version` tracks which keyword / rule set was active in
  `feature_extractor.py` when the observation was produced.
- `feature_spec_version` tracks which normalization formula set was active when
  intent features were computed.
- Both default to `"v1"` and are stored on every run record.
- When keyword sets change (e.g. `_AUTO_KEYWORDS` updated), increment
  `extractor_version`.
- When normalization formulas or weights change, increment
  `feature_spec_version`.
- Extractor replay surfaces a version mismatch warning when stored version tags
  differ from the current module values.
- Engine replay is independent of these version tags.

---

## Intentionally deferred beyond v1

| Capability | Reason deferred |
|---|---|
| Push blocking / verdict enforcement | Shadow mode only in v1; enforcement requires verdict accuracy validation first |
| LLM-based or non-deterministic extractor | Breaks replay guarantee; violates determinism principle |
| Learned / calibrated PoR weights or ΔE weights | Requires historical data accumulation; calibration deferred |
| Cross-PR learning or persistent trend tracking | Requires cross-run aggregation state; out of scope |
| Human approval UI | No service layer in this repository |
| Adaptive verdict thresholds | Fixed thresholds in v1; calibration deferred |
| Extractor replay persistence (storing diff results) | Ephemeral in v1 |
| Non-uniform ΔE component weights | Uniform 0.25 in v1; per-feature weighting deferred |
| Async execution | Repository is synchronous throughout |
| REST / gRPC API layer | Out of scope per architecture principles |
