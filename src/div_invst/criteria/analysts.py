"""Analyst and third-party rating criteria: 13 (StarMine score) and 15 (rating agreement)."""
from .base import FAIL, PASS, UNKNOWN, criterion, make, src


def revision_score(rev: dict | None, cfg: dict) -> tuple[float | None, dict]:
    """0-10 revision proxy from `rec["cache"]["revision"]`; missing components are skipped and the weights re-scaled.
    The recommendation component uses the mean rating level (1 strong buy ... 5 sell): Finnhub's recommendation trend
    is 4 months only on the free tier, so it is not fetched."""
    if not rev:
        return None, {}
    r = cfg["revision"]
    line = lambda x, full: None if x is None else max(0.0, min(10.0, 5 + 5 * x / full))  # noqa: E731
    balance = lambda up, down: None if up is None or down is None or up + down == 0 else 5 + 5 * (up - down) / (up + down)  # noqa: E731
    rec_mean = rev.get("recommendation_mean")
    parts = {
        "eps_rev_90d": line(rev.get("eps_rev_90d"), r["eps_rev_90d_full"]),
        "revision_balance": balance(rev.get("eps_up_30d"), rev.get("eps_down_30d")),
        "grade_balance": balance(rev.get("upgrades_90d"), rev.get("downgrades_90d")),
        "recommendation": None if rec_mean is None else max(0.0, min(10.0, (5 - rec_mean) / 4 * 10)),
        "target_upside": line(rev.get("target_upside"), r["target_upside_full"]),
    }
    have = {k: v for k, v in parts.items() if v is not None}
    if len(have) < r["min_components"]:
        return None, parts
    total = sum(r["weights"][k] for k in have)
    return sum(r["weights"][k] * v for k, v in have.items()) / total, parts


@criterion(13, "Beat market (StarMine)")
def starmine(rec, cfg, ctx):
    """ESS is the primary input; the revision proxy is shown as a second signal and decides when the screener has no ESS."""
    c = cfg["starmine"]
    ess, change = src(rec, "screener", "ess"), src(rec, "screener", "ess_change")
    proxy, parts = revision_score((rec.get("cache") or {}).get("revision"), cfg)
    extra = {} if proxy is None else {"proxy": round(proxy, 1)}
    if ess is None:
        if proxy is None:
            return make(13, UNKNOWN)
        return make(13, PASS if proxy >= cfg["revision"]["pass_score"] else FAIL, proxy, ["revision proxy, no ESS"], **parts)
    ok = ess in c["pass_levels"] or (ess == "Neutral" and change in c["neutral_pass_if_change"])
    return make(13, PASS if ok else FAIL, ess, change=change, **extra)


def _votes(rec: dict, cfg: dict) -> dict:
    """+1 / 0 / -1 per available third-party rating. StarMine ESS is left out: criterion 13 already uses it."""
    q = cfg["quality"]
    votes = {}
    table = {"jefferson": {"Buy": 1, "Hold": 0, "Sell": -1}, "zacks": {"OUTPERFORM": 1, "NEUTRAL": 0, "UNDERPERFORM": -1},
             "mclean": {"Buy": 1, "Neutral": 0, "Sell": -1}, "argus_rating": {"Buy": 1, "Hold": 0}}
    for field, mapping in table.items():
        v = src(rec, "screener", field)
        if v in mapping:
            votes[field] = mapping[v]
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
