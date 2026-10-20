# /// script
# requires-python = ">=3.12"
# dependencies = ["yfinance", "requests", "pandas"]
# ///
"""Coverage spike: which data the 15 criteria need can each free source supply?

Run from the repo root:
  uv run --python 3.13 scripts/coverage_spike.py [--tickers JNJ,KO] [--fmp-tickers 10]

Keys are read from the environment or from .env in the repo root. Env vars:
  EDGAR_USER_AGENT    required for EDGAR, e.g. "div-invst spike you@example.com"
  FMP_API_KEY         optional; skips FMP when unset
  FINNHUB_API_KEY     optional; skips Finnhub when unset
  ALPHAVANTAGE_API_KEY optional; skips Alpha Vantage when unset (25 calls/day)

Raw HTTP responses are cached under <out>/cache so reruns do not spend quota.
Default <out> is data/spike_out (gitignored). Writes <out>/results.json and <out>/report.md.
"""
import argparse
import hashlib
import io
import json
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import requests

DEFAULT_TICKERS = (
    # aristocrat-style staples / health
    "JNJ KO PG MCD ABBV "
    # energy, industrial, tech, telecom, tobacco
    "XOM CVX MMM CAT MSFT AAPL T MO "
    # REITs, utilities, banks, pipeline/MLP-like
    "O PLD NEE DUK ED JPM USB WMB"
).split()

YF_INFO_FIELDS = [
    "sector", "marketCap", "currentPrice", "dividendYield", "dividendRate",
    "fiveYearAvgDividendYield", "payoutRatio", "trailingPE", "forwardPE",
    "priceToBook", "priceToSalesTrailing12Months", "totalDebt", "totalCash",
    "freeCashflow", "operatingCashflow", "returnOnEquity", "earningsGrowth",
    "revenueGrowth", "ebitda", "targetMeanPrice", "recommendationMean",
    "numberOfAnalystOpinions", "trailingEps", "bookValue",
]
YF_STMT_ROWS = {
    "income_stmt": ["Diluted EPS", "Net Income", "Total Revenue", "Interest Expense",
                    "Operating Income", "EBITDA"],
    "balance_sheet": ["Total Debt", "Cash And Cash Equivalents", "Stockholders Equity",
                      "Total Assets"],
    "cashflow": ["Free Cash Flow", "Operating Cash Flow", "Cash Dividends Paid"],
}

# EDGAR XBRL tag fallback chains; kind: flow (duration ~1y) or instant
EDGAR_FIELDS = {
    "eps_diluted": ("USD/shares", "flow", ["EarningsPerShareDiluted", "EarningsPerShareBasicAndDiluted"]),
    "net_income": ("USD", "flow", ["NetIncomeLoss", "ProfitLoss"]),
    "revenue": ("USD", "flow", ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                                "SalesRevenueNet", "RevenuesNetOfInterestExpense",
                                "RevenueFromContractWithCustomerIncludingAssessedTax"]),
    "interest_expense": ("USD", "flow", ["InterestExpense", "InterestExpenseNonoperating",
                                         "InterestExpenseDebt", "InterestExpenseDebtExcludingAmortization",
                                         "InterestPaidNet", "InterestPaid"]),
    "op_cash_flow": ("USD", "flow", ["NetCashProvidedByUsedInOperatingActivities"]),
    "dividends_paid": ("USD", "flow", ["PaymentsOfDividendsCommonStock", "PaymentsOfDividends",
                                       "PaymentsOfOrdinaryDividends", "DividendsCommonStockCash",
                                       "DividendsCash", "DividendsCommonStock"]),
    "dps_declared": ("USD/shares", "flow", ["CommonStockDividendsPerShareDeclared",
                                            "CommonStockDividendsPerShareCashPaid"]),
    "equity": ("USD", "instant", ["StockholdersEquity",
                                  "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"]),
    "cash": ("USD", "instant", ["CashAndCashEquivalentsAtCarryingValue",
                                "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
                                "CashAndDueFromBanks", "CashCashEquivalentsAndShortTermInvestments", "Cash"]),
    "long_term_debt": ("USD", "instant", ["LongTermDebt", "LongTermDebtNoncurrent",
                                          "LongTermDebtAndCapitalLeaseObligations",
                                          "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities",
                                          "LongTermNotesPayable", "NotesPayable", "SeniorNotes", "UnsecuredDebt"]),
}

