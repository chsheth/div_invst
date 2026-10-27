"""Valuation: criterion 9 (multiples) and criterion 8 (discount to fair value).

Sub-tests: P/S below the cap, P/B at or below the cap, earnings yield above the 10-year Treasury yield, cash at least 5% of
market cap (skipped for banks and insurers), P/E below its own 10-year median (needs the cached Finnhub P/E history).
Not yet evaluated: P/B below the market's. Fail if any evaluable sub-test fails; pass if at least `min_subtests` were
evaluable and all passed; otherwise unknown.
"""
from statistics import median

from .base import FAIL, PASS, UNKNOWN, criterion, first, is_bank_or_insurer, is_reit, make, src
from .fundamentals import pe_vs_history


@criterion(9, "Valuation multiples")
def multiples(rec, cfg, ctx):
    v = cfg["valuation"]
    tests = {}
    ps, pb = src(rec, "screener", "ps"), src(rec, "screener", "pb")
    pe = src(rec, "screener", "pe")
    earnings_yield = first(src(rec, "screener", "earnings_yield"), 1 / pe if pe else None)
    cash_m, mcap = src(rec, "screener", "cash_m"), rec.get("market_cap")
    if ps is not None:
        tests["ps"] = 0 < ps < v["max_ps"]
    if pb is not None:
        tests["pb"] = 0 < pb <= v["max_pb"]  # negative book equity fails
    if earnings_yield is not None:
        tests["earnings_yield_vs_treasury"] = earnings_yield > cfg["macro"]["treasury_10y"]
    if cash_m is not None and mcap and not is_bank_or_insurer(rec):
        tests["cash"] = cash_m * 1e6 / mcap >= v["min_cash_to_market_cap"]
    own_pe = pe_vs_history(rec, cfg)
    if own_pe is not None:
        tests["pe_below_history"] = own_pe
    if any(not ok for ok in tests.values()):
        return make(9, FAIL, sum(tests.values()), **tests)
    if len(tests) >= v["min_subtests"]:
        return make(9, PASS, sum(tests.values()), **tests)
    return make(9, UNKNOWN, **tests)


def fair_values(rec: dict, cfg: dict) -> dict:
    """The two fair-value estimates, each None when its inputs are missing.

    ddm: two-stage dividend discount. The current annual dividend grows at the 5-year dividend CAGR (capped at
    `stage1_cap` against one-off jumps, floored at 0) for `stage1_years`, then at `terminal_growth` for good, discounted
    at the 10-year Treasury + equity premium. Skipped when required return - terminal growth is under `min_spread`.
    pe: median of the last `eps_years` fiscal-year EPS (smooths one-offs) x the median P/E of the last 10 years
    (positive P/Es; a median because one-off GAAP charges create P/Es of 40 to 150). Skipped for REITs, whose GAAP EPS is depressed by depreciation.
    """
    c = cfg["fair_value"]
    cache = rec.get("cache") or {}
    price = first(cache.get("price"), rec.get("price"))
    out = {"price": price, "ddm": None, "pe": None}
    rate = cache.get("forward_yield")
    growth = first((cache.get("dividends") or {}).get("cagr5"), src(rec, "screener", "dgr_5y"), src(rec, "drip", "dgr_5y"))
    if price and rate and growth is not None:
        r, g1, g2 = cfg["macro"]["treasury_10y"] + c["equity_premium"], max(0.0, min(growth, c["stage1_cap"])), c["terminal_growth"]
        if r - g2 >= c["min_spread"]:
            d, value = price * rate, 0.0
            for t in range(1, c["stage1_years"] + 1):
                d *= 1 + g1
                value += d / (1 + r) ** t
            out["ddm"] = value + d * (1 + g2) / (r - g2) / (1 + r) ** c["stage1_years"]
    eps = [v for _, v in sorted(((cache.get("eps") or {}).get("years") or {}).items(), key=lambda kv: int(kv[0]))][-c["eps_years"]:]
    pes = [v for _, v in sorted(((cache.get("fundamentals") or {}).get("pe") or {}).items())[-10:] if v and v > 0]
    if not is_reit(rec) and len(eps) == c["eps_years"] and len(pes) >= cfg["fundamentals"]["min_pe_years"] and median(eps) > 0:
        out["pe"] = median(eps) * median(pes)
    return out


@criterion(8, "Discount to fair value")
def fair_value_discount(rec, cfg, ctx):
    c = cfg["fair_value"]
    fv = fair_values(rec, cfg)
    found = {k: v for k, v in fv.items() if k in ("ddm", "pe") and v}
    if not fv["price"] or not found:
        return make(8, UNKNOWN, **{k: v for k, v in fv.items() if v})
    fair = min(found.values())
    discount = 1 - fv["price"] / fair
    flags = [] if len(found) == 2 else [f"{next(iter(found))} estimate only"]
    return make(8, PASS if discount >= c["min_discount"] else FAIL, discount, flags, fair=round(fair, 2), price=fv["price"],
                ddm=found.get("ddm"), pe=found.get("pe"))
