# div-invst: Plan (v1)

## Context
Build a tool that aggregates dividend stock data/history, screens it against the user's criteria (ideas_v1.md original, ideas_v2.md structured), and outputs (a) a ranked entry list with per-criterion pass/fail and (b) an exit list for current holdings showing which sell trigger fired. Repo is a bare `uv` Python skeleton (main.py hello world, empty README, pyproject requires-python >=3.14, no commits). Step 1 is capturing decisions in docs; step 2 is the build.

## Decisions (all confirmed)
**Data / universe**
- Free sources first; evaluate adequacy, then consider paid.
- Universe: ALL dividend payers. Aristocrats/Champions/Contenders (CCC) flagged as primary tier; others included so matches outside CCC are not missed.
- CCC lists: Dividend Radar (free weekly xlsx) or DRIP Investing Champions xlsx (free personal use). URLs/formats to verify in spike.

**Inputs**
- Holdings file: Excel or CSV, user is assembling it. Ticker required; shares optional. No cost basis (no tax logic).

- No holdings file: tool still runs. Entry list is produced with the diversification cut skipped (flagged "no holdings loaded"); exit report is skipped. Holdings file is only needed for criterion 2 and exit triggers.
- Universe scope: US-listed dividend-paying stocks (start with the CCC lists, then widen to all US dividend payers). ADRs/foreign listings out of scope for v1 unless the user says otherwise.

**Run mode**
- On-demand CLI writing CSV/Markdown reports. SQLite cache that also stores run snapshots from day one ("what changed since last run").

**Scoring**
- All criteria are equal-weighted pass/fail; weights configurable later.
- Missing data: score on available criteria, show coverage count; configurable min coverage (~70%) below which a stock is not ranked.
- Entry list: top 50 ranked.

**Diversification (criterion 2)**
- Exclude candidates already owned; optional configurable sector-share threshold.

**Fair value / benchmarks**
- Own fair-value estimate (DDM and PE-vs-historical-PE); use the lower (conservative) value.
- Entry: price >= 15% below fair value. Chowder yield rule uses live SPY yield. 10-yr Treasury yield pulled from a free source for the P/E-vs-bond rule.

**Exit rules (report shows which trigger fired per holding)**
1. Fair-value ceiling: price > fair value + 15%.
2. Yield compression: yield <= 50% of 5-yr average yield.
3. Fundamental break (flag "review now"): dividend cut/freeze, payout ratio over limit, falling earnings.
Per holding: current price, target sell price, % upside, trigger(s) fired.

**Paywalled criteria**
- Crit 1 credit ratings: computed Financial Strength proxy score + optional manual rating column override.
- Crit 3 StarMine: analyst-consensus/price-target/estimate-revision proxy (labeled as proxy); fall back to manual column.
- Crit 8 accuracy calls: manual yes/no check on finalists; drop if not workable.

**Tech**
- Lower Python requirement to 3.12/3.13 if data libs lack 3.14 wheels.

## Criteria data map (draft; verify in spike)
| # | Criterion | Free source candidate | Confidence |
|---|-----------|-----------------------|------------|
| Universe | CCC lists + streak years | Dividend Radar / DRIP Investing xlsx | High |
| 1 | Credit ratings | Proxy score (below) from statements | Medium |
| 2 | Diversification | Sector from yfinance vs holdings | High |
| 3 | StarMine 7+ | Analyst consensus proxy (yfinance) | Low |
| 4 | Discount to fair value | Own DDM / PE-vs-hist-PE | Medium |
| 5 | Chowder rule | yield + dividend history CAGR | High |
| 6 | Rising dividend 5+ yrs; earnings 7 of 10 | Streak from CCC/dividend history; EPS history needs FMP/EDGAR for 10 yrs | Medium |
| 7 | PE vs hist PE, ROE, ROIC trend, est. growth | yfinance (4-5 yrs) / FMP free (250 calls/day) / SEC EDGAR XBRL | Medium |
| 8 | Accuracy calls | Manual flag | Low |
| SBI | debt/mkt cap <50% or 3:1 coverage, payout <=60%, P/S, P/B, cash growth | statements + info | High/Med |
| SBI | insider buying | SEC EDGAR Form 4 (free, EdgarTools) | Medium |
| ACN | min(10%,Y)+min(30%,avg(min(D,E,R),median(D,E,R))) | 5-yr growth from statements + yield | Medium |

