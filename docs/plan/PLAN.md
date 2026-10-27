# div-invst: Build plan

The architecture and the build slices with their status. What the criteria are: `../criteria/ideas_v2.md`. Why: `../criteria/decisions_log.md`.
Data source findings: `../research/data_sources.md`. Where we left off: `../sessions/session_resume.md`.

## Goal
Aggregate dividend stock data and history, screen it against the criteria, and output (a) a ranked top-50 entry list with per-criterion
pass/fail and (b) an exit list for current holdings showing which sell trigger fired.

## Design
- **Data:** free sources first (yfinance, Finnhub free tier, SEC EDGAR, FRED); paid only if inadequate. Monthly manual drops supply what has no API (CCC universe, Fidelity screener, Morningstar and Argus PDFs): `../guides/monthly_drop.md`.
- **Flow:** `reference/` loaders build one record per ticker (`dataset.py`), the data layer adds `rec["cache"]` from the SQLite cache (`data/readers.py`), `criteria/` evaluates (one function per criterion, `@criterion`), `engine.py` ranks, `scripts/run_screen.py` writes `data/reports/<month>/top50.{csv,md}`.
- **Config:** every threshold and macro input is in `config/criteria.toml`. Criteria return pass / fail / unknown / na; missing data is unknown, never a fail.
- **Cache:** append-only SQLite (`data/cache/div_invst.sqlite`) of timestamped snapshots, refreshed by `scripts/refresh_data.py` with a max age per data kind (`[refresh]` in the config; cadence rationale in `../research/data_sources.md`).
- **Run mode:** on-demand CLI writing CSV and Markdown reports. Holdings come from an Excel or CSV file (ticker required, shares optional, no cost basis); without one the entry list runs with the diversification cut skipped and no exit report.
- **Tech:** Python >= 3.12 pinned to 3.13, managed with `uv`; keys in `.env` (gitignored): `FINNHUB_API_KEY`, `EDGAR_USER_AGENT` (and `FMP_API_KEY`, `ALPHAVANTAGE_API_KEY`, read only by the spike script).

## Build slices
**Done: data spikes** (coverage 2026-10-19, revisions 2026-10-21) and **monthly reference loaders** (DRIP, Morningstar, Argus, screener merge, folder check, monthly guide; 2026-10-25).

| Slice | Scope | Status |
|-------|-------|--------|
| 1. Screener-based entry list | `reference/screener.py`, `reference/dataset.py`, `scripts/build_dataset.py`; engine, config, ranking, `scripts/run_screen.py`; criteria 2, 3, 4, 5, 6, 9, 13, 14, 15; tests | **Done** (2026-10-25 and 26) |
| 2. Data layer | `data/`: `store.py` (snapshot store), `refresh.py`, fetchers `yahoo.py`, `finnhub.py`, `edgar.py`, `fred.py`, `readers.py` (`rec["cache"]`, macro); `scripts/refresh_data.py` | **Built**; first full fetch of the eligible pool in progress (EDGAR and splits still to run). Still to do: SPY yield, run snapshots tied to a report month, scheduling |
| 3. Remaining criteria | Criteria 1, 7, 8, 10, 11, 12, the revision proxy for 13, REIT FFO payout (`criteria/history.py`, `fundamentals.py`, `valuation.py`, `analysts.py`) | **Built** (2026-10-26), unknown until the cache is populated. Still to do: banks and insurers for criterion 1, Altman Z, calibration on known tickers, decision on the criterion 8 yield-trap guard, exit-rule inputs |
| 4. Holdings and exit | Holdings loader (layout from the user), diversification cut, exit report (fair-value ceiling, yield compression, fundamental break, Morningstar deletions as a note) | Not started; blocked on the holdings file |
| 5. Tests and CLI | Fixture tests per criterion (unit tests exist for all built criteria), CLI in `main.py` (`--holdings`, `--month`), hand-check 3 known aristocrats | Not started |

## Verification
- `uv run python -m unittest discover -s tests` (stdlib unittest, no pandas).
- `uv run --python 3.13 scripts/run_screen.py`, then spot-check known names (KO, JNJ, PG, O) against `../research/fidelity_screener.md` section 6.
- Once the cache is full: recheck coverage, the number of rankable tickers, and whether yield traps reach the top 50.
- The spikes reproduce from cached responses: `scripts/coverage_spike.py`, `scripts/revision_spike.py`, `scripts/finnhub_vs_edgar.py`.
