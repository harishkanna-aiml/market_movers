"""Shared HTTP, conversion, and normalization helpers."""
from __future__ import annotations

import math
import re
from typing import Any, Iterable

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

STANDARD_COLUMNS = [
    "Symbol", "Company", "Price", "Change", "Change %", "Volume",
    "Market Cap", "Exchange", "Category", "Source", "URL",
]


def build_retry_session(total: int = 3, backoff: float = 0.8) -> requests.Session:
    retry = Retry(
        total=total,
        connect=total,
        read=total,
        status=total,
        backoff_factor=backoff,
        status_forcelist=(408, 425, 429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "HEAD"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def safe_float(value: Any) -> float | None:
    if value is None or value == "" or value == "-":
        return None
    if isinstance(value, (int, float)):
        try:
            return None if math.isnan(float(value)) else float(value)
        except (TypeError, ValueError):
            return None
    text = str(value).strip().replace(",", "").replace("$", "")
    multiplier = 1.0
    if text.endswith("%"):
        text = text[:-1]
    if text and text[-1:].upper() in {"K", "M", "B", "T"}:
        multiplier = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}[text[-1].upper()]
        text = text[:-1]
    try:
        return float(text) * multiplier
    except ValueError:
        return None


def clean_change_percent(value: Any) -> float | None:
    """Return percentage as a human percentage number, e.g. 5.25 means 5.25%."""
    return safe_float(value)


def first_value(mapping: dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return default


def normalize_records(records: list[dict[str, Any]], source: str, category: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for item in records:
        symbol = first_value(item, ["symbol", "ticker", "Symbol", "Ticker"], "")
        symbol = str(symbol).strip().upper()
        if not symbol:
            continue
        rows.append({
            "Symbol": symbol,
            "Company": first_value(item, ["name", "companyName", "company", "shortName", "longName", "Company"], ""),
            "Price": safe_float(first_value(item, ["price", "last", "regularMarketPrice", "Price"])),
            "Change": safe_float(first_value(item, ["change", "todaysChange", "regularMarketChange", "Change"])),
            "Change %": clean_change_percent(first_value(item, ["changesPercentage", "changePercent", "todaysChangePerc", "regularMarketChangePercent", "Change %", "Change"])),
            "Volume": safe_float(first_value(item, ["volume", "dayVolume", "regularMarketVolume", "Volume"])),
            "Market Cap": safe_float(first_value(item, ["marketCap", "market_cap", "Market Cap"])),
            "Exchange": first_value(item, ["exchange", "exchangeShortName", "fullExchangeName", "Exchange"], ""),
            "Category": category,
            "Source": source,
            "URL": first_value(item, ["url", "URL"], f"https://finance.yahoo.com/quote/{symbol}"),
        })
    return ensure_schema(pd.DataFrame(rows))


def ensure_schema(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=STANDARD_COLUMNS)
    result = df.copy()
    for column in STANDARD_COLUMNS:
        if column not in result.columns:
            result[column] = None
    return result[STANDARD_COLUMNS]


def parse_finviz_number(value: Any) -> float | None:
    return safe_float(value)


def sanitize_sheet_name(name: str) -> str:
    return re.sub(r"[\\/*?:\[\]]", "_", name)[:31]