## Resources / websites used (status: V = seen in search, U = unverified until spike)
- Dividend Radar (FerdiS / Portfolio Insight) - weekly CCC xlsx, free (V, file URL U)
- DRIP Investing Resource Center, dripinvesting.org "U.S. Dividend Champions" xlsx, free personal use (V, URL U)
- Yahoo Finance via `yfinance` Python lib - prices, dividends, statements, info, sector, analyst data (U: field coverage and rate limits)
- Financial Modeling Prep (FMP) free tier - 250 calls/day, EOD; for longer statement history (V quota, U which endpoints are free)
- SEC EDGAR (data.sec.gov) - XBRL financials + Form 4 insider filings, free, no key, requires User-Agent header; `edgartools` lib (V)
- FRED (St. Louis Fed) or Treasury.gov - 10-yr Treasury yield, free (U: needs API key for FRED)
- SPY yield - from yfinance
- Seeking Alpha (seekingalpha.com) - Dividend Scorecard/grades, ratings, Champions articles. Mostly paywalled, no free official API, scraping restricted by ToS -> MANUAL reference or optional paid/RapidAPI later (U)
- Dividend.com - DARS rating, yield/streak data. No free API; scraping restricted by ToS -> MANUAL cross-check (U)
- Candidate extra free APIs (all U, evaluate in spike): Finnhub (free tier: basic financials, recommendation trends, price targets, insider transactions), Alpha Vantage (free, ~25 calls/day), Tiingo (free tier, dividends + prices), Nasdaq.com dividend-history endpoints (unofficial), Stooq (free price CSV), OpenBB / FinanceToolkit libraries (aggregators over Yahoo/FMP), Digrin / StockAnalysis.com / Macrotrends / Finviz (view-only cross-checks; scraping ToS restricted)
- Manual-lookup references (not automated): Fidelity (StarMine, Jefferson/Ford), Value Line (Austin library), Morningstar, S&P Capital IQ, dividendinvestor.com (for cross-checking streaks/CAGR)

## Financial Strength Score (proxy for criterion 1)
0-100; tier A>=80, B 65-79, C 50-64, D<50; shown as "proxy tier", never a named rating.
Weights: debt/mkt cap <50% (20), interest coverage >=3x (20), debt/EBITDA sector-adjusted (15), payout <=60% earnings+FCF based with REIT/utility/MLP exempt (20), FCF positive 5 yrs (10), Altman Z (10), cash growing YoY (5).
Banks/insurers scored separately; REITs use FFO payout + net debt/EBITDA. Missing components skipped and re-weighted, coverage shown. Validate on ~20 known tickers vs public S&P ratings.

## Docs to create (separate from CLAUDE.md) - first action after plan approval
1. `PLAN.md` (repo root): copy of this plan; kept current.
2. `ideas_v2.md` (new; `ideas_v1.md` stays untouched): numbered criteria (threshold, data source, feasibility), exit rules, scoring, universe, decisions log, open questions.
3. `README.md`: overview, quick start (uv run), inputs, outputs, layout, status.
4. `session_resume.md`: overwritten each session: summary, decisions, repo state, ordered next steps, open questions, how to resume.
Rule: decisions live in ideas_v2.md; session_resume.md points to them and lists next steps; README stays high level.

## Build phases
1. Data spike (scratchpad script): per-criterion field coverage on ~20 tickers; fix criteria data map; confirm Python version and CCC file URLs.
2. Data layer + SQLite cache under `src/div_invst/`: universe, prices, dividends, statements, EDGAR insider.
3. Criteria engine: each criterion returns pass/fail/unknown + value; thresholds in TOML config. Include Financial Strength proxy.
4. Holdings loader (xlsx/csv) + diversification cut.
5. Fair-value + ranking + entry report; exit-trigger calculator + exit report.
6. Tests with fixture data; CLI in `main.py`.

## Verification
- Docs: four files exist; ideas_v2.md decisions log matches this list; session_resume.md has next steps.
- Build: run CLI on sample holdings; hand-check 3 known aristocrats (yield, Chowder, streak); unit tests per criterion; proxy-score ordering sanity check vs known ratings.
