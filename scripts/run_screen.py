# /// script
# requires-python = ">=3.12"
# dependencies = ["openpyxl>=3.1", "pymupdf>=2.0", "requests>=2.31"]
# ///
"""Run the criteria over the newest month's dataset -> data/reports/<month>/top50.csv and top50.md.

  uv run --python 3.13 scripts/run_screen.py              # the top 50 (`ranking.top_n` in the config) -> top50.csv, top50.md
  uv run --python 3.13 scripts/run_screen.py --top 200    # the top 200 -> ranked.csv, ranked.md
  uv run --python 3.13 scripts/run_screen.py --top 0      # every ranked stock, then the low-coverage ones unranked (rank "-")
  uv run --python 3.13 scripts/run_screen.py --month 2026-10   # a month other than the newest
  uv run --python 3.13 scripts/run_screen.py --month 2026-10 --as-of 2026-10-27 --top 0   # that month on the cache as it was then
"""
import argparse
import csv
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from div_invst.criteria import REGISTRY, load_config, rank, screen, unranked  # noqa: E402
from div_invst.data import DEFAULT_DB, Store, apply_macro, attach, read_macro  # noqa: E402
from div_invst.reference import build_dataset, month_folder  # noqa: E402

SYMBOL = {"pass": "Y", "fail": "n", "unknown": "?", "na": "-"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--month", help="YYYY-MM folder under docs/reference (default: newest)")
    ap.add_argument("--top", type=int, metavar="N", help="list N ranked stocks (0 = all, then the low-coverage ones unranked) "
                    "and write ranked.csv / ranked.md instead of top50.*")
    ap.add_argument("--as-of", metavar="YYYY-MM-DD", help="read the cache as it stood at the end of this day (default: now)")
    args = ap.parse_args()
    as_of = None
    if args.as_of:
        try:
            as_of = datetime.strptime(args.as_of, "%Y-%m-%d") + timedelta(days=1) - timedelta(microseconds=1)
        except ValueError:
            ap.error("--as-of must be YYYY-MM-DD")
    if args.top is not None and args.top < 0:
        ap.error("--top must be 0 or more")
    try:
        month = month_folder(args.month)
    except (ValueError, FileNotFoundError) as e:
        ap.error(str(e))
    cfg = load_config()
    dataset = build_dataset(month)
    if DEFAULT_DB.exists():  # cached data layer: FRED replaces the manual Treasury and CPI inputs, snapshots attach as rec["cache"]
        store = Store(as_of=as_of)
        cfg = apply_macro(cfg, read_macro(store))
        print(f"cache: {attach(dataset, store)} tickers, macro as of {cfg['macro']['as_of']}, Treasury {cfg['macro']['treasury_10y']:.2%}, CPI {cfg['macro']['inflation']:.2%}")
    rows = screen(dataset, cfg)
    top = rank(rows, cfg, args.top)
    entries = [(i, x) for i, x in enumerate(top, 1)]
    if args.top == 0:
        entries += [(None, x) for x in unranked(rows, cfg)]
    out = ROOT / "data" / "reports" / month.name
    out.mkdir(parents=True, exist_ok=True)
    stem = "top50" if args.top is None else "ranked"
    nums = sorted(REGISTRY)
    with open(out / f"{stem}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank", "ticker", "company", "sector", "ccc_tier", "yield", "acn", "passes", "evaluated", "coverage", "score",
                    *[f"c{n}" for n in nums], "flags"])
        for i, x in entries:
            flags = "; ".join(fl for r in x["results"].values() for fl in r.flags)
            if i is None:
                flags = "; ".join(filter(None, ["low coverage", flags]))
            w.writerow(["" if i is None else i, x["ticker"], x["company"], x["sector"], x["ccc_tier"], f"{x['yield']:.4f}",
                        "" if x["acn"] is None else f"{x['acn']:.4f}", x["passes"], x["evaluated"], f"{x['coverage']:.2f}",
                        f"{x['score']:.2f}", *[x["results"][n].status for n in nums], flags])
    legend = ", ".join(f"c{n} {REGISTRY[n].name}" for n in nums)
    title = (f"Top {len(top)} entry list, {month.name}" if args.top is None else
             f"Ranked entry list, {month.name}: {len(top)} ranked" + (f", then {len(entries) - len(top)} below the coverage cutoff (unranked)" if args.top == 0 else ""))
    lines = [f"# {title}", "", f"Y pass, n fail, ? unknown, - n/a. {legend}.", "",
             "| # | Ticker | Company | Yield | ACN | Pass | " + " | ".join(f"c{n}" for n in nums) + " |",
             "|---|---|---|---|---|---|" + "---|" * len(nums)]
    for i, x in entries:
        lines.append(f"| {'-' if i is None else i} | {x['ticker']} | {(x['company'] or '')[:28].replace('|', '/')} | {x['yield']:.1%} | "
                     f"{'' if x['acn'] is None else format(x['acn'], '.1%')} | {x['passes']}/{x['evaluated']} | "
                     + " | ".join(SYMBOL[x["results"][n].status] for n in nums) + " |")
    (out / f"{stem}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(rows)} screened, {sum(r['coverage'] >= cfg['ranking']['min_coverage'] for r in rows)} with enough coverage; wrote {out / stem}.csv and .md ({len(entries)} rows)")


if __name__ == "__main__":
    main()
