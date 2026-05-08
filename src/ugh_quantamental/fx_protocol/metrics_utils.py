"""Shared row-aggregation helpers used by analytics, weekly, and monthly
reports.

Operates on the labeled-observation row shape (``list[dict[str, str]]``)
produced by the analytics pipeline: every value is the CSV-string form,
empty string denotes missing, and boolean fields use the ``"true"`` /
``"1"`` / ``"yes"`` truthy convention.
"""

from __future__ import annotations

from statistics import median

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


def safe_rate(
    numerator: int, denominator: int, *, ndigits: int | None = 4
) -> float | None:
    """Return ``numerator / denominator`` or ``None`` when *denominator* is 0.

    With ``ndigits=None`` rounding is skipped; otherwise the result is
    rounded to *ndigits* decimal places (default 4).
    """
    if denominator == 0:
        return None
    rate = numerator / denominator
    return rate if ndigits is None else round(rate, ndigits)


def safe_mean(values: list[float], *, ndigits: int | None = 2) -> float | None:
    """Return the arithmetic mean of *values* or ``None`` if empty.

    With ``ndigits=None`` rounding is skipped; otherwise the result is
    rounded to *ndigits* decimal places (default 2).
    """
    if not values:
        return None
    mean = sum(values) / len(values)
    return mean if ndigits is None else round(mean, ndigits)


def safe_median(values: list[float], *, ndigits: int | None = 2) -> float | None:
    """Return the median of *values* or ``None`` if empty.

    With ``ndigits=None`` rounding is skipped; otherwise the result is
    rounded to *ndigits* decimal places (default 2).
    """
    if not values:
        return None
    med = median(values)
    return med if ndigits is None else round(med, ndigits)


__all__ = [
    "collect_floats",
    "count_bool_rows",
    "safe_mean",
    "safe_median",
    "safe_rate",
]
