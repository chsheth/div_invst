"""Morningstar US Large Cap and Mid Cap Pick List PDFs (morningstar_large_cap.pdf, morningstar_mid_cap.pdf).

Each pick row: [Upgrade|Downgrade|Addition]Company  Ticker  Industry  Exchange\\Currency  MarketCap(Mil) N Stars  Moat
Uncertainty  FairValue  Price  Price/FairValue, grouped under sector headings that carry across pages. Only the
tables are read; the commentary pages are ignored. The list holds picks only, so a ticker's absence says nothing
about it. Fair value, rating, moat and uncertainty feed criterion 8 (cross-check) and the manual columns for 2 and 3.
A "Pick List Deletions" table lists stocks dropped from the list this month; those rows get status "deleted" (a possible
exit signal) and no sector, current picks get status "pick".
"""
import re
from datetime import date
from pathlib import Path

from .common import number, parse_long_date, pdf_pages

SECTORS = {"Basic Materials", "Communication Services", "Consumer Cyclical", "Consumer Defensive", "Energy",
           "Financial Services", "Healthcare", "Industrials", "Real Estate", "Technology", "Utilities"}
CHANGES = {"Upgrade": "upgrade", "Downgrade": "downgrade", "Addition": "addition"}

ROW = re.compile(
    r"^(?P<flag>Upgrade|Downgrade|Addition)?(?P<company>\S.*?)\s{2,}(?P<ticker>[A-Z][A-Z.\-]*)\s+(?P<industry>.+?)\s+"
    r"(?P<exchange>X\w+)\\(?P<currency>[A-Z]{3})\s+(?P<mcap>\d+)\s+(?P<stars>\d)\s*(?:Stars?)?\s+(?P<moat>Wide|Narrow|None)\s+"
    r"(?P<uncertainty>Very High|Extreme|High|Medium|Low)\s+(?P<fv>[\d,.]+)\s+(?P<price>[\d,.]+)\s+(?P<ratio>[\d.]+)\s*$")
LOOKS_LIKE_ROW = re.compile(r"\\[A-Z]{3}\s+\d")


def parse_pick_list(pages: list[str], cap: str) -> tuple[date | None, list[dict]]:
    """Rows and the "Data as of" date from the page texts of one pick list. `cap` is "large" or "mid".
    Raises ValueError for a line that looks like a pick row but does not parse, so a layout change is never silent."""
    rows, sector, as_of = [], None, None
    for text in pages:
        status = "pick"
        for line in text.splitlines():
            s = line.strip()
            if s == "Pick List Deletions":
                status, sector = "deleted", None
                continue
            if s in SECTORS:
                sector = s
                continue
            if s.startswith("Data as of"):
                as_of = as_of or parse_long_date(s)
                continue
            if not LOOKS_LIKE_ROW.search(line):
                continue
            m = ROW.match(s)
            if not m:
                raise ValueError(f"unparsed Morningstar {cap} cap row: {s!r}")
            fv, price = number(m["fv"]), number(m["price"])
            rows.append({
                "ticker": m["ticker"], "company": m["company"].strip(), "cap": cap, "status": status, "sector": sector,
                "industry": m["industry"].strip(), "exchange": m["exchange"], "currency": m["currency"],
                "market_cap_m": int(m["mcap"]), "star_rating": int(m["stars"]), "moat": m["moat"].lower(),
                "uncertainty": m["uncertainty"].lower(), "fair_value": fv, "price": price,
                "price_to_fv": number(m["ratio"]), "change": CHANGES.get(m["flag"] or ""),
            })
    return as_of, rows


def load_pick_list(path: Path, cap: str) -> dict[str, dict]:
    """One pick list keyed by ticker; each row also carries `as_of` (the list's "Data as of" date).
    Raises ValueError when the PDF yields no picks."""
    as_of, rows = parse_pick_list(pdf_pages(path), cap)
    if not rows:
        raise ValueError(f"no Morningstar picks found in {path.name}")
    return {r["ticker"]: {**r, "as_of": as_of} for r in rows}


def load_morningstar(month_dir: Path) -> dict[str, dict]:
    """Large and mid cap pick lists for a month, keyed by ticker: current picks (status "pick") plus this month's
    deletions (status "deleted"). A current pick wins over a deletion, and large cap over mid cap. A missing file is
    skipped, so the result may hold only one list."""
    out: dict[str, dict] = {}
    for name, cap in (("morningstar_large_cap.pdf", "large"), ("morningstar_mid_cap.pdf", "mid")):
        path = month_dir / name
        if path.exists():
            for ticker, rec in load_pick_list(path, cap).items():
                if ticker not in out or (out[ticker]["status"] == "deleted" and rec["status"] == "pick"):
                    out[ticker] = rec
    return out
