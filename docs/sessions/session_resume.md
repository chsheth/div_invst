# Session resume

_Last updated: 2026-10-26 (session 7)_. Live state only: open items and next steps. History is `session_log.md`; the criteria and thresholds
are `../criteria/ideas_v2.md`; the reasons behind them are `../criteria/decisions_log.md`; the build status per slice is `../plan/PLAN.md`.

## How to resume
1. Read `../plan/PLAN.md` (what is built) and the Open items below.
2. For a criterion's rule read `../criteria/ideas_v2.md`; for why, grep `../criteria/decisions_log.md`.
3. Monthly files: `../guides/monthly_drop.md`. Source behaviour: `../research/data_sources.md`.

## State
- All 15 criteria are implemented (14 is na without holdings); 30 unit tests pass. Criteria 1, 7, 8, 10, 11, 12 and the revision proxy read the SQLite cache, so they are unknown until a ticker's data is cached.
- Last commit `b1bc8c7` on `main` (not pushed). Uncommitted: `scripts/refresh_data.py` and `Store.tickers()` (pool fix), the markdown reorganisation.
- Two background fetches were running at 2026-10-26: the main `scripts/refresh_data.py` run (yfinance done for 1,331 to 1,334 tickers; Finnhub `fh_metric` about 770 of 1,334, then `fh_insider`) and `refresh_data.py --kinds edgar,yf_splits` (EDGAR about 385 of about 1,334, then splits). Check with `uv run python` against `data/cache/div_invst.sqlite` (count distinct tickers per kind), or just rerun the script: it only fetches what is stale.
- Interim screen (cache partly filled): 642 rankable tickers; this number will move as the cache fills.

## Open items
1. **Criterion 8 yield-trap guard (deferred):** of 197 DDM passes, 57 yield 10% or more (mortgage REITs, BDCs, NHTC at 45%). Decide after the full ranking whether to skip the dividend estimate above about 12% yield or a payout above 100%.
2. **Criterion 7 calibration:** fails KO (6 of 10 up years) and JNJ (3 of 10) on noisy GAAP EPS; JNJ has back-to-back one-off years the one-off rule handles awkwardly.
3. **Coverage cutoff:** revisit the 70% minimum once the cache is full (about 14 applicable criteria now, not 8).
4. **I/B/E/S in criterion 15** is also LSEG data, with some overlap with the ESS in 13; drop it from 15 if a stricter split is wanted.
5. **Aristocrat label:** needs an S&P 500 constituent list (not in our data). Plan: fetch it automatically (the Wikipedia "List of S&P 500 companies" table through the MediaWiki API, with a User-Agent) with a manual `sp500.csv` override; Aristocrat = S&P 500 and band Champion or King. User chose to look for an automatic source; nothing is built.
6. **Backtest:** asked how, deferred. The monthly vendor files exist only for 2026-10, so the options are a forward test from now (store each month's list and score later returns) or a historical rebuild from free sources for the reconstructable criteria only. Scope and metrics unanswered.
7. **Holdings file:** the user has none, so criterion 14 and the exit report (Slice 4) wait.
8. **Equity units and odd tickers:** NEE/PS, NEE/PT, NEE/PV (NEE equity units) get NEE common-stock EDGAR data under their own ticker, which would mislead EPS-based criteria; consider excluding preferred and unit tickers from the universe. BRK.B pays no dividend.
9. **Smaller items:** banks and insurers for criterion 1 (unknown now); Altman Z (dropped); SPY yield to replace the manual S&P yield; quality composite thresholds are defaults to keep calibrating; the Fidelity open checks in `../research/fidelity_screener.md` section 7; why XOM, CABO and TGLS are missing from the screener.

## Next steps (ordered)
1. Let both fetches finish (the class-share ticker fix is in the code; Finnhub for those 23 comes with the next rerun); rerun `refresh_data.py` (and `--kinds edgar,yf_splits` if EDGAR is incomplete) until it reports nothing left to fetch.
2. Run `scripts/run_screen.py`; recheck coverage and the top 50; decide open items 1 to 4 from what it shows.
3. Commit the pool fix and the doc reorganisation.
4. Pick up an open item: the Aristocrat label, the backtest scope, banks for criterion 1, or SPY yield.
5. Slice 4 when the holdings file exists; then the CLI and fixture tests (`../plan/PLAN.md`).
