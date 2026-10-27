# Session log

History of what each session did, newest first. The live state (open items and next steps) is `session_resume.md`; the reasons behind
decisions are in `../criteria/decisions_log.md`.

## Session 7 (2026-10-26)
- **Decided and built:** StarMine double count (ESS only in 13, out of the 15 panel) and the ranking key (passes / applicable); documented how ranking works. Slice 2: SQLite snapshot store, `refresh()`, yfinance / Finnhub / EDGAR / FRED fetchers, readers (`rec["cache"]`), FRED macro in the screen, `scripts/refresh_data.py`. Slice 3: criteria 7, 11, 12, 1, 10, 8 and the revision proxy; REIT FFO proxy validated against reported FFO for O and PLD and an 85% payout cutoff set; criterion 8 tuned to a two-stage DDM with a 3.5% equity premium; median P/E history. 30 tests.
- **Findings:** the fair-value DDM passes 197 of 1,215 cached tickers, mostly yield traps (mortgage REITs, BDCs, NHTC); criterion 7 fails KO (6 of 10 up years) and JNJ (3 of 10) on noisy GAAP EPS; the first fetch pool came out empty once criteria read the cache (fixed: screener coverage plus already-cached tickers).
- **Commits:** `59afd83` (decisions and ranking), `9f69939` (data layer), `ae54cf0` (Slice 3 start, FFO), `b1bc8c7` (criteria 1, 8, 10).
- **Asked, not done:** an Aristocrat label (needs an S&P 500 list; plan written, nothing run) and a backtest approach (scope question unanswered).

## Session 6 (2026-10-25)
- Built the screener loader and the combined per-ticker dataset (`reference/screener.py`, `reference/dataset.py`, `scripts/build_dataset.py`): 2,908 tickers, 681 of 684 CCC names in the screener (CABO, TGLS, XOM missing), key CCC fields 73% to 100% filled. Writes `data/dataset/2026-10.csv`.
- Decisions and checks recorded in `ideas_v2.md` and `../research/fidelity_screener.md` section 7. Dividend Vision dropped; criteria 2, 3 and 15 get a collective quality composite from the screener.
- Fidelity screener: first download (four bands) replaced by a second (seven bands, 0.07% and up, 62 Search Criteria columns) merged to `docs/reference/2026-10/screener_results.xlsx` (2,883 stocks, 5 tabs) with `scripts/merge_screener.py` (now prints each band and rejects copies); reviewed against the criteria (see `ideas_v2.md` "Fidelity screener"). StarMine ESS fills criterion 13; S&P Financial Health and Quality scores are candidates for criterion 1 (calibrate first).
- `reference.py` became the `reference/` package; wrote the Morningstar and Argus PDF loaders (Morningstar also reads the Pick List Deletions table), `scripts/check_month.py`, and `docs/guides/monthly_drop.md` (the monthly steps). PyMuPDF is now a project dependency.
- Raw screener `.xls` files deleted after the merge; only `screener_results.xlsx` is kept.


- Criteria engine built (9 criteria, ranking, report, tests); code review fixes applied (negative P/B, Morningstar None, bank interest coverage). Open: calibration, StarMine double count, ranking tie rule.
- Calibration 2026-10-25: composite pass cutoff 65 -> 70, debt/capital skipped for financials. Still open: ACN is inflated for cyclical growers (energy, REITs with 30% growth).

