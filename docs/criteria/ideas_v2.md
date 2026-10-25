# div-invst: Ideas and Criteria (v2)

Structured version of `ideas_v1.md` (the original notes, same folder).
Single source of truth for criteria and decisions. Related: `../plan/PLAN.md` (build plan), `../research/data_sources.md` (source research), `../sessions/session_resume.md` (where we left off), `../../README.md` (overview).

## Goal
Aggregate dividend stock data and history, apply the criteria below, and produce:
1. A ranked **entry list** (what to buy), with per-criterion pass/fail.
2. An **exit list** for current holdings (what to sell/review), showing which trigger fired.

Main interest: dividend Aristocrats, Champions, Contenders (CCC), but all US dividend payers are screened so
matches outside the CCC lists are not missed.

## Universe
- US-listed dividend-paying stocks. CCC flagged as primary tier. ADRs/foreign out of scope for v1.
- CCC universe and tier come from the monthly DRIP "All CCC" export (684 stocks, 2026-10), merged with Dividend Vision (288) for streak years. Both files are manual or semi-manual monthly inputs in `docs/reference/<YYYY-MM>/` (see Monthly reference inputs below).
- Start with the CCC lists, then widen to all US dividend payers.

## Criteria
Each criterion: pass / fail / unknown. All are equal-weighted pass/fail filters (weights configurable later).
Stocks are ranked on available data; coverage count is shown; below ~70% coverage a stock is not ranked. Ties are broken by ACN (criterion 6), highest first.
Criteria come from the original notes (v1 criteria 1-8) and the SBI list; overlapping items are merged into one row.

| # | Criterion | Threshold | Planned free data source | Feasibility |
|---|-----------|-----------|--------------------------|-------------|
| **A** | **Financial strength** | | | |
| 1 | Credit quality and balance sheet | Ratings: Morningstar BBB+, Value Line 1 or 2 (B+), S&P BBB+ / S&P CIQ quality B+ or better. Low debt: debt/market cap < 50% OR cash flow after tax >= 3x interest. Strong cash flow: earnings growth 5-10%, payout <= 60% (REIT/utility/MLP exempt) | Computed Financial Strength proxy score (below) covers debt, coverage and payout; optional manual rating column | Medium |
| 2 | Management quality | Morningstar Stewardship | Manual column only | Low |
| 3 | Jefferson Research quality grades | Balance Sheet, Cash Flow Quality, Earnings Quality = strongest; Operating Efficiency = strong; Valuation = low risk | Manual column; proxy score components approximate it | Low |
| **B** | **Income and dividend growth** | | | |
| 4 | High current yield | 1.5 to 2.5 times the S&P yield; above 2.5x passes with a "yield trap?" flag | yfinance yield; SPY yield as the S&P proxy | High |
| 5 | Chowder rule | Yield >= 50% of SPY yield; yield + 5y div CAGR >= 12% (most stocks, yield >= 3%), 15% (tech/growth, yield < 3%), 8% (utilities/telecom). Growth component must be at least inflation + margin of safety | yfinance dividends and price; CAGR computed | High |
| 6 | Adjusted Chowder Number (ACN) | ACN >= the same sector tier as criterion 5 (12% / 15% / 8%, Chowder tiers used as-is). Formula: ACN = min(10%, Y) + min(30%, average(min(D,E,R), median(D,E,R))); Y = forward dividend yield, D/E/R = 5-yr dividend / earnings / revenue growth rate. Also the ranking tiebreaker | Forward yield from yfinance; 5-yr growth from Finnhub annual series (EDGAR for banks, split-adjusted) | Medium |
| 7 | Rising dividends / earnings | Dividend up 5+ yrs; earnings up 7 of last 10 yrs | CCC dividend streak from the monthly lists using the conservative rule (decisions log 2026-10-22); non-CCC streak computed from yfinance history as a screen only; EPS history from Finnhub annual series (EDGAR for banks). Finnhub EPS is GAAP; an EPS year that swings more than 40% from both neighbors is flagged and counts as an up year only if the following year recovers | Medium |
| **C** | **Valuation** | | | |
| 8 | Discount to fair value | >= 15% below fair value | Own estimate: DDM and PE-vs-historical-PE, take the lower | Medium |
| 9 | Valuation multiples | P/S < 1.5; P/E below its own 10-yr average and earnings yield (1/PE) above the 10-yr Treasury yield (low P/E is read as lower volatility); P/B <= 3 and below the market's P/B; price/cash: market cap / cash under 20 or cash >= 5% of market cap (skipped for banks and insurers) | yfinance; Finnhub annual P/E, P/B, P/S history; 10-yr Treasury from FRED | High |
| **D** | **Fundamentals and momentum** | | | |
| 10 | Better fundamentals | PE vs historical PE; ROE and ROIC rising (3-yr average above the prior 3-yr average, or latest >= 90% of the 10-yr high); next-year consensus EPS growth >= 3% or inflation (FRED CPI) if higher | Finnhub annual series (ROE, ROIC, PE history), yfinance estimates; SEC EDGAR cross-check | Medium |
| 11 | Cash growth | Cash and equivalents growing YoY | Statements (yfinance 4 yrs; EDGAR longer) | High |
| 12 | Insider buying | At least 2 open-market purchases by different insiders in the last 6 months, and net buying above net selling (option exercises, grants and tax-withholding sales excluded) | yfinance or Finnhub insider transactions (EDGAR Form 4 not needed); screener Net Insider Shares Bought shows buying only (no sells) | Medium |
| 13 | Beat market next 6-12 months | Fidelity StarMine 7+ is the original target; the screener's StarMine Equity Summary Score (5 levels) is the primary input, the revision proxy (0-10, pass at 7+) the second signal | Screener StarMine ESS + Zacks; revision proxy from yfinance (eps_trend, eps_revisions, upgrades_downgrades, price targets) and Finnhub recommendations; 21/21 coverage in the 2026-10-21 spike (`scripts/revision_spike.py`). Weights: 40% 90-day EPS revision, 20% up/down revision balance, 20% rating-change momentum, 10% recommendation trend, 10% price-target upside; calibrate against 4-6 hand-looked-up Fidelity StarMine scores. Manual column fallback | Medium |
| **E** | **Portfolio and manual checks** | | | |
| 14 | Diversification cut | Drop candidates already owned; optional sector-share cap | Sector from yfinance vs holdings file | High |
| 15 | Accuracy calls | Jefferson Research, Ford Equity Research agree | Manual yes/no on finalists; drop if not workable | Low |

