# /// script
# requires-python = ">=3.12"
# dependencies = ["openpyxl>=3.1", "pymupdf>=2.0"]
# ///
"""Run the criteria over the newest month's dataset -> data/reports/<month>/top50.csv and top50.md."""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from div_invst.criteria import REGISTRY, load_config, rank, screen  # noqa: E402
from div_invst.reference import build_dataset, latest_month_dir  # noqa: E402

SYMBOL = {"pass": "Y", "fail": "n", "unknown": "?", "na": "-"}


def main() -> None:
    month = latest_month_dir()
    cfg = load_config()
    rows = screen(build_dataset(month), cfg)
    top = rank(rows, cfg)
    out = ROOT / "data" / "reports" / month.name
    out.mkdir(parents=True, exist_ok=True)
    nums = sorted(REGISTRY)
    with open(out / "top50.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank", "ticker", "company", "sector", "ccc_tier", "yield", "acn", "passes", "evaluated", "coverage", "score",
                    *[f"c{n}" for n in nums], "flags"])
        for i, x in enumerate(top, 1):
            flags = "; ".join(fl for r in x["results"].values() for fl in r.flags)
            w.writerow([i, x["ticker"], x["company"], x["sector"], x["ccc_tier"], f"{x['yield']:.4f}",
                        "" if x["acn"] is None else f"{x['acn']:.4f}", x["passes"], x["evaluated"], f"{x['coverage']:.2f}",
                        f"{x['score']:.2f}", *[x["results"][n].status for n in nums], flags])
    legend = ", ".join(f"c{n} {REGISTRY[n].name}" for n in nums)
    lines = [f"# Top {len(top)} entry list, {month.name}", "", f"Y pass, n fail, ? unknown, - n/a. {legend}.", "",
             "| # | Ticker | Company | Yield | ACN | Pass | " + " | ".join(f"c{n}" for n in nums) + " |",
             "|---|---|---|---|---|---|" + "---|" * len(nums)]
    for i, x in enumerate(top, 1):
        lines.append(f"| {i} | {x['ticker']} | {(x['company'] or '')[:28].replace('|', '/')} | {x['yield']:.1%} | "
                     f"{'' if x['acn'] is None else format(x['acn'], '.1%')} | {x['passes']}/{x['evaluated']} | "
                     + " | ".join(SYMBOL[x["results"][n].status] for n in nums) + " |")
    (out / "top50.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(rows)} screened, {sum(r['coverage'] >= cfg['ranking']['min_coverage'] for r in rows)} with enough coverage; wrote {out}")


if __name__ == "__main__":
    main()
