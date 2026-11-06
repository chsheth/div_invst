# Session resume

_Last updated: 2026-11-05 (session 8)_. Live state only: open items and next steps. History is `session_log.md`; the criteria and thresholds
are `../criteria/ideas_v2.md`; the reasons behind them are `../criteria/decisions_log.md`; the build status per slice is `../plan/PLAN.md`.

## How to resume
1. Read `../plan/PLAN.md` (what is built) and the Open items below.
2. For a criterion's rule read `../criteria/ideas_v2.md`; for why, grep `../criteria/decisions_log.md`.
3. Monthly files: `../guides/monthly_drop.md`. Source behaviour: `../research/data_sources.md`.

## State
- All 15 criteria are implemented (14 is na without holdings); 35 unit tests pass. Criteria 1, 7, 8, 10, 11, 12 and the revision proxy read the SQLite cache, so they are unknown until a ticker's data is cached.
- Last commit `1daa42d` on `main`, pushed.
- First full fetch finished 2026-10-26: 1,354 tickers cached; the 6 EDGAR errors (BSRT, OZK, PFBC, GAMI, HIFS, TOWN) are tickers with no SEC 10-K filings; `NO_SEC_FILINGS` in `edgar.py` stores an empty record for them (2026-11-05), so criteria 7's EDGAR fallback and 11 stay unknown for them.
- Uncommitted: the falling-dividend check for criteria 5 and 6 (2026-11-05) and the calibration notes. Top 50 changes from it: KRP, CHRD, JBSS, INSW out; MLI, BYD, JOE, AGX in.
- First full screen (2026-10-26): 1,679 screened, 1,333 with enough coverage to rank; top 50 are 8 to 11 of 13-14 applicable. Yield traps no longer dominate: IIPR (14.0%, #11), KRP (#14), INSW (18.2%, #37) and VRTS (#39) are the only 8%+ yields in the top 50.

## Open items
1. **Stale dividend CAGR (partly handled 2026-11-05):** criteria 5 and 6 now fail when the latest annual dividend is falling (CHRD, KRP out of the top 50). Still open: IIPR-style stale CAGRs where the dividend is flat rather than falling, rebounds from a cut that are already up (RCL, 35% growth from the 2020 base) and tiny-base growth (MGY).
2. **Criterion 7 calibration (decided 2026-11-05: keep strict):** fails KO (6 of 10 up years) and JNJ (3 of 10) on noisy GAAP EPS; JNJ has back-to-back one-off years the one-off rule handles awkwardly. Threshold stays 7 of 10; the one-off rule could still be improved.
3. **Coverage cutoff (decided 2026-11-05):** stays 70%; the top 50 is identical from 50% to 90%.
4. **I/B/E/S in criterion 15** is also LSEG data, with some overlap with the ESS in 13; drop it from 15 if a stricter split is wanted.
5. **Aristocrat label:** needs an S&P 500 constituent list (not in our data). Plan: fetch it automatically (the Wikipedia "List of S&P 500 companies" table through the MediaWiki API, with a User-Agent) with a manual `sp500.csv` override; Aristocrat = S&P 500 and band Champion or King. User chose to look for an automatic source; nothing is built.
6. **Backtest:** asked how, deferred. The monthly vendor files exist only for 2026-10, so the options are a forward test from now (store each month's list and score later returns) or a historical rebuild from free sources for the reconstructable criteria only. Scope and metrics unanswered.
7. **Holdings file:** the user has none, so criterion 14 and the exit report (Slice 4) wait.
8. **Equity units and odd tickers:** NEE/PS, NEE/PT, NEE/PV (NEE equity units) get NEE common-stock EDGAR data under their own ticker, which would mislead EPS-based criteria; consider excluding preferred and unit tickers from the universe. BRK.B pays no dividend.
9. **Smaller items:** banks and insurers for criterion 1 (unknown now); Altman Z (dropped); SPY yield to replace the manual S&P yield; quality composite thresholds are defaults to keep calibrating; the Fidelity open checks in `../research/fidelity_screener.md` section 7; why XOM, CABO and TGLS are missing from the screener.

## Next steps (ordered)
1. **Start here:** commit the falling-dividend check and the calibration notes, then check whether a November monthly drop is due (`../guides/monthly_drop.md`).
2. Open item 4 (I/B/E/S in criterion 15). The calibration review is done (2026-11-05, `../criteria/decisions_log.md`): criteria 5 to 10 and 12 stay strict.
3. Pick up an open item: the Aristocrat label, the backtest scope, banks for criterion 1, or SPY yield.
4. Slice 4 when the holdings file exists; then the CLI and fixture tests (`../plan/PLAN.md`).
