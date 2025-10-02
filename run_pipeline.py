"""Command-line orchestrator for the ArtCallFinder pipeline.

Runs all state scrapers, enriches new listings with OpenAI summaries,
and exports the results to the Excel workbook in a single invocation.
"""

from __future__ import annotations

import argparse
import inspect
import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterable


ROOT_DIR = Path(__file__).resolve().parent
SCRAPER_DIR = ROOT_DIR / "scrapers"


def configure_logging(verbose: bool) -> None:
    """Configure console logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s | %(levelname)s | %(message)s")


def load_scraper_modules(scraper_dir: Path) -> Iterable[ModuleType]:
    """Yield scraper modules discovered under the scraper directory."""
    import importlib.util

    if not scraper_dir.exists():
        raise FileNotFoundError(f"Scraper directory not found: {scraper_dir}")

    for scraper_path in sorted(scraper_dir.glob("*_scraper.py")):
        module_name = f"scrapers.{scraper_path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, scraper_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            yield module
        else:
            logging.warning("Unable to load scraper file %s", scraper_path)


def run_scrapers(max_pages: int | None) -> None:
    """Import each scraper module and execute its scrape_art_calls function."""
    logging.info("Running scrapers in %s", SCRAPER_DIR)
    for module in load_scraper_modules(SCRAPER_DIR):
        scrape_func = getattr(module, "scrape_art_calls", None)
        if not callable(scrape_func):
            logging.warning("Module %s does not expose scrape_art_calls; skipping", module.__name__)
            continue

        scraper_name = module.__name__.split(".")[-1]
        logging.info("→ %s", scraper_name)

        try:
            params = inspect.signature(scrape_func).parameters
            if max_pages is not None and "max_pages" in params:
                scrape_func(max_pages=max_pages)
            else:
                scrape_func()
        except Exception as exc:  # pragma: no cover - defensive logging
            logging.exception("Scraper %s failed: %s", scraper_name, exc)
            raise


def run_summarizer() -> None:
    """Process raw listings into structured JSON via OpenAI."""
    logging.info("Running event_summarizer.py")
    from event_summarizer import main as summarize_main

    summarize_main()


def run_excel_export() -> None:
    """Append new listings to the Excel workbook."""
    logging.info("Exporting processed data to Excel")
    from util.excel_writer import write_to_excel

    write_to_excel()


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    """Parse orchestrator command-line arguments."""
    parser = argparse.ArgumentParser(description="Run the ArtCallFinder data pipeline end-to-end.")
    parser.add_argument("--skip-scrape", action="store_true", help="Skip running the web scrapers")
    parser.add_argument("--skip-summarize", action="store_true", help="Skip the OpenAI summarization step")
    parser.add_argument("--skip-export", action="store_true", help="Skip exporting to Excel")
    parser.add_argument("--max-pages", type=int, help="Limit paginated scraper requests (applies to scrapers that accept max_pages)")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging(args.verbose)

    try:
        if not args.skip_scrape:
            run_scrapers(args.max_pages)
        else:
            logging.info("Skipping scrape step")

        if not args.skip_summarize:
            run_summarizer()
        else:
            logging.info("Skipping summarize step")

        if not args.skip_export:
            run_excel_export()
        else:
            logging.info("Skipping Excel export")
    except Exception as exc:  # pragma: no cover - top-level safeguard
        logging.error("Pipeline failed: %s", exc)
        return 1

    logging.info("Pipeline finished successfully")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
