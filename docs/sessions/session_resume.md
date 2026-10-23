# Session Resume

_Last updated: 2026-10-22 (session 5)_

## How to resume
1. Read `../criteria/ideas_v2.md` (criteria table A-E, exit rules, decisions log).
2. Read `../research/coverage_spike_2026-10-19.md` (what data each source supplies, verdicts, caveats) and `../research/revision_spike_2026-10-21.md` (criterion 13 proxy inputs). `../research/data_sources.md` is the earlier 4-ticker draft; the spike doc wins where they differ.
3. Read `../plan/PLAN.md` (build phases). Then answer the open questions below and start phase 2.

## To check next session (2026-10-23)
1. Review the 16 DRIP vs Dividend Vision tier conflicts by hand (ABBV, ABT, ADC, AMCR, CAH, CSL, GRC, GS, HTO, MCD, MLM, MS, MSEX, MZTI, NC, PNR; list in `data/ccc_compare.md`, rerun `scripts/compare_ccc.py`). Until then the conservative (lower) streak is used.
2. Pick the 5-yr average yield source for exit rule 2: DRIP `5Y Avg Yield` vs yfinance `fiveYearAvgDividendYield` (DRIP runs about 0.2 points higher; MO 8.83% vs 7.42%).
3. Confirm Dividend Vision's terms of use allow one fetch a month.
4. User adds one more data source to `docs/reference/2026-10/`; review it the same way (what it is, columns, overlap with existing sources, which criteria it feeds).
5. After 1-4, review the plan (`../plan/PLAN.md`) and the build order.

## Session 5 summary (2026-10-22)
- User added reference material under `docs/reference/` (gitignored): `2026-10/` holds the monthly drops (Morningstar large and mid cap pick lists, Argus Top 30, `drip_ccc.csv`, `ccc_list.csv`) and `samples/` holds the one-off Argus, CFRA, Morningstar and Fidelity files. Only the pick lists, Argus Top 30 and the DRIP export are tabular enough to use; the rest is commentary.
- Wrote `scripts/fetch_ccc.py` (Dividend Vision, 288 tickers), `src/div_invst/reference.py` (loaders, `load_universe`, `conservative_streak`) and `scripts/compare_ccc.py` (report at `data/ccc_compare.md`).
- Findings: DRIP covers 684 stocks vs 288; DRIP 5-yr dividend growth matches our computed CAGR (median 0.3 points); DRIP's Chowder Number is just yield + 5-yr growth; DRIP and Dividend Vision disagree on 16 of 268 shared tickers' tiers (ABBV, ABT, MCD, GS, MS and others), handled by the conservative-streak rule (lower claim). yfinance streaks are wrong for PG, MCD, XOM, MO, ED.
- Reading PDFs: PyMuPDF sorted-text works for the Morningstar and Argus tables (run with `uv run --with pymupdf`; not yet a project dependency). Poppler is not installed.
- Committed together with the doc updates.

## Session 4 summary (2026-10-21)
- Wrote and ran `scripts/revision_spike.py` (21 tickers): yfinance revision data covers 21/21 so criterion 13 becomes an automated StarMine-style proxy; Finnhub recommendations are 4 months only and price targets are gated. Output in `data/revision_out/` (gitignored). Store daily yfinance snapshots from the first cache run.
- Broker research (Fidelity, Schwab, Robinhood) has no API and logged-in scraping is brittle and against terms; decided to keep StarMine, Jefferson, Ford and Stewardship as manual override columns with occasional manual spot checks.
- Accepted default thresholds for every undefined item (see `ideas_v2.md` decisions log, 2026-10-21). Growth rates use point-to-point CAGRs.
- Committed everything (`1f6911f`); docs refreshed again afterward and a revision spike write-up added under `docs/research/`.

