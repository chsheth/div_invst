"""Loaders for the manual monthly reference downloads in docs/reference/<YYYY-MM>/ (see docs/guides/monthly_drop.md).

common.py       month folder lookup, cell cleaning, PDF text
ccc.py          drip_ccc.csv                 -> CCC universe, tiers, streak bands
morningstar.py  morningstar_large_cap.pdf, morningstar_mid_cap.pdf -> fair value, rating, moat
argus.py        argus_top30.pdf              -> Top 30 table, stock screen
"""
from .argus import load_argus
from .ccc import DRIP_COLUMNS, DRIP_TIER_YEARS, load_drip, load_universe
from .common import MONTH_DIR, REFERENCE_DIR, latest_month_dir
from .morningstar import load_morningstar, load_pick_list

__all__ = [
    "DRIP_COLUMNS", "DRIP_TIER_YEARS", "MONTH_DIR", "REFERENCE_DIR", "latest_month_dir",
    "load_argus", "load_drip", "load_morningstar", "load_pick_list", "load_universe",
]
