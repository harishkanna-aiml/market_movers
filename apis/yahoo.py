"""Yahoo Finance integration through the yfinance package."""
from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import yfinance as yf

from utils.helpers import ensure_schema, safe_float

SCREENS = ("day_gainers", "day_losers", "most_actives")


def _quotes_from_result(result: Any) -> list[dict]:
    if isinstance(result, dict):
        return result.get("quotes", []) or result.get("finance", {}).get("result", [{}])[0].get("quotes", [])
    return []


def get_market(limit: int, logger: logging.Logger, **_: object) -> pd.DataFrame:
    rows = []
    for screen_name in SCREENS:
        try:
            result = yf.screen(screen_name, count=min(limit, 250))
            category = {
                "day_gainers": "Gainers",
                "day_losers": "Losers",
                "most_actives": "Actives",
            }[screen_name]
            for item in _quotes_from_result(result):
                symbol = str(item.get("symbol", "")).upper()
                if not symbol:
                    continue
                rows.append({
                    "Symbol": symbol,
                    "Company": item.get("shortName") or item.get("longName") or "",
                    "Price": safe_float(item.get("regularMarketPrice")),
                    "Change": safe_float(item.get("regularMarketChange")),
                    "Change %": safe_float(item.get("regularMarketChangePercent")),
                    "Volume": safe_float(item.get("regularMarketVolume")),
                    "Market Cap": safe_float(item.get("marketCap")),
                    "Exchange": item.get("fullExchangeName") or item.get("exchange") or "",
                    "Category": category,
                    "Source": "Yahoo Finance",
                    "URL": f"https://finance.yahoo.com/quote/{symbol}",
                })
        except Exception as exc:  # Keep other screens available if one Yahoo screen fails.
            logger.warning("Yahoo screen %s failed: %s", screen_name, exc)
    result_df = ensure_schema(pd.DataFrame(rows))
    if not result_df.empty:
        result_df = result_df.drop_duplicates(subset=["Symbol", "Category"], keep="first")
    return result_df
