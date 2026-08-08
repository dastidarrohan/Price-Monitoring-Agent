"""Builds the CodeAgent and runs price-monitoring tasks.

Design choice: each product is run as a *separate* agent.run() call inside
a try/except, rather than one giant task ("check all these products"). This
means one product with a broken page, a bot-detection wall, or a confusing
layout fails in isolation and gets logged, instead of derailing the whole
batch or (worse) causing the agent to silently give up partway through with
no record of which products succeeded.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from smolagents import CodeAgent, OpenAIServerModel

from . import browser
from .callbacks import save_screenshot
from .config import settings
from .tools import extract_prices_from_current_page, record_price, search_item_ctrl_f

logger = logging.getLogger(__name__)

HELIUM_INSTRUCTIONS = """
You can use helium to browse websites. The browser is already running and
managed for you — do not try to start or close it yourself.

Navigate with:
go_to('https://example.com')

Click elements by their visible text:
click("Add to cart")
click(Link("See details"))

Scroll with:
scroll_down(num_pixels=1200)

If an element isn't found you'll get a LookupError — try search_item_ctrl_f
instead of guessing coordinates.

Never try to log in, accept cookies dialogs by guessing coordinates (use
search_item_ctrl_f and click the parent text block instead), or interact
with anything unrelated to finding the product price.

Work in small steps: navigate, observe, then act. Once you've identified
the price with extract_prices_from_current_page, call record_price to save
it, then call final_answer with a short confirmation.
"""


@dataclass
class Product:
    name: str
    url: str


def build_agent() -> CodeAgent:
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Export it or pass it via config."
        )

    model = OpenAIServerModel(
        model_id=settings.model_id, api_key=settings.openai_api_key
    )

    agent = CodeAgent(
        tools=[extract_prices_from_current_page, record_price, search_item_ctrl_f],
        model=model,
        additional_authorized_imports=["helium"],
        step_callbacks=[save_screenshot],
        max_steps=settings.max_steps,
        verbosity_level=settings.verbosity_level,
    )
    # Inject helium's functions (go_to, click, scroll_down, ...) into the
    # agent's sandboxed execution namespace.
    agent.python_executor("from helium import *")
    return agent


def run_monitor(products: list[Product]) -> dict[str, str]:
    """Run the agent once per product. Returns {product_name: status}."""
    results: dict[str, str] = {}
    driver = browser.start_browser()
    try:
        agent = build_agent()
        for product in products:
            logger.info("Checking price for: %s", product.name)
            try:
                task = f"""
I'm tracking prices for competitor analysis. Go to this product page and
find the current listed price for "{product.name}".

URL: {product.url}

Once you've confirmed the price, call record_price with the product name,
this URL, and the price you found, then finish.
""" + HELIUM_INSTRUCTIONS
                agent.run(task)
                results[product.name] = "ok"
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to check %s: %s", product.name, exc)
                results[product.name] = f"error: {exc}"
    finally:
        browser.stop_browser()

    return results
