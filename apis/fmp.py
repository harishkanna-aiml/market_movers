"""Financial Modeling Prep market movers integration."""
from __future__ import annotations

import logging

import pandas as pd

from utils.helpers import build_retry_session, normalize_records

BASE_URL = "https://financialmodelingprep.com/stable"


def _fetch(endpoint: str, category: str, api_key: str, limit: int, timeout: int,
           retry_total: int, retry_backoff: float, logger: logging.Logger) -> pd.DataFrame:
    if not api_key:
        logger.warning("FMP_API_KEY is not configured; %s will be empty.", category)
        return normalize_records([], "FMP", category)
    session = build_retry_session(retry_total, retry_backoff)
    response = session.get(
        f"{BASE_URL}/{endpoint}",
        params={"apikey": api_key},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict) and payload.get("Error Message"):
        raise RuntimeError(payload["Error Message"])
    records = payload if isinstance(payload, list) else payload.get("data", [])
    return normalize_records(records[:limit], "FMP", category)


def get_gainers(**kwargs) -> pd.DataFrame:
    return _fetch("biggest-gainers", "Gainers", **kwargs)


def get_losers(**kwargs) -> pd.DataFrame:
    return _fetch("biggest-losers", "Losers", **kwargs)


def get_actives(**kwargs) -> pd.DataFrame:
    return _fetch("most-actives", "Actives", **kwargs)
