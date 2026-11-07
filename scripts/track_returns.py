# /// script
# requires-python = ">=3.12"
# dependencies = ["openpyxl>=3.1", "pymupdf>=2.0", "requests>=2.31", "yfinance>=0.2.40"]
# ///
"""Score each stored monthly list against what happened next -> data/reports/tracking.md and tracking.csv.

  uv run --python 3.13 scripts/track_returns.py                       # every month under data/reports/
  uv run --python 3.13 scripts/track_returns.py --set 2026-12=2026-12-05   # record a month's list date, then run

For each month it reads ranked.csv (else top50.csv) and measures the total return (adjusted close, dividends included)
of the top 50, the rest of the ranked list, the unranked names and SPY, over 30, 91, 182 and 365 days (once the data
covers them) and to date. It also splits returns by each criterion's pass and fail, and counts dividend cuts in the
top 50. Report only: it changes no threshold. A month's list date is kept in data/reports/snapshots.json.
"""
import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from div_invst.criteria import load_config  # noqa: E402
from div_invst.data import Store, yahoo  # noqa: E402
from div_invst.tracking import HORIZONS, dividend_cut, group_stats, horizon_end, split_by_criterion, total_return  # noqa: E402

REPORTS = ROOT / "data" / "reports"
SNAPSHOTS = REPORTS / "snapshots.json"
DEFAULT_SNAPSHOTS = {"2026-10": "2026-10-26", "2026-11": "2026-11-07"}   # the dates the first two lists were made
BENCH = "SPY"


def pct(v, signed: bool = True) -> str:
    return "-" if v is None else f"{v:+.1%}" if signed else f"{v:.0%}"


def load_snapshots() -> dict:
    data = dict(DEFAULT_SNAPSHOTS)
    if SNAPSHOTS.exists():
        data.update(json.loads(SNAPSHOTS.read_text()))
    return data


def read_month(folder: Path) -> list[dict]:
    path = folder / "ranked.csv"
    path = path if path.exists() else folder / "top50.csv"
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def groups(rows: list[dict]) -> dict[str, list[str]]:
    top = [r["ticker"] for r in rows if r["rank"] and int(r["rank"]) <= 50]
    rest = [r["ticker"] for r in rows if r["rank"] and int(r["rank"]) > 50]
    unranked = [r["ticker"] for r in rows if not r["rank"]]
    return {"top 50": top, "other ranked": rest, "unranked": unranked}


def load_prices(store: Store, tickers: list[str], start: str, max_age: float) -> dict[str, list]:
    """Cached closes where fresh (and early enough), one batched download for the rest."""
    out, need = {}, []
    for t in tickers:
        row = store.latest("yahoo", "yf_prices", t, max_age)
        if row and row[1] and row[1][0][0] <= start:   # cached from at or before the start date (series starts on a trading day)
            out[t] = row[1]
        elif row and not row[1]:
            out[t] = []
        else:
            need.append(t)
    if need:
        print(f"downloading prices for {len(need)} tickers from {start}")
        fetched = yahoo.prices(need, start)
        for t, series in fetched.items():
            store.put("yahoo", "yf_prices", t, series)
            out[t] = series
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", action="append", default=[], metavar="MONTH=DATE", help="record a month's list date (YYYY-MM=YYYY-MM-DD)")
    args = ap.parse_args()
    snaps = load_snapshots()
    for item in args.set:
        try:
            month, d = item.split("=")
            date.fromisoformat(d)
        except ValueError:
            ap.error(f"--set wants YYYY-MM=YYYY-MM-DD, got {item!r}")
        snaps[month] = d
        REPORTS.mkdir(parents=True, exist_ok=True)
        SNAPSHOTS.write_text(json.dumps({m: d for m, d in snaps.items() if DEFAULT_SNAPSHOTS.get(m) != d}, indent=1))
    months = sorted(p for p in REPORTS.iterdir() if p.is_dir() and ((p / "ranked.csv").exists() or (p / "top50.csv").exists()))
    missing = [p.name for p in months if p.name not in snaps]
    if missing:
        ap.error(f"no list date for {', '.join(missing)}: pass --set {missing[0]}=YYYY-MM-DD")
    if not months:
        ap.error(f"no monthly reports under {REPORTS}")
    cfg = load_config()
    store = Store()
    data = {p.name: read_month(p) for p in months}
    earliest = min(snaps[m] for m in data)
    tickers = sorted({r["ticker"] for rows in data.values() for r in rows} | {BENCH})
    prices = load_prices(store, tickers, earliest, cfg["refresh"]["yf_prices"])
    today = date.today().isoformat()
    spy = prices.get(BENCH, [])
    if not spy:
        sys.exit("no SPY prices: cannot compare")
    crits = sorted({k for rows in data.values() for k in rows[0] if k.startswith("c") and k[1:].isdigit()}, key=lambda c: int(c[1:]))

    lines = [f"# Return tracker, as of {today}", "",
             "Total return (adjusted close, dividends included) from each month's list date. Equal weight. Unpriced tickers are "
             "counted in n but not in the averages. Hit = share of priced names that beat SPY. Report only: no threshold is tuned on this.", ""]
    table = []
    for month, rows in data.items():
        start = snaps[month]
        lines += [f"## {month} (list date {start}, {len(rows)} rows)", "", "| Horizon | Group | n | priced | mean | median | hit vs SPY | excess vs SPY |", "|---|---|---|---|---|---|---|---|"]
        for days in (*HORIZONS, None):
            end = today if days is None else horizon_end(start, days)
            label = "to date" if days is None else f"{days}d"
            if days is not None and end > today:
                continue
            spy_r = total_return(spy, start, end)
            if spy_r is None:
                continue
            for name, tick in groups(rows).items():
                if not tick:
                    continue
                rets = {t: total_return(prices.get(t, []), start, end) for t in tick}
                s = group_stats(rets, spy_r)
                lines.append(f"| {label} | {name} | {s['n']} | {s['priced']} | {pct(s['mean'])} | {pct(s['median'])} | "
                             f"{pct(s['hit'], False)} | {pct(s['excess'])} |")
                table.append([month, label, name, s["n"], s["priced"], s["mean"], s["median"], s["hit"], s["excess"], spy_r])
            lines.append(f"| {label} | SPY | 1 | 1 | {spy_r:+.1%} | | | |")
        # to-date split by criterion over every row that has a return, and dividend cuts in the top 50
        all_ret = {r["ticker"]: total_return(prices.get(r["ticker"], []), start, today) for r in rows}
        lines += ["", f"Pass versus fail to date ({month}; n, mean):", "", "| Criterion | pass | fail |", "|---|---|---|"]
        for c, cell in split_by_criterion(rows, all_ret, crits).items():
            lines.append(f"| {c} | {cell['pass'][0]}, {pct(cell['pass'][1])} | {cell['fail'][0]}, {pct(cell['fail'][1])} |")
        top = groups(rows)["top 50"]
        cuts = []
        for t in top:
            row = store.latest("yahoo", "yf_dividends", t)
            if row and dividend_cut(row[1], start):
                cuts.append(t)
        lines += ["", f"Dividend cuts since the list date among the top {len(top)}: {', '.join(cuts) if cuts else 'none'} "
                  "(from the cached dividend history; the cache only knows payments up to its last refresh).", ""]
    (REPORTS / "tracking.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with open(REPORTS / "tracking.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["month", "horizon", "group", "n", "priced", "mean", "median", "hit", "excess", "spy"])
        w.writerows(table)
    print(f"wrote {REPORTS / 'tracking.md'} and tracking.csv")


if __name__ == "__main__":
    main()
