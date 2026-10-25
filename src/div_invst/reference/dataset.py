"""The combined monthly dataset: one record per ticker across all reference sources.

Each record keeps the sources side by side (`drip`, `screener`, `morningstar`, `argus`) so no value is overwritten and
every criterion can say which source it used, plus a few resolved top-level fields. Sources that a ticker is not in
are None. Percent fields are fractions in every source.

Top-level fields: ticker, company, in (dict of source -> bool), us_scope, ccc_tier, sector, industry, country,
security_type, market_cap (dollars), price.
us_scope: True for a US-headquartered non-ADR in the screener, or (when not in the screener) any name from the US-only
lists (DRIP, Morningstar, Argus); False for ADRs and foreign headquarters.
"""
import csv
from pathlib import Path

from .argus import load_argus
from .ccc import load_drip
from .common import latest_month_dir
from .morningstar import load_morningstar
from .screener import load_screener

SOURCES = ("drip", "screener", "morningstar", "argus")
US = "United States of America"


def _first(*values):
    return next((v for v in values if v is not None), None)


def build_dataset(month_dir: Path | None = None) -> dict[str, dict]:
    """Combined dataset for a month folder (newest by default), keyed by ticker. A missing optional file is skipped
    (its source is None for every ticker); drip_ccc.csv and screener_results.xlsx are required."""
    month_dir = month_dir or latest_month_dir()
    raw = {
        "drip": load_drip(month_dir / "drip_ccc.csv"),
        "screener": load_screener(month_dir / "screener_results.xlsx"),
        "morningstar": load_morningstar(month_dir) if (month_dir / "morningstar_large_cap.pdf").exists()
        or (month_dir / "morningstar_mid_cap.pdf").exists() else {},
        "argus": load_argus(month_dir / "argus_top30.pdf") if (month_dir / "argus_top30.pdf").exists() else {},
    }
    out: dict[str, dict] = {}
    for ticker in sorted(set().union(*raw.values())):
        d, s, m, a = (raw[k].get(ticker) for k in SOURCES)
        if s is not None:
            scope = s.get("security_type") != "Depository Receipt" and s.get("country") == US
        else:
            scope = True
        out[ticker] = {
            "ticker": ticker,
            "company": _first(s and s.get("company"), d and d.get("company"), m and m.get("company"), a and a.get("company")),
            "in": {k: raw[k].get(ticker) is not None for k in SOURCES},
            "us_scope": scope,
            "ccc_tier": d.get("tier") if d else None,
            "sector": _first(s and s.get("sector"), d and d.get("sector"), m and m.get("sector")),
            "industry": _first(s and s.get("industry"), d and d.get("industry"), m and m.get("industry")),
            "country": s.get("country") if s else None,
            "security_type": s.get("security_type") if s else None,
            "market_cap": _first(s and s.get("market_cap"), m and m.get("market_cap_m") and m["market_cap_m"] * 1e6),
            "price": _first(s and s.get("price"), d and d.get("price"), m and m.get("price"), a and a.get("price")),
            "drip": d, "screener": s, "morningstar": m, "argus": a,
        }
    return out


def flatten(record: dict) -> dict:
    """One flat row for CSV: top-level fields, then each source's fields prefixed drip_, scr_, ms_ or argus_."""
    prefix = {"drip": "drip_", "screener": "scr_", "morningstar": "ms_", "argus": "argus_"}
    row = {k: v for k, v in record.items() if k not in SOURCES and k != "in"}
    for src in SOURCES:
        row[f"in_{src}"] = record["in"][src]
    for src in SOURCES:
        for k, v in (record[src] or {}).items():
            if k not in ("ticker", "company"):
                row[prefix[src] + k] = v
    return row


def write_csv(dataset: dict[str, dict], path: Path) -> int:
    """Write the flattened dataset to `path`, creating parent folders. Returns the number of rows."""
    rows = [flatten(r) for r in dataset.values()]
    columns = list(dict.fromkeys(k for row in rows for k in row))
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)
    return len(rows)

