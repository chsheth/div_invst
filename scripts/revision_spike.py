# /// script
# requires-python = ">=3.12"
# dependencies = ["yfinance", "requests", "pandas"]
# ///
"""Revision spike: can free sources supply a StarMine-style analyst-revision proxy (criterion 13)?

Run from the repo root:
  uv run --python 3.13 scripts/revision_spike.py [--tickers JNJ,KO]

Checks, per ticker:
  yfinance  eps_trend (consensus now vs 7/30/60/90 days ago), eps_revisions (up/down counts),
            earnings_estimate (analyst count), analyst_price_targets, earnings_history (surprises),
            recommendations (monthly buckets), upgrades_downgrades (dated rating changes)
  Finnhub   /stock/recommendation (monthly history depth), /stock/earnings (surprises),
            /stock/price-target (expected premium, confirms still gated)

Needs FINNHUB_API_KEY in the environment or .env (Finnhub section skipped when unset).
yfinance payloads are snapshotted to <out>/snapshots/<date>/<ticker>.json (yfinance only gives point-in-time
revision data, so the daily snapshots are what would build real revision history). Finnhub responses are cached
under <out>/cache so reruns cost no quota.
Default <out> is data/revision_out (gitignored). Writes <out>/results.json and <out>/report.md.
"""
import argparse
import hashlib
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

DEFAULT_TICKERS = (
    "JNJ KO PG MCD ABBV XOM CVX MMM CAT MSFT AAPL T MO O PLD NEE DUK ED JPM USB WMB"
).split()
REPO_ROOT = Path(__file__).resolve().parent.parent
TREND_COLS = ["current", "7daysAgo", "30daysAgo", "60daysAgo", "90daysAgo"]


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


def df_to_obj(df) -> object:
    """JSON-safe form of a yfinance frame (index kept, dates as strings)."""
    if df is None:
        return None
    if isinstance(df, dict):
        return df
    if not isinstance(df, pd.DataFrame):
        return None
    if df.empty:
        return {}
    d = df.copy()
    d.index = [str(i) for i in d.index]
    d.columns = [str(c) for c in d.columns]
    return json.loads(d.to_json(orient="index", date_format="iso"))


# ---------------------------------------------------------------- yfinance
def yf_fetch(tkr: str) -> dict:
    t = yf.Ticker(tkr)
    out = {}
    getters = {
        "eps_trend": lambda: t.eps_trend,
        "eps_revisions": lambda: t.eps_revisions,
        "earnings_estimate": lambda: t.earnings_estimate,
        "analyst_price_targets": lambda: t.analyst_price_targets,
        "earnings_history": lambda: t.earnings_history,
        "recommendations": lambda: t.recommendations,
        "upgrades_downgrades": lambda: t.upgrades_downgrades,
    }
    for name, g in getters.items():
        try:
            out[name] = {"data": df_to_obj(g())}
        except Exception as e:  # noqa: BLE001
            out[name] = {"error": repr(e)[:200]}
    try:
        out["price"] = t.fast_info.get("lastPrice")
    except Exception:  # noqa: BLE001
        out["price"] = None
    return out


def yf_snapshot(tkr: str, snap_dir: Path) -> dict:
    path = snap_dir / f"{tkr}.json"
    if path.exists():
        return json.loads(path.read_text())
    time.sleep(1.0)
    data = yf_fetch(tkr)
    path.write_text(json.dumps(data, indent=1, default=str))
    return data


def pct(a, b):
    try:
        if a is None or b in (None, 0) or pd.isna(a) or pd.isna(b):
            return None
        return (a - b) / abs(b)
    except TypeError:
        return None