Target portfolio size is 30-40 stocks. This is a constraint, not a scored criterion: the report ranks the top 50 entries as a candidate pool, and the 30-40 held portfolio is built from it, with criterion 14 applied against it.

### Financial Strength proxy score (criterion 1)
0-100, tiers A >= 80, B 65-79, C 50-64, D < 50. Shown as "proxy tier", never as a named rating.
Pass cutoff: tier B or better (65+).
Weights: debt/market cap < 50% (20), interest coverage >= 3x (20), debt/EBITDA sector-adjusted (15), payout <= 60% earnings/FCF based with REIT/utility/MLP exempt (20), FCF positive 5 yrs (10), Altman Z (10), cash growing YoY (5).
Banks/insurers scored separately; REITs use FFO payout + net debt/EBITDA. Missing components skipped and re-weighted. Validate on ~20 known tickers vs public S&P ratings.

### Monthly reference inputs
Dropped by hand into `docs/reference/<YYYY-MM>/` (gitignored; loaders in `src/div_invst/reference/` read the newest folder, falling back to the latest earlier month and marking data stale):
- `drip_ccc.csv`: DRIP Investing "All CCC" export (emailed). Primary CCC universe and tier (Stock Type = streak band: Challenger 5-9, Contender 10-24, Champion 25-49, King 50+). Also carries 5Y Avg Yield (candidate source for exit rule 2), DGR 1/3/5/10Y, Chowder Number (equals yield + DGR 5Y, so not an independent check), Peter Lynch fair value, ROE, Debt/Capital, P/E, P/BV, PEG.
- `ccc_list.csv`: Dividend Vision lists via `scripts/fetch_ccc.py` (kings, aristocrats, champions, contenders, challengers). Gives streak years. Yield, price and P/E in it are stale snapshots and are not used.
- `morningstar_large_cap.pdf`, `morningstar_mid_cap.pdf`: Morningstar pick lists (fair value, rating, moat, uncertainty). Optional cross-check for criterion 8 and manual columns for criteria 2 and 3. Names are picks only, so absence says nothing.
- `argus_top30.pdf`: Argus Top 30 (Financial Strength grade, yield, PE) and stock screen. Optional cross-check for criterion 1.
- `screener_results.xlsx`: Fidelity stock screener export, merged from yield-band downloads (see "Fidelity screener" below).
- `ratings.csv`: optional per-stock ratings (`as_of, ticker, source, rating, target_price`).
PDFs are read with PyMuPDF sorted-text extraction (its table finder splits decimals); PyMuPDF is now a project dependency. Loaders: `src/div_invst/reference/` (`ccc.py`, `morningstar.py`, `argus.py`, shared `common.py`). The Morningstar loader also reads the "Pick List Deletions" table (status `deleted`, a possible exit signal). The Argus loader reads the Top 30 table (Financial Strength grade) and the Stock Screen table. Screener loader not written yet. Month steps: `../guides/monthly_drop.md`.

