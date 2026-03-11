# ugh-quantamental

Minimal Python bootstrap scaffold for a utility/library-style repository.

## Scope of this milestone

This repository currently provides only:

- Installable Python package layout under `src/ugh_quantamental/`
- Placeholder subpackages for domain models, schemas, and engine logic
- Basic lint/test tooling configuration (`ruff`, `pytest`)
- A smoke test confirming imports and package metadata

## Development

```bash
ruff check .
pytest -q
```