def yf_summary(raw: dict) -> dict:
    s = {}

    def data(name):
        v = raw.get(name, {})
        return None if "error" in v else v.get("data")

    s["errors"] = {k: v["error"] for k, v in raw.items() if isinstance(v, dict) and "error" in v}

    trend = data("eps_trend") or {}
    cy = trend.get("0y") or trend.get("+1y") or {}
    s["eps_trend_periods"] = sorted(trend.keys())
    if cy:
        s["fy_rev_30d"] = pct(cy.get("current"), cy.get("30daysAgo"))
        s["fy_rev_90d"] = pct(cy.get("current"), cy.get("90daysAgo"))
        s["eps_trend_complete"] = all(cy.get(c) is not None for c in TREND_COLS)
    else:
        s["eps_trend_complete"] = False

    rev = data("eps_revisions") or {}
    r0 = rev.get("0y") or {}
    s["revisions_0y"] = {"up30": r0.get("upLast30days"), "down30": r0.get("downLast30days")} if r0 else None

    est = data("earnings_estimate") or {}
    e0 = est.get("0y") or {}
    s["n_analysts_0y"] = e0.get("numberOfAnalysts")

    pt = data("analyst_price_targets") or {}
    s["target_mean"] = pt.get("mean")
    s["target_upside"] = pct(pt.get("mean"), pt.get("current") or raw.get("price"))

    eh = data("earnings_history") or {}
    surprises = [v.get("surprisePercent") for v in eh.values() if isinstance(v, dict)]
    surprises = [x for x in surprises if x is not None]
    s["surprise_quarters"] = len(surprises)
    s["surprise_beats"] = sum(1 for x in surprises if x > 0)

    recs = data("recommendations") or {}
    s["rec_periods"] = len(recs)
    ud = data("upgrades_downgrades") or {}
    s["rating_changes"] = len(ud)
    if ud:
        dates = sorted(ud.keys())
        s["rating_changes_span"] = f"{dates[0][:10]} .. {dates[-1][:10]}"
        cutoff = (pd.Timestamp.now() - pd.Timedelta(days=90)).strftime("%Y-%m-%d")
        recent = [v for k, v in ud.items() if k[:10] >= cutoff and isinstance(v, dict)]
        s["ups_90d"] = sum(1 for v in recent if v.get("Action") == "up")
        s["downs_90d"] = sum(1 for v in recent if v.get("Action") == "down")
    return s


# ---------------------------------------------------------------- finnhub
class Http:
    def __init__(self, cache_dir: Path):
        self.dir = cache_dir
        self.dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.live_calls = 0

    def get(self, url, params):
        safe = {k: v for k, v in params.items() if k.lower() not in ("apikey", "token")}
        key = hashlib.sha1((url + json.dumps(safe, sort_keys=True)).encode()).hexdigest()
        path = self.dir / f"{key}.json"
        if path.exists():
            return json.loads(path.read_text())
        time.sleep(1.1)
        self.live_calls += 1
        try:
            r = self.session.get(url, params=params, timeout=60)
        except requests.RequestException as e:
            return {"status": -1, "body": str(e)}
        try:
            body = r.json()
        except ValueError:
            body = r.text[:300]
        out = {"status": r.status_code, "body": body}
        if r.status_code not in (429, 500, 502, 503):
            path.write_text(json.dumps(out))
        return out


def finnhub_summary(http: Http, key: str, tkr: str) -> dict:
    s = {}
    base = "https://finnhub.io/api/v1"

    r = http.get(f"{base}/stock/recommendation", {"symbol": tkr, "token": key})
    body = r["body"]
    if r["status"] == 200 and isinstance(body, list):
        periods = sorted(x.get("period", "") for x in body)
        s["rec_months"] = len(body)
        s["rec_span"] = f"{periods[0]} .. {periods[-1]}" if periods else None
        if len(body) >= 4:
            latest = max(body, key=lambda x: x["period"])
            old = sorted(body, key=lambda x: x["period"])[-4]  # ~3 months before latest

            def score(x):
                n = sum(x.get(k, 0) for k in ("strongBuy", "buy", "hold", "sell", "strongSell"))
                if not n:
                    return None
                return (2 * x.get("strongBuy", 0) + x.get("buy", 0) - x.get("sell", 0)
                        - 2 * x.get("strongSell", 0)) / n
            a, b = score(latest), score(old)
            s["rec_score_now"] = a
            s["rec_score_delta_3m"] = None if a is None or b is None else a - b
    else:
        s["rec_status"] = r["status"]

    r = http.get(f"{base}/stock/earnings", {"symbol": tkr, "token": key})
    body = r["body"]
    if r["status"] == 200 and isinstance(body, list):
        s["earn_quarters"] = len(body)
        s["earn_beats"] = sum(1 for x in body if (x.get("surprise") or 0) > 0)
    else:
        s["earn_status"] = r["status"]

    r = http.get(f"{base}/stock/price-target", {"symbol": tkr, "token": key})
    s["price_target_status"] = r["status"]
    return s


# ---------------------------------------------------------------- report
def fmt(v, pctfmt=False):
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v * 100:+.1f}%" if pctfmt else f"{v:.2f}"
    return str(v)