### Fidelity screener (`screener_results.xlsx`, reviewed 2026-10-25, second download)
Column-by-column reference (units, fill rates, parsing rules, open checks): `../research/fidelity_screener.md`.
Seven yield-band downloads (0.07% and up; Fidelity caps an export at 500 rows) merged by tab with `scripts/merge_screener.py`: 2,883 stocks (1,764 common, 124 REIT, 60 unit trusts, 935 ADRs). 681 of the 684 DRIP CCC names are in it (XOM, CABO and TGLS are missing; XOM at 2.44% should be there, so Fidelity omitted it). Filter ADRs and tiny names in our code (Security Type, HQ country, market cap), not in Fidelity: fields used as Fidelity filters drop every stock with a blank value.
Five tabs (Search Criteria 62 columns, Basic Facts, Performance & Volatility, Valuation Growth & Ownership, Analyst Opinions), joined on `Symbol`. The full column list, units and parsing rules are in `../research/fidelity_screener.md`; this section only maps the fields to criteria.

Fill rates below are all stocks / DRIP CCC names.

| Criterion | What the screener adds | Verdict |
|-----------|------------------------|---------|
| 13 Beat market | StarMine ESS (5 levels) + 1-month change (47% / 92%), I/B/E/S mean, Zacks (OUTPERFORM / NEUTRAL / UNDERPERFORM, 71% / 93%) | Fills the gap with the real StarMine product; pass line on the 5 levels to define (suggest Bullish or better, or Neutral with a rising change); keep the yfinance revision score as a second signal and Zacks as a tiebreak |
| 1 Credit and balance sheet | Interest coverage (55% / 74%), debt to capital (74% / 99%), current ratio (47% / 65%), debt/equity, payout, FCF, S&P Financial Health and Quality scores | Mostly covered now. Debt/market cap = (D/E) / (P/B) when both positive. No 5-yr FCF history (cash flow growth 5-yr is a partial stand-in). Check S&P score direction and scale on known tickers first (KO Quality 45, NEE 31 look odd) |
| 5 Chowder | Yield + 5-yr dividend growth | Cross-check; 64% within 1 point of DRIP's DGR 5Y, median gap 0.5 |
| 6 ACN | D from 5-yr dividend growth, E from EPS growth 5-yr history (59% / 90%), R from revenue growth 5 yrs (75% / 100%) | All three terms now in the file for most CCC names. Fidelity's growth definition (annualised vs point-to-point) is unchecked, so compare with Finnhub CAGRs on a sample before replacing them |
| 9 Multiples | Current P/S, P/B, price/cash flow, P/E, cash (market cap / cash computable) | Current values only; 10-yr average P/E, market P/B and Treasury yield still external |
| 10 Fundamentals | Return on investment (70% / 98%), operating margin 5-yr average and TTM vs 5-yr, EPS growth projected next year vs this year | Next-year consensus growth test is direct. ROI approximates ROIC but only as a current value; the TTM vs 5-yr margin ratio gives a direction. The earlier implied growth from P/E is no longer needed |
| 12 Insider buying | Net Insider Shares Bought (62% / 97%) | Partial. The column has no negative values and no stated period, so it shows buying only; net buying above selling and the 2+ buyers test cannot be checked. Confirm the definition on Fidelity before use |
| 3 Jefferson grades | SG&A / net sales (55% / 79%), operating margin (73% / 100%), profit margin, Jefferson Research Buy/Hold/Sell | SG&A and margins are a proxy for Operating Efficiency; the Balance Sheet, Cash Flow Quality and Earnings Quality grades still have no source. Jefferson Buy/Hold/Sell stays a manual input for 15 |
| 2 Management | MSCI Governance (Leader/Average/Laggard) | Weak stand-in; informational column only |
| 14 Diversification | Sector and industry | Usable; map labels to yfinance sectors |
| 11 Cash growth | Cash flow growth (3 and 5 yr, TTM), single-point total cash | Partial: cash flow, not cash and equivalents |
| 8, 7 | Nothing usable (no fair value, no dividend streak) | Unchanged |
| Exit rules | Dividend growth vs prior year (0 or negative = freeze or cut), payout, coverage, interest coverage | Helps rule 3; rule 2 still needs a 5-yr average yield |

