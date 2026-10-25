# /// script
# requires-python = ">=3.12"
# dependencies = ["pandas", "xlrd", "openpyxl"]
# ///
"""Merge the Fidelity screener yield-band downloads into one workbook.

Run from the repo root:
  uv run --python 3.13 scripts/merge_screener.py [--month 2026-10]

Reads every docs/reference/<month>/screener_results*.xls (newest month by default), stacks each tab across the
files, drops the Fidelity disclaimer footer rows (no Company Name) and de-duplicates on Symbol (a stock on a band
edge appears in two files), then writes docs/reference/<month>/screener_results.xlsx with the same tabs.
Prints one line per file (rows and yield range) so the bands can be eyeballed for gaps. Stops if the files disagree on
tabs or columns, or if two files share more than 5% of their symbols (a re-downloaded copy, not a neighbouring band).
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "reference"


def month_dir(month: str | None) -> Path:
    if month:
        return REFERENCE_DIR / month
    return max(p for p in REFERENCE_DIR.iterdir() if re.fullmatch(r"\d{4}-\d{2}", p.name))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--month", help="YYYY-MM folder under docs/reference (default: newest)")
    args = ap.parse_args()

    folder = month_dir(args.month)
    files = sorted(folder.glob("screener_results*.xls"))
    if not files:
        sys.exit(f"No screener_results*.xls in {folder}")

    books = [pd.read_excel(f, sheet_name=None) for f in files]
    tabs = list(books[0])

    symbols = {}
    for f, book in zip(files, books):
        sc = book[tabs[0]]
        sc = sc[sc["Company Name"].notna()]
        symbols[f.name] = set(sc["Symbol"])
        print(f"  {f.name:28} {len(sc):5} stocks, yield {sc['Dividend Yield'].min():g} to {sc['Dividend Yield'].max():g}")
    names = list(symbols)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            shared = len(symbols[a] & symbols[b])
            if shared > 0.05 * min(len(symbols[a]), len(symbols[b])):
                sys.exit(f"{a} and {b} share {shared} symbols: one is a copy of the other (or of the same band); remove it")

    out = {}
    for tab in tabs:
        frames = []
        for f, book in zip(files, books):
            if tab not in book:
                sys.exit(f"{f.name} has no tab {tab!r}")
            if list(book[tab].columns) != list(books[0][tab].columns):
                sys.exit(f"{f.name} tab {tab!r} has different columns")
            frames.append(book[tab])
        df = pd.concat(frames, ignore_index=True)
        df = df[df["Company Name"].notna()].drop_duplicates("Symbol").reset_index(drop=True)
        out[tab] = df

    counts = {len(df) for df in out.values()}
    if len(counts) != 1:
        sys.exit(f"Tabs have different row counts: { {t: len(d) for t, d in out.items()} }")

    dest = folder / "screener_results.xlsx"
    with pd.ExcelWriter(dest) as w:
        for tab, df in out.items():
            df.to_excel(w, sheet_name=tab, index=False)
    print(f"{len(files)} files -> {dest.relative_to(ROOT)}: {counts.pop()} stocks, {len(out)} tabs")


if __name__ == "__main__":
    main()
