# /// script
# requires-python = ">=3.12"
# dependencies = ["pandas", "openpyxl", "pymupdf"]
# ///
"""Check a monthly reference folder: which files are present and whether each one loads.

Run from the repo root:
  uv run --python 3.13 scripts/check_month.py [--month 2026-10]

Prints one line per expected file (found or missing, row count, as-of date) and exits 1 if a required file is missing
or fails to load. Steps and file sources: docs/guides/monthly_drop.md.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from div_invst import reference as ref  # noqa: E402


def count_drip(p):
    return f"{len(ref.load_drip(p))} stocks"


def count_morningstar(cap):
    def f(p):
        rows = ref.load_pick_list(p, cap)
        picks = sum(r["status"] == "pick" for r in rows.values())
        return f"{picks} picks, {len(rows) - picks} deletions, as of {next(iter(rows.values()))['as_of']}"
    return f


def count_argus(p):
    rows = ref.load_argus(p)
    return f"{sum(r['in_top30'] for r in rows.values())} top 30, {sum(r['in_screen'] for r in rows.values())} screen"


def count_screener(p):
    sheets = pd.read_excel(p, sheet_name=None)
    sizes = {len(df) for df in sheets.values()}
    note = "" if len(sizes) == 1 else f" (tabs differ: { {k: len(v) for k, v in sheets.items()} })"
    return f"{max(sizes)} stocks, {len(sheets)} tabs{note}"


# (file, required, source, checker)
EXPECTED = [
    ("drip_ccc.csv", True, "DRIP Investing email export", count_drip),
    ("screener_results.xlsx", True, "scripts/merge_screener.py", count_screener),
    ("morningstar_large_cap.pdf", False, "Morningstar pick list", count_morningstar("large")),
    ("morningstar_mid_cap.pdf", False, "Morningstar pick list", count_morningstar("mid")),
    ("argus_top30.pdf", False, "Argus Portfolio Selector", count_argus),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--month", help="YYYY-MM folder under docs/reference (default: newest)")
    args = ap.parse_args()
    folder = ref.REFERENCE_DIR / args.month if args.month else ref.latest_month_dir()
    print(f"Checking {folder.relative_to(ROOT)}")
    failed = False
    for name, required, source, check in EXPECTED:
        path = folder / name
        tag = "required" if required else "optional"
        if not path.exists():
            print(f"  MISSING  {name:28} ({tag}; from {source})")
            failed |= required
            continue
        try:
            print(f"  ok       {name:28} {check(path)}")
        except Exception as e:  # report every file, not just the first failure
            print(f"  FAILED   {name:28} {type(e).__name__}: {e}")
            failed |= required
    raw = sorted(folder.glob("screener_results*.xls"))
    merged = folder / "screener_results.xlsx"
    if raw and not merged.exists():
        print(f"  note     {len(raw)} raw screener_results*.xls file(s) present; run scripts/merge_screener.py")
    elif raw and max(f.stat().st_mtime for f in raw) > merged.stat().st_mtime:
        print("  note     a raw screener_results*.xls is newer than screener_results.xlsx; rerun scripts/merge_screener.py")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
