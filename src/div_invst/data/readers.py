"""Readers: turn the newest stored snapshots into plain per-ticker fields for the criteria.

`read_ticker` returns one dict per ticker (None when nothing is cached), `read_macro` the FRED inputs, and `attach`
puts the ticker dict on each dataset record as `rec["cache"]`. Percent fields are fractions here (yfinance gives
percent for the yields; they are divided by 100 on the way in). Fields are None when their source is missing, never 0.
Derived values are facts (growth, counts, revisions); pass/fail thresholds stay in the criteria and the config.
"""
import statistics
from datetime import date, datetime, timedelta

from . import edgar
from .store import Store

INSIDER_DAYS = 183   # "6 months" in the insider-buying criterion
GRADE_DAYS = 90


def _payload(store: Store, source: str, kind: str, ticker: str):
    row = store.latest(source, kind, ticker)
    return row[1] if row else None


def _rows(frame) -> list[dict]:
    """A stored yahoo frame ({"columns", "rows"}) as a list of dicts; [] when missing or an error."""
    if not frame or "rows" not in frame:
        return []
    return [dict(zip(frame["columns"], r)) for r in frame["rows"]]


def _change(now, then):
    return None if now is None or then in (None, 0) else (now - then) / abs(then)


# ---------------------------------------------------------------- dividends
def dividend_stats(payments: list[list], this_year: int) -> dict:
    """Streak of consecutive annual raises and the 5-year CAGR from [[date, amount], ...].

    Annual totals per share; a payment slipping across Dec 31 gives a year with 3 or 5 quarterly payments, and such
    years are ambiguous: they count as a raise when the clean years on either side rise, and one fully missing year is
    bridged the same way (two in a row break the streak). Payments above 1.8x the median of their neighbours (five
    centred) are dropped as specials. A screen only: yfinance streaks are wrong for XOM, PG and ED (see the
    2026-10-19 spike), and CCC names take their streak from the DRIP band.
    """
    pays = sorted((d, a) for d, a in payments if a > 0)
    amounts = [a for _, a in pays]
    regular = []
    for i, (d, a) in enumerate(pays):
        window = amounts[max(0, i - 2): i + 3]
        if len(window) >= 3 and a <= 1.8 * statistics.median(window):
            regular.append((d, a))
    totals: dict[int, float] = {}
    count: dict[int, int] = {}
    for d, a in regular:
        y = int(d[:4])
        totals[y] = totals.get(y, 0.0) + a
        count[y] = count.get(y, 0) + 1
    clean, ambiguous = {}, []
    for y in sorted(totals):
        if y >= this_year:
            continue
        if count[y] in (1, 2, 4, 12):
            clean[y] = totals[y]
        else:
            ambiguous.append(y)
    years = sorted(clean)
    streak = 0
    for i in range(len(years) - 1, 0, -1):
        newer, older = years[i], years[i - 1]
        if sum(y not in ambiguous for y in range(older + 1, newer)) > 1:
            break
        if clean[newer] > clean[older] * 1.0001:
            streak += newer - older
        else:
            break
    cagr5 = None
    if years:
        last = years[-1]
        older_years = [y for y in years if y <= last - 5]
        if older_years and clean[older_years[-1]] > 0:
            cagr5 = (clean[last] / clean[older_years[-1]]) ** (1 / (last - older_years[-1])) - 1
    return {"streak_years": streak, "cagr5": cagr5, "annual": clean, "ambiguous_years": ambiguous[-12:]}


# ---------------------------------------------------------------- earnings history
def eps_history(metric: dict | None, edgar_data: dict | None, splits: list | None) -> dict:
    """{"years": {fiscal_year: eps}, "source": {fiscal_year: "finnhub" | "edgar"}}. Finnhub (split-adjusted, GAAP) is
    primary; EDGAR (restated for splits with `split_adjust`) fills years it lacks, and is the only source for banks."""
    years, source = {}, {}
    for row in ((metric or {}).get("series", {}).get("annual", {}).get("eps") or []):
        if row.get("v") is not None and row.get("period"):
            y = edgar.fiscal_year(row["period"])
            years[y], source[y] = row["v"], "finnhub"
    for y, (val, _tag, filed) in ((edgar_data or {}).get("fields", {}).get("eps_diluted", {}).items()):
        y = int(y)
        if y not in years:
            years[y], source[y] = edgar.split_adjust(val, filed, splits or []), "edgar"
    return {"years": dict(sorted(years.items())), "source": source}


# ---------------------------------------------------------------- insiders and revisions
def insider_activity(transactions: list | None, today: date) -> dict | None:
    """Open-market activity (Finnhub codes P = purchase, S = sale) over the last INSIDER_DAYS."""
    if transactions is None:
        return None
    since = (today - timedelta(days=INSIDER_DAYS)).isoformat()
    buys = [t for t in transactions if t.get("transactionCode") == "P" and (t.get("transactionDate") or "") >= since]
    sells = [t for t in transactions if t.get("transactionCode") == "S" and (t.get("transactionDate") or "") >= since]
    bought = sum(abs(t.get("change") or 0) for t in buys)
    sold = sum(abs(t.get("change") or 0) for t in sells)
    return {"buys": len(buys), "buyers": len({t.get("name") for t in buys}), "sells": len(sells),
            "sellers": len({t.get("name") for t in sells}), "net_shares": bought - sold}


