"""Portfolio criterion 14: diversification cut. Needs a holdings list in the run context; without one it does not apply."""
from .base import FAIL, NA, PASS, criterion, make


@criterion(14, "Diversification cut")
def diversification(rec, cfg, ctx):
    holdings = ctx.get("holdings")
    if holdings is None:
        return make(14, NA)
    if rec["ticker"] in holdings:
        return make(14, FAIL, "already owned")
    return make(14, PASS)
