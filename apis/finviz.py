"""Finviz public screener scraper."""
from __future__ import annotations

import logging
from io import StringIO

import pandas as pd

from utils.helpers import build_retry_session, ensure_schema, parse_finviz_number

SCREENS = {
    "Gainers": "ta_topgainers",
    "Losers": "ta_toplosers",
    "Actives": "ta_mostactive",
}
BASE_URL = "https://finviz.com/screener.ashx"


def _scrape_screen(category: str, signal: str, limit: int, timeout: int,
                   retry_total: int, retry_backoff: float, user_agent: str) -> list[dict]:
    session = build_retry_session(retry_total, retry_backoff)
    response = session.get(
        BASE_URL,
        params={"v": "111", "s": signal},
        headers={"User-Agent": user_agent, "Accept-Language": "en-US,en;q=0.9"},
        timeout=timeout,
    )
    response.raise_for_status()
    tables = pd.read_html(StringIO(response.text))
    table = next((t for t in tables if "Ticker" in t.columns and "Price" in t.columns), None)
    if table is None:
        raise RuntimeError("Could not locate the Finviz screener table; page layout may have changed.")
    rows = []
    for _, item in table.head(limit).iterrows():
        ticker = str(item.get("Ticker", "")).upper()
        rows.append({
            "Symbol": ticker,
            "Company": item.get("Company", ""),
            "Price": parse_finviz_number(item.get("Price")),
            "Change": None,
            "Change %": parse_finviz_number(item.get("Change")),
            "Volume": parse_finviz_number(item.get("Volume")),
            "Market Cap": parse_finviz_number(item.get("Market Cap")),
            "Exchange": "",
            "Category": category,
            "Source": "Finviz",
            "URL": f"https://finviz.com/quote.ashx?t={ticker}",
        })
    return rows


def get_market(limit: int, timeout: int, retry_total: int, retry_backoff: float,
               user_agent: str, logger: logging.Logger, **_: object) -> pd.DataFrame:
    all_rows: list[dict] = []
    for category, signal in SCREENS.items():
        try:
            all_rows.extend(_scrape_screen(
                category, signal, limit, timeout, retry_total, retry_backoff, user_agent
            ))
        except Exception as exc:
            logger.warning("Finviz %s scrape failed: %s", category, exc)
    return ensure_schema(pd.DataFrame(all_rows))