## Session 5 (2026-10-22)
- User added reference material under `docs/reference/` (gitignored): `2026-10/` holds the monthly drops (Morningstar large and mid cap pick lists, Argus Top 30, `drip_ccc.csv`, `ccc_list.csv`) and `samples/` holds the one-off Argus, CFRA, Morningstar and Fidelity files. Only the pick lists, Argus Top 30 and the DRIP export are tabular enough to use; the rest is commentary.
- Wrote `scripts/fetch_ccc.py` (Dividend Vision, 288 tickers), `src/div_invst/reference.py` (now the `reference/` package; loaders, `load_universe`, `conservative_streak`) and `scripts/compare_ccc.py` (report at `data/ccc_compare.md`).
- Findings: DRIP covers 684 stocks vs 288; DRIP 5-yr dividend growth matches our computed CAGR (median 0.3 points); DRIP's Chowder Number is just yield + 5-yr growth; DRIP and Dividend Vision disagree on 16 of 268 shared tickers' tiers (ABBV, ABT, MCD, GS, MS and others), handled by the conservative-streak rule (lower claim). yfinance streaks are wrong for PG, MCD, XOM, MO, ED.
- Reading PDFs: PyMuPDF sorted-text works for the Morningstar and Argus tables (now a project dependency). Poppler is not installed.
- Committed together with the doc updates.


## Session 4 (2026-10-21)
- Wrote and ran `scripts/revision_spike.py` (21 tickers): yfinance revision data covers 21/21 so criterion 13 becomes an automated StarMine-style proxy; Finnhub recommendations are 4 months only and price targets are gated. Output in `data/revision_out/` (gitignored). Store daily yfinance snapshots from the first cache run.
- Broker research (Fidelity, Schwab, Robinhood) has no API and logged-in scraping is brittle and against terms; decided to keep StarMine, Jefferson, Ford and Stewardship as manual override columns with occasional manual spot checks.
- Accepted default thresholds for every undefined item (see `ideas_v2.md` decisions log, 2026-10-21). Growth rates use point-to-point CAGRs.
- Committed everything (`1f6911f`); docs refreshed again afterward and a revision spike write-up added under `docs/research/`.


## Session 3 (2026-10-19)
- Lowered `requires-python` to >=3.12 and pinned `.python-version` to 3.13 (yfinance also works on 3.14).
- Wrote and ran the coverage spike: `scripts/coverage_spike.py` (21 tickers across staples, energy, tech, REITs, utilities, banks, pipelines). Keys are in `.env`, now gitignored (it was not before). Output goes to `data/spike_out/` (gitignored, cached so reruns cost no quota).
- Verdicts: Finnhub free is the primary history source (annual series back to 1985, works for all 21). FMP free is capped at 5 years and refuses some symbols, so dropped. Alpha Vantage is 25 calls/day, dropped. yfinance and EDGAR stay as backbone and cross-check. FRED works.
- Finnhub vs EDGAR spot-checks (`scripts/finnhub_vs_edgar.py`): JNJ, KO, NEE, O EPS and ROE match (Finnhub is split-adjusted and GAAP, not adjusted). Banks (JPM, USB) have no Finnhub annual EPS, so EDGAR is needed there.
- Fixed in the script: XOM's CIK (the SEC ticker map points at a successor entity with no history; override table added), the 52/53-week fiscal-year keying bug (JNJ), the dividend-streak payment-count bug (O 1 to 26), and EDGAR tag chains (every field now 8+ years for all 21 tickers except CVX dividends per share).
- Updated all docs: `PLAN.md`, `ideas_v2.md` (sources and decisions log), `data_sources.md`, both READMEs, this file.


## Findings carried from the early sessions

- Every rating-agency source in v1 is human-only, so they are proxies or manual columns (unchanged).
- Streak from yfinance is a screen only: JNJ, KO, CVX, NEE, MCD, CAT look right; XOM 53 (about 43), PG 42 (about 69), ED 44 (about 51) are wrong.
- Finnhub EPS is GAAP, so one-off years (JNJ 2017 and 2023, KO 2017) appear as spikes in the earnings 7-of-10 test.
- REITs: GAAP payout is 195-325%, so an FFO-based payout is required; no free FFO source found yet.
- EDGAR per-share history must be split-adjusted (NEE 2016-2017 differ by exactly 4x).
- The test universe was 21 large caps; small-cap coverage is untested.
