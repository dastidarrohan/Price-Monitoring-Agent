"""Chrome/Helium browser lifecycle management.

This isolates all the fiddly, environment-dependent bits of getting a
headless Chrome session running inside a container (Colab, Docker, CI)
so the rest of the codebase doesn't need to know about sandbox flags,
retries, or driver resolution.
"""

from __future__ import annotations

import logging
import time

import helium
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from .config import settings

logger = logging.getLogger(__name__)


def _build_chrome_options() -> webdriver.ChromeOptions:
    options = webdriver.ChromeOptions()
    if settings.headless:
        options.add_argument("--headless=new")
    # Required when running as root inside a container (Colab, Docker, CI).
    options.add_argument("--no-sandbox")
    # /dev/shm is often too small in containers and crashes Chrome shortly
    # after launch if not disabled.
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    width, height = settings.window_size
    options.add_argument(f"--window-size={width},{height}")
    return options


def start_browser() -> "webdriver.Chrome":
    """Start a Chrome session with retries.

    Chrome can fail to start intermittently in constrained container
    environments (resource pressure, transient permission issues). Retrying
    with backoff avoids a flaky one-off crash killing an entire monitoring
    run.
    """
    last_error: Exception | None = None
    for attempt in range(1, settings.browser_start_retries + 1):
        try:
            options = _build_chrome_options()
            driver = helium.start_chrome(
                headless=settings.headless, options=options
            )
            driver.set_page_load_timeout(settings.page_load_timeout_s)
            logger.info("Chrome started successfully (attempt %d)", attempt)
            return driver
        except WebDriverException as exc:
            last_error = exc
            logger.warning(
                "Chrome failed to start (attempt %d/%d): %s",
                attempt,
                settings.browser_start_retries,
                exc,
            )
            time.sleep(settings.browser_start_backoff_s * attempt)

    raise RuntimeError(
        "Could not start Chrome after multiple attempts. If you're running "
        "in Colab or another container, make sure Chrome is installed "
        "(see README) and that '--no-sandbox' is set."
    ) from last_error


def stop_browser() -> None:
    try:
        helium.kill_browser()
    except Exception as exc:  # noqa: BLE001 - cleanup should never raise
        logger.warning("Error while closing browser: %s", exc)


def safe_go_to(url: str) -> None:
    """Navigate with retries, so one flaky page load doesn't kill a run."""
    last_error: Exception | None = None
    for attempt in range(1, settings.action_retries + 1):
        try:
            helium.go_to(url)
            return
        except WebDriverException as exc:
            last_error = exc
            logger.warning(
                "Navigation to %s failed (attempt %d/%d): %s",
                url,
                attempt,
                settings.action_retries,
                exc,
            )
            time.sleep(settings.action_backoff_s * attempt)
    raise RuntimeError(f"Failed to load {url} after retries") from last_error
