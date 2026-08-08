from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from price_monitor import storage  # noqa: E402


def test_save_and_load_record(tmp_path, monkeypatch):
    monkeypatch.setattr(storage.settings, "output_dir", str(tmp_path))
    monkeypatch.setattr(storage.settings, "results_file", "test_prices.csv")

    record = storage.PriceRecord(
        timestamp="2026-08-08T00:00:00+00:00",
        product_name="Widget Pro",
        url="https://example.com/widget-pro",
        price="$29.99",
        notes="on sale",
    )
    storage.save_record(record)

    rows = storage.load_records()
    assert len(rows) == 1
    assert rows[0]["product_name"] == "Widget Pro"
    assert rows[0]["price"] == "$29.99"


def test_multiple_records_append(tmp_path, monkeypatch):
    monkeypatch.setattr(storage.settings, "output_dir", str(tmp_path))
    monkeypatch.setattr(storage.settings, "results_file", "test_prices2.csv")

    for i in range(3):
        storage.save_record(
            storage.PriceRecord(
                timestamp=f"2026-08-0{i+1}T00:00:00+00:00",
                product_name="Widget Pro",
                url="https://example.com/widget-pro",
                price=f"${20 + i}.99",
            )
        )

    rows = storage.load_records()
    assert len(rows) == 3