FMP_ENDPOINTS = [
    "income-statement", "balance-sheet-statement", "cash-flow-statement",
    "ratios", "key-metrics", "dividends", "price-target-consensus", "profile",
]
FINNHUB_ENDPOINTS = {
    "metric": ("stock/metric", {"metric": "all"}),
    "recommendation": ("stock/recommendation", {}),
    "price_target": ("stock/price-target", {}),
    "insider_tx": ("stock/insider-transactions", {}),
    "dividend": ("stock/dividend", {"from": "2000-01-01", "to": date.today().isoformat()}),
    "profile": ("stock/profile2", {}),
}
AV_FUNCTIONS = ["OVERVIEW", "INCOME_STATEMENT", "DIVIDENDS"]
# SEC ticker map points some tickers at a successor entity with no filing history.
# ticker -> CIK holding the historical 10-K facts.
CIK_OVERRIDES = {
    "XOM": "0000034088",  # ExxonMobil Holdings Corp (2115436) has no history yet; Exxon Mobil Corp does
}
REPO_ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(path: Path) -> None:
    """Minimal .env reader; real environment variables win."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip("'\""))


# ---------------------------------------------------------------- http cache
class Http:
    def __init__(self, cache_dir: Path):
        self.dir = cache_dir
        self.dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.live_calls = 0

    def get(self, url, params=None, headers=None, sleep=0.0, parse="json"):
        """Return {"status": int, "body": parsed|text|None, "cached": bool}."""
        params = dict(params or {})
        safe = {k: v for k, v in params.items() if k.lower() not in ("apikey", "token")}
        key = hashlib.sha1((url + json.dumps(safe, sort_keys=True)).encode()).hexdigest()
        path = self.dir / f"{key}.json"
        if path.exists():
            d = json.loads(path.read_text())
            d["cached"] = True
            return d
        time.sleep(sleep)
        self.live_calls += 1
        try:
            r = self.session.get(url, params=params, headers=headers, timeout=60)
        except requests.RequestException as e:
            return {"status": -1, "body": str(e), "cached": False}
        body = None
        try:
            body = r.json() if parse == "json" else r.text
        except ValueError:
            body = r.text[:500]
        out = {"status": r.status_code, "body": body}
        if r.status_code not in (429, 500, 502, 503):
            path.write_text(json.dumps(out))
        out["cached"] = False
        return out


def dividend_stats(divs: pd.Series, this_year: int) -> dict:
    """Streak of consecutive annual raises and ~5-yr CAGR from a payment series.

    Annual total per share is the usual convention (it counts a carry-over raise),
    but yfinance dates payments, so a payment slipping across Dec 31 gives a year
    with 3 or 5 quarterly payments (O: 11 and 13 monthly payments in 2024 and 2025;
    KO, PG, XOM, CAT in older years). Such years are ambiguous and not compared.
    The clean years on either side bridge them: each ambiguous year counts as a
    raise when the later clean year beats the earlier one. One fully missing year
    is bridged the same way; two or more in a row break the streak.
    Specials are dropped when a payment exceeds 1.8x the median of its neighbors.
    """
    s = divs[divs > 0]
    med = s.rolling(5, center=True, min_periods=3).median()
    reg = s[s <= 1.8 * med]
    by_year = reg.groupby(reg.index.year)
    totals, count = by_year.sum(), by_year.count()
    freqs = (1, 2, 4, 12)
    clean = {}
    ambiguous = []
    for y in totals.index:
        if y >= this_year:
            continue
        if count[y] in freqs:
            clean[y] = float(totals[y])
        else:
            ambiguous.append(int(y))
    years = sorted(clean)
    streak = 0
    for i in range(len(years) - 1, 0, -1):
        newer, older = years[i], years[i - 1]
        if sum(y not in ambiguous for y in range(older + 1, newer)) > 1:
            break  # more than one year with no payments is a real gap, not missing data
        if clean[newer] > clean[older] * 1.0001:
            streak += newer - older
        else:
            break
    cagr5 = None
    if years:
        y1 = years[-1]
        older = [y for y in years if y <= y1 - 5]
        if older and clean[older[-1]] > 0:
            n = y1 - older[-1]
            cagr5 = float((clean[y1] / clean[older[-1]]) ** (1 / n) - 1)
    return {"streak_years": streak, "cagr5": cagr5, "ambiguous_years": ambiguous[-12:]}


# ---------------------------------------------------------------- yfinance
def yf_section(tkr: str) -> dict:
    import yfinance as yf

    res: dict = {}
    t = yf.Ticker(tkr)
    try:
        info = t.info or {}
    except Exception as e:  # noqa: BLE001
        info = {}
        res["info_error"] = repr(e)[:200]
    res["info_present"] = {f: info.get(f) is not None for f in YF_INFO_FIELDS}
    res["info_values"] = {f: info.get(f) for f in
                          ("sector", "dividendYield", "fiveYearAvgDividendYield", "payoutRatio",
                           "marketCap")}

    try:
        divs = t.dividends
        if len(divs):
            res["dividends"] = {"first_year": int(divs.index[0].year), "rows": len(divs),
                                **dividend_stats(divs, date.today().year)}
        else:
            res["dividends"] = {"rows": 0}
    except Exception as e:  # noqa: BLE001
        res["dividends"] = {"error": repr(e)[:200]}

    stmts = {}
    for attr, rows in YF_STMT_ROWS.items():
        try:
            df = getattr(t, attr)
            counts = {}
            for row in rows:
                counts[row] = int(df.loc[row].notna().sum()) if row in df.index else 0
            stmts[attr] = counts
        except Exception as e:  # noqa: BLE001
            stmts[attr] = {"error": repr(e)[:200]}
    res["statements_years"] = stmts

    def n_rows(getter):
        try:
            x = getter()
            return 0 if x is None else len(x)
        except Exception as e:  # noqa: BLE001
            return f"err:{repr(e)[:80]}"

    res["analyst"] = {
        "insider_transactions": n_rows(lambda: t.insider_transactions),
        "recommendations": n_rows(lambda: t.recommendations),
        "upgrades_downgrades": n_rows(lambda: t.upgrades_downgrades),
        "earnings_estimate": n_rows(lambda: t.earnings_estimate),
        "eps_revisions": n_rows(lambda: t.eps_revisions),
        "price_targets": n_rows(lambda: [t.analyst_price_targets] if t.analyst_price_targets else []),
    }
    return res


# ---------------------------------------------------------------- EDGAR
def edgar_ticker_map(http: Http, ua: str) -> dict:
    r = http.get("https://www.sec.gov/files/company_tickers.json", headers={"User-Agent": ua}, sleep=0.2)
    if r["status"] != 200:
        return {}
    return {v["ticker"].upper(): str(v["cik_str"]).zfill(10) for v in r["body"].values()}


def edgar_annual(facts: dict, unit: str, kind: str, tags: list[str]) -> dict:
    """Merge a tag chain into {fiscal_end_year: (value, tag)}; earlier tags win."""
    merged: dict[int, tuple] = {}
    gaap = facts.get("facts", {}).get("us-gaap", {})
    for tag in tags:
        entries = gaap.get(tag, {}).get("units", {}).get(unit, [])
        per_tag: dict[int, float] = {}
        for e in entries:
            if not str(e.get("form", "")).startswith("10-K"):
                continue
            end = e.get("end")
            if not end:
                continue
            if kind == "flow":
                start = e.get("start")
                if not start:
                    continue
                days = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).days
                if not 340 <= days <= 380:
                    continue
            # 52/53-week filers (JNJ) end in the first days of January: count that as the prior year
            yr = int(end[:4]) - (1 if end[5:7] == "01" and int(end[8:10]) <= 7 else 0)
            per_tag[yr] = e["val"]
        for yr, val in per_tag.items():
            merged.setdefault(yr, (val, tag))
    return merged


def edgar_section(http: Http, ua: str, cik: str | None) -> dict:
    if not cik:
        return {"error": "ticker not in SEC ticker map"}
    r = http.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
                 headers={"User-Agent": ua}, sleep=0.2)
    if r["status"] != 200:
        return {"error": f"HTTP {r['status']}"}
    facts = r["body"]
    this_year = date.today().year
    out = {}
    if not any(edgar_annual(facts, u, k, tg) for u, k, tg in EDGAR_FIELDS.values()):
        out["warning"] = (f"CIK {cik} ({facts.get('entityName')}) has no 10-K facts; "
                          "likely a successor entity, add the old CIK to CIK_OVERRIDES")
    for name, (unit, kind, tags) in EDGAR_FIELDS.items():
        m = edgar_annual(facts, unit, kind, tags)
        recent = {y: v for y, v in m.items() if y >= this_year - 12}
        out[name] = {
            "years": len(recent),
            "span": [min(recent), max(recent)] if recent else None,
            "tags_used": sorted({v[1] for v in recent.values()}),
        }
    return out


# ---------------------------------------------------------------- FRED / SPY
def fred_section(http: Http) -> dict:
    out = {}
    for sid in ("DGS10", "CPIAUCSL"):
        r = http.get("https://fred.stlouisfed.org/graph/fredgraph.csv", params={"id": sid},
                     parse="text", sleep=0.3)
        if r["status"] == 200:
            df = pd.read_csv(io.StringIO(r["body"]))
            df = df[pd.to_numeric(df.iloc[:, 1], errors="coerce").notna()]
            out[sid] = {"last_date": df.iloc[-1, 0], "last_value": float(df.iloc[-1, 1]), "rows": len(df)}
        else:
            out[sid] = {"error": f"HTTP {r['status']}"}
    try:
        import yfinance as yf
        spy = yf.Ticker("SPY").info
        out["SPY"] = {"dividendYield": spy.get("dividendYield"),
                      "yield": spy.get("yield"), "trailingAnnualDividendYield": spy.get("trailingAnnualDividendYield")}
    except Exception as e:  # noqa: BLE001
        out["SPY"] = {"error": repr(e)[:200]}
    return out


# ---------------------------------------------------------------- FMP / Finnhub / AV
def summarize_rows(body) -> dict:
    """Shape of a JSON response: row count, year span if rows carry dates, error text."""
    if isinstance(body, dict) and body:
        msg = body.get("Error Message") or body.get("error") or body.get("Note") or body.get("Information")
        if msg:
            return {"error": str(msg)[:160]}
    if isinstance(body, str):
        return {"error": body[:160]}
    rows = body if isinstance(body, list) else None
    if rows is None:
        return {"rows": 1 if body else 0, "keys": len(body) if isinstance(body, dict) else 0}
    s = {"rows": len(rows)}
    years = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        d = row.get("date") or row.get("fiscalYear") or row.get("period")
        if d and str(d)[:4].isdigit():
            years.append(int(str(d)[:4]))
    if years:
        s["span"] = [min(years), max(years)]
    return s


def fmp_section(http: Http, key: str, tkr: str) -> dict:
    out = {}
    for ep in FMP_ENDPOINTS:
        params = {"symbol": tkr, "apikey": key}
        if ep in ("income-statement", "balance-sheet-statement", "cash-flow-statement",
                  "ratios", "key-metrics"):
            params.update(limit=10, period="annual")
        r = http.get(f"https://financialmodelingprep.com/stable/{ep}", params=params, sleep=0.3)
        out[ep] = {"status": r["status"], **summarize_rows(r["body"])}
    return out


def finnhub_section(http: Http, key: str, tkr: str) -> dict:
    out = {}
    for name, (path, extra) in FINNHUB_ENDPOINTS.items():
        r = http.get(f"https://finnhub.io/api/v1/{path}", params={"symbol": tkr, "token": key, **extra},
                     sleep=1.1)
        s = {"status": r["status"]}
        body = r["body"]
        if r["status"] == 200 and name == "metric" and isinstance(body, dict):
            m = body.get("metric", {})
            s["metric_keys"] = len(m)
            s["has"] = {k: (m.get(k) is not None) for k in
                        ("dividendYieldIndicatedAnnual", "payoutRatioTTM", "dividendGrowthRate5Y",
                         "currentDividendYieldTTM", "peTTM", "pbAnnual", "roeTTM", "roicTTM")}
            ann = body.get("series", {}).get("annual", {})
            s["annual_series"] = {k: len(v) for k, v in ann.items() if k in
                                  ("eps", "currentRatio", "netMargin", "roe", "totalDebtToEquity")}
        elif r["status"] == 200 and name in ("recommendation", "insider_tx", "dividend") and isinstance(body, (list, dict)):
            rows = body.get("data") if isinstance(body, dict) and "data" in body else body
            s["rows"] = len(rows) if hasattr(rows, "__len__") else 0
        elif r["status"] == 200 and name == "price_target" and isinstance(body, dict):
            s["has_target"] = body.get("targetMean") is not None
        else:
            s.update(summarize_rows(body) if r["status"] != 200 else {})
        out[name] = s
    return out


def av_section(http: Http, key: str, tkr: str) -> dict:
    out = {}
    for fn in AV_FUNCTIONS:
        r = http.get("https://www.alphavantage.co/query",
                     params={"function": fn, "symbol": tkr, "apikey": key}, sleep=1.5)
        body = r["body"]
        s = {"status": r["status"]}
        if isinstance(body, dict) and ("Note" in body or "Information" in body):
            s["error"] = str(body.get("Note") or body.get("Information"))[:160]
        elif fn == "INCOME_STATEMENT" and isinstance(body, dict):
            s["annual_years"] = len(body.get("annualReports", []))
        elif fn == "DIVIDENDS" and isinstance(body, dict):
            s["rows"] = len(body.get("data", []))
        elif isinstance(body, dict):
            s["fields"] = len(body)
        out[fn] = s
    return out


# ---------------------------------------------------------------- report
def mark(ok):
    return "yes" if ok else "-"


def build_report(res: dict, tickers: list[str]) -> str:
    L = [f"# Coverage spike report ({date.today().isoformat()})", "",
         f"Tickers ({len(tickers)}): {', '.join(tickers)}", "",
         "Cells are counts of years/rows or yes/-. `-` or 0 means missing.", ""]

    def table(title, cols, getter, note=""):
        L.extend([f"## {title}", note, "", "| ticker | " + " | ".join(cols) + " |",
                  "|---|" + "---|" * len(cols)])
        for t in tickers:
            try:
                cells = [str(getter(res[t], c)) for c in cols]
            except Exception:  # noqa: BLE001
                cells = ["err"] * len(cols)
            L.append(f"| {t} | " + " | ".join(cells) + " |")
        L.append("")

    table("yfinance: info fields present", YF_INFO_FIELDS,
          lambda r, c: mark(r["yfinance"]["info_present"].get(c)))
    table("yfinance: dividend history", ["first_year", "rows", "streak_years", "cagr5"],
          lambda r, c: (lambda v: "-" if v is None else (f"{v:.3f}" if isinstance(v, float) else v))(
              r["yfinance"]["dividends"].get(c)),
          "streak_years counts consecutive years with a higher annualized payment rate (see dividend_stats).")
    cols = [f"{s}.{row}" for s, rows in YF_STMT_ROWS.items() for row in rows]
    table("yfinance: statement years available", cols,
          lambda r, c: r["yfinance"]["statements_years"][c.split(".")[0]].get(c.split(".", 1)[1], "-"))
    acols = ["insider_transactions", "recommendations", "upgrades_downgrades",
             "earnings_estimate", "eps_revisions", "price_targets"]
    table("yfinance: analyst / insider rows", acols, lambda r, c: r["yfinance"]["analyst"][c])
    table("SEC EDGAR: annual years (last 12 fiscal years)", list(EDGAR_FIELDS),
          lambda r, c: r["edgar"][c]["years"] if "error" not in r["edgar"] else "ERR")

    L.append("## SEC EDGAR: tags that supplied data (per field, union across tickers)")
    L.append("")
    for f in EDGAR_FIELDS:
        tags: dict[str, int] = {}
        for t in tickers:
            e = res[t]["edgar"]
            if "error" in e:
                continue
            for tag in e[f]["tags_used"]:
                tags[tag] = tags.get(tag, 0) + 1
        L.append(f"- **{f}**: " + (", ".join(f"{k} ({v} tickers)" for k, v in sorted(tags.items(), key=lambda x: -x[1])) or "none"))
    L.append("")

    L.extend(["## FRED / SPY", "", "```", json.dumps(res["_macro"], indent=1), "```", ""])

    for name, ep_list in (("fmp", FMP_ENDPOINTS), ("finnhub", list(FINNHUB_ENDPOINTS)), ("alphavantage", AV_FUNCTIONS)):
        tested = [t for t in tickers if name in res[t]]
        if not tested:
            L.extend([f"## {name}", "Not run (no key set, or ticker budget 0).", ""])
            continue
        L.extend([f"## {name} (tested on {len(tested)} tickers)", "",
                  "| ticker | " + " | ".join(ep_list) + " |", "|---|" + "---|" * len(ep_list)])
        for t in tested:
            cells = []
            for ep in ep_list:
                s = res[t][name][ep]
                bits = [f"HTTP {s['status']}"]
                for k in ("rows", "annual_years"):
                    if k in s:
                        bits.append(f"{k}={s[k]}")
                if s.get("span"):
                    bits.append(f"{s['span'][0]}-{s['span'][1]}")
                if s.get("error"):
                    bits.append(s["error"][:50])
                if "metric_keys" in s:
                    bits.append(f"keys={s['metric_keys']}")
                cells.append(", ".join(bits))
            L.append(f"| {t} | " + " | ".join(cells) + " |")
        L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", default=",".join(DEFAULT_TICKERS))
    ap.add_argument("--fmp-tickers", type=int, default=10, help="FMP calls = 8 per ticker (250/day free)")
    ap.add_argument("--finnhub-tickers", type=int, default=20)
    ap.add_argument("--av-tickers", type=int, default=3, help="AV calls = 3 per ticker (25/day free)")
    ap.add_argument("--out", default=str(REPO_ROOT / "data" / "spike_out"))
    args = ap.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    http = Http(out_dir / "cache")

    load_dotenv(REPO_ROOT / ".env")
    ua = os.environ.get("EDGAR_USER_AGENT")
    if not ua:
        sys.exit("Set EDGAR_USER_AGENT, e.g. 'div-invst spike you@example.com' (SEC requires contact info).")
    fmp_key = os.environ.get("FMP_API_KEY")
    fh_key = os.environ.get("FINNHUB_API_KEY")
    av_key = os.environ.get("ALPHAVANTAGE_API_KEY")
    print(f"python {sys.version.split()[0]} | keys: FMP={bool(fmp_key)} Finnhub={bool(fh_key)} AV={bool(av_key)}")

    cik_map = edgar_ticker_map(http, ua)
    if not cik_map:
        print("WARNING: could not load SEC ticker map; EDGAR section will be empty")

    res: dict = {}
    for i, t in enumerate(tickers):
        print(f"[{i + 1}/{len(tickers)}] {t}", flush=True)
        res[t] = {}
        try:
            res[t]["yfinance"] = yf_section(t)
        except Exception as e:  # noqa: BLE001
            res[t]["yfinance"] = {"info_present": {}, "dividends": {}, "statements_years": {}, "analyst": {},
                                  "error": repr(e)[:200]}
        time.sleep(1.0)
        res[t]["edgar"] = edgar_section(http, ua, CIK_OVERRIDES.get(t, cik_map.get(t)))
        if res[t]["edgar"].get("warning"):
            print(f"  WARNING {t}: {res[t]['edgar']['warning']}")
        if fmp_key and i < args.fmp_tickers:
            res[t]["fmp"] = fmp_section(http, fmp_key, t)
        if fh_key and i < args.finnhub_tickers:
            res[t]["finnhub"] = finnhub_section(http, fh_key, t)
        if av_key and i < args.av_tickers:
            res[t]["alphavantage"] = av_section(http, av_key, t)

    res["_macro"] = fred_section(http)
    (out_dir / "results.json").write_text(json.dumps(res, indent=1, default=str))
    (out_dir / "report.md").write_text(build_report(res, tickers))
    print(f"live HTTP calls this run: {http.live_calls}")
    print(f"wrote {out_dir / 'results.json'} and {out_dir / 'report.md'}")


if __name__ == "__main__":
    main()
