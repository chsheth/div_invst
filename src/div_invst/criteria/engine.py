"""Run the registered criteria over the dataset and rank.

Score = passes / evaluated (pass or fail), shown in the report. Coverage = evaluated / applicable (everything except na).
A ticker needs `ranking.min_coverage` to be ranked. Rank key is passes / applicable (unknowns count as not passed, so a
perfect score on few criteria cannot beat a strong one on many); ties are broken by ACN, then yield, then ticker.
"""
from .base import FAIL, NA, PASS, REGISTRY, dividend_yield


def evaluate(rec: dict, cfg: dict, ctx: dict | None = None) -> dict:
    """All criteria for one record, keyed by criterion number."""
    ctx = ctx or {}
    return {n: c.fn(rec, cfg, ctx) for n, c in sorted(REGISTRY.items())}


def summarize(rec: dict, results: dict, cfg: dict) -> dict:
    statuses = [r.status for r in results.values()]
    applicable = [s for s in statuses if s != NA]
    evaluated = [s for s in applicable if s in (PASS, FAIL)]
    passes = statuses.count(PASS)
    acn = results[6].value if 6 in results else None
    return {"ticker": rec["ticker"], "company": rec.get("company"), "sector": rec.get("sector"), "ccc_tier": rec.get("ccc_tier"),
            "yield": dividend_yield(rec), "acn": acn, "passes": passes, "evaluated": len(evaluated), "applicable": len(applicable),
            "coverage": len(evaluated) / len(applicable) if applicable else 0.0,
            "score": passes / len(evaluated) if evaluated else 0.0,
            "rank_score": passes / len(applicable) if applicable else 0.0, "results": results}


def screen(dataset: dict, cfg: dict, ctx: dict | None = None, us_only: bool = True) -> list[dict]:
    rows = []
    for rec in dataset.values():
        if us_only and not rec["us_scope"]:
            continue
        if dividend_yield(rec) is None:
            continue
        rows.append(summarize(rec, evaluate(rec, cfg, ctx), cfg))
    return rows


def _sort_key(x: dict):
    return (-x["rank_score"], -(x["acn"] or 0), -(x["yield"] or 0), x["ticker"])


def rank(rows: list[dict], cfg: dict, top_n: int | None = None) -> list[dict]:
    """The ranked stocks (coverage at or above `ranking.min_coverage`), best first. `top_n` keeps that many (default
    `ranking.top_n` from the config); 0 keeps all of them."""
    r = cfg["ranking"]
    n = r["top_n"] if top_n is None else top_n
    eligible = sorted((x for x in rows if x["coverage"] >= r["min_coverage"]), key=_sort_key)
    return eligible[:n] if n else eligible


def unranked(rows: list[dict], cfg: dict) -> list[dict]:
    """The screened stocks left out of the ranking for low coverage, in the same order the ranking would give them."""
    return sorted((x for x in rows if x["coverage"] < cfg["ranking"]["min_coverage"]), key=_sort_key)
