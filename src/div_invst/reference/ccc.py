"""CCC universe loader for the monthly DRIP Investing "All CCC" export (docs/reference/<YYYY-MM>/drip_ccc.csv): the CCC
universe with tier, yield, growth and valuation columns. The tier (Stock Type) gives a streak band, not exact years.

Percent columns become fractions (6.80% -> 0.068), dollar and multiple columns become floats, and blank or "-"
cells become None.
"""
import csv
from pathlib import Path

from .common import clean, latest_month_dir

# DRIP column -> (field name, kind); kinds: str, pct, num, int, date
DRIP_COLUMNS = {
    "Symbol": ("ticker", "str"), "Stock Type": ("tier", "str"), "Company": ("company", "str"),
    "Sector": ("sector", "str"), "Industry": ("industry", "str"), "Price": ("price", "num"),
    "Div Yield": ("div_yield", "pct"), "5Y Avg Yield": ("avg_yield_5y", "pct"), "Current Div": ("current_div", "num"),
    "Payouts/Year": ("payouts_per_year", "int"), "Annualized": ("annual_div", "num"), "Previous Div": ("previous_div", "num"),
    "Ex-Date": ("ex_date", "date"), "Pay-Date": ("pay_date", "date"), "Low": ("low_52w", "num"), "High": ("high_52w", "num"),
    "Chowder Number": ("chowder", "num"), "DGR 1Y": ("dgr_1y", "pct"), "DGR 3Y": ("dgr_3y", "pct"),
    "DGR 5Y": ("dgr_5y", "pct"), "DGR 10Y": ("dgr_10y", "pct"), "TTR 1Y": ("ttr_1y", "pct"), "TTR 3Y": ("ttr_3y", "pct"),
    "FV (Peter Lynch)": ("fv_lynch", "num"), "FV (Peter Lynch) %": ("fv_lynch_pct", "pct"), "EPS 1Y": ("eps_growth_1y", "pct"),
    "Revenue 1Y": ("revenue_growth_1y", "pct"), "NPM": ("npm", "pct"), "CF/Share": ("cf_per_share", "num"),
    "ROE": ("roe", "pct"), "Current R": ("current_ratio", "num"), "Debt/Capital": ("debt_to_capital", "pct"),
    "ROTC": ("rotc", "pct"), "P/E": ("pe", "num"), "P/BV": ("pb", "num"), "PEG": ("peg", "num"),
}

# Streak band implied by the DRIP Stock Type (years of consecutive increases)
DRIP_TIER_YEARS = {"Challenger": (5, 9), "Contender": (10, 24), "Champion": (25, 49), "King": (50, None)}


def load_drip(path: Path) -> dict[str, dict]:
    """DRIP CCC export keyed by ticker. Unknown columns are ignored; a missing known column is left out of the row."""
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rec = {name: clean(row[col], kind) for col, (name, kind) in DRIP_COLUMNS.items() if col in row}
            if rec.get("ticker"):
                out[rec["ticker"]] = rec
    return out


def load_universe(month_dir: Path | None = None) -> dict[str, dict]:
    """DRIP rows keyed by ticker, with the streak band added: `streak_min` and `streak_max` (years of consecutive
    increases implied by the Stock Type; `streak_max` None for Kings). Criterion 7 (dividend up 5+ years) passes for
    every row, since the lowest band starts at 5."""
    month_dir = month_dir or latest_month_dir()
    out = {}
    for t, rec in load_drip(month_dir / "drip_ccc.csv").items():
        lo, hi = DRIP_TIER_YEARS.get(rec["tier"], (None, None))
        out[t] = {**rec, "streak_min": lo, "streak_max": hi}
    return out