def build_report(res: dict, tickers: list[str], snap_date: str) -> str:
    L = [f"# Revision data spike ({snap_date})", ""]
    n = len(tickers)

    def count(fn):
        return sum(1 for t in tickers if fn(res[t]))

    ys = lambda t: res[t]["yfinance"]  # noqa: E731
    fh = lambda t: res[t].get("finnhub", {})  # noqa: E731
    L += ["## Coverage", "", "| Field | Tickers with data |", "|---|---|"]
    L.append(f"| yfinance eps_trend complete (now/7/30/60/90d) | {count(lambda r: r['yfinance'].get('eps_trend_complete'))}/{n} |")
    L.append(f"| yfinance eps_revisions up/down counts | {count(lambda r: r['yfinance'].get('revisions_0y'))}/{n} |")
    L.append(f"| yfinance analyst count | {count(lambda r: r['yfinance'].get('n_analysts_0y'))}/{n} |")
    L.append(f"| yfinance price target | {count(lambda r: r['yfinance'].get('target_mean'))}/{n} |")
    L.append(f"| yfinance earnings history (4 qtrs) | {count(lambda r: r['yfinance'].get('surprise_quarters', 0) >= 4)}/{n} |")
    L.append(f"| yfinance dated rating changes | {count(lambda r: r['yfinance'].get('rating_changes', 0) > 0)}/{n} |")
    if any(res[t].get("finnhub") for t in tickers):
        L.append(f"| Finnhub recommendation history (12+ months) | {count(lambda r: r.get('finnhub', {}).get('rec_months', 0) >= 12)}/{n} |")
        L.append(f"| Finnhub earnings surprises | {count(lambda r: r.get('finnhub', {}).get('earn_quarters', 0) >= 4)}/{n} |")
        gated = [t for t in tickers if fh(t).get("price_target_status") in (401, 403)]
        L.append(f"| Finnhub price target (free tier) | {n - len(gated)}/{n} |")
    L.append("")

    L += ["## Revision signals", "",
          "FY = current fiscal year consensus EPS now vs 30/90 days ago. Rating changes are dated up/down actions in the last 90 days.", "",
          "| Ticker | Analysts | FY EPS 30d | FY EPS 90d | Up/Down 30d | Target upside | Beats (yf) | Rating chg 90d up/down | Rec score | 3m delta |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for t in tickers:
        y, f = ys(t), fh(t)
        rv = y.get("revisions_0y") or {}
        ud = f"{fmt(rv.get('up30'))}/{fmt(rv.get('down30'))}" if rv else "-"
        beats = f"{y.get('surprise_beats', 0)}/{y.get('surprise_quarters', 0)}"
        chg = f"{y.get('ups_90d', '-')}/{y.get('downs_90d', '-')}"
        L.append(f"| {t} | {fmt(y.get('n_analysts_0y'))} | {fmt(y.get('fy_rev_30d'), True)} | {fmt(y.get('fy_rev_90d'), True)} | "
                 f"{ud} | {fmt(y.get('target_upside'), True)} | {beats} | {chg} | {fmt(f.get('rec_score_now'))} | {fmt(f.get('rec_score_delta_3m'))} |")
    L.append("")

    L += ["## Depth", "", "| Ticker | yf rating-change span | yf rec buckets | Finnhub rec span | Finnhub earnings qtrs |", "|---|---|---|---|---|"]
    for t in tickers:
        y, f = ys(t), fh(t)
        L.append(f"| {t} | {y.get('rating_changes', 0)} ({y.get('rating_changes_span', '-')}) | {y.get('rec_periods', 0)} | "
                 f"{f.get('rec_months', '-')} ({f.get('rec_span', '-')}) | {f.get('earn_quarters', '-')} |")
    L.append("")

    errs = [(t, ys(t)["errors"]) for t in tickers if ys(t).get("errors")]
    if errs:
        L += ["## yfinance errors", ""]
        L += [f"- {t}: {e}" for t, e in errs]
        L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", default=",".join(DEFAULT_TICKERS))
    ap.add_argument("--out", default=str(REPO_ROOT / "data" / "revision_out"))
    args = ap.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    out_dir = Path(args.out)
    snap_date = date.today().isoformat()
    snap_dir = out_dir / "snapshots" / snap_date
    snap_dir.mkdir(parents=True, exist_ok=True)
    http = Http(out_dir / "cache")

    load_dotenv(REPO_ROOT / ".env")
    fh_key = os.environ.get("FINNHUB_API_KEY")
    print(f"python {sys.version.split()[0]} | Finnhub key: {bool(fh_key)}")

    res: dict = {}
    for i, t in enumerate(tickers):
        print(f"[{i + 1}/{len(tickers)}] {t}", flush=True)
        res[t] = {}
        try:
            res[t]["yfinance"] = yf_summary(yf_snapshot(t, snap_dir))
        except Exception as e:  # noqa: BLE001
            res[t]["yfinance"] = {"errors": {"fetch": repr(e)[:200]}}
        if fh_key:
            res[t]["finnhub"] = finnhub_summary(http, fh_key, t)

    (out_dir / "results.json").write_text(json.dumps(res, indent=1, default=str))
    (out_dir / "report.md").write_text(build_report(res, tickers, snap_date))
    print(f"live Finnhub calls this run: {http.live_calls}")
    print(f"wrote {out_dir / 'results.json'} and {out_dir / 'report.md'}")


if __name__ == "__main__":
    main()
