"""Forward tracking of the stored monthly lists: total return per ticker and per group, versus SPY.

Pure functions, no network. A price series is [(iso_date, adjusted_close)] sorted by date; the adjusted close includes
reinvested dividends, so a return from it is a total return. A return is None when the series cannot cover the window
(no price on or after the start, none on or before the end, or the series stops before the end): unpriced is never 0.
"""
import statistics
from datetime import date, timedelta

CUT_RATIO = 0.90        # a payment below this share of the previous one counts as a cut
HORIZONS = (30, 91, 182, 365)


def total_return(series, start: str, end: str) -> float | None:
    """Return from the first close on or after `start` to the last close on or before `end`. The series must reach within
    5 days of `end` (weekends, holidays), else the window is not covered yet and the result is None."""
    entry = next(((d, p) for d, p in series if d >= start), None)
    exit_ = next(((d, p) for d, p in reversed(series) if d <= end), None)
    if entry is None or exit_ is None or entry[1] <= 0 or exit_[0] <= entry[0]:
        return None
    if series[-1][0] < (date.fromisoformat(end) - timedelta(days=5)).isoformat():
        return None
    return exit_[1] / entry[1] - 1


def horizon_end(start: str, days: int) -> str:
    return (date.fromisoformat(start) + timedelta(days=days)).isoformat()


def group_stats(returns: dict, spy: float | None) -> dict:
    """returns: {ticker: float | None}. n counts the group, priced those with a return."""
    vals = [r for r in returns.values() if r is not None]
    out = {"n": len(returns), "priced": len(vals), "mean": None, "median": None, "hit": None, "excess": None}
    if vals:
        out["mean"], out["median"] = statistics.fmean(vals), statistics.median(vals)
        if spy is not None:
            out["hit"] = sum(v > spy for v in vals) / len(vals)
            out["excess"] = out["mean"] - spy
    return out


def split_by_criterion(rows: list[dict], returns: dict, crits: list[str]) -> dict:
    """{criterion: {"pass": (n, mean), "fail": (n, mean)}} over rows with a return; unknown and na are left out."""
    out = {}
    for c in crits:
        cell = {}
        for status in ("pass", "fail"):
            vals = [returns[r["ticker"]] for r in rows if r.get(c) == status and returns.get(r["ticker"]) is not None]
            cell[status] = (len(vals), statistics.fmean(vals) if vals else None)
        out[c] = cell
    return out


def dividend_cut(payments: list, start: str) -> bool | None:
    """True when a payment after `start` is below CUT_RATIO of the payment before it. payments: [[iso_date, amount]].
    None when there is no payment before `start` to compare with (cannot tell)."""
    before = [a for d, a in payments if d <= start]
    after = [(d, a) for d, a in payments if d > start]
    if not before:
        return None
    prev = before[-1]
    for _, a in after:
        if prev > 0 and a < CUT_RATIO * prev:
            return True
        prev = a
    return False
