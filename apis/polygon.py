"""Polygon.io stock snapshots integration."""
from __future__ import annotations

import logging

import pandas as pd

from utils.helpers import build_retry_session, ensure_schema

BASE_URL = "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks"


def _fetch(direction: str, category: str, api_key: str, limit: int, timeout: int,
           retry_total: int, retry_backoff: float, logger: logging.Logger) -> pd.DataFrame:
    if not api_key:
        logger.warning("POLYGON_API_KEY is not configured; Polygon %s will be empty.", category)
        return ensure_schema(None)
    session = build_retry_session(retry_total, retry_backoff)
    response = session.get(
        f"{BASE_URL}/{direction}",
        params={"apiKey": api_key},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") not in (None, "OK", "DELAYED"):
        raise RuntimeError(payload.get("error") or payload.get("message") or str(payload))

    rows = []
    for item in payload.get("tickers", [])[:limit]:
        day = item.get("day") or {}
        prev = item.get("prevDay") or {}
        last_trade = item.get("lastTrade") or {}
        ticker = item.get("ticker", "")
        price = last_trade.get("p") or day.get("c")
        change = item.get("todaysChange")
        if change is None and price is not None and prev.get("c") is not None:
            change = price - prev["c"]
        rows.append({
            "Symbol": ticker,
            "Company": "",
            "Price": price,
            "Change": change,
            "Change %": item.get("todaysChangePerc"),
            "Volume": day.get("v"),
            "Market Cap": None,
            "Exchange": "US Stocks",
            "Category": category,
            "Source": "Polygon",
            "URL": f"https://finance.yahoo.com/quote/{ticker}",
        })
    return ensure_schema(pd.DataFrame(rows))


def get_gainers(**kwargs) -> pd.DataFrame:
    return _fetch("gainers", "Gainers", **kwargs)


def get_losers(**kwargs) -> pd.DataFrame:
    return _fetch("losers", "Losers", **kwargs)
