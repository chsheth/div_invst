# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Merge the Schwab screener yield-band downloads into one file.

Run from the repo root:
  uv run --python 3.13 scripts/merge_schwab.py [--month 2026-11]

Reads every docs/reference/<month>/Results*.csv (newest month by default), de-duplicates on Symbol (a stock on a band
edge appears in two files) and writes docs/reference/<month>/schwab_results.csv. Prints one line per file (rows and
yield range) so the bands can be eyeballed for gaps. Stops if the files disagree on columns, if a file has exactly
1000 rows (Schwab's export cap: the band is cut off, split it into narrower yield bands), or if two files share more
than 5% of their symbols (a re-downloaded copy, not a neighbouring band).
"""
import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "reference"
EXPORT_CAP = 1000


def month_dir(month: str | None) -> Path:
    if month:
        return REFERENCE_DIR / month
    return max(p for p in REFERENCE_DIR.iterdir() if re.fullmatch(r"\d{4}-\d{2}", p.name))


def read(path: Path) -> tuple[list[str], list[dict]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), [r for r in reader if (r.get("Symbol") or "").strip()]


def yield_range(rows: list[dict]) -> str:
    ys = []
    for r in rows:
        try:
            ys.append(float(r["Annual Dividend Yield"].rstrip("%")))
        except (KeyError, ValueError):
            pass
    return f"yield {min(ys):g}% to {max(ys):g}%" if ys else "no yield values"


def merge(files: list[Path]) -> tuple[list[str], list[dict]]:
    """Merged columns and rows; calls sys.exit with a message on any of the checks in the module docstring."""
    books = [(f, *read(f)) for f in files]
    columns = books[0][1]
    symbols = {}
    for f, cols, rows in books:
        if cols != columns:
            sys.exit(f"{f.name} has different columns from {books[0][0].name}: another export or a changed layout")
        if len(rows) >= EXPORT_CAP:
            sys.exit(f"{f.name} has {len(rows)} rows, Schwab's export cap: the band is cut off. Split it into narrower yield bands")
        symbols[f.name] = {r["Symbol"].strip() for r in rows}
        print(f"  {f.name:20} {len(rows):5} stocks, {yield_range(rows)}")
    names = list(symbols)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            shared = len(symbols[a] & symbols[b])
            if shared > 0.05 * min(len(symbols[a]), len(symbols[b])):
                sys.exit(f"{a} and {b} share {shared} symbols: one is a copy of the other (or of the same band); remove it")
    merged: dict[str, dict] = {}
    for _, _, rows in books:
        for r in rows:
            merged.setdefault(r["Symbol"].strip(), r)
    return columns, list(merged.values())


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--month", help="YYYY-MM folder under docs/reference (default: newest)")
    args = ap.parse_args()
    folder = month_dir(args.month)
    files = sorted(folder.glob("Results*.csv"))
    if not files:
        sys.exit(f"No Results*.csv in {folder}")
    columns, rows = merge(files)
    dest = folder / "schwab_results.csv"
    with open(dest, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(files)} files -> {dest.relative_to(ROOT)}: {len(rows)} stocks")


if __name__ == "__main__":
    main()
