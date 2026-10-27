# div-invst

A personal dividend-investing screener. It aggregates dividend stock data and history, applies a fixed set of
criteria, and produces:

- a **ranked entry list** (what to buy) with per-criterion pass/fail, and
- an **exit list** for your current holdings (what to sell or review) showing which trigger fired.

Focus is on dividend Aristocrats, Champions and Contenders, but all US dividend payers are screened.

## Status
All 15 criteria are implemented and the top-50 report runs; the data layer (SQLite cache over yfinance, Finnhub, EDGAR and FRED) is built and its first full fetch is in progress. Not built: the holdings loader and exit report (waiting for a holdings file), the CLI, and the Aristocrat label. Current state and next steps: `docs/sessions/session_resume.md`. Documentation index and conventions: `docs/README.md`.

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
Free sources first: yfinance, Finnhub (free tier), SEC EDGAR, FRED. The CCC universe, the Fidelity screener, and the Morningstar and Argus PDFs are monthly manual drops. Dividend Vision was dropped (its terms prohibit automated extraction); FMP and Alpha Vantage were tested and dropped. What each source supplies and its status: `docs/research/data_sources.md`.

## Setup
Python 3.12 or later (pinned to 3.13), managed with `uv`. Put keys in `.env` in the repo root (gitignored):
```
FINNHUB_API_KEY=...
EDGAR_USER_AGENT=div-invst you@example.com
```
(`FMP_API_KEY` and `ALPHAVANTAGE_API_KEY` are only read by the spike script.)

## Monthly routine
Drop the month's files in `docs/reference/<YYYY-MM>/` (gitignored), refresh the cache, run the screen. Step by step: `docs/guides/monthly_drop.md`.

## Scripts
```
uv run --python 3.13 scripts/merge_screener.py                  # Fidelity screener yield-band .xls files -> screener_results.xlsx
uv run --python 3.13 scripts/check_month.py                     # check the month folder: files present and loading
uv run --python 3.13 scripts/build_dataset.py                   # combined per-ticker dataset -> data/dataset/<YYYY-MM>.csv
uv run --python 3.13 scripts/refresh_data.py                    # fill/refresh the SQLite cache (yfinance, Finnhub, EDGAR, FRED) -> data/cache/
uv run --python 3.13 scripts/run_screen.py                      # criteria over the dataset -> data/reports/<YYYY-MM>/top50.md
uv run python -m unittest discover -s tests                    # unit tests
uv run --python 3.13 scripts/coverage_spike.py                  # data coverage report -> data/spike_out/report.md
uv run --python 3.13 scripts/finnhub_vs_edgar.py --tickers JNJ,KO   # Finnhub vs EDGAR spot-check
uv run --python 3.13 scripts/revision_spike.py                  # analyst revision data coverage -> data/revision_out/report.md
```
