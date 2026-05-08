"""Shared CSV write helpers for ``fx_protocol`` exports.

A single canonical implementation of "write rows to a CSV path" reused by
forecasts, outcomes, evaluations, observability artifacts, weekly /
monthly review exports, and AI annotation drafts. Modules that need
backwards-compatible aliases (``write_csv_rows`` in :mod:`csv_exports`,
``write_csv_artifact`` / ``append_csv_row`` in :mod:`observability`)
re-export from here.
"""

from __future__ import annotations

import csv
import os
from typing import Any, Literal

ExtrasAction = Literal["raise", "ignore"]


def write_csv_rows(
    path: str,
    rows: list[dict[str, Any]],
    fieldnames: tuple[str, ...],
    *,
    extrasaction: ExtrasAction = "raise",
) -> str:
    """Write *rows* to *path* with *fieldnames* column order.

    Parent directories are created if they do not exist; existing files
    are overwritten (idempotent rerun policy). Returns the absolute path.
    """
    abs_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(fieldnames), extrasaction=extrasaction)
        writer.writeheader()
        writer.writerows(rows)
    return abs_path


def append_csv_row(
    path: str,
    row: dict[str, Any],
    fieldnames: tuple[str, ...],
    *,
    extrasaction: ExtrasAction = "raise",
) -> str:
    """Append *row* to *path*; create the file with a header if missing.

    Returns the absolute path.
    """
    abs_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    write_header = not os.path.exists(abs_path)
    with open(abs_path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(fieldnames), extrasaction=extrasaction)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
    return abs_path


__all__ = ["write_csv_rows", "append_csv_row"]
