# Session Resume

_Last updated: 2026-10-25 (session 6, ready to build)_

## How to resume
1. Read `../criteria/ideas_v2.md` (criteria table A-E, exit rules, decisions log).
2. Read `../research/coverage_spike_2026-10-19.md` (what data each source supplies, verdicts, caveats) and `../research/revision_spike_2026-10-21.md` (criterion 13 proxy inputs). `../research/data_sources.md` is the earlier 4-ticker draft; the spike doc wins where they differ.
3. Read `../research/fidelity_screener.md` (the Fidelity screener download: columns, units, open checks) and `../guides/monthly_drop.md` (the monthly steps).
4. Read `../plan/PLAN.md` (build phases). Then answer the open questions below and start phase 2.

## Pending decisions and checks (updated 2026-10-25)
Decided 2026-10-25 (see `ideas_v2.md` decisions log): StarMine pass rule, yfinance 5-yr average yield for exit rule 2, Finnhub for insider transactions, REIT FFO proxy, Morningstar deletions kept as info only, conservative streak rule kept, S&P scores informational only.
1. **Dividend Vision: dropped** (user decision 2026-10-25). Its scripts, loader, conservative streak rule and `ccc_list.csv` are removed; CCC streaks are DRIP bands.
2. **Holdings file layout:** the user has no holdings file yet.
3. **Criteria 2, 3, 15:** now proxies from a quality composite built from the screener (`ideas_v2.md` "Quality composite"); thresholds are defaults to calibrate once the screener loader exists. Stewardship, Jefferson grades and Ford have no direct source.
4. **Build:** criteria engine on the combined dataset, then the data layer; review the plan and build order.
5. The 16 DRIP/Dividend Vision tier conflicts are moot now that Dividend Vision is dropped.

## Session 6 summary (2026-10-25)
- Built the screener loader and the combined per-ticker dataset (`reference/screener.py`, `reference/dataset.py`, `scripts/build_dataset.py`): 2,908 tickers, 681 of 684 CCC names in the screener (CABO, TGLS, XOM missing), key CCC fields 73% to 100% filled. Writes `data/dataset/2026-10.csv`.
- Decisions and checks recorded in `ideas_v2.md` and `../research/fidelity_screener.md` section 7. Dividend Vision dropped; criteria 2, 3 and 15 get a collective quality composite from the screener.
- Fidelity screener: first download (four bands) replaced by a second (seven bands, 0.07% and up, 62 Search Criteria columns) merged to `docs/reference/2026-10/screener_results.xlsx` (2,883 stocks, 5 tabs) with `scripts/merge_screener.py` (now prints each band and rejects copies); reviewed against the criteria (see `ideas_v2.md` "Fidelity screener"). StarMine ESS fills criterion 13; S&P Financial Health and Quality scores are candidates for criterion 1 (calibrate first).
- `reference.py` became the `reference/` package; wrote the Morningstar and Argus PDF loaders (Morningstar also reads the Pick List Deletions table), `scripts/check_month.py`, and `docs/guides/monthly_drop.md` (the monthly steps). PyMuPDF is now a project dependency.
- Raw screener `.xls` files deleted after the merge; only `screener_results.xlsx` is kept.

## Session 5 summary (2026-10-22)
- User added reference material under `docs/reference/` (gitignored): `2026-10/` holds the monthly drops (Morningstar large and mid cap pick lists, Argus Top 30, `drip_ccc.csv`, `ccc_list.csv`) and `samples/` holds the one-off Argus, CFRA, Morningstar and Fidelity files. Only the pick lists, Argus Top 30 and the DRIP export are tabular enough to use; the rest is commentary.
- Wrote `scripts/fetch_ccc.py` (Dividend Vision, 288 tickers), `src/div_invst/reference.py` (now the `reference/` package; loaders, `load_universe`, `conservative_streak`) and `scripts/compare_ccc.py` (report at `data/ccc_compare.md`).
- Findings: DRIP covers 684 stocks vs 288; DRIP 5-yr dividend growth matches our computed CAGR (median 0.3 points); DRIP's Chowder Number is just yield + 5-yr growth; DRIP and Dividend Vision disagree on 16 of 268 shared tickers' tiers (ABBV, ABT, MCD, GS, MS and others), handled by the conservative-streak rule (lower claim). yfinance streaks are wrong for PG, MCD, XOM, MO, ED.
- Reading PDFs: PyMuPDF sorted-text works for the Morningstar and Argus tables (now a project dependency). Poppler is not installed.
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
See "Pending decisions and checks" above; it replaces the earlier list.

Resolved 2026-10-21: all thresholds, one-off EPS handling, 15% exit margin, ADRs out of v1.

