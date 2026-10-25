"""Quality composite: criterion 2 (management, from MSCI governance) and criterion 3 (quality score).

Criterion 3 is the average of four sub-scores (balance sheet, cash flow quality, earnings quality, operating efficiency),
each the average of its available inputs on a 0-100 scale; at least `min_subscores` must exist. These are proxies for the
Jefferson Research grades; thresholds are defaults in docs/criteria/ideas_v2.md ("Quality composite").
"""
from .base import FAIL, PASS, UNKNOWN, criterion, is_reit, make, src


def _ladder(value, steps, floor):
    """Score of the first (limit, score) step the value meets (descending limits), else `floor`."""
    for limit, score in steps:
        if value >= limit:
            return score
    return floor


def _mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def subscores(rec: dict) -> dict:
    s = lambda name: src(rec, "screener", name)  # noqa: E731
    financial = rec.get("sector") == "Financials"
    skip_ratios = financial or is_reit(rec) or rec.get("sector") == "Utilities"

    dc = s("debt_to_capital")
    debt_score = None if dc is None or financial else (0 if dc < 0 else 100 if dc <= 0.35 else 70 if dc <= 0.50 else 40 if dc <= 0.65 else 20 if dc <= 0.75 else 0)
    ic = s("interest_coverage")
    cr = s("current_ratio")
    balance = _mean([None if ic is None or financial else _ladder(ic, [(8, 100), (5, 80), (3, 60), (1.5, 30)], 0), debt_score,
                     None if cr is None or skip_ratios else _ladder(cr, [(1.5, 100), (1.0, 70)], 40)])

    fcf, cfg5 = s("fcf_m"), s("cf_growth_5y")
    cash_flow = _mean([None if fcf is None else (100 if fcf > 0 else 0),
                       None if cfg5 is None else _ladder(cfg5, [(0.05, 100), (0.0, 70)], 20)])

    growth = [g for g in (s("eps_growth_3y"), s("eps_growth_5y")) if g is not None]
    trend, cover = s("op_margin_trend"), s("div_coverage_ttm")
    earnings = _mean([None if not growth else 100 * sum(g > 0 for g in growth) / len(growth),
                      None if trend is None else _ladder(trend, [(0.95, 100), (0.85, 60)], 20),
                      None if cover is None or is_reit(rec) else _ladder(cover, [(1.5, 100), (1.0, 60)], 0)])

    sga, om, roi = s("sga_to_sales"), s("op_margin_5y"), s("roi")
    efficiency = _mean([None if sga is None or skip_ratios else (100 if sga <= 0.20 else 60 if sga <= 0.35 else 20),
                        None if om is None else _ladder(om, [(0.15, 100), (0.08, 60)], 20),
                        None if roi is None else _ladder(roi, [(0.10, 100), (0.05, 60)], 20)])
    return {"balance_sheet": balance, "cash_flow": cash_flow, "earnings_quality": earnings, "operating_efficiency": efficiency}


@criterion(2, "Management quality")
def management(rec, cfg, ctx):
    g = src(rec, "screener", "msci_g")
    if g is None:
        return make(2, UNKNOWN)
    return make(2, PASS if g in cfg["quality"]["governance_pass"] else FAIL, g)


@criterion(3, "Quality grades")
def quality_score(rec, cfg, ctx):
    q = cfg["quality"]
    parts = subscores(rec)
    known = {k: v for k, v in parts.items() if v is not None}
    if len(known) < q["min_subscores"]:
        return make(3, UNKNOWN, **parts)
    score = sum(known.values()) / len(known)
    return make(3, PASS if score >= q["pass_score"] else FAIL, round(score, 1), **parts)
