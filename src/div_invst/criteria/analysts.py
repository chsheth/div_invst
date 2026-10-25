"""Analyst and third-party rating criteria: 13 (StarMine score) and 15 (rating agreement)."""
from .base import FAIL, PASS, UNKNOWN, criterion, make, src


@criterion(13, "Beat market (StarMine)")
def starmine(rec, cfg, ctx):
    c = cfg["starmine"]
    ess, change = src(rec, "screener", "ess"), src(rec, "screener", "ess_change")
    if ess is None:
        return make(13, UNKNOWN)
    ok = ess in c["pass_levels"] or (ess == "Neutral" and change in c["neutral_pass_if_change"])
    return make(13, PASS if ok else FAIL, ess, change=change)


def _votes(rec: dict, cfg: dict) -> dict:
    """+1 / 0 / -1 per available third-party rating."""
    q = cfg["quality"]
    votes = {}
    table = {"jefferson": {"Buy": 1, "Hold": 0, "Sell": -1}, "zacks": {"OUTPERFORM": 1, "NEUTRAL": 0, "UNDERPERFORM": -1},
             "mclean": {"Buy": 1, "Neutral": 0, "Sell": -1}, "argus_rating": {"Buy": 1, "Hold": 0}}
    for field, mapping in table.items():
        v = src(rec, "screener", field)
        if v in mapping:
            votes[field] = mapping[v]
    ess = src(rec, "screener", "ess")
    if ess:
        votes["ess"] = 1 if ess in ("Bullish", "Very Bullish") else -1 if ess in ("Bearish", "Very Bearish") else 0
    ibes = src(rec, "screener", "ibes_mean")
    if ibes is not None:
        votes["ibes"] = 1 if ibes <= q["ibes_buy_at_most"] else -1 if ibes >= q["ibes_sell_at_least"] else 0
    ms = rec.get("morningstar")
    stars = ms.get("star_rating") if ms and ms.get("status") == "pick" else None
    if stars is not None:
        votes["morningstar"] = 1 if stars >= 4 else -1 if stars <= 2 else 0
    return votes


@criterion(15, "Rating agreement")
def agreement(rec, cfg, ctx):
    q = cfg["quality"]
    votes = _votes(rec, cfg)
    if len(votes) < q["agreement_min_sources"]:
        return make(15, UNKNOWN, sources=len(votes), **votes)
    score = sum(votes.values()) / len(votes)
    return make(15, PASS if score >= q["agreement_pass"] else FAIL, score, sources=len(votes), **votes)
