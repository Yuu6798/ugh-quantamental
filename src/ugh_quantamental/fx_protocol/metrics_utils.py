"""Shared row-aggregation helpers used by analytics, weekly, and monthly
reports.

Operates on the labeled-observation row shape (``list[dict[str, str]]``)
produced by the analytics pipeline: every value is the CSV-string form,
empty string denotes missing, and boolean fields use the ``"true"`` /
``"1"`` / ``"yes"`` truthy convention.
"""

from __future__ import annotations

_TRUTHY = ("true", "1", "yes")


def count_bool_rows(rows: list[dict[str, str]], field: str) -> int:
    """Count rows where *field* is truthy."""
    return sum(1 for r in rows if r.get(field, "").lower() in _TRUTHY)


def collect_floats(rows: list[dict[str, str]], field: str) -> list[float]:
    """Collect non-empty parseable float values from *field*."""
    result: list[float] = []
    for r in rows:
        v = r.get(field, "")
        if v != "":
            try:
                result.append(float(v))
            except (ValueError, TypeError):
                pass
    return result


__all__ = ["count_bool_rows", "collect_floats"]
