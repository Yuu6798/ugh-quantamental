"""Shared report-window helpers for FX weekly / monthly aggregations.

Pure helpers for the read-only post-processing pipelines:

- :func:`resolve_business_day_window`: walk a JST timestamp backwards over
  Mon-Fri days to compute the closed YYYYMMDD window the report covers.
- :func:`is_in_window`: inclusive YYYYMMDD range check.
- :func:`stratify_observations_by_versions`: Spec §7.5 filtering by
  ``theory_version`` / ``engine_version`` with auto-detect.

Importable without SQLAlchemy. No I/O. Logging only (the auto-detect
warning).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

_JST = ZoneInfo("Asia/Tokyo")


def resolve_business_day_window(
    report_date_jst: datetime,
    business_day_count: int,
) -> tuple[str, str]:
    """Return ``(start_yyyymmdd, end_yyyymmdd)`` for the report window.

    Walks backwards from the day *before* *report_date_jst* collecting
    *business_day_count* Mon-Fri dates. The report date itself is
    excluded to avoid including an incomplete current-day bucket.
    Returns YYYYMMDD strings for the oldest and newest dates.
    """
    if report_date_jst.tzinfo is not None:
        ts = report_date_jst.astimezone(_JST)
    else:
        ts = report_date_jst.replace(tzinfo=_JST)

    dates: list[datetime] = []
    candidate = ts.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    while len(dates) < business_day_count:
        if candidate.isoweekday() in range(1, 6):
            dates.append(candidate)
        candidate -= timedelta(days=1)

    dates.reverse()
    return dates[0].strftime("%Y%m%d"), dates[-1].strftime("%Y%m%d")


def is_in_window(date_str: str, start: str, end: str) -> bool:
    """Inclusive YYYYMMDD range check: ``start <= date_str <= end``."""
    return start <= date_str <= end


def stratify_observations_by_versions(
    rows: list[dict[str, str]],
    *,
    theory_version_filter: str | None = None,
    engine_version_filter: str | None = None,
) -> list[dict[str, str]]:
    """Stratify observations by ``theory_version`` and ``engine_version``.

    Spec §7.5: weekly / monthly aggregations must stratify by
    ``theory_version`` (and ideally ``engine_version``) to avoid mixing
    v1 and v2 records under shared ``strategy_kind`` values across the
    boundary week.

    Behavior:

    * If both ``theory_version_filter`` and ``engine_version_filter``
      are ``None``, **auto-detect**: when the input rows contain more
      than one distinct ``theory_version`` the latest one (lexicographic
      max across the v1/v2/... sequence) is selected and a warning is
      logged; single-version data is returned unchanged.
    * If either filter is non-None, rows whose corresponding column
      does not match are dropped.
    * Rows missing the version column entirely are kept under the
      auto-detect path (they predate stratification) but dropped under
      an explicit filter (no silent inclusion).
    """
    if theory_version_filter is None and engine_version_filter is None:
        present = {row.get("theory_version", "") for row in rows} - {""}
        if len(present) <= 1:
            return rows
        latest = max(present)
        logger.warning(
            "auto-stratifying mixed theory_versions %s; filtering to latest=%s",
            sorted(present),
            latest,
        )
        return [r for r in rows if r.get("theory_version", "") == latest]

    filtered = rows
    if theory_version_filter is not None:
        filtered = [
            r for r in filtered if r.get("theory_version", "") == theory_version_filter
        ]
    if engine_version_filter is not None:
        filtered = [
            r for r in filtered if r.get("engine_version", "") == engine_version_filter
        ]
    return filtered


__all__ = [
    "is_in_window",
    "resolve_business_day_window",
    "stratify_observations_by_versions",
]
