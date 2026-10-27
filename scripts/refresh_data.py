# /// script
# requires-python = ">=3.12"
# dependencies = ["openpyxl>=3.1", "pymupdf>=2.0", "requests>=2.31", "yfinance>=0.2.40"]
# ///
"""Refresh the SQLite cache (data/cache/div_invst.sqlite) from yfinance, Finnhub and FRED.

  uv run --python 3.13 scripts/refresh_data.py                 # every ticker with enough coverage (the rankable pool)
  uv run --python 3.13 scripts/refresh_data.py --scope top50   # only the current top 50
  uv run --python 3.13 scripts/refresh_data.py --scope ccc     # every CCC name in US scope
  uv run --python 3.13 scripts/refresh_data.py --tickers JNJ,KO --kinds yf_info,fred

Only snapshots older than their max age (`[refresh]` in config/criteria.toml) are fetched, so a rerun is cheap.
Keys are read from the environment or .env.
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from div_invst.criteria import load_config, rank, screen  # noqa: E402
from div_invst.data import Store, refresh  # noqa: E402
from div_invst.data.refresh import FETCHERS  # noqa: E402
from div_invst.reference import build_dataset  # noqa: E402


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def pick_tickers(args, cfg) -> list[str]:
    if args.tickers:
        return [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    dataset = build_dataset()
    if args.scope == "ccc":
        return sorted(t for t, r in dataset.items() if r["us_scope"] and r["ccc_tier"])
    rows = screen(dataset, cfg)
    if args.scope == "top50":
        return [r["ticker"] for r in rank(rows, cfg)]
    floor = cfg["ranking"]["min_coverage"]
    return sorted(r["ticker"] for r in rows if r["coverage"] >= floor)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scope", choices=("eligible", "top50", "ccc"), default="eligible")
    ap.add_argument("--tickers", help="comma-separated; overrides --scope")
    ap.add_argument("--kinds", help=f"comma-separated subset of: {', '.join(FETCHERS)}")
    args = ap.parse_args()
    load_dotenv(ROOT / ".env")
    cfg = load_config()
    kinds = [k.strip() for k in args.kinds.split(",")] if args.kinds else None
    tickers = pick_tickers(args, cfg)
    print(f"{len(tickers)} tickers, kinds: {', '.join(kinds or FETCHERS)}")
    store = Store()
    stats = refresh(store, tickers, cfg, kinds)
    print(f"fetched {stats['fetched']}, already fresh {stats['fresh']}, errors {len(stats['errors'])}")


if __name__ == "__main__":
    main()
