"""Read-only query layer for persisted projection and state runs (v1).

Query models, summary types, and bundle types are importable without SQLAlchemy::

    from ugh_quantamental.query import (
        CreatedAtRange,
        ProjectionRunQuery, StateRunQuery,
        ProjectionRunSummary, StateRunSummary,
        ProjectionRunBundle, StateRunBundle,
    )

Reader functions require SQLAlchemy and must be imported from the submodule directly::

    from ugh_quantamental.query.readers import (
        list_projection_run_summaries,
        list_state_run_summaries,
        get_projection_run_bundle,
        get_state_run_bundle,
    )
"""

from __future__ import annotations

from ugh_quantamental.query.models import (
    CreatedAtRange,
    ProjectionRunBundle,
    ProjectionRunQuery,
    ProjectionRunSummary,
    StateRunBundle,
    StateRunQuery,
    StateRunSummary,
)

__all__ = [
    "CreatedAtRange",
    "ProjectionRunBundle",
    "ProjectionRunQuery",
    "ProjectionRunSummary",
    "StateRunBundle",
    "StateRunQuery",
    "StateRunSummary",
]
