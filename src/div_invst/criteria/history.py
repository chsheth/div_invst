"""Criteria that need the cached data layer (`rec["cache"]`, see data/readers.py): 7, 11 and 12.

All three are unknown when the ticker has no cached data for the part they need.
"""
from .base import FAIL, PASS, UNKNOWN, criterion, make, src


def eps_up_years(eps: dict, swing: float) -> tuple[list, list]:
    """(up flags for the latest comparisons, flagged one-off years) from {fiscal_year: eps}.

    A year is one-off when EPS moves more than `swing` from both neighbours in opposite directions (a spike or a dip).
    A one-off year counts as up only if the next year beats the year before it, and that next year is compared with the
    year before the one-off. A one-off in the latest year cannot be judged and is skipped. Years must be consecutive.
    """
    years = sorted(eps)
    flagged = []
    for i in range(1, len(years) - 1):
        a, b, c = eps[years[i - 1]], eps[years[i]], eps[years[i + 1]]
        if years[i] - years[i - 1] == 1 and years[i + 1] - years[i] == 1 and a > 0 and b > 0 and c > 0:
            if abs(b / a - 1) > swing and abs(b / c - 1) > swing and (b > a) == (b > c):
                flagged.append(years[i])
    ups = []
    for i in range(1, len(years)):
        y, prev = years[i], years[i - 1]
        if y - prev != 1:
            continue
        if y in flagged:
            if i + 1 < len(years):
                ups.append(eps[years[i + 1]] > eps[prev])
        elif prev in flagged:
            ups.append(eps[y] > eps[years[i - 2]])
        else:
            ups.append(eps[y] > eps[prev])
    return ups, flagged


@criterion(7, "Rising dividends and earnings")
def rising(rec, cfg, ctx):
    c = cfg["history"]
    cache = rec.get("cache") or {}
    tier = rec.get("ccc_tier") or src(rec, "drip", "tier")
    if tier:  # every DRIP band starts at 5 years
        dividend_ok, streak = True, None
    else:
        streak = (cache.get("dividends") or {}).get("streak_years")
        dividend_ok = None if streak is None else streak >= c["min_dividend_years"]
    eps = {int(y): v for y, v in ((cache.get("eps") or {}).get("years") or {}).items()}
    if dividend_ok is None or len(eps) < 2:
        return make(7, UNKNOWN, streak=streak)
    ups, flagged = eps_up_years(eps, c["one_off_swing"])
    ups = ups[-c["earnings_window"]:]
    flags = [f"one-off EPS {y}" for y in flagged[-3:]]
    if len(ups) < c["min_comparisons"]:
        return make(7, UNKNOWN, flags, streak=streak, comparisons=len(ups))
    needed = c["earnings_up_years"] if len(ups) == c["earnings_window"] else -(-c["earnings_up_years"] * len(ups) // c["earnings_window"])
    earnings_ok = sum(ups) >= needed
    return make(7, PASS if dividend_ok and earnings_ok else FAIL, sum(ups), flags, streak=streak, comparisons=len(ups),
                dividend_ok=dividend_ok, earnings_ok=earnings_ok)


@criterion(11, "Cash growth")
def cash_growth(rec, cfg, ctx):
    e = (rec.get("cache") or {}).get("edgar") or {}
    cash, prev = e.get("cash"), e.get("cash_prev")
    if cash is None or prev is None:
        return make(11, UNKNOWN)
    return make(11, PASS if cash > prev else FAIL, cash / prev - 1 if prev > 0 else None, fiscal_year=e.get("fiscal_year"))


@criterion(12, "Insider buying")
def insider_buying(rec, cfg, ctx):
    i = (rec.get("cache") or {}).get("insider")
    if i is None:
        return make(12, UNKNOWN)
    ok = i["buyers"] >= cfg["insider"]["min_buyers"] and i["net_shares"] > 0
    return make(12, PASS if ok else FAIL, i["net_shares"], buyers=i["buyers"], buys=i["buys"], sellers=i["sellers"])
