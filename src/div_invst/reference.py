"""Loaders for the manual monthly reference downloads in docs/reference/<YYYY-MM>/.

drip_ccc.csv   DRIP Investing "All CCC" export (the primary CCC universe, with yield, growth and valuation columns)
ccc_list.csv   Dividend Vision CCC lists from scripts/fetch_ccc.py (adds streak years)

Percent columns become fractions (6.80% -> 0.068), dollar and multiple columns become floats, and blank or "-"
cells become None.
"""
import csv
import re
from datetime import datetime
from pathlib import Path

REFERENCE_DIR = Path(__file__).resolve().parents[2] / "docs" / "reference"
MONTH_DIR = re.compile(r"\d{4}-\d{2}")

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


def conservative_streak(drip_tier: str | None, dv_streak: int | None) -> tuple[int | None, str]:
    """Streak years to trust and how it was settled, taking the lower figure when the sources disagree.

    verified   Dividend Vision streak sits inside the DRIP Stock Type band: use it.
    conflict   outside the band: use the lower claim (the band's top when Dividend Vision is higher, else its streak).
    band_only  not on Dividend Vision: use the bottom of the DRIP band.
    dv_only    not on DRIP: use the Dividend Vision streak unchecked.
    """
    band = DRIP_TIER_YEARS.get(drip_tier or "")
    if band is None:
        return (dv_streak, "dv_only") if dv_streak is not None else (None, "none")
    lo, hi = band
    if dv_streak is None:
        return lo, "band_only"
    if dv_streak >= lo and (hi is None or dv_streak <= hi):
        return dv_streak, "verified"
    return (min(dv_streak, hi) if hi is not None else dv_streak), "conflict"


def tier_for_streak(streak: int | None) -> str | None:
    """CCC tier name for a streak (below 5 years is None)."""
    for tier, (lo, hi) in DRIP_TIER_YEARS.items():
        if streak is not None and streak >= lo and (hi is None or streak <= hi):
            return tier
    return None


def latest_month_dir(root: Path = REFERENCE_DIR, today: str | None = None) -> Path:
    """Newest YYYY-MM folder (not after `today`'s month when given). Raises FileNotFoundError when there is none."""
    months = sorted(p for p in root.iterdir() if p.is_dir() and MONTH_DIR.fullmatch(p.name) and (today is None or p.name <= today[:7]))
    if not months:
        raise FileNotFoundError(f"no YYYY-MM folder in {root}")
    return months[-1]


def _clean(raw: str, kind: str):
    s = (raw or "").strip()
    if s in ("", "-", "N/A", "n/a"):
        return None
    if kind == "str":
        return s
    if kind == "date":
        try:
            return datetime.strptime(s, "%b %d, %Y").date()
        except ValueError:
            return None
    t = s.replace("$", "").replace(",", "").replace("x", "")
    try:
        if kind == "pct":
            return round(float(t.replace("%", "")) / 100, 6)
        return int(float(t)) if kind == "int" else float(t)
    except ValueError:
        return None


def load_drip(path: Path) -> dict[str, dict]:
    """DRIP CCC export keyed by ticker. Unknown columns are ignored; a missing known column is left out of the row."""
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rec = {name: _clean(row[col], kind) for col, (name, kind) in DRIP_COLUMNS.items() if col in row}
            if rec.get("ticker"):
                out[rec["ticker"]] = rec
    return out


def load_dividend_vision(path: Path) -> dict[str, dict]:
    """Dividend Vision CCC list written by scripts/fetch_ccc.py, keyed by ticker (percent columns stay in percent)."""
    out = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            out[row["ticker"]] = {**row, "streak": int(row["streak"]), "lists": row["lists"].split("|")}
    return out


def load_universe(month_dir: Path | None = None) -> dict[str, dict]:
    """DRIP rows (primary) merged with Dividend Vision streak and tier. A ticker only in Dividend Vision gets a
    minimal row with `in_drip` False. Fields added: dv_tier, dv_streak, in_drip, in_dv, plus the conservative `streak`,
    its `streak_basis` and `tier_effective` (see conservative_streak). Use `streak`, not `dv_streak`, for criterion 7."""
    month_dir = month_dir or latest_month_dir()
    drip = load_drip(month_dir / "drip_ccc.csv")
    dv_path = month_dir / "ccc_list.csv"
    dv = load_dividend_vision(dv_path) if dv_path.exists() else {}
    out = {}
    for t, rec in drip.items():
        d = dv.get(t)
        dv_streak = d["streak"] if d else None
        streak, basis = conservative_streak(rec["tier"], dv_streak)
        out[t] = {**rec, "dv_tier": d["tier"] if d else None, "dv_streak": dv_streak, "in_drip": True, "in_dv": d is not None,
                  "streak": streak, "streak_basis": basis, "tier_effective": tier_for_streak(streak)}
    for t, d in dv.items():
        if t not in out:
            out[t] = {"ticker": t, "company": d["company"], "sector": d["sector"], "tier": None, "dv_tier": d["tier"],
                      "dv_streak": d["streak"], "in_drip": False, "in_dv": True, "streak": d["streak"],
                      "streak_basis": "dv_only", "tier_effective": tier_for_streak(d["streak"])}
    return out
