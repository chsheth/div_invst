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
| 4 | High current yield | 1.5 to 2 times the S&P yield | yfinance yield; SPY yield as the S&P proxy | High |
| 5 | Chowder rule | Yield >= 50% of SPY yield; yield + 5y div CAGR >= 12% (most stocks, yield >= 3%), 15% (tech/growth, yield < 3%), 8% (utilities/telecom). Growth component must be at least inflation + margin of safety | yfinance dividends and price; CAGR computed | High |
| 6 | Adjusted Chowder Number (ACN) | ACN >= the same sector tier as criterion 5 (12% / 15% / 8%). Formula: ACN = min(10%, Y) + min(30%, average(min(D,E,R), median(D,E,R))); Y = forward dividend yield, D/E/R = 5-yr dividend / earnings / revenue growth rate. Also the ranking tiebreaker | Forward yield from yfinance; 5-yr growth from Finnhub annual series (EDGAR for banks, split-adjusted) | Medium |
| 7 | Rising dividends / earnings | Dividend up 5+ yrs; earnings up 7 of last 10 yrs | Dividend streak computed from yfinance history (cross-check Dividend Vision); EPS history from Finnhub annual series (EDGAR for banks). Finnhub EPS is GAAP, so one-off years show as spikes | Medium |
| **C** | **Valuation** | | | |
| 8 | Discount to fair value | >= 15% below fair value | Own estimate: DDM and PE-vs-historical-PE, take the lower | Medium |
| 9 | Valuation multiples | P/S < 1.5; low P/E (below average and below reciprocal of bond rate; low P/E is read as lower volatility); P/B lower than the market and close to 1; low price/cash | yfinance; Finnhub annual P/E, P/B, P/S history; 10-yr Treasury from FRED | High |
| **D** | **Fundamentals and momentum** | | | |
| 10 | Better fundamentals | PE vs historical PE, ROE rising, ROIC rising, est. earnings growth | Finnhub annual series (ROE, ROIC, PE history), yfinance estimates; SEC EDGAR cross-check | Medium |
| 11 | Cash growth | Cash and equivalents growing YoY | Statements (yfinance 4 yrs; EDGAR longer) | High |
| 12 | Insider buying | Insiders increasing purchases | yfinance or Finnhub insider transactions (EDGAR Form 4 not needed) | Medium |
| 13 | Beat market next 6-12 months | Fidelity StarMine 7+ | Analyst consensus / price-target upside / estimate revisions proxy; manual column fallback | Low |
| **E** | **Portfolio and manual checks** | | | |
| 14 | Diversification cut | Drop candidates already owned; optional sector-share cap | Sector from yfinance vs holdings file | High |
| 15 | Accuracy calls | Jefferson Research, Ford Equity Research agree | Manual yes/no on finalists; drop if not workable | Low |

Target portfolio size is 30-40 stocks. This is a constraint, not a scored criterion: the report ranks the top 50 entries as a candidate pool, and the 30-40 held portfolio is built from it, with criterion 14 applied against it.

### Financial Strength proxy score (criterion 1)
0-100, tiers A >= 80, B 65-79, C 50-64, D < 50. Shown as "proxy tier", never as a named rating.
Weights: debt/market cap < 50% (20), interest coverage >= 3x (20), debt/EBITDA sector-adjusted (15), payout <= 60% earnings/FCF based with REIT/utility/MLP exempt (20), FCF positive 5 yrs (10), Altman Z (10), cash growing YoY (5).
Banks/insurers scored separately; REITs use FFO payout + net debt/EBITDA. Missing components skipped and re-weighted. Validate on ~20 known tickers vs public S&P ratings.

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
- 2026-10-19: API keys (FMP, Finnhub, Alpha Vantage) and `EDGAR_USER_AGENT` live in `.env` (gitignored).

## Open questions
Data-source questions raised on 2026-10-18 are listed in `../research/data_sources.md` section 5 (blocked sources, CCC list route, API keys, undefined thresholds).
- Proxy score cutoff for criterion 1 pass (suggest tier B or better).
- Whether ACN, which blends forward yield with a median of dividend/earnings/revenue growth, should use the Chowder tiers as-is or its own.
- Whether criterion 4 means >= 1.5x S&P yield (current reading) or must also be <= 2x.
- Which free sources truly cover each criterion: resolved by the 2026-10-19 spike, except a REIT FFO source (not found) and smaller-cap coverage (spike used 21 large caps).
- Whether one-off GAAP EPS years (JNJ 2017 and 2023, KO 2017) should be flagged or normalized for the earnings 7-of-10 test.
- Exact holdings file layout (user to supply).
- Whether ADRs/foreign listings should be added after v1.
- Whether the 15% exit margin is right.
