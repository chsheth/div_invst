# div-invst: Ideas and Criteria (v2)

Structured version of `ideas_v1.md`, which is left untouched as the original notes.
Single source of truth for criteria and decisions. Related: `PLAN.md` (build plan), `session_resume.md` (where we left off), `README.md` (overview).

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
Stocks are ranked on available data; coverage count is shown; below ~70% coverage a stock is not ranked.

| # | Criterion | Threshold | Planned free data source | Feasibility |
|---|-----------|-----------|--------------------------|-------------|
| 1 | Financial strength / credit quality | Morningstar BBB+, Value Line 1 or 2, S&P CIQ B+ or better | Computed Financial Strength proxy score (below) + optional manual rating column | Medium |
| 2 | Diversification cut | Drop candidates already owned; optional sector-share cap | Sector from yfinance vs holdings file | High |
| 3 | Beat market next 6-12 months | Fidelity StarMine 7+ | Analyst consensus / price-target upside / estimate revisions proxy; manual column fallback | Low |
| 4 | Discount to fair value | >= 15% below fair value | Own estimate: DDM and PE-vs-historical-PE, take the lower | Medium |
| 5 | Chowder rule | Yield >= 50% of SPY yield; yield + 5y div CAGR >= 12% (most), 15% (tech/growth, yield < 3%), 8% (utilities/telecom) | yfinance dividends and price; CAGR computed | High |
| 6 | Rising dividends / earnings | Dividend up 5+ yrs; earnings up 7 of last 10 yrs | CCC list streak; EPS history via FMP / SEC EDGAR | Medium |
| 7 | Better fundamentals | PE vs historical PE, ROE rising, ROIC rising, est. earnings growth | yfinance / FMP free / SEC EDGAR XBRL | Medium |
| 8 | Accuracy calls | Jefferson Research, Ford Equity Research agree | Manual yes/no on finalists; drop if not workable | Low |

### From SBI
- Financial strength: credit ratings (ValueLine B+/2, S&P BBB+, Morningstar BBB+); low debt (debt/market cap < 50% OR 3:1 coverage); strong cash flow (earnings growth 5-10%, payout <= 60% except REIT/utility/MLP); management quality (Morningstar Stewardship, manual).
- High current yield: 1.5 to 2 times S&P yield.
- High growth of yield: inflation + margin of safety, using 5-yr growth rate for the Chowder number.
- Other buy factors: P/S < 1.5; low P/E (below average and below reciprocal of bond rate); P/B near 1; low price/cash; cash and equivalents growing YoY; insider buying (SEC Form 4).
- Target portfolio size: 30-40 stocks.
- Jefferson Research quality: Balance Sheet, Cash Flow Quality, Earnings Quality = strongest; Operating Efficiency = strong; Valuation = low risk.
- ACN = min(10%, Y) + min(30%, average(min(D,E,R), median(D,E,R))); Y = forward dividend yield, D/E/R = 5-yr dividend / earnings / revenue growth rate.

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
See `PLAN.md` ("Resources / websites used") for the full list with verification status.
Free first: Dividend Radar / DRIP Investing (CCC lists), yfinance, FMP free tier, SEC EDGAR, Finnhub (candidate), FRED/Treasury.
Manual references: Seeking Alpha, Dividend.com, Fidelity, Value Line, Morningstar, S&P Capital IQ, dividendinvestor.com.

## Decisions log
- 2026-10-13: Free data sources first; paid only if inadequate.
- 2026-10-13: Universe = all US dividend payers, CCC flagged as primary.
- 2026-10-13: Output = ranked entry list + exit list; 3 exit triggers approved; report shows which fired.
- 2026-10-13: Holdings via Excel/CSV, no cost basis.
- 2026-10-13: CLI + SQLite cache with run snapshots; coverage-aware scoring (70% min); equal-weighted criteria; top 50 entries.
- 2026-10-13: Crit 1 = proxy score + manual override; Crit 3 = analyst proxy w/ manual fallback; Crit 8 = manual on finalists.
- 2026-10-13: Fair value = lower of DDM and PE-vs-historical-PE; entry >= 15% discount; exit margin +15%.
- 2026-10-13: Python version may be lowered to 3.12/3.13 if libs lack 3.14 support.
- 2026-10-13: `ideas_v1.md` kept as untouched original; structured version lives in `ideas_v2.md`.

## Open questions
- Which free sources truly cover each criterion (resolved by the data spike).
- Exact holdings file layout (user to supply).
- Whether ADRs/foreign listings should be added after v1.
- Whether the 15% exit margin is right.
