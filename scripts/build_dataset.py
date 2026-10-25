# /// script
# requires-python = ">=3.12"
# dependencies = ["openpyxl", "pymupdf"]
# ///
"""Build the combined monthly dataset (one row per ticker across DRIP, Fidelity screener, Morningstar and Argus).

Run from the repo root:
  uv run --python 3.13 scripts/build_dataset.py [--month 2026-10]

Writes data/dataset/<month>.csv (flat columns prefixed drip_, scr_, ms_, argus_; data/ is gitignored) and prints a join
summary: how many tickers each source has, overlaps, tickers that did not join the screener, and how complete the key
fields are for CCC names. Source file layouts: docs/guides/monthly_drop.md.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from div_invst import reference as ref  # noqa: E402

KEY_FIELDS = [("scr_div_yield", "yield"), ("scr_dgr_5y", "5-yr dividend growth"), ("scr_eps_growth_5y", "5-yr EPS growth"),
              ("scr_revenue_growth_5y", "5-yr revenue growth"), ("scr_interest_coverage", "interest coverage"),
              ("scr_debt_to_capital", "debt to capital"), ("scr_ess", "StarMine ESS"), ("scr_msci_g", "MSCI governance"),
              ("scr_roi", "ROI"), ("scr_sga_to_sales", "SG&A / sales"), ("scr_pe", "P/E"), ("scr_pb", "P/B")]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--month", help="YYYY-MM folder under docs/reference (default: newest)")
    args = ap.parse_args()
    folder = ref.REFERENCE_DIR / args.month if args.month else ref.latest_month_dir()
    ds = ref.build_dataset(folder)
    out = ROOT / "data" / "dataset" / f"{folder.name}.csv"
    n = ref.write_csv(ds, out)
    print(f"{folder.relative_to(ROOT)} -> {out.relative_to(ROOT)}: {n} tickers")

    recs = list(ds.values())
    for src in ref.dataset.SOURCES:
        print(f"  in {src:12} {sum(r['in'][src] for r in recs):5}")
    in_scope = [r for r in recs if r["us_scope"]]
    ccc = [r for r in recs if r["in"]["drip"]]
    print(f"  US scope (non-ADR, US headquarters or US-only lists): {len(in_scope)}")
    print(f"  CCC (DRIP) names: {len(ccc)}, of which in the screener: {sum(r['in']['screener'] for r in ccc)}")
    for src in ("morningstar", "argus"):
        miss = sorted(r["ticker"] for r in recs if r["in"][src] and not r["in"]["screener"])
        print(f"  {src} tickers not in the screener ({len(miss)}): {', '.join(miss) or 'none'}")
    miss = sorted(r["ticker"] for r in ccc if not r["in"]["screener"])
    print(f"  CCC names not in the screener ({len(miss)}): {', '.join(miss) or 'none'}")

    flat = [ref.flatten(r) for r in ccc]
    print(f"\nCompleteness for CCC names ({len(flat)}):")
    for col, label in KEY_FIELDS:
        have = sum(row.get(col) is not None for row in flat)
        print(f"  {label:24} {have:4}  {have / len(flat):.0%}")


if __name__ == "__main__":
    main()
