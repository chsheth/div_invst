"""Finnhub free-tier endpoints (60 calls/minute). Key from FINNHUB_API_KEY. stock/dividend is premium (403), so dividends come from yfinance."""
import os
from . import http
from .symbols import vendor

BASE = "https://finnhub.io/api/v1/"
PAUSE = 1.1


def _get(path: str, symbol: str, **extra):
    key = os.environ.get("FINNHUB_API_KEY")
    if not key:
        raise RuntimeError("FINNHUB_API_KEY is not set")
    return http.get(BASE + path, params={"symbol": vendor(symbol), "token": key, **extra}, sleep=PAUSE)


def metric(symbol: str) -> dict:
    """stock/metric?metric=all: current metrics plus the annual series back to the 1980s."""
    return _get("stock/metric", symbol, metric="all")


def insider_transactions(symbol: str) -> list:
    body = _get("stock/insider-transactions", symbol)
    return body.get("data", []) if isinstance(body, dict) else []

