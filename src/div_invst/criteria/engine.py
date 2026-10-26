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


def rank(rows: list[dict], cfg: dict) -> list[dict]:
    r = cfg["ranking"]
    eligible = [x for x in rows if x["coverage"] >= r["min_coverage"]]
    eligible.sort(key=lambda x: (-x["rank_score"], -(x["acn"] or 0), -(x["yield"] or 0), x["ticker"]))
    return eligible[:r["top_n"]]
