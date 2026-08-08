"""Agent step callbacks: screenshot capture for an auditable trail.

Every navigation/click step gets a screenshot attached to the agent's memory
so a human can later review *what the agent actually saw* when it decided
on a price — important for a monitoring tool where silently-wrong output
(e.g. picking up a shipping fee instead of a price) is worse than a crash.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from io import BytesIO

import helium
from PIL import Image
from smolagents import CodeAgent
from smolagents.memory import ActionStep

from .config import settings

logger = logging.getLogger(__name__)


def save_screenshot(step_log: ActionStep, agent: CodeAgent) -> None:
    """Attach a screenshot of the current page to this step's memory.

    Also prunes screenshots from steps older than the last 2, so the
    agent's context doesn't balloon with images it no longer needs to
    reason about.
    """
    time.sleep(1.0)  # let JS animations / lazy-loaded prices settle
    driver = helium.get_driver()
    if driver is None:
        return

    current_step = step_log.step_number
    for previous_step in agent.memory.steps:
        if (
            isinstance(previous_step, ActionStep)
            and previous_step.step_number <= current_step - 2
        ):
            previous_step.observations_images = None

    try:
        png_bytes = driver.get_screenshot_as_png()
        image = Image.open(BytesIO(png_bytes))
        step_log.observations_images = [image.copy()]

        os.makedirs(settings.screenshot_dir, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        path = os.path.join(
            settings.screenshot_dir, f"step_{current_step:03d}_{ts}.png"
        )
        image.save(path)
    except Exception as exc:  # noqa: BLE001 - screenshots are best-effort
        logger.warning("Failed to capture screenshot at step %d: %s", current_step, exc)

    url_info = f"Current url: {driver.current_url}"
    step_log.observations = (
        url_info if step_log.observations is None else f"{step_log.observations}\n{url_info}"
    )
