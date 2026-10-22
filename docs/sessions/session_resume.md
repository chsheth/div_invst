# Session Resume

_Last updated: 2026-10-21 (session 4)_

## How to resume
1. Read `../criteria/ideas_v2.md` (criteria table A-E, exit rules, decisions log).
2. Read `../research/coverage_spike_2026-10-19.md` (what data each source supplies, verdicts, caveats). `../research/data_sources.md` is the earlier 4-ticker draft; the spike doc wins where they differ.
3. Read `../plan/PLAN.md` (build phases). Then answer the open questions below and start phase 2.

## Session 4 summary (2026-10-21)
- Wrote and ran `scripts/revision_spike.py` (21 tickers): yfinance revision data covers 21/21 so criterion 13 becomes an automated StarMine-style proxy; Finnhub recommendations are 4 months only and price targets are gated. Output in `data/revision_out/` (gitignored). Store daily yfinance snapshots from the first cache run.
- Broker research (Fidelity, Schwab, Robinhood) has no API and logged-in scraping is brittle and against terms; decided to keep StarMine, Jefferson, Ford and Stewardship as manual override columns with occasional manual spot checks.
- Accepted default thresholds for every undefined item (see `ideas_v2.md` decisions log, 2026-10-21).

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
2. CCC list route: recommended is computing streaks from yfinance history with Dividend Vision as the cross-check.
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
- Code: `main.py` is a hello-world stub. `pyproject.toml` requires Python >=3.12, no dependencies yet. `scripts/` holds the two spike scripts (PEP 723, run with `uv run --python 3.13`).
- Docs: reorganized into `docs/` (criteria, research, plan, sessions); all updated this session.
- Git: one commit from session 1. Everything since is uncommitted (docs reorganization, `scripts/`, `.gitignore`, Python version, `uv.lock`). `.env` and `data/` are ignored.

## Next steps (ordered)
1. User supplies the holdings layout and confirms the remaining open questions.
2. Spike follow-ups: Dividend Vision streak cross-check; find a REIT FFO source; test a few small caps; calibrate the criterion 13 proxy against a few Fidelity StarMine scores.
3. Build the data layer + SQLite cache with scheduled refresh (`src/div_invst/`): Finnhub series, EDGAR (CIK overrides, tag chains, split adjustment, bank path), yfinance (including daily revision snapshots), FRED.
4. Criteria engine + Financial Strength proxy + revision proxy + TOML config (thresholds from `ideas_v2.md`); enter/exit decision roll-up.
5. Holdings loader + diversification cut; fair value, ranking, entry and exit reports.
6. Tests and CLI.