Other columns (shares outstanding, 3/5/10-yr beta, return and standard deviation, Argus 14% filled, McLean, Trading Central) are informational. Caveats: hand-downloaded monthly snapshot; cash and FCF look like $ millions and debt/equity like a percent (unconfirmed); Net Insider Shares Bought units unknown; 935 ADRs and microcaps in the file need filtering.

## Exit rules
The exit report shows which trigger fired for each holding, plus current price, target sell price, % upside.
1. **Fair-value ceiling:** price > fair value + 15%.
2. **Yield compression:** current yield <= 50% of 5-yr average yield.
3. **Fundamental break ("review now"):** dividend cut or freeze, payout ratio over limit, falling earnings.

## Inputs
- Holdings file: Excel or CSV (user is assembling it). Ticker required, shares optional, no cost basis.
- No holdings file: entry list runs with the diversification cut skipped; exit report skipped.

## Data sources
Detailed research with tested/blocked status per source and per data element: `../research/data_sources.md` (2026-10-18). Coverage spike results and the updated per-criterion sources: `../research/coverage_spike_2026-10-19.md`. Build-plan list: `../plan/PLAN.md` ("Resources / websites used").
Free first, as settled by the 2026-10-19 spike: yfinance (prices, yield, dividends, analyst, insider), Finnhub free (annual history back to 1985), SEC EDGAR (cross-check, banks' EPS), FRED (10-yr Treasury, CPI). CCC streaks computed from yfinance dividend history, cross-checked against Dividend Vision. FMP and Alpha Vantage dropped (free tiers too shallow or too small).
Manual references: Seeking Alpha, Dividend.com, Fidelity, Value Line, Morningstar, S&P Capital IQ, dividendinvestor.com, TD Ameritrade

### Original source recommendations and free alternatives
| Criterion | Original source (ideas_v1) | Free alternative |
|-----------|----------------------------|------------------|
| Credit quality | Morningstar, Value Line (Austin public library), S&P Capital IQ (TD Ameritrade) | Computed Financial Strength proxy score from yfinance/Finnhub/EDGAR; optional manual rating column filled from the library or broker |
| Management quality | Morningstar Stewardship | Manual column only; no free equivalent |
| Beat market 6-12 months | Fidelity StarMine 0-10 | Analyst consensus, price-target upside, estimate revisions (yfinance/Finnhub); manual StarMine column from Fidelity if available |
| Discount to fair value | S&P Capital IQ, Morningstar fair value (TD Ameritrade, library) | Own DDM and PE-vs-historical-PE estimate, lower of the two |
| Current yield | Morningstar | yfinance dividends and price |
| 5-yr dividend CAGR | dividendinvestor.com | Computed from yfinance dividend history |
| Rising dividend / earnings strings | dividendinvestor.com | Dividend Radar / DRIP Investing CCC lists for dividend streak; EPS history from Finnhub annual series (EDGAR for banks) |
| PE vs historical PE, ROE, ROIC, earnings growth | Not specified | Finnhub annual series, yfinance, SEC EDGAR XBRL |
| Accuracy calls | Jefferson Research, Ford Equity Research via fidelity.com | Manual yes/no on finalists; drop if not workable |
| Jefferson quality grades (SBI) | Jefferson Research | Covered by the proxy score components; manual column for the actual grades |
| Insider buying | Not specified | SEC EDGAR Form 4 |
| Bond rate for P/E test | Not specified | FRED / Treasury |
| Dividend Aristocrat lists | Seeking Alpha | Dividend Radar / DRIP Investing CCC lists |

## Decisions log
- 2026-10-18: Data source research done (see `../research/data_sources.md`). Rating-agency sources in v1 are not programmatic; user decisions on proxies vs manual columns pending.
- 2026-10-13: Free data sources first; paid only if inadequate.
- 2026-10-13: Universe = all US dividend payers, CCC flagged as primary.
- 2026-10-13: Output = ranked entry list + exit list; 3 exit triggers approved; report shows which fired.
- 2026-10-13: Holdings via Excel/CSV, no cost basis.
- 2026-10-13: CLI + SQLite cache with run snapshots; coverage-aware scoring (70% min); equal-weighted criteria; top 50 entries.
- 2026-10-13: Crit 1 = proxy score + manual override; Crit 3 = analyst proxy w/ manual fallback; Crit 8 = manual on finalists.
- 2026-10-13: Fair value = lower of DDM and PE-vs-historical-PE; entry >= 15% discount; exit margin +15%.
- 2026-10-13: Python version may be lowered to 3.12/3.13 if libs lack 3.14 support.
- 2026-10-19: Python requirement lowered to >=3.12, pinned to 3.13 (yfinance also works on 3.14).
- 2026-10-18: Criteria merged into one grouped table (15 criteria, A-E). ACN = Adjusted Chowder Number: pass/fail on the Chowder sector tiers, also the ranking tiebreaker. SBI overlaps merged (ratings, low debt and payout into criterion 1).
- 2026-10-13: `ideas_v1.md` kept as untouched original; structured version lives in `ideas_v2.md`.
- 2026-10-19: Coverage spike run on 21 tickers (results in `../research/coverage_spike_2026-10-19.md`). Finnhub free is the primary source for multi-year history (matches EDGAR for JNJ, KO, NEE, O); FMP (5-year cap, partial symbols) and Alpha Vantage (25 calls/day) dropped; EDGAR kept for cross-checks and for banks (no Finnhub annual EPS for JPM, USB).
- 2026-10-19: EDGAR rules: CIK override table (XOM maps to a successor entity with no history), extended tag fallback chains (8+ years for all fields on the 21 tickers except CVX dividends per share), fiscal years ending Jan 1-7 count as the prior year, EDGAR per-share history must be split-adjusted (Finnhub already is).
- 2026-10-19: Dividend streak computed from yfinance with ambiguous payment-count years bridged; treated as a screen only. Residual errors seen (XOM 53 vs about 43, PG 42 vs about 69, ED 44 vs about 51), so cross-check against Dividend Vision.
- 2026-10-21: Revision spike on 21 tickers (`scripts/revision_spike.py`): yfinance eps_trend, eps_revisions, price targets, earnings history and dated upgrades/downgrades (back to about 2012) cover 21/21; Finnhub recommendations only 4 months on free tier, price targets gated. yfinance revision data is point-in-time, so daily snapshots should be stored from the first cache run.
- 2026-10-21: Thresholds accepted: yield 1.5-2.5x S&P with a yield-trap flag above 2.5x; P/B <= 3 and below market; price/cash market cap/cash < 20 or cash >= 5% of cap; P/E below own 10-yr average and earnings yield above 10-yr Treasury; estimated growth >= 3% or inflation; ROE/ROIC rising = 3-yr average above prior 3-yr; insider buying = 2+ open-market buys by different insiders in 6 months with net buying; proxy pass cutoff tier B (65+); criterion 13 proxy 0-10, pass at 7+, weights 40/20/20/10/10; ACN uses Chowder tiers as-is; one-off EPS years flagged (40% swing vs both neighbors, counts as up year only if next year recovers); 15% exit margin kept; ADRs out of v1; 70% min coverage.
- 2026-10-21: Growth rates (D, E, R and the 5-yr dividend CAGR) are point-to-point CAGRs over 5 years. Zero or negative start values make a growth rate unknown for that term (ACN then uses the remaining terms); a dividend cut and restore lowers D by design.
- 2026-10-22: DRIP "All CCC" export added (684 stocks) and Dividend Vision fetch script written (288 stocks). DRIP is the primary universe; Dividend Vision adds streak years. Comparison (`scripts/compare_ccc.py`): DRIP 5-yr dividend growth matches our computed CAGR (median gap 0.3 points over 19 tickers), so we keep computing ours and use DRIP as a cross-check; DRIP 5Y avg yield runs 0.2 points above yfinance's (median) with larger gaps for some (MO 8.83% vs 7.42%).
- 2026-10-22: Conservative streak rule. When the sources cannot be reconciled, use the lower claim: Dividend Vision streak inside the DRIP type band is verified and used; outside the band, the lower of the two (the band's top when Dividend Vision is higher, else the Dividend Vision streak); not on Dividend Vision, the bottom of the band; not on DRIP, the Dividend Vision streak unchecked. Result for 2026-10: 252 verified, 16 conflicts (ABBV, ABT, MCD, GS, MS and others, to review by hand), 416 band only, 20 Dividend Vision only. yfinance-computed streaks are wrong for PG, MCD, XOM, MO and ED, so they are not used for CCC names.
- 2026-10-25: Fidelity screener export added (first download: four yield-band files merged into `screener_results.xlsx`; footer rows dropped, JCSE de-duplicated). StarMine ESS becomes the primary input for criterion 13; S&P Financial Health and Quality scores become candidate inputs for criterion 1 pending calibration; other mappings in "Fidelity screener". User is adding the 1-2.25% yield band.
- 2026-10-25: Second Fidelity download replaces the first: seven yield bands (0.07% and up), 62 Search Criteria columns, 2,883 stocks; merged with `scripts/merge_screener.py`, which now prints each band and stops if a file is a copy of another. The new fields cover interest coverage and debt to capital (criterion 1), 5-yr EPS and revenue growth (ACN terms E and R), next-year EPS growth and ROI (10), SG&A and margins (3 proxy) and insider buying (12, partial). The file is saved monthly in the month folder like `drip_ccc.csv`. Filter ADRs in code, not in the Fidelity screen.
- 2026-10-19: API keys (FMP, Finnhub, Alpha Vantage) and `EDGAR_USER_AGENT` live in `.env` (gitignored).

## Open questions
Data-source questions raised on 2026-10-18 are listed in `../research/data_sources.md` section 5 (blocked sources, CCC list route, API keys, undefined thresholds).
- Which free sources truly cover each criterion: resolved by the 2026-10-19 spike, except a REIT FFO source (not found) and smaller-cap coverage (spike used 21 large caps).
- Exact holdings file layout (user to supply).
- Criterion 13 proxy weights need calibration against a few Fidelity StarMine scores looked up by hand.
- Open spike items: REIT FFO source, small-cap coverage. The Dividend Vision streak cross-check is done (2026-10-22): 16 DRIP/Dividend Vision conflicts remain, settled conservatively and worth a manual look.
- Fidelity screener: pass line for the StarMine ESS levels; S&P score direction and scale (calibrate on known tickers); units of cash, FCF and debt/equity; Net Insider Shares Bought definition (period, units, sells); Fidelity growth-rate definition vs Finnhub CAGRs; why XOM is missing.
- Exit rule 2 needs one 5-yr average yield source: DRIP `5Y Avg Yield` (monthly, stated) vs yfinance `fiveYearAvgDividendYield` (differs). Undecided.
