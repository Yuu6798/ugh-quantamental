# UGH Persistence v1 — Minimal deterministic run persistence scaffold

## Why v1 uses JSON-backed persistence with typed metadata

Milestone 6 needs durable storage for deterministic projection/state runs without redesigning current schema or engine contracts. v1 therefore stores full run payloads as JSON derived from existing Pydantic contracts, while extracting a minimal set of typed metadata columns for common lookup and filtering (`projection_id`, `snapshot_id`, `omega_id`, `dominant_state`).

This keeps persistence thin, safe, and aligned with the current codebase state.

## Projection run persistence

`ProjectionRunRecord` persists one deterministic projection execution:

- `run_id` (PK)
- `created_at`
- `projection_id`
- `question_features_json`
- `signal_features_json`
- `alignment_inputs_json`
- `config_json`
- `result_json`

Policy:
- Inputs and outputs are serialized from existing Pydantic models.
- `result_json` stores full `ProjectionEngineResult`, including the outward `ProjectionSnapshot`.

## State run persistence

`StateRunRecord` persists one deterministic state-engine execution:

- `run_id` (PK)
- `created_at`
- `snapshot_id`
- `omega_id`
- `projection_id` (nullable)
- `dominant_state`
- `transition_confidence`
- `snapshot_json`
- `omega_json`
- `projection_result_json`
- `event_features_json`
- `config_json`
- `result_json`

Policy:
- Persist full deterministic run context as JSON so runs are replay/audit friendly.
- Keep only essential searchable metadata typed at column level.

## Serialization policy

- Serialization uses `model_dump(mode="json")` from current Pydantic models.
- Rehydration uses `model_validate(...)` against the same models.
- Serializer helpers are pure and side-effect free.
- No custom transformation layer is added in v1.
- `created_at` is normalized at repository save boundaries to **naive UTC** (aware timestamps are converted to UTC first; naive timestamps are treated as already UTC).

This ensures deterministic contracts remain source-of-truth for persistence shape.

## Why deeper normalization is deferred

v1 intentionally avoids normalized domain tables (e.g., per-question ledgers, evidence lineage tables, or analytics-specific dimensions). The current requirement is to persist deterministic engine inputs/results safely with minimal moving parts.

Deeper normalization would add migration complexity, coupling, and query design overhead before runtime requirements are stable.

## Intentionally deferred beyond v1

- Query optimization/index tuning beyond minimal metadata indexes
- Warehouses/OLAP materializations
- External DB deployment patterns
- Runtime orchestration/scheduling
- Analytics views/derived marts
- Service layer, CLI, async persistence, cache/connectors