## Key decisions (full list in `ideas_v2.md`)
- Free data first; paid only if inadequate. Primary sources: yfinance, Finnhub, EDGAR, FRED.
- Universe: all US dividend payers, CCC flagged primary.
- Output: ranked entry list (top 50) + exit list showing which trigger fired. Held portfolio target is 30-40.
- Exit triggers: fair-value ceiling (+15%), yield <= 50% of 5-yr average, fundamental break.
- Equal-weighted pass/fail; coverage-aware ranking (70% min); ties broken by ACN.
- Criterion 13 primary input is the Fidelity screener's StarMine Equity Summary Score; the revision proxy is the second signal.
- CLI + SQLite cache with run snapshots. Holdings: Excel/CSV, no cost basis.
- Data refreshes on a cadence (`data_sources.md` section 4) and feeds an enter/exit decision from threshold results.

## Repo state
- Code: `main.py` is a hello-world stub; `src/div_invst/reference/` (package: ccc, morningstar, argus, common) loads the monthly reference files; `scripts/merge_screener.py` and `scripts/check_month.py` handle the Fidelity screener merge and the folder check; `pyproject.toml` requires Python >=3.12, one dependency (pymupdf). `scripts/` also holds the spike scripts (PEP 723, run with `uv run --python 3.13`).
- Docs: `docs/` holds criteria, guides, research, plan, sessions; all updated 2026-10-25.
- Git: last commit is `ff88cd9` on `main` (not pushed); the session 6 work (reference package, screener merge, check script, guide, docs) is uncommitted. `.env`, `data/` and `docs/reference/` are ignored.

## Next steps (ordered)
1. Slice 1 (see `../plan/PLAN.md` "Build phases"): dataset and criteria engine are built (`scripts/run_screen.py` writes `data/reports/<month>/top50.md`); next is calibrating the quality composite on known tickers, then deciding the StarMine double count (13 and 15) and the ranking tie rule.
2. Slice 2: data layer + SQLite cache (yfinance, Finnhub, EDGAR, FRED) with run snapshots.
3. Slice 3: remaining criteria (Financial Strength proxy, fair value, earnings history, insider, revision proxy as second signal, REIT FFO proxy).
4. Slice 4: holdings loader (when the user has the file), diversification cut, exit report.
5. Tests and CLI. Each month: follow `../guides/monthly_drop.md`.

## Session 6 (continued)
Criteria engine built (9 criteria, ranking, report, tests); code review fixes applied (negative P/B, Morningstar None, bank interest coverage). Open: calibration, StarMine double count, ranking tie rule.
Calibration 2026-10-25: composite pass cutoff 65 -> 70, debt/capital skipped for financials. Still open: ACN is inflated for cyclical growers (energy, REITs with 30% growth).
Decided 2026-10-26: StarMine ESS only in criterion 13 (removed from 15's panel); rank key = passes / applicable, ties by ACN, yield, ticker. ACN growth capped at 15% (commit 7425882). Slice 1 is closed; next is Slice 2 (data layer + SQLite cache).
Revisit at Slice 3: the 70% minimum coverage (applicable criteria rise from 8 to about 14) and whether I/B/E/S should also leave criterion 15 (LSEG overlap with ESS).
Slice 2 started 2026-10-26: SQLite snapshot store, refresh with max ages, fetchers for yfinance, Finnhub and FRED, `scripts/refresh_data.py` (live-tested on JNJ and KO; second run fetched nothing). Next: EDGAR fetcher, then readers that feed the criteria (including the missing criteria of Slice 3). `.gitignore` now anchors `/data/` so `src/div_invst/data/` is tracked.
EDGAR fetcher built 2026-10-26 (`edgar` and `yf_splits` kinds, 7 and 30 day max ages) and live-checked on NEE, XOM, JNJ, O, JPM: 15 years of EPS and net income for all five; NEE 2016 EPS 6.24 restates to 1.56 with the split history; O's FFO proxy for 2025 is 3.41B (not yet validated against reported FFO for O and PLD). Gaps: operating income is missing for XOM, O, JPM and has only 4 years for JNJ (needs another tag or the Finnhub/yfinance fallback); property-sale gains are missing for non-REITs, as expected. The big eligible-pool fetch started before EDGAR, so rerun it with `--kinds edgar,yf_splits` when it finishes.
Readers built 2026-10-26 (`src/div_invst/data/readers.py`, 17 tests pass): `rec["cache"]` per ticker, FRED macro wired into `run_screen.py` (Treasury 5.00% and CPI 3.72% as of 2026-10-23; the top 50 did not change). JNJ checks: streak 63, 5-yr dividend CAGR 5.2%, forward yield 2.01%. Nothing reads `rec["cache"]` yet: next is Slice 3 (criteria 1, 7, 8, 10, 11, 12, revision proxy for 13, REIT FFO payout). Open: S&P yield still manual (add SPY to the fetch); EDGAR for the eligible pool needs the `--kinds edgar,yf_splits` rerun once the first fetch finishes.
