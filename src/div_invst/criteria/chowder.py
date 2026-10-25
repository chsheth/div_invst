"""Income and dividend growth: criteria 4 (yield vs the S&P), 5 (Chowder rule) and 6 (Adjusted Chowder Number)."""
from statistics import median

from .base import FAIL, PASS, UNKNOWN, criterion, dividend_growth_5y, dividend_yield, make, src


def chowder_tier(rec: dict, y: float, cfg: dict) -> float:
    """12% for most stocks, 15% when yield is under 3% (tech and growth), 8% for utilities and telecom."""
    c = cfg["chowder"]
    if rec.get("sector") == "Utilities" or "Telecommunication" in (rec.get("industry") or ""):
        return c["tier_utility_telecom"]
    return c["tier_low_yield"] if y < c["low_yield_cutoff"] else c["tier_default"]


@criterion(4, "High current yield")
def high_yield(rec, cfg, ctx):
    y = dividend_yield(rec)
    if y is None:
        return make(4, UNKNOWN)
    ratio = y / cfg["macro"]["sp_yield"]
    c = cfg["yield"]
    if ratio < c["min_multiple"]:
        return make(4, FAIL, ratio, yield_=y)
    return make(4, PASS, ratio, flags=["yield trap?"] if ratio > c["max_multiple"] else [], yield_=y)


@criterion(5, "Chowder rule")
def chowder(rec, cfg, ctx):
    y, g = dividend_yield(rec), dividend_growth_5y(rec)
    if y is None or g is None:
        return make(5, UNKNOWN)
    number = y + g
    tier = chowder_tier(rec, y, cfg)
    checks = {"yield_vs_sp": y >= cfg["chowder"]["min_yield_vs_sp"] * cfg["macro"]["sp_yield"],
              "chowder_number": number >= tier, "growth_vs_inflation": g >= cfg["macro"]["inflation"]}
    return make(5, PASS if all(checks.values()) else FAIL, number, tier=tier, growth=g, **checks)


def acn_value(rec: dict, cfg: dict):
    """(ACN, terms) with ACN = min(10%, Y) + min(30%, average(min(D,E,R), median(D,E,R))); None when fewer than
    `acn_min_terms` of the three growth rates are known."""
    c = cfg["chowder"]
    y = dividend_yield(rec)
    terms = {"D": dividend_growth_5y(rec), "E": src(rec, "screener", "eps_growth_5y"), "R": src(rec, "screener", "revenue_growth_5y")}
    known = [v for v in terms.values() if v is not None]
    if y is None or len(known) < c["acn_min_terms"]:
        return None, terms
    growth = (min(known) + median(known)) / 2
    return min(c["acn_yield_cap"], y) + min(c["acn_growth_cap"], growth), terms


@criterion(6, "Adjusted Chowder Number")
def acn(rec, cfg, ctx):
    value, terms = acn_value(rec, cfg)
    y = dividend_yield(rec)
    if value is None:
        return make(6, UNKNOWN, **terms)
    tier = chowder_tier(rec, y, cfg)
    return make(6, PASS if value >= tier else FAIL, value, tier=tier, **terms)
