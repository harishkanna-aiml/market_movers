"""Run all market-mover integrations and export one formatted Excel workbook."""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Callable

import pandas as pd

from apis import finviz, fmp, polygon, robinhood, yahoo
from config import settings
from utils.excel_writer import export_workbook
from utils.helpers import STANDARD_COLUMNS, ensure_schema
from utils.logger import setup_logger

DataCall = Callable[..., pd.DataFrame]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect market movers and export to Excel.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output .xlsx path. Defaults to output/market_movers_YYYYMMDD_HHMMSS.xlsx",
    )
    parser.add_argument("--limit", type=int, default=settings.max_results, help="Rows per API/category.")
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    settings.ensure_directories()
    logger = setup_logger("market_movers", settings.log_dir, settings.log_level)
    limit = max(1, min(args.limit, 250))

    common = {
        "limit": limit,
        "timeout": settings.request_timeout,
        "retry_total": settings.retry_total,
        "retry_backoff": settings.retry_backoff,
        "logger": logger,
    }
    tasks: dict[str, tuple[DataCall, dict]] = {
        "Robinhood_Gainers": (robinhood.get_gainers, common),
        "Robinhood_Losers": (robinhood.get_losers, common),
        "Robinhood_Actives": (robinhood.get_actives, common),
        "FMP_Gainers": (fmp.get_gainers, {**common, "api_key": settings.fmp_api_key}),
        "FMP_Losers": (fmp.get_losers, {**common, "api_key": settings.fmp_api_key}),
        "FMP_Actives": (fmp.get_actives, {**common, "api_key": settings.fmp_api_key}),
        "Polygon_Gainers": (polygon.get_gainers, {**common, "api_key": settings.polygon_api_key}),
        "Polygon_Losers": (polygon.get_losers, {**common, "api_key": settings.polygon_api_key}),
        "Yahoo_Market": (yahoo.get_market, common),
        "Finviz_Market": (finviz.get_market, {**common, "user_agent": settings.finviz_user_agent}),
    }

    frames: dict[str, pd.DataFrame] = {}
    logger.info("Starting %d market-data tasks with up to %d workers.", len(tasks), settings.max_workers)
    with ThreadPoolExecutor(max_workers=min(settings.max_workers, len(tasks))) as executor:
        future_map = {executor.submit(func, **kwargs): name for name, (func, kwargs) in tasks.items()}
        for future in as_completed(future_map):
            name = future_map[future]
            try:
                frames[name] = ensure_schema(future.result())
                logger.info("%s completed with %d rows.", name, len(frames[name]))
            except Exception as exc:
                logger.exception("%s failed: %s", name, exc)
                frames[name] = pd.DataFrame(columns=STANDARD_COLUMNS)

    output_path = args.output or (
        settings.output_dir / f"market_movers_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    )
    if output_path.suffix.lower() != ".xlsx":
        output_path = output_path.with_suffix(".xlsx")
    export_workbook(frames, output_path)
    logger.info("Workbook created: %s", output_path.resolve())
    print(output_path.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(run())
