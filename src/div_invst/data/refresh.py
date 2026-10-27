"""Refresh the store: fetch each (source, kind, ticker) whose newest snapshot is older than its max age.

The ages come from `[refresh]` in config/criteria.toml (days). A failed fetch is reported and not stored, so the next
run retries it. `fetchers` maps kind -> (source, function, per_ticker) and can be replaced in tests.
"""
from datetime import datetime

from . import edgar, finnhub, fred, yahoo
from .store import Store

FETCHERS = {
    "yf_info": ("yahoo", yahoo.info, True),
    "yf_dividends": ("yahoo", yahoo.dividends, True),
    "yf_revisions": ("yahoo", yahoo.revisions, True),
    "fh_metric": ("finnhub", finnhub.metric, True),
    "fh_insider": ("finnhub", finnhub.insider_transactions, True),
    "yf_splits": ("yahoo", yahoo.splits, True),
    "edgar": ("edgar", edgar.fetch, True),
    "fred": ("fred", fred.fetch, False),
}


def refresh(store: Store, tickers: list[str], cfg: dict, kinds: list[str] | None = None, fetchers: dict | None = None,
            now: datetime | None = None, log=print) -> dict:
    """Returns {"fetched": n, "fresh": n, "errors": [(kind, ticker, message)]}."""
    fetchers = fetchers or FETCHERS
    ages = cfg["refresh"]
    stats = {"fetched": 0, "fresh": 0, "errors": []}
    for kind in kinds or list(fetchers):
        source, fn, per_ticker = fetchers[kind]
        if per_ticker:
            jobs = [(t, (t,)) for t in tickers]
        else:
            jobs = [(sid, (sid,)) for sid in fred.SERIES]
        for ticker, args in jobs:
            key = ticker if per_ticker else ""
            kind_key = kind if per_ticker else f"{kind}:{ticker}"
            if store.latest(source, kind_key, key, ages[kind], now) is not None:
                stats["fresh"] += 1
                continue
            try:
                store.put(source, kind_key, key, fn(*args), now)
                stats["fetched"] += 1
            except Exception as e:  # noqa: BLE001  one bad ticker must not stop the run
                stats["errors"].append((kind, ticker, repr(e)[:200]))
                log(f"  {kind} {ticker}: {e!r}"[:200])
    return stats
