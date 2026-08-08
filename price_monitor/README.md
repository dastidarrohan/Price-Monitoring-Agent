![Price Monitor](price monitor.png)


# Competitor Price Monitor

An autonomous browsing agent that visits competitor product pages, extracts
current prices, and logs them to a CSV history file for trend tracking —
built with [smolagents](https://github.com/huggingface/smolagents) (agent
loop + LLM reasoning), [Helium](https://github.com/mherrmann/helium)/
[Selenium](https://www.selenium.dev/) (browser automation), and a
deterministic regex/BeautifulSoup extraction layer for the actual price
parsing.

## Why this design

LLM agents are good at *navigating* messy, unpredictable web pages (finding
the right product, handling cookie banners, scrolling to the price) but are
an unreliable and expensive way to *extract* a specific piece of structured
data. This project splits those two concerns:

- **The agent** (`price_monitor/agent.py`) handles navigation and judgment:
  which page, which element, is this the real price vs. a shipping fee or
  a "compare at" price.
- **A deterministic tool** (`extract_prices_from_current_page` in
  `price_monitor/tools.py`) parses the page with a currency-aware regex and
  hands the agent a short list of candidates — the agent picks, it doesn't
  guess from a screenshot.
- **Every step is screenshotted** (`price_monitor/callbacks.py`) and saved
  to disk, so any recorded price has an auditable "here's what the agent
  saw" trail — important for something meant to inform business decisions.
- **Each product runs in its own isolated try/except** (`run_monitor` in
  `agent.py`), so one broken page or bot-detection wall doesn't take down
  an entire batch run.

## Project structure

```
price_monitor/
  price_monitor/
    config.py      # all tunables in one place (model, retries, paths)
    browser.py      # Chrome/Helium lifecycle, retry-safe navigation
    tools.py         # extract_prices_from_current_page, record_price, search_item_ctrl_f
    storage.py       # CSV-backed price history
    callbacks.py     # per-step screenshot capture for auditability
    agent.py         # builds the CodeAgent, runs the per-product loop
  tests/
    test_tools.py    # price-regex unit tests (no browser/API needed)
    test_storage.py  # CSV read/write tests
  run.py              # CLI entrypoint
  products.example.json
  colab_setup.sh
  requirements.txt
```

## Setup

### Local / Linux

```bash
pip install -r requirements.txt
# Make sure Chrome or Chromium + a matching driver are installed.
export OPENAI_API_KEY="sk-..."
```

### Google Colab

Chrome isn't preinstalled and apt's `chromium-browser` package is a
non-functional snap stub on current Colab images, so use the included
script, which installs real Google Chrome:

```python
!bash colab_setup.sh
import os
os.environ["OPENAI_API_KEY"] = "sk-..."  # or load from Colab secrets
```

## Usage

1. Copy `products.example.json` to `products.json` and fill in real product
   names/URLs.
2. Run:

```bash
python run.py products.json
```

3. Results append to `data/price_history.csv`; screenshots land in
   `screenshots/`.

## Testing

```bash
pytest tests/ -v
```

Unit tests cover the price-extraction regex and CSV storage — the parts of
the system that should behave deterministically. Browser/agent behavior is
inherently non-deterministic (depends on live page layouts and an LLM's
navigation choices), so it's better validated with a small manual eval set
of real product URLs than with mocked unit tests that just re-assert
whatever the mock says.

## Possible extensions

- Charting: plot `data/price_history.csv` over time per product (pandas +
  matplotlib) to visualize price trends/discounting patterns.
- Alerting: send a Slack/email notification when a tracked price drops
  below a threshold.
- Scheduling: wrap `run.py` in a cron job or GitHub Actions workflow for
  daily checks.
- Swap `OpenAIServerModel` for `LiteLLMModel` to support other providers,
  or a local model via `TransformersModel` to avoid API costs entirely.

## Notes on limitations

- This automates browsing on your own behalf; always check a site's terms
  of service and `robots.txt` before scraping it, and keep request
  frequency reasonable.
- Regex-based price extraction is not perfect on every site layout — the
  agent's job is to sanity-check candidates, but spot-check the CSV output
  periodically, especially after a target site redesigns its pages.
