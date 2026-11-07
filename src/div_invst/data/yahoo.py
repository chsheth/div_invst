"""yfinance snapshots. Each function returns JSON-able data; yfinance and pandas are imported lazily.

Percent fields keep yfinance's own units here (fiveYearAvgDividendYield is in percent, 2.8 = 2.8%); convert to
fractions where they are read, not in the store.
"""
import time

from .symbols import vendor

INFO_FIELDS = [
    "sector", "marketCap", "currentPrice", "dividendYield", "dividendRate", "fiveYearAvgDividendYield", "payoutRatio",
    "trailingPE", "forwardPE", "priceToBook", "totalDebt", "totalCash", "freeCashflow", "operatingCashflow",
    "returnOnEquity", "earningsGrowth", "revenueGrowth", "targetMeanPrice", "recommendationMean",
    "numberOfAnalystOpinions", "trailingEps", "bookValue",
]
PAUSE = 1.0


def _frame(df):
    """DataFrame -> {"columns", "index", "data"} with strings for dates; None when missing or empty."""
    if df is None or getattr(df, "empty", True):
        return None
    df = df.reset_index() if df.index.name or df.index.nlevels > 1 else df
    return {"columns": [str(c) for c in df.columns], "rows": df.astype(object).where(df.notna(), None).values.tolist()}


def _ticker(symbol: str):
    import yfinance as yf

    time.sleep(PAUSE)
    return yf.Ticker(vendor(symbol))


def info(symbol: str) -> dict:
    data = _ticker(symbol).info or {}
    return {f: data.get(f) for f in INFO_FIELDS}


def dividends(symbol: str) -> list:
    s = _ticker(symbol).dividends
    return [[d.date().isoformat(), float(v)] for d, v in s.items()] if len(s) else []


def splits(symbol: str) -> list:
    """[[ex_date, ratio], ...]; ratio is new shares per old share (4:1 is 4.0)."""
    s = _ticker(symbol).splits
    return [[d.date().isoformat(), float(v)] for d, v in s.items()] if len(s) else []


def revisions(symbol: str) -> dict:
    """Point-in-time analyst data for criterion 13's proxy; each part is None when Yahoo has none."""
    t = _ticker(symbol)
    parts = {}
    for name in ("eps_trend", "eps_revisions", "earnings_estimate", "upgrades_downgrades", "insider_transactions"):
        try:
            parts[name] = _frame(getattr(t, name))
        except Exception as e:  # noqa: BLE001  yfinance raises assorted errors per endpoint
            parts[name] = {"error": repr(e)[:200]}
    try:
        parts["price_targets"] = dict(t.analyst_price_targets or {})
    except Exception as e:  # noqa: BLE001
        parts["price_targets"] = {"error": repr(e)[:200]}
    return parts


def prices(symbols: list[str], start: str) -> dict[str, list]:
    """Adjusted daily closes (dividends and splits included) from `start` on, in one batched download:
    {symbol: [[iso_date, close], ...]}. A symbol Yahoo has no prices for maps to []."""
    import yfinance as yf

    vend = {s: vendor(s) for s in symbols}
    df = yf.download(sorted(set(vend.values())), start=start, auto_adjust=True, progress=False, group_by="ticker", threads=True)
    out = {}
    for sym, v in vend.items():
        try:
            col = df[v]["Close"].dropna()
        except KeyError:
            try:
                col = df["Close"].dropna() if len(vend) == 1 else None  # older yfinance: flat columns for one ticker
            except KeyError:
                col = None
        out[sym] = [[d.date().isoformat(), float(p)] for d, p in col.items()] if col is not None else []
    return out
