"""Valuation multiples: criterion 9.

Sub-tests: P/S below the cap, P/B at or below the cap, earnings yield above the 10-year Treasury yield, cash at least 5% of
market cap (skipped for banks and insurers). Not yet evaluated: P/E below its own 10-year average and P/B below the market's
(both need history from the data layer). Fail if any evaluable sub-test fails; pass if at least `min_subtests` were
evaluable and all passed; otherwise unknown.
"""
from .base import FAIL, PASS, UNKNOWN, criterion, first, is_bank_or_insurer, make, src


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
    if any(not ok for ok in tests.values()):
        return make(9, FAIL, sum(tests.values()), **tests)
    if len(tests) >= v["min_subtests"]:
        return make(9, PASS, sum(tests.values()), **tests)
    return make(9, UNKNOWN, **tests)
