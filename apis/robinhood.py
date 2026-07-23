"""Robinhood market movers placeholder.

Robinhood does not publish a supported public market-movers API for this use case.
This module deliberately returns empty, correctly-shaped DataFrames so the workbook
always contains the requested Robinhood sheets. Replace ``_fetch_placeholder`` with
an approved data source or an authenticated integration that complies with your
account agreement and applicable terms.
"""
from __future__ import annotations

import logging

import pandas as pd

from utils.helpers import ensure_schema


def _fetch_placeholder(category: str, logger: logging.Logger, **_: object) -> pd.DataFrame:
    logger.info("Robinhood %s: placeholder module returned no rows.", category)
    return ensure_schema(None)


def get_gainers(**kwargs) -> pd.DataFrame:
    return _fetch_placeholder("Gainers", **kwargs)


def get_losers(**kwargs) -> pd.DataFrame:
    return _fetch_placeholder("Losers", **kwargs)


def get_actives(**kwargs) -> pd.DataFrame:
    return _fetch_placeholder("Actives", **kwargs)