def revision_metrics(revisions: dict | None, price: float | None, rec_mean: float | None, today: date) -> dict | None:
    """Inputs of the criterion 13 revision proxy, from one point-in-time yfinance snapshot."""
    if not revisions:
        return None
    trend = {r["period"]: r for r in _rows(revisions.get("eps_trend"))}
    cur = trend.get("0y") or trend.get("+1y") or {}
    rev = {r["period"]: r for r in _rows(revisions.get("eps_revisions"))}
    r0 = rev.get("0y") or rev.get("+1y") or {}
    since = (today - timedelta(days=GRADE_DAYS)).isoformat()
    grades = [g for g in _rows(revisions.get("upgrades_downgrades")) if str(g.get("GradeDate", ""))[:10] >= since]
    target = (revisions.get("price_targets") or {}).get("mean")
    return {
        "eps_rev_30d": _change(cur.get("current"), cur.get("30daysAgo")),
        "eps_rev_90d": _change(cur.get("current"), cur.get("90daysAgo")),
        "eps_up_30d": r0.get("upLast30days"), "eps_down_30d": r0.get("downLast30days"),
        "upgrades_90d": sum(g.get("Action") == "up" for g in grades),
        "downgrades_90d": sum(g.get("Action") == "down" for g in grades),
        "target_upside": _change(target, price), "recommendation_mean": rec_mean,
    }


# ---------------------------------------------------------------- EDGAR derived
def edgar_latest(edgar_data: dict | None) -> dict | None:
    """Latest fiscal-year values, plus EBITDA and the REIT FFO proxy (net income + D&A - property-sale gains) and
    its payout (dividends paid / FFO) when the inputs are there."""
    fields = (edgar_data or {}).get("fields")
    if not fields:
        return None

    def val(name, year):
        row = fields.get(name, {}).get(str(year))
        return row[0] if row else None

    ni_years = sorted(map(int, fields.get("net_income", {})))
    year = ni_years[-1] if ni_years else None
    if year is None:
        return None
    ni, dep, gain = val("net_income", year), val("depreciation", year), val("property_sale_gain", year)
    opinc, paid = val("operating_income", year), val("dividends_paid", year)
    ffo = ni + dep - (gain or 0) if ni is not None and dep is not None else None
    return {
        "fiscal_year": year, "net_income": ni, "operating_income": opinc, "interest_expense": val("interest_expense", year),
        "long_term_debt": val("long_term_debt", year), "cash": val("cash", year), "dividends_paid": paid,
        "ebitda": opinc + dep if opinc is not None and dep is not None else None,
        "ffo": ffo, "ffo_payout": paid / ffo if paid is not None and ffo and ffo > 0 else None,
    }


# ---------------------------------------------------------------- one ticker
def read_ticker(store: Store, ticker: str, today: date | None = None) -> dict | None:
    today = today or date.today()
    p = lambda source, kind: _payload(store, source, kind, ticker)  # noqa: E731
    info, divs, revisions = p("yahoo", "yf_info"), p("yahoo", "yf_dividends"), p("yahoo", "yf_revisions")
    metric, insiders, splits, edg = p("finnhub", "fh_metric"), p("finnhub", "fh_insider"), p("yahoo", "yf_splits"), p("edgar", "edgar")
    if all(x is None for x in (info, divs, revisions, metric, insiders, edg)):
        return None
    info = info or {}
    price = info.get("currentPrice")
    pct = lambda v: v / 100 if v is not None else None  # noqa: E731  yfinance yields are in percent
    rate = info.get("dividendRate")
    return {
        "price": price, "market_cap": info.get("marketCap"), "sector": info.get("sector"),
        "forward_yield": rate / price if rate and price else None, "yield_yf": pct(info.get("dividendYield")),
        "avg_yield_5y": pct(info.get("fiveYearAvgDividendYield")), "payout": info.get("payoutRatio"),
        "pe": info.get("trailingPE"), "forward_pe": info.get("forwardPE"), "pb": info.get("priceToBook"),
        "dividends": dividend_stats(divs, today.year) if divs else None,
        "eps": eps_history(metric, edg, splits) if metric or edg else None,
        "insider": insider_activity(insiders, today),
        "revision": revision_metrics(revisions, price, info.get("recommendationMean"), today),
        "edgar": edgar_latest(edg),
    }


# ---------------------------------------------------------------- macro and dataset
def read_macro(store: Store) -> dict:
    """{"treasury_10y", "inflation", "as_of"} from FRED, as fractions; keys are missing when not cached."""
    out = {}
    dgs = _payload(store, "fred", "fred:DGS10", "")
    if dgs:
        out["treasury_10y"], out["as_of"] = dgs[-1][1] / 100, dgs[-1][0]
    cpi = _payload(store, "fred", "fred:CPIAUCSL", "")
    if cpi:
        by_month = {d[:7]: v for d, v in cpi}
        last = cpi[-1][0]
        prior = f"{int(last[:4]) - 1}{last[4:7]}"
        if prior in by_month:
            out["inflation"] = by_month[last[:7]] / by_month[prior] - 1
    return out


def apply_macro(cfg: dict, macro: dict) -> dict:
    """A copy of the config with its manual macro inputs replaced by the cached FRED values (S&P yield stays manual)."""
    new = {**cfg, "macro": {**cfg["macro"], **{k: v for k, v in macro.items() if k in ("treasury_10y", "inflation", "as_of")}}}
    return new


def attach(dataset: dict[str, dict], store: Store, today: date | None = None) -> int:
    """Set rec["cache"] on every record (None when the ticker has no snapshots); returns how many have one."""
    n = 0
    for ticker, rec in dataset.items():
        rec["cache"] = read_ticker(store, ticker, today)
        n += rec["cache"] is not None
    return n
