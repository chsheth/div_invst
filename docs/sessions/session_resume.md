# Session resume

_Last updated: 2026-11-07 (session 10)_. Live state only: open items and next steps. History is `session_log.md`; the criteria and thresholds
are `../criteria/ideas_v2.md`; the reasons behind them are `../criteria/decisions_log.md`; the build status per slice is `../plan/PLAN.md`.

## How to resume
1. Read `../plan/PLAN.md` (what is built) and the Open items below.
2. For a criterion's rule read `../criteria/ideas_v2.md`; for why, grep `../criteria/decisions_log.md`.
3. Monthly files: `../guides/monthly_drop.md`. Source behaviour: `../research/data_sources.md`.

## State
- All 15 criteria are implemented (14 is na without holdings); 41 unit tests pass. Criteria 1, 7, 8, 10, 11, 12 and the revision proxy read the SQLite cache, so they are unknown until a ticker's data is cached.
- Committed and pushed through session 10 (2026-11-07): the Schwab source, `--month` and the notebooks, the `refresh_data --scope top50` fix, `Store(as_of=...)` and `run_screen --as-of`, the forward tracker (`scripts/track_returns.py`, `notebooks/forward_test.ipynb`). `data/reports/2026-10/ranked.csv` is the full October list (rebuilt as of 2026-10-27; its top 50 equals the original).
- November drop (2026-11-06): `docs/reference/2026-11/` holds `drip_ccc.csv`, `screener_results.xlsx` (2,882 stocks, eight bands), `morningstar_mid_cap.pdf`, `schwab_results.csv` (3,666 stocks, six bands); `build_dataset` ran on it, then `refresh_data` finished 2026-11-07 (3,018 fetched, 0 errors; 1,349 tickers cached) and `run_screen` (top 50 and `--top 0`, 1,327 ranked) and `track_returns.py` ran on the refreshed cache. The 2026-11 list is dated 2026-11-07 in the tracker. Missing: the Morningstar large cap list (the file received was October's again, byte for byte) and the Argus Top 30 (none of the `ar_1106_*.pdf` files is the Portfolio Selector). The unused commentary PDFs received with the drop were deleted.
- First full fetch finished 2026-10-26: 1,354 tickers cached; the 6 EDGAR errors (BSRT, OZK, PFBC, GAMI, HIFS, TOWN) are tickers with no SEC 10-K filings; `NO_SEC_FILINGS` in `edgar.py` stores an empty record for them (2026-11-05), so criteria 7's EDGAR fallback and 11 stay unknown for them.
- First full screen (2026-10-26): 1,679 screened, 1,333 with enough coverage to rank; top 50 are 8 to 11 of 13-14 applicable. Yield traps no longer dominate: IIPR (14.0%, #11), KRP (#14), INSW (18.2%, #37) and VRTS (#39) are the only 8%+ yields in the top 50.

## Open items
1. **Stale dividend CAGR (partly handled 2026-11-05):** criteria 5 and 6 now fail when the latest annual dividend is falling (CHRD, KRP out of the top 50). Still open: IIPR-style stale CAGRs where the dividend is flat rather than falling, rebounds from a cut that are already up (RCL, 35% growth from the 2020 base) and tiny-base growth (MGY).
2. **Criterion 7 calibration (decided 2026-11-05: keep strict):** fails KO (6 of 10 up years) and JNJ (3 of 10) on noisy GAAP EPS; JNJ has back-to-back one-off years the one-off rule handles awkwardly. Threshold stays 7 of 10; the one-off rule could still be improved.
3. **Coverage cutoff (decided 2026-11-05):** stays 70%; the top 50 is identical from 50% to 90%.
4. **I/B/E/S in criterion 15 (decided 2026-11-05: keep):** it does not overlap with StarMine in practice (correlation 0.02) and criterion 15 needs it for coverage. Open side note: Zacks and McLean vote 0 for most tickers, diluting the net score.
5. **Aristocrat label:** needs an S&P 500 constituent list (not in our data). Plan: fetch it automatically (the Wikipedia "List of S&P 500 companies" table through the MediaWiki API, with a User-Agent) with a manual `sp500.csv` override; Aristocrat = S&P 500 and band Champion or King. User chose to look for an automatic source; nothing is built.
6. **Backtest (decided 2026-11-07: forward tracker):** `scripts/track_returns.py` scores each month's `ranked.csv` against later total returns versus SPY (`../guides/monthly_drop.md` step 7). Built and tested (`notebooks/forward_test.ipynb` shows one month step by step); first full run done 2026-11-07. First look, October top 50 at 12 days: -1.1% against SPY -3.9% (too early to mean anything). Needs 6 to 12 months before it says anything; run `run_screen --top 0` every month so each month has a full list. A historical rebuild was rejected (decisions log 2026-11-07).
7. **Holdings file:** the user has none, so criterion 14 and the exit report (Slice 4) wait.
8. **CFRA vote (added 2026-11-06):** it swapped 7 of the 2026-11 top 50 against the same data without it and has no outcome evidence yet; judge it in the tracker (item 6). Morningstar fair value from Schwab covers 46% of CCC names and is a cross-check only.
9. **Equity units and odd tickers:** NEE/PS, NEE/PT, NEE/PV (NEE equity units) get NEE common-stock EDGAR data under their own ticker, which would mislead EPS-based criteria; consider excluding preferred and unit tickers from the universe. BRK.B pays no dividend.
10. **`refresh_data.py --scope top50` (fixed 2026-11-07):** it now attaches the cache and macro before ranking, so it picks the same top 50 as `run_screen.py` (checked on 2026-11). It ranks on cached data, so it only refreshes names already cached: use it after a full refresh, not on a cold cache. A shared ranking helper for both scripts would stop the two from drifting apart.
11. **Smaller items:** banks and insurers for criterion 1 (unknown now); Altman Z (dropped); SPY yield to replace the manual S&P yield; quality composite thresholds are defaults to keep calibrating; the Fidelity open checks in `../research/fidelity_screener.md` section 7; why XOM, CABO and TGLS are missing from the screener.

## Next steps (ordered)
1. **Start here:** the monthly flow is by hand in the first week of each month (no schedule, decided 2026-11-07): `../guides/monthly_drop.md` or `notebooks/monthly_run.ipynb` with `TOP = 0`, then `track_returns.py`. For November, the Morningstar large cap list and the Argus Top 30 are still missing (optional; add them and re-run the screen if wanted). The tracker needs 6 to 12 months before it says anything.
2. Pick up an open item: the Aristocrat label, banks for criterion 1, or SPY yield.
3. Slice 4 when the holdings file exists; then the CLI and fixture tests (`../plan/PLAN.md`).
