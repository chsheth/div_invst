# div-invst

A personal dividend-investing screener. It aggregates dividend stock data and history, applies a fixed set of
criteria, and produces:

- a **ranked entry list** (what to buy) with per-criterion pass/fail, and
- an **exit list** for your current holdings (what to sell or review) showing which trigger fired.

Focus is on dividend Aristocrats, Champions and Contenders, but all US dividend payers are screened.

## Status
Planning, the data coverage spike, the revision data spike and the monthly reference loaders (CCC, Morningstar, Argus) are complete, and the default thresholds are settled; the application itself is not built yet. See `docs/sessions/session_resume.md` for the current state and next steps.

## Documents
| File | Purpose |
|------|---------|
| `docs/criteria/ideas_v1.md` | Original notes |
| `docs/criteria/ideas_v2.md` | Structured criteria, exit rules, decisions log (source of truth) |
| `docs/research/data_sources.md` | Data source research: which sources work programmatically, element-to-source map |
| `docs/research/coverage_spike_2026-10-19.md` | Coverage spike results on 21 tickers: source verdicts, EDGAR tag chains, Finnhub vs EDGAR checks |
| `docs/research/revision_spike_2026-10-21.md` | Analyst revision data coverage for the StarMine-style proxy (criterion 13) |
| `docs/research/fidelity_screener.md` | Column-by-column reference for the monthly Fidelity screener download (layout, units, fill rates, open checks) |
| `docs/guides/monthly_drop.md` | Step-by-step for the monthly reference drop: what to download, file names, commands, checks |
| `docs/plan/PLAN.md` | Build plan, phases |
| `docs/sessions/session_resume.md` | Session summaries, open questions, next steps (start here when resuming) |

## Planned usage
```
uv run main.py                          # entry list only (no holdings)
uv run main.py --holdings holdings.csv  # entry list + exit report
```
(CLI is not implemented yet.)

## Inputs
- Optional holdings file (Excel or CSV): `ticker` required, `shares` optional. No cost basis needed.

## Outputs
- Ranked entry list (top 50): per-criterion pass/fail, coverage count.
- Exit report: price, target sell price, % upside, trigger(s) fired.

## Data
Free sources first: yfinance, Finnhub (free tier), SEC EDGAR, FRED. The CCC universe comes from the monthly DRIP "All CCC" export plus Dividend Vision tables (streak years, conservative when they disagree); yfinance-computed streaks are a screen only. FMP and Alpha Vantage were tested and dropped. See `docs/research/coverage_spike_2026-10-19.md` and `docs/plan/PLAN.md`.

## Setup
Python 3.12 or later (pinned to 3.13), managed with `uv`. Put keys in `.env` in the repo root (gitignored):
```
FINNHUB_API_KEY=...
EDGAR_USER_AGENT=div-invst you@example.com
```
(`FMP_API_KEY` and `ALPHAVANTAGE_API_KEY` are only read by the spike script.)

## Monthly reference inputs
Drop the month's files in `docs/reference/<YYYY-MM>/` (gitignored): `drip_ccc.csv` (DRIP "All CCC" email export), `screener_results.xlsx` (Fidelity screener yield bands, merged by `scripts/merge_screener.py`), Morningstar large and mid cap pick list PDFs, Argus Top 30 PDF, optional `ratings.csv`; `ccc_list.csv` is written by the fetch script. Step-by-step: `docs/guides/monthly_drop.md`. Details: `docs/criteria/ideas_v2.md`.

## Scripts
```
uv run --python 3.13 scripts/fetch_ccc.py                       # Dividend Vision CCC lists -> docs/reference/<YYYY-MM>/ccc_list.csv
uv run --python 3.13 scripts/merge_screener.py                  # Fidelity screener yield-band .xls files -> screener_results.xlsx
uv run --python 3.13 scripts/check_month.py                     # check the month folder: files present and loading
uv run --python 3.13 scripts/compare_ccc.py                     # DRIP vs Dividend Vision vs computed -> data/ccc_compare.md
uv run --python 3.13 scripts/coverage_spike.py                  # data coverage report -> data/spike_out/report.md
uv run --python 3.13 scripts/finnhub_vs_edgar.py --tickers JNJ,KO   # Finnhub vs EDGAR spot-check
uv run --python 3.13 scripts/revision_spike.py                  # analyst revision data coverage -> data/revision_out/report.md
```
