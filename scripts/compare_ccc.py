# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Compare the DRIP CCC export with Dividend Vision and with our spike-computed figures.

Run from the repo root:
  uv run --python 3.13 scripts/compare_ccc.py [--month 2026-10]

Reads docs/reference/<month>/drip_ccc.csv and ccc_list.csv (newest month by default) and data/spike_out/results.json
(the 21-ticker yfinance spike, so no API calls). Prints a report and writes data/ccc_compare.md.
Sections: universe overlap, tier agreement, DRIP Chowder check, DRIP vs computed growth/yield/streak.
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from div_invst import reference as ref  # noqa: E402


def band(tier):
    lo, hi = ref.DRIP_TIER_YEARS[tier]
    return f"{lo}-{hi}" if hi else f"{lo}+"


def in_band(tier, streak):
    lo, hi = ref.DRIP_TIER_YEARS[tier]
    return streak >= lo and (hi is None or streak <= hi)


def pct(x, d=1):
    return "n/a" if x is None else f"{x * 100:.{d}f}%"


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)] + ["| " + " | ".join(map(str, r)) + " |" for r in rows])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", help="YYYY-MM folder under docs/reference (default: newest)")
    args = ap.parse_args()
    month = ref.REFERENCE_DIR / args.month if args.month else ref.latest_month_dir()
    uni = ref.load_universe(month)
    drip = {t: r for t, r in uni.items() if r["in_drip"]}
    dv = {t: r for t, r in uni.items() if r["in_dv"]}
    both = [t for t in drip if t in dv]
    out = [f"# CCC comparison ({month.name})", ""]

    # 1. overlap
    only_dv = sorted(t for t in dv if t not in drip)
    out += ["## Universe", f"- DRIP {len(drip)} tickers, Dividend Vision {len(dv)}, both {len(both)}.",
            f"- Only in DRIP: {len(drip) - len(both)}. Only in Dividend Vision: {len(only_dv)} ({', '.join(only_dv)}).", ""]
    drip_types = {}
    for r in drip.values():
        drip_types[r["tier"]] = drip_types.get(r["tier"], 0) + 1
    out += ["DRIP tiers: " + ", ".join(f"{k} {v}" for k, v in drip_types.items()), ""]

    # 2. tier agreement: Dividend Vision streak vs the band implied by the DRIP Stock Type
    bad = [(t, drip[t]["tier"], dv[t]["dv_streak"]) for t in both if drip[t]["tier"] in ref.DRIP_TIER_YEARS
           and not in_band(drip[t]["tier"], dv[t]["dv_streak"])]
    out += ["## Tier agreement (Dividend Vision streak vs DRIP Stock Type band)",
            f"- {len(both) - len(bad)} of {len(both)} shared tickers agree. Mismatches: {len(bad)}.", ""]
    if bad:
        out += ["Streak used is the lower claim (`streak` in the loader).", "",
                table(["ticker", "DRIP type (band)", "DV streak", "streak used", "effective tier"],
                      [(t, f"{d} ({band(d)})", s, uni[t]["streak"], uni[t]["tier_effective"]) for t, d, s in sorted(bad)]), ""]

    basis = {}
    for r in uni.values():
        basis[r["streak_basis"]] = basis.get(r["streak_basis"], 0) + 1
    out += ["Streak basis across the universe: " + ", ".join(f"{k} {v}" for k, v in sorted(basis.items())), ""]

    # 3. Chowder check: DRIP chowder vs yield + 5y DGR
    diffs = []
    for t, r in drip.items():
        if None not in (r.get("chowder"), r.get("div_yield"), r.get("dgr_5y")):
            diffs.append((abs(r["chowder"] - (r["div_yield"] + r["dgr_5y"]) * 100), t))
    close = sum(d <= 0.15 for d, _ in diffs)
    out += ["## DRIP Chowder Number vs yield + 5y DGR",
            f"- {close} of {len(diffs)} within 0.15 points; worst: " + ", ".join(f"{t} ({d:.1f})" for d, t in sorted(diffs, reverse=True)[:5]), ""]

    # 4. against the spike figures
    spike_path = ROOT / "data" / "spike_out" / "results.json"
    rows = []
    if spike_path.exists():
        spike = json.loads(spike_path.read_text())
        for t, s in spike.items():
            d = drip.get(t)
            yf = s.get("yfinance", {}) if isinstance(s, dict) else {}
            if not d or not yf.get("dividends"):
                continue
            divs, vals = yf["dividends"], yf.get("info_values", {})
            y_now, y_avg = vals.get("dividendYield"), vals.get("fiveYearAvgDividendYield")
            rows.append({"t": t, "type": d["tier"], "dv_streak": d["dv_streak"], "our_streak": divs.get("streak_years"),
                         "dgr5": d["dgr_5y"], "cagr5": divs.get("cagr5"),
                         "y": d["div_yield"], "yf_y": y_now / 100 if y_now is not None else None,
                         "avg": d["avg_yield_5y"], "yf_avg": y_avg / 100 if y_avg is not None else None})
    out += ["## DRIP vs our computed figures (21-ticker spike)"]
    if rows:
        gdiff = [abs(r["dgr5"] - r["cagr5"]) for r in rows if None not in (r["dgr5"], r["cagr5"])]
        ydiff = [abs(r["avg"] - r["yf_avg"]) for r in rows if None not in (r["avg"], r["yf_avg"])]
        out += [f"- 5y dividend growth: median gap {pct(statistics.median(gdiff))} points over {len(gdiff)} tickers (DRIP DGR 5Y vs our CAGR).",
                f"- 5y average yield: median gap {pct(statistics.median(ydiff))} points over {len(ydiff)} tickers (DRIP vs yfinance fiveYearAvgDividendYield).",
                "- Streak: DRIP gives only a band, so it is checked against the band. Dividend Vision streak shown for reference.", ""]
        out.append(table(["ticker", "DRIP type", "DV streak", "our streak", "streak in band", "DRIP DGR5Y", "our CAGR5", "DRIP 5y avg yld", "yf 5y avg yld", "DRIP yld", "yf yld"],
                         [(r["t"], r["type"], r["dv_streak"], r["our_streak"],
                           "n/a" if r["our_streak"] is None else ("yes" if in_band(r["type"], r["our_streak"]) else "NO"),
                           pct(r["dgr5"]), pct(r["cagr5"]), pct(r["avg"], 2), pct(r["yf_avg"], 2), pct(r["y"], 2), pct(r["yf_y"], 2)) for r in rows]))
    else:
        out.append("- No spike results found (data/spike_out/results.json); skipped.")
    text = "\n".join(out) + "\n"
    print(text)
    (ROOT / "data" / "ccc_compare.md").write_text(text)


if __name__ == "__main__":
    main()
