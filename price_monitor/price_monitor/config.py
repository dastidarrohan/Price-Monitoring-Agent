"""Central configuration for the price monitoring agent.

Keeping these values here (instead of scattered across scripts) makes the
project configurable without touching agent logic, and makes it easy to
swap models, retry counts, or output paths for different environments
(local machine, Colab, CI).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    # --- Model ---
    model_id: str = os.environ.get("PRICE_AGENT_MODEL", "gpt-4o")
    openai_api_key: str | None = os.environ.get("OPENAI_API_KEY")

    # --- Agent behavior ---
    max_steps: int = int(os.environ.get("PRICE_AGENT_MAX_STEPS", "12"))
    verbosity_level: int = int(os.environ.get("PRICE_AGENT_VERBOSITY", "1"))

    # --- Browser ---
    headless: bool = os.environ.get("PRICE_AGENT_HEADLESS", "true").lower() == "true"
    window_size: tuple[int, int] = (1280, 1600)
    page_load_timeout_s: int = 20
    browser_start_retries: int = 3
    browser_start_backoff_s: float = 2.0

    # --- Retries for in-agent browser actions (navigation, clicks, etc.) ---
    action_retries: int = 3
    action_backoff_s: float = 1.5

    # --- Output ---
    output_dir: str = os.environ.get("PRICE_AGENT_OUTPUT_DIR", "data")
    screenshot_dir: str = os.environ.get("PRICE_AGENT_SCREENSHOT_DIR", "screenshots")
    results_file: str = field(default="price_history.csv")

    def results_path(self) -> str:
        os.makedirs(self.output_dir, exist_ok=True)
        return os.path.join(self.output_dir, self.results_file)


settings = Settings()
