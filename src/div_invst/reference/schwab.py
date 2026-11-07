"""Schwab stock screener export (schwab_results.csv, built by scripts/merge_schwab.py).

Only the columns the criteria use are read: the CFRA star ranking (a vote in criterion 15) and Morningstar's rating,
fair value and moat (fair value feeds the criterion 8 cross-check). Layout, fill rates and the reasons the other
columns are ignored: docs/research/schwab_screener.md.

Conversions: "4 Stars" -> 4, "--" and blanks -> None, fair value -> float. A Morningstar row marked "dropping coverage",
"Rating Drop" or "notrated" has no usable rating or fair value, so those fields are None and `ms_status` says why.
Schwab is an enrichment source: its tickers do not enter the dataset on their own, and a ticker whose description names a
different company than the screener's (a reused ticker) is ignored; see `same_company`.
"""
import csv
import re
from pathlib import Path

# Schwab column -> (field, kind)
COLUMNS = {"Description": ("description", "str"), "CFRA Star Ranking": ("cfra_stars", "stars"),
           "Morningstar Rating": ("ms_stars", "ms"), "Morningstar Fair Value Estimate": ("ms_fair_value", "num"),
           "Morningstar Economic Moat": ("ms_moat", "cat")}
REQUIRED = ("Symbol", *COLUMNS)
MS_UNUSABLE = {"dropping coverage": "dropping coverage", "rating drop": "rating drop", "notrated": "not rated"}
STOPWORDS = {"the", "inc", "corp", "corporation", "company", "group", "holdings", "holding", "limited", "ltd", "plc", "trust"}


def _cell(raw: str):
    s = (raw or "").strip()
    return None if s in ("", "--", "-", "N/A") else s


def _stars(s: str | None) -> int | None:
    m = re.match(r"([1-5])\s*stars?$", s or "", re.I)
    return int(m[1]) if m else None


def _num(s: str | None) -> float | None:
    try:
        return float((s or "").replace(",", "").replace("$", ""))
    except ValueError:
        return None


def parse_row(row: dict) -> dict:
    out = {}
    ms_status = None
    for col, (field, kind) in COLUMNS.items():
        s = _cell(row.get(col))
        if kind == "stars":
            out[field] = _stars(s)
        elif kind == "ms":
            out[field] = _stars(s)
            if s and out[field] is None:
                ms_status = MS_UNUSABLE.get(s.lower(), s.lower())
        elif kind == "num":
            out[field] = _num(s)
        else:
            out[field] = s
    if ms_status:
        out["ms_fair_value"] = None
    out["ms_status"] = ms_status
    return out


def load_schwab(path: Path) -> dict[str, dict]:
    """The merged Schwab file keyed by ticker (first row wins). Raises ValueError when a needed column is missing or the
    file has no rows, so a changed export layout is never silent."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path.name} lacks column(s): {', '.join(missing)}")
        out: dict[str, dict] = {}
        for row in reader:
            sym = (row["Symbol"] or "").strip()
            if sym and sym not in out:
                out[sym] = {"ticker": sym, **parse_row(row)}
    if not out:
        raise ValueError(f"no rows in {path.name}")
    return out


def _tokens(name: str | None) -> set[str]:
    return {w[:4] for w in re.findall(r"[a-z0-9]+", (name or "").lower()) if len(w) >= 4 and w not in STOPWORDS}


def same_company(a: str | None, b: str | None) -> bool:
    """True when two company names share a significant word (compared on the first four letters, so Centerspace and
    Centrespace match; "The", "Inc" and similar are ignored). True when either name has no significant word: nothing to
    contradict. Guards against a ticker that Schwab and Fidelity assign to different companies."""
    ta, tb = _tokens(a), _tokens(b)
    return not ta or not tb or bool(ta & tb)
