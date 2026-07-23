"""Application configuration loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _as_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _as_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    fmp_api_key: str = os.getenv("FMP_API_KEY", "")
    polygon_api_key: str = os.getenv("POLYGON_API_KEY", "")
    max_results: int = _as_int("MAX_RESULTS", 50)
    request_timeout: int = _as_int("REQUEST_TIMEOUT", 20)
    retry_total: int = _as_int("RETRY_TOTAL", 3)
    retry_backoff: float = _as_float("RETRY_BACKOFF", 0.8)
    max_workers: int = _as_int("MAX_WORKERS", 8)
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    output_dir: Path = Path(os.getenv("OUTPUT_DIR", str(BASE_DIR / "output")))
    log_dir: Path = Path(os.getenv("LOG_DIR", str(BASE_DIR / "logs")))
    finviz_user_agent: str = os.getenv(
        "FINVIZ_USER_AGENT",
        "Mozilla/5.0 (compatible; market_movers/1.0; +https://github.com/)",
    )

    def ensure_directories(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
