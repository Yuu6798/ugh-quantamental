"""Shared annotation-coverage counting for weekly / monthly reports.

The weekly report (``weekly_reports_v2.build_annotation_coverage``) and
monthly review (``monthly_review.compute_annotation_coverage_summary``)
both summarize the same per-row breakdown of ``annotation_status``
(``confirmed`` / ``pending`` / unlabeled), differing only in the output
dict key conventions of their respective downstreams. Each remains a
thin adapter around :func:`count_by_annotation_status`.

Importable without SQLAlchemy. Pure function, no I/O.
"""

from __future__ import annotations


def count_by_annotation_status(
    observations: list[dict[str, str]],
) -> dict[str, int | float]:
    """Return ``{total, confirmed, pending, unlabeled, coverage_rate}``.

    ``annotation_status`` is matched case-insensitively after stripping
    whitespace. ``coverage_rate`` is ``confirmed / total`` rounded to
    4 decimal places, or ``0.0`` for an empty input.
    """
    total = len(observations)
    if total == 0:
        return {
            "total": 0,
            "confirmed": 0,
            "pending": 0,
            "unlabeled": 0,
            "coverage_rate": 0.0,
        }

    confirmed = sum(
        1
        for r in observations
        if r.get("annotation_status", "").strip().lower() == "confirmed"
    )
    pending = sum(
        1
        for r in observations
        if r.get("annotation_status", "").strip().lower() == "pending"
    )
    unlabeled = total - confirmed - pending

    return {
        "total": total,
        "confirmed": confirmed,
        "pending": pending,
        "unlabeled": unlabeled,
        "coverage_rate": round(confirmed / total, 4),
    }


__all__ = ["count_by_annotation_status"]
