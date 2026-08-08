"""Unit tests for price extraction regex and storage.

These deliberately don't touch Selenium/Helium or the OpenAI API — they
test the deterministic parsing logic in isolation, which is what should be
unit-tested. Browser/agent behavior is better covered by a small manual or
integration eval (see README) rather than mocked-to-uselessness unit tests.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from price_monitor.tools import _PRICE_PATTERN  # noqa: E402


def find_prices(text: str) -> list[str]:
    return [m.group() for m in _PRICE_PATTERN.finditer(text)]


def test_finds_dollar_price():
    assert find_prices("Now only $19.99 today") == ["$19.99"]


def test_finds_price_with_thousands_separator():
    assert find_prices("Retail: $1,299.00") == ["$1,299.00"]


def test_finds_multiple_currencies():
    text = "US: $19.99, UK: £15.50, EU: €17.20"
    assert find_prices(text) == ["$19.99", "£15.50", "€17.20"]


def test_finds_currency_code_price():
    assert find_prices("Price: USD 49.99") == ["USD 49.99"]


def test_ignores_plain_numbers():
    assert find_prices("In stock: 42 units, SKU 10293") == []


def test_no_prices_returns_empty_list():
    assert find_prices("No pricing information available.") == []


def test_handles_crossed_out_and_sale_price_both_captured():
    # The tool intentionally returns *all* candidates with context;
    # deciding which is the "real" price is the agent's job, not the regex's.
    text = "Was $59.99, now $39.99"
    assert find_prices(text) == ["$59.99", "$39.99"]
