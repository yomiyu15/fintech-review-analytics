"""CSV helpers using the standard library (no pandas required for Task 1)."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def read_csv_rows(path: Path | str) -> list[dict[str, Any]]:
    path = Path(path)
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv_rows(
    path: Path | str,
    rows: list[dict[str, Any]],
    fieldnames: list[str] | None = None,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("Cannot write empty CSV")
    cols = fieldnames or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path
