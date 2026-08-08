"""Custom tools the agent can call.

Price extraction is done with plain regex/BeautifulSoup parsing rather than
asking the vision model to "read" the price off a screenshot. This is
deliberate: prices are a case where deterministic extraction is more
reliable and auditable than a model guess, and it's cheaper (no extra
vision call). The agent's job is navigation and judgment (which page, which
product, is this the right price on the page); the tool's job is precise
extraction.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

import helium
from bs4 import BeautifulSoup
from smolagents import tool

from .storage import PriceRecord, save_record

# Matches things like: $19.99  $1,299  £45.00  €9.99  USD 19.99
_PRICE_PATTERN = re.compile(
    r"(?:[$€£]|USD|EUR|GBP)\s?\d{1,3}(?:[,.]\d{3})*(?:\.\d{2})?"
)


@tool
def extract_prices_from_current_page(context_hint: str = "") -> str:
    """
    Extracts candidate prices from the currently loaded browser page.

    Parses the visible text of the current page with a currency-aware regex
    and returns up to 10 matches, each with a short snippet of surrounding
    text so the agent can judge which one is the actual product price
    (as opposed to shipping cost, a crossed-out original price, or an
    unrelated recommended product).

    Args:
        context_hint: Optional text describing what to look for (e.g. the
            product name), used only to help you interpret the results —
            not used for filtering internally.
    """
    driver = helium.get_driver()
    if driver is None:
        return "No active browser session."

    soup = BeautifulSoup(driver.page_source, "html.parser")
    text = soup.get_text(separator=" ", strip=True)

    matches = []
    for m in _PRICE_PATTERN.finditer(text):
        start = max(0, m.start() - 40)
        end = min(len(text), m.end() + 40)
        snippet = text[start:end].replace("\n", " ")
        matches.append(f"{m.group()}  (context: ...{snippet}...)")
        if len(matches) >= 10:
            break

    if not matches:
        return "No price-like text found on the current page."

    hint_note = f" Looking for: {context_hint}." if context_hint else ""
    return f"Found {len(matches)} candidate price(s).{hint_note}\n" + "\n".join(
        matches
    )


@tool
def record_price(product_name: str, url: str, price: str, notes: str = "") -> str:
    """
    Saves a confirmed product price to the results file.

    Call this once you have identified the correct price for a product on
    the current page (after reviewing extract_prices_from_current_page
    output). Each call appends one row to the price history file, so
    repeated runs over time build up a trend you can chart later.

    Args:
        product_name: Human-readable name of the product being tracked.
        url: The product page URL the price was found on.
        price: The price string as found on the page (e.g. "$19.99").
        notes: Optional free-text notes (e.g. "on sale", "out of stock").
    """
    record = PriceRecord(
        timestamp=datetime.now(timezone.utc).isoformat(),
        product_name=product_name,
        url=url,
        price=price,
        notes=notes,
    )
    save_record(record)
    return f"Recorded: {product_name} -> {price} ({url})"


@tool
def search_item_ctrl_f(text: str, nth_result: int = 1) -> str:
    """
    Searches for text on the current page via Ctrl+F-style matching and
    scrolls to the nth occurrence.

    More reliable than trying to visually locate an element, especially on
    dense e-commerce pages.

    Args:
        text: The text to search for.
        nth_result: Which occurrence to jump to (1-indexed).
    """
    driver = helium.get_driver()
    if driver is None:
        return "No active browser session."

    elements = driver.find_elements("xpath", f"//*[contains(text(), '{text}')]")
    if nth_result > len(elements):
        return f"Match n°{nth_result} not found (only {len(elements)} matches found)"
    result = f"Found {len(elements)} matches for '{text}'."
    elem = elements[nth_result - 1]
    driver.execute_script("arguments[0].scrollIntoView(true);", elem)
    result += f" Focused on element {nth_result} of {len(elements)}."
    return result