## Session 3 summary (2026-10-19)
- Lowered `requires-python` to >=3.12 and pinned `.python-version` to 3.13 (yfinance also works on 3.14).
- Wrote and ran the coverage spike: `scripts/coverage_spike.py` (21 tickers across staples, energy, tech, REITs, utilities, banks, pipelines). Keys are in `.env`, now gitignored (it was not before). Output goes to `data/spike_out/` (gitignored, cached so reruns cost no quota).
- Verdicts: Finnhub free is the primary history source (annual series back to 1985, works for all 21). FMP free is capped at 5 years and refuses some symbols, so dropped. Alpha Vantage is 25 calls/day, dropped. yfinance and EDGAR stay as backbone and cross-check. FRED works.
- Finnhub vs EDGAR spot-checks (`scripts/finnhub_vs_edgar.py`): JNJ, KO, NEE, O EPS and ROE match (Finnhub is split-adjusted and GAAP, not adjusted). Banks (JPM, USB) have no Finnhub annual EPS, so EDGAR is needed there.
- Fixed in the script: XOM's CIK (the SEC ticker map points at a successor entity with no history; override table added), the 52/53-week fiscal-year keying bug (JNJ), the dividend-streak payment-count bug (O 1 to 26), and EDGAR tag chains (every field now 8+ years for all 21 tickers except CVX dividends per share).
- Updated all docs: `PLAN.md`, `ideas_v2.md` (sources and decisions log), `data_sources.md`, both READMEs, this file.

## Key findings
- Every rating-agency source in v1 is human-only, so they are proxies or manual columns (unchanged).
- Streak from yfinance is a screen only: JNJ, KO, CVX, NEE, MCD, CAT look right; XOM 53 (about 43), PG 42 (about 69), ED 44 (about 51) are wrong.
- Finnhub EPS is GAAP, so one-off years (JNJ 2017 and 2023, KO 2017) appear as spikes in the earnings 7-of-10 test.
- REITs: GAAP payout is 195-325%, so an FFO-based payout is required; no free FFO source found yet.
- EDGAR per-share history must be split-adjusted (NEE 2016-2017 differ by exactly 4x).
- The test universe was 21 large caps; small-cap coverage is untested.

## Open questions for the user
1. Holdings file layout (still to supply).
2. CCC list route: resolved 2026-10-22 (DRIP export + Dividend Vision, conservative streak). Still open: review the 16 DRIP/Dividend Vision tier conflicts by hand; decide the 5-yr average yield source for exit rule 2 (DRIP vs yfinance); confirm Dividend Vision's terms of use allow a monthly fetch.
3. What do you pull from dividendinvestor.com (403 to my fetch)?
4. Confirm proxies for credit quality and StarMine; manual columns for Stewardship, Jefferson, Ford (criteria 2, 3, 15 stay unknown unless filled).

Resolved 2026-10-21: all thresholds, one-off EPS handling, 15% exit margin, ADRs out of v1.

## Key decisions (full list in `ideas_v2.md`)
- Free data first; paid only if inadequate. Primary sources: yfinance, Finnhub, EDGAR, FRED.
- Universe: all US dividend payers, CCC flagged primary.
- Output: ranked entry list (top 50) + exit list showing which trigger fired. Held portfolio target is 30-40.
- Exit triggers: fair-value ceiling (+15%), yield <= 50% of 5-yr average, fundamental break.
- Equal-weighted pass/fail; coverage-aware ranking (70% min); ties broken by ACN.
- CLI + SQLite cache with run snapshots. Holdings: Excel/CSV, no cost basis.
- Data refreshes on a cadence (`data_sources.md` section 4) and feeds an enter/exit decision from threshold results.

## Repo state
- Code: `main.py` is a hello-world stub; `src/div_invst/reference.py` loads the monthly reference files; `scripts/fetch_ccc.py` and `scripts/compare_ccc.py` support them. `pyproject.toml` requires Python >=3.12, no dependencies yet. `scripts/` holds the three spike scripts (PEP 723, run with `uv run --python 3.13`).
- Docs: reorganized into `docs/` (criteria, research, plan, sessions); all updated this session.
- Git: all work is committed on `main` (not pushed). `.env`, `data/` and `docs/reference/` are ignored.

## Next steps (ordered)
1. User supplies the holdings layout and confirms the remaining open questions. Drop each month's files in `docs/reference/<YYYY-MM>/`.
2. Spike follow-ups: review the 16 CCC tier conflicts; find a REIT FFO source; test a few small caps; calibrate the criterion 13 proxy against a few Fidelity StarMine scores.
3. Build the data layer + SQLite cache with scheduled refresh (`src/div_invst/`): Finnhub series, EDGAR (CIK overrides, tag chains, split adjustment, bank path), yfinance (including daily revision snapshots), FRED.
4. Criteria engine + Financial Strength proxy + revision proxy + TOML config (thresholds from `ideas_v2.md`); enter/exit decision roll-up.
5. Holdings loader + diversification cut; fair value, ranking, entry and exit reports.
6. Tests and CLI.
