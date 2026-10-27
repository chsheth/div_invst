"""Criteria built on cached history: 1 (Financial Strength proxy score) and 10 (better fundamentals).

Both read `rec["cache"]` (data/readers.py). Missing inputs are skipped; too few evaluable inputs gives unknown.
Criterion 1 follows "Financial Strength proxy score" in docs/criteria/ideas_v2.md. Altman Z is not computed (the
statements it needs are not fetched), so its 10 points are dropped and the rest re-weighted. Banks and insurers are
scored separately in the spec; that is not built, so they are unknown.
"""
from statistics import mean, median

from .base import FAIL, PASS, UNKNOWN, criterion, ffo_payout, first, is_bank_or_insurer, is_reit, make, src


def pe_vs_history(rec: dict, cfg: dict):
    """True when the current P/E is below its own median over the last 10 fiscal years (positive P/Es only; the median
    because one-off GAAP charges produce P/Es of 40 to 150 that wreck a mean: KO and JNJ), else
    False; None without a current P/E or at least `min_pe_years` of history."""
    c = cfg["fundamentals"]
    pe = first(src(rec, "screener", "pe"), (rec.get("cache") or {}).get("pe"))
    series = ((rec.get("cache") or {}).get("fundamentals") or {}).get("pe") or {}
    years = [v for _, v in sorted(series.items())[-10:] if v and v > 0]
    if pe is None or pe <= 0 or len(years) < c["min_pe_years"]:
        return None
    return pe < median(years)


def rising(series: dict, cfg: dict):
    """ROE or ROIC trend: the last 3 years average above the 3 before them, or the latest at 90% or more of the 10-year
    high. None with fewer than 6 years."""
    values = [v for _, v in sorted(series.items())[-10:]]
    if len(values) < 6:
        return None
    return mean(values[-3:]) > mean(values[-6:-3]) or values[-1] >= cfg["fundamentals"]["near_high"] * max(values)


@criterion(10, "Better fundamentals")
def better_fundamentals(rec, cfg, ctx):
    f = (rec.get("cache") or {}).get("fundamentals") or {}
    tests = {}
    pe = pe_vs_history(rec, cfg)
    if pe is not None:
        tests["pe_below_history"] = pe
    trends = [t for t in (rising(f.get("roe") or {}, cfg), rising(f.get("roic") or {}, cfg)) if t is not None]
    if trends:
        tests["roe_roic_rising"] = all(trends)
    growth = f.get("eps_growth_next_year")
    if growth is not None:
        tests["next_year_eps_growth"] = growth >= max(cfg["fundamentals"]["min_eps_growth"], cfg["macro"]["inflation"])
    if any(not ok for ok in tests.values()):
        return make(10, FAIL, sum(tests.values()), **tests)
    if len(tests) >= cfg["fundamentals"]["min_subtests"]:
        return make(10, PASS, sum(tests.values()), **tests)
    return make(10, UNKNOWN, **tests)


def strength_components(rec: dict, cfg: dict) -> dict:
    """Each component 0-100 (None when its inputs are missing or exempt)."""
    s = cfg["strength"]
    cache = rec.get("cache") or {}
    f, e = cache.get("fundamentals") or {}, cache.get("edgar") or {}
    reit, utility = is_reit(rec), rec.get("sector") == "Utilities"
    debt, mcap = f.get("total_debt"), rec.get("market_cap")
    out = {}
    out["debt_to_market_cap"] = None if debt is None or not mcap else (100 if debt / mcap < s["max_debt_to_market_cap"] else 0)
    ic = src(rec, "screener", "interest_coverage")
    out["interest_coverage"] = None if ic is None else (100 if ic >= s["min_interest_coverage"] else 0)
    ebitda = f.get("ebitda")
    if debt is None or not ebitda or ebitda <= 0:
        out["debt_to_ebitda"] = None
    else:
        net = debt - (e.get("cash") or 0) if reit else debt  # REITs: net debt
        full, part = s["debt_ebitda_capital_heavy"] if reit or utility else s["debt_ebitda_default"]
        x = net / ebitda
        out["debt_to_ebitda"] = 100 if x <= full else 60 if x <= part else 0
    if reit:
        p = ffo_payout(rec)
        out["payout"] = None if p is None else (100 if p <= cfg["reit"]["max_ffo_payout"] else 0)
    elif utility:
        out["payout"] = None  # exempt
    else:
        earnings = first(cache.get("payout"), src(rec, "screener", "payout"))  # TTM before last-quarter
        paid, fcf = e.get("dividends_paid"), f.get("free_cash_flow")
        by_fcf = paid / fcf if paid is not None and fcf and fcf > 0 else None
        known = [p for p in (earnings, by_fcf) if p is not None]
        out["payout"] = None if not known else (100 if max(known) <= s["max_payout"] else 0)
    margins = [v for _, v in sorted((f.get("fcf_margin") or {}).items())[-5:]]
    out["fcf_positive_5y"] = None if len(margins) < s["min_fcf_years"] else (100 if all(m > 0 for m in margins) else 0)
    cash, prev = e.get("cash"), e.get("cash_prev")
    out["cash_growth"] = None if cash is None or prev is None else (100 if cash > prev else 0)
    return out


@criterion(1, "Financial strength")
def financial_strength(rec, cfg, ctx):
    s = cfg["strength"]
    if is_bank_or_insurer(rec):
        return make(1, UNKNOWN, flags=["banks and insurers are scored separately (not built)"])
    parts = strength_components(rec, cfg)
    known = {k: v for k, v in parts.items() if v is not None}
    if len(known) < s["min_components"]:
        return make(1, UNKNOWN, **parts)
    total = sum(s["weights"][k] for k in known)
    score = sum(s["weights"][k] * v for k, v in known.items()) / total
    tier = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D"
    return make(1, PASS if score >= s["pass_score"] else FAIL, round(score, 1), tier=tier, **parts)
