# /// script
# requires-python = ">=3.12"
# dependencies = ["requests", "pandas", "yfinance"]
# ///
"""Spot-check Finnhub annual series (eps, roe, payoutRatio) against EDGAR facts.

Run from the repo root:  uv run --python 3.13 scripts/finnhub_vs_edgar.py [--tickers JNJ,KO]
Reuses the response cache in data/spike_out/cache, so it spends little or no quota.
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import coverage_spike as cs  # noqa: E402


def finnhub_series(http, key, tkr):
    r = http.get("https://finnhub.io/api/v1/stock/metric",
                 params={"symbol": tkr, "token": key, "metric": "all"}, sleep=1.1)
    ann = r["body"]["series"]["annual"]
    # Finnhub roe and payoutRatio are fractions; convert to percent. Same year rule as edgar_annual.
    scale = {"eps": 1, "roe": 100, "payoutRatio": 100}
    out = {}
    for n, k in scale.items():
        out[n] = {}
        for p in ann.get(n, []):
            per = p["period"]
            yr = int(per[:4]) - (1 if per[5:7] == "01" and int(per[8:10]) <= 7 else 0)
            out[n][yr] = p["v"] * k
    return out


def pct(a, b):
    return "-" if a is None or b in (None, 0) else f"{(a - b) / abs(b) * 100:+.1f}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", default="JNJ,KO")
    args = ap.parse_args()
    cs.load_dotenv(cs.REPO_ROOT / ".env")
    ua, key = os.environ["EDGAR_USER_AGENT"], os.environ["FINNHUB_API_KEY"]
    http = cs.Http(cs.REPO_ROOT / "data" / "spike_out" / "cache")
    cik_map = cs.edgar_ticker_map(http, ua)

    for t in args.tickers.upper().split(","):
        cik = cs.CIK_OVERRIDES.get(t, cik_map[t])
        facts = http.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
                         headers={"User-Agent": ua}, sleep=0.2)["body"]
        fh = finnhub_series(http, key, t)
        absent = [n for n, v in fh.items() if not v]
        if absent:
            print(f"\n!! {t}: Finnhub annual series missing: {absent}")

        def ed(name):
            unit, kind, tags = cs.EDGAR_FIELDS[name]
            return {y: v for y, (v, _) in cs.edgar_annual(facts, unit, kind, tags).items()}

        eps, ni, eq, dps = ed("eps_diluted"), ed("net_income"), ed("equity"), ed("dps_declared")
        print(f"\n== {t} (CIK {cik})  Finnhub vs EDGAR; diff = (Finnhub - EDGAR) / EDGAR")
        print(f"{'year':<6}{'FH eps':>9}{'SEC eps':>9}{'diff':>8} | {'FH roe%':>8}{'NI/endEq%':>10}{'NI/avgEq%':>10} | {'FH payout%':>11}{'DPS/EPS%':>10}")
        eps_diffs = []
        for y in sorted(set(eps) & set(fh["eps"]))[-10:]:
            e_eq = eq.get(y)
            avg_eq = (e_eq + eq[y - 1]) / 2 if e_eq and eq.get(y - 1) else None
            roe_end = ni[y] / e_eq * 100 if y in ni and e_eq else None
            roe_avg = ni[y] / avg_eq * 100 if y in ni and avg_eq else None
            payout = dps[y] / eps[y] * 100 if y in dps and eps[y] else None
            fmt = lambda v: "-" if v is None else f"{v:.1f}"  # noqa: E731
            print(f"{y:<6}{fh['eps'][y]:>9.2f}{eps[y]:>9.2f}{pct(fh['eps'][y], eps[y]):>8} | "
                  f"{fmt(fh['roe'].get(y)):>8}{fmt(roe_end):>10}{fmt(roe_avg):>10} | "
                  f"{fmt(fh['payoutRatio'].get(y)):>11}{fmt(payout):>10}")
            eps_diffs.append(abs(fh["eps"][y] - eps[y]) / abs(eps[y]))
        if eps_diffs:
            print(f"EPS: {sum(d < 0.02 for d in eps_diffs)} of {len(eps_diffs)} years within 2% of EDGAR; "
                  f"max gap {max(eps_diffs) * 100:.1f}%")
        missing = sorted(set(eps) - set(fh["eps"]))
        if missing:
            print("EDGAR years with no Finnhub EPS:", missing)
    print(f"\nlive HTTP calls: {http.live_calls}")


if __name__ == "__main__":
    main()
