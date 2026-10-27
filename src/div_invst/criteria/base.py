"""Criterion results and the registry that the engine runs.

A criterion is a function `fn(rec, cfg, ctx) -> Result` registered with @criterion(number, name). `rec` is one record of
the combined dataset (reference/dataset.py), `cfg` the parsed config/criteria.toml, `ctx` run-level data (holdings).
Status is pass, fail, unknown (not enough data) or na (does not apply to this run, for example no holdings loaded);
unknown and na never count as a fail.
"""
from dataclasses import dataclass, field

PASS, FAIL, UNKNOWN, NA = "pass", "fail", "unknown", "na"


@dataclass
class Result:
    number: int
    name: str
    status: str
    value: object = None
    detail: dict = field(default_factory=dict)
    flags: list = field(default_factory=list)


@dataclass
class Criterion:
    number: int
    name: str
    fn: object


REGISTRY: dict[int, Criterion] = {}


def criterion(number: int, name: str):
    def register(fn):
        REGISTRY[number] = Criterion(number, name, fn)
        return fn
    return register


def make(number: int, status: str, value=None, flags=None, **detail) -> Result:
    return Result(number, REGISTRY[number].name, status, value, detail, list(flags or []))


def src(rec: dict, source: str, name: str):
    """Field `name` of one source in the record, or None when the ticker is not in that source."""
    data = rec.get(source)
    return data.get(name) if data else None


def first(*values):
    return next((v for v in values if v is not None), None)


def dividend_yield(rec: dict):
    return first(src(rec, "screener", "div_yield"), src(rec, "drip", "div_yield"))


def dividend_growth_5y(rec: dict):
    return first(src(rec, "screener", "dgr_5y"), src(rec, "drip", "dgr_5y"))


def is_reit(rec: dict) -> bool:
    return "REIT" in (rec.get("security_type") or "") or rec.get("sector") == "Real Estate"


def is_bank_or_insurer(rec: dict) -> bool:
    return rec.get("sector") == "Financials" and (rec.get("industry") or "") in ("Banks", "Insurance", "Thrifts & Mortgage Finance")


def ffo_payout(rec: dict):
    """REIT payout from the cache (dividends paid / FFO proxy), or None."""
    return ((rec.get("cache") or {}).get("edgar") or {}).get("ffo_payout")
