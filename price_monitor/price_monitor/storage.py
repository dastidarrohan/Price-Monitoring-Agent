"""Simple CSV-backed storage for price observations.

Kept deliberately dependency-light (no database) since this is a monitoring
script, not a service — but isolated behind a small interface so it could
be swapped for SQLite/Postgres later without touching agent code.
"""

from __future__ import annotations

import csv
import os
from dataclasses import asdict, dataclass

from .config import settings

FIELDNAMES = ["timestamp", "product_name", "url", "price", "notes"]


@dataclass
class PriceRecord:
    timestamp: str
    product_name: str
    url: str
    price: str
    notes: str = ""


def save_record(record: PriceRecord) -> None:
    path = settings.results_path()
    file_exists = os.path.isfile(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(asdict(record))


def load_records() -> list[dict]:
    path = settings.results_path()
    if not os.path.isfile(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
