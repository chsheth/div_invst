"""Argus Portfolio Selector PDF (argus_top30.pdf): the Top 30 table and the Stock Screen (mid-cap model portfolio).

Top 30 row: Price Company Industry Symbol EPS PE 5-yr-growth PEG DivRate Yield FinStrength Beta. Financial Strength is
Argus' grade (H, MH, M, ML, L), the Argus cross-check for criterion 1. Screen row: [*]Symbol Name Sector $Price ROE%
$MarketCap(Mil) P/S P/B Beta, where * marks a new holding. Both tables are read from the page text; commentary pages
are ignored. Percent figures stay in percent units (3.6 means 3.6%).
"""
import re
from datetime import date
from pathlib import Path

from .common import number, parse_long_date, pdf_pages

INDUSTRY_CODES = {"CS": "Communication Services", "C": "Consumer Cyclical", "E": "Energy", "F": "Financial",
                  "H": "Healthcare", "I": "Industrial", "M": "Materials", "R": "Real Estate", "S": "Consumer Staples",
                  "TU": "Utilities", "U": "Utilities", "X": "Information Technology"}
SCREEN_SECTORS = ["Communication Services", "Consumer Discretionary", "Consumer Staples", "Energy", "Financial",
                  "Healthcare", "Industrial", "Information Technology", "Materials", "Real Estate", "Utilities"]

_NUM = r"[\d,.]+|NM"
TOP30_ROW = re.compile(
    rf"^\s*(?P<price>[\d,.]+)\s+(?P<company>\S.*?)\s+(?P<code>{'|'.join(sorted(INDUSTRY_CODES, key=len, reverse=True))})\s+"
    rf"(?P<ticker>[A-Z][A-Z.\-]*)\s+(?P<eps>{_NUM})\s+(?P<pe>{_NUM})\s+(?P<growth>{_NUM})\s+(?P<peg>{_NUM})\s+"
    rf"(?P<div>{_NUM})\s+(?P<yield>{_NUM})\s+(?P<strength>MH|ML|H|M|L)\s+(?P<beta>{_NUM})\s*$")
SCREEN_ROW = re.compile(
    rf"^\s*(?P<new>\*)?\s*(?P<ticker>[A-Z][A-Z.\-]*)\s+(?P<name>\S.*?)\s+(?P<sector>{'|'.join(SCREEN_SECTORS)})\s+"
    r"\$(?P<price>[\d,.]+)\s+(?P<roe>-?[\d,.]+)%\s+\$(?P<mcap>[\d,]+)\s+(?P<ps>-?[\d.]+)\s+(?P<pb>-?[\d.]+)\s+(?P<beta>-?[\d.]+)\s*$")


def parse_top30(pages: list[str]) -> tuple[date | None, list[dict]]:
    """Top 30 rows and the "Prices as of" date. Only the page holding "The Argus Top 30" table is read."""
    rows, as_of = [], None
    for text in pages:
        if "Fin." not in text or "Strength" not in text:
            continue
        for line in text.splitlines():
            if "Prices as of" in line:
                as_of = as_of or parse_long_date(line)
            m = TOP30_ROW.match(line)
            if m:
                rows.append({
                    "ticker": m["ticker"], "company": m["company"].strip(), "industry": INDUSTRY_CODES[m["code"]],
                    "price": number(m["price"]), "eps": number(m["eps"]), "pe": number(m["pe"]),
                    "growth_5y": number(m["growth"]), "peg": number(m["peg"]), "div_rate": number(m["div"]),
                    "yield_pct": number(m["yield"]), "fin_strength": m["strength"], "beta": number(m["beta"]),
                })
    return as_of, rows


def parse_screen(pages: list[str]) -> tuple[date | None, str | None, list[dict]]:
    """Stock Screen rows, the "Prices as of" date and the portfolio name (for example "The Argus Mid-Cap Model Portfolio").
    Raises ValueError for a line that looks like a screen row ($ price then a % figure) but does not parse."""
    rows, as_of, portfolio = [], None, None
    for text in pages:
        if "STOCKSCREEN" not in text.upper().replace(" ", ""):
            continue
        for line in text.splitlines():
            if re.match(r"The Argus .*Portfolio", line.strip()):
                portfolio = line.strip()
            if "Prices as of" in line:
                as_of = as_of or parse_long_date(line)
            if not re.search(r"\$[\d,.]+\s+-?[\d.]+%\s+\$[\d,]+", line):
                continue
            m = SCREEN_ROW.match(line)
            if not m:
                raise ValueError(f"unparsed Argus screen row: {line.strip()!r}")
            rows.append({
                "ticker": m["ticker"], "company": m["name"].strip(), "sector": m["sector"], "price": number(m["price"]),
                "roe_pct": number(m["roe"]), "market_cap_m": number(m["mcap"]), "price_to_sales": number(m["ps"]),
                "price_to_book": number(m["pb"]), "beta": number(m["beta"]), "new_holding": m["new"] is not None,
            })
    return as_of, portfolio, rows


def load_argus(path: Path) -> dict[str, dict]:
    """Argus issue keyed by ticker. A ticker in the Top 30 gets `in_top30` True with its table fields; a ticker in the
    stock screen gets `in_screen` True with `screen_*` fields and `portfolio`. Raises ValueError when no Top 30 rows parse."""
    pages = pdf_pages(path)
    top_date, top = parse_top30(pages)
    if not top:
        raise ValueError(f"no Argus Top 30 rows found in {path.name}")
    scr_date, portfolio, screen = parse_screen(pages)
    out = {}
    for r in top:
        out[r["ticker"]] = {**r, "in_top30": True, "in_screen": False, "top30_as_of": top_date}
    for r in screen:
        base = out.setdefault(r["ticker"], {"ticker": r["ticker"], "company": r["company"], "in_top30": False})
        base.update(in_screen=True, portfolio=portfolio, screen_as_of=scr_date, screen_sector=r["sector"],
                    screen_price=r["price"], roe_pct=r["roe_pct"], market_cap_m=r["market_cap_m"],
                    price_to_sales=r["price_to_sales"], price_to_book=r["price_to_book"],
                    screen_beta=r["beta"], new_holding=r["new_holding"])
    return out
