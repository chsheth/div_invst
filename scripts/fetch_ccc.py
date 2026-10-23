# /// script
# requires-python = ">=3.12"
# dependencies = ["requests"]
# ///
"""Fetch the Dividend Vision CCC lists into the monthly reference folder.

Run from the repo root:
  uv run --python 3.13 scripts/fetch_ccc.py [--out docs/reference/2026-10/ccc_list.csv]

Pages fetched: kings, aristocrats, champions, contenders, challengers (public HTML tables, no key).
A ticker on several pages gets one row: `tier` is its highest tier (king > aristocrat > champion > contender >
challenger) and `lists` shows every page it appeared on. Default output is docs/reference/<YYYY-MM>/ccc_list.csv.
"""
import argparse
import csv
import html
import re
import sys
from datetime import date
from pathlib import Path

import requests

BASE = "https://www.dividendvision.com/lists/dividend-{}"
TIERS = ["king", "aristocrat", "champion", "contender", "challenger"]
PAGES = {"king": "kings", "aristocrat": "aristocrats", "champion": "champions",
         "contender": "contenders", "challenger": "challengers"}
COLUMNS = ["ticker", "company", "sector", "streak", "yield_pct", "safety_score", "fwd_pe", "market_cap_b", "price"]


def cells(row_html):
    """First text segment of each cell (the company cell also holds an industry label in a nested tag)."""
    out = []
    for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, re.S):
        parts = [html.unescape(x).strip() for x in re.sub(r"<[^>]+>", "\n", c).split("\n")]
        out.append(next((x for x in parts if x), ""))
    return out


def num(s):
    s = s.replace("$", "").replace(",", "").replace("%", "").strip()
    mult = {"T": 1e3, "B": 1, "M": 1e-3}.get(s[-1:], None)
    try:
        return float(s[:-1]) * mult if mult else float(s)
    except ValueError:
        return None


def parse(page_html):
    """Rows of the main table: ticker, company, [industry], sector, streak, yield, safety, fwd P/E, cap, price."""
    out = []
    for row in re.findall(r"<tr.*?</tr>", page_html, re.S):
        c = [x for x in cells(row) if x]
        if len(c) < 8 or not re.fullmatch(r"[A-Z][A-Z.\-]{0,5}", c[0]):
            continue
        # industry is optional: the fields after the company are [industry,] sector, streak, yield, ...
        tail = c[-6:]
        sector = c[-7]
        if not tail[0].isdigit():
            continue
        out.append({"ticker": c[0], "company": c[1], "sector": sector, "streak": int(tail[0]),
                    "yield_pct": num(tail[1]), "safety_score": num(tail[2]), "fwd_pe": num(tail[3]),
                    "market_cap_b": num(tail[4]), "price": num(tail[5])})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=f"docs/reference/{date.today():%Y-%m}/ccc_list.csv")
    args = ap.parse_args()

    rows = {}
    for tier in TIERS:
        r = requests.get(BASE.format(PAGES[tier]), headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        if r.status_code != 200:
            print(f"{tier}: HTTP {r.status_code}, skipped", file=sys.stderr)
            continue
        parsed = parse(r.text)
        print(f"{tier}: {len(parsed)} rows")
        for p in parsed:
            e = rows.setdefault(p["ticker"], {**p, "tier": tier, "lists": []})
            e["lists"].append(tier)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, ["as_of", "tier", *COLUMNS, "lists"])
        w.writeheader()
        for e in sorted(rows.values(), key=lambda e: (TIERS.index(e["tier"]), -e["streak"], e["ticker"])):
            w.writerow({**e, "as_of": date.today().isoformat(), "lists": "|".join(e["lists"])})
    print(f"wrote {len(rows)} tickers to {out}")


if __name__ == "__main__":
    main()
