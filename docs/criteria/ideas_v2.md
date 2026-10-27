# div-invst: Criteria and scoring (v2)

The current spec: what is screened, the thresholds, how stocks are scored and ranked, and the exit rules. Structured version of
`ideas_v1.md` (the original notes, same folder). Why each number is what it is (findings, calibration, superseded options):
`decisions_log.md`. All thresholds live in `config/criteria.toml`; change numbers there, not in code. Build status per slice:
`../plan/PLAN.md`. Where we left off: `../sessions/session_resume.md`.

## Goal
Aggregate dividend stock data and history, apply the criteria below, and produce:
1. A ranked **entry list** (what to buy), with per-criterion pass/fail.
2. An **exit list** for current holdings (what to sell/review), showing which trigger fired.

Main interest: dividend Aristocrats, Champions, Contenders (CCC), but all US dividend payers are screened so matches outside
the CCC lists are not missed.

## Universe
- US-listed dividend payers (ADRs and foreign listings out of scope for v1). CCC names are flagged as the primary tier.
- CCC universe and tier: the monthly DRIP "All CCC" export (684 stocks, 2026-10). Its Stock Type is a streak band (Challenger 5-9,
  Contender 10-24, Champion 25-49, King 50+ years); exact streak years are not available because Dividend Vision was dropped (its
  terms prohibit automated extraction). The band is enough for criterion 7. Non-CCC streaks come from yfinance dividend history and
  are a screen only (wrong for XOM, PG, ED in the spike).
- Dividend Aristocrat (S&P 500 member with 25+ years) is not labelled: the data has the streak band but no index membership.
  Planned approach and the open source question are in `../sessions/session_resume.md`.

## Scoring and ranking
- Each criterion returns pass, fail, unknown or na per ticker. Missing data is unknown, never a fail. All criteria are equally weighted.
- Applicable = every criterion except na (criterion 14 is na without a holdings file). Evaluated = pass or fail. Coverage = evaluated / applicable.
- A ticker is ranked only with a yield, US scope and coverage >= 70% (`ranking.min_coverage`).
- Rank key = passes / applicable (unknowns count as not passed, so a perfect score on few criteria cannot beat a strong one on many);
  ties by ACN (criterion 6), then yield, then ticker. The report shows passes / evaluated as the score. Top 50 are kept.
- The applicable count differs per ticker (n/a for sector skips, unknown for missing data). Coverage falls as more criteria depend on cached data; revisit the 70% cutoff once all of them are populated.
- Target portfolio size is 30-40 stocks: a constraint, not a scored criterion. The top 50 is the candidate pool; the held portfolio is built from it with criterion 14 applied.

## Criteria
Status: built = implemented in `src/div_invst/criteria/`; "needs cache" criteria are unknown for a ticker until its data is in the SQLite cache (`scripts/refresh_data.py`).

| # | Criterion | Rule (thresholds in the config) | Inputs | Status |
|---|-----------|---------------------------------|--------|--------|
| **A** | **Financial strength** | | | |
| 1 | Credit quality and balance sheet | Financial Strength proxy score >= 65 (tier B), see below | Screener interest coverage; yfinance debt, FCF, payout; Finnhub EBITDA and FCF margin; EDGAR cash and dividends paid | Built, needs cache; banks and insurers unknown |
| 2 | Management quality | MSCI Governance Average or better (proxy for Morningstar Stewardship) | Screener | Built |
| 3 | Quality grades | Quality composite >= 70 (proxy for the Jefferson grades), see below | Screener; REIT payout from the cache | Built |
| **B** | **Income and dividend growth** | | | |
| 4 | High current yield | Yield 1.5 to 2.5 times the S&P yield; above 2.5x still passes with a "yield trap?" flag | Screener or DRIP yield; S&P yield (manual in the config) | Built |
| 5 | Chowder rule | Yield >= 50% of the S&P yield; yield + 5-yr dividend CAGR >= 12% (default), 15% (tech and growth, yield < 3%), 8% (utilities, telecom); growth at least inflation | Screener or DRIP growth; CPI from FRED | Built |
| 6 | Adjusted Chowder Number (ACN) | ACN >= the same tier. ACN = min(10%, Y) + min(15%, average(min(D,E,R), median(D,E,R))); Y = forward yield, D/E/R = 5-yr dividend / EPS / revenue growth (point-to-point CAGRs; at least 2 of 3 needed). The growth part is capped at 15% (it was 30% in the original formula; energy and REITs with 30% growth inflated it, calibrated 2026-10-25). Also the ranking tiebreaker | Screener growth rates (equal Finnhub's CAGRs) | Built |
| 7 | Rising dividends and earnings | Dividend up 5+ years (CCC: through the DRIP band; others: yfinance streak >= 5) and EPS up in 7 of the last 10 year-over-year comparisons (fewer comparisons scale the need; under 8 is unknown). A one-off EPS year (moves > 40% from both neighbours in opposite directions) counts as up only if the next year beats the year before it | DRIP band; cache: yfinance dividends, Finnhub EPS (EDGAR split-adjusted for banks) | Built, needs cache |
| **C** | **Valuation** | | | |
| 8 | Discount to fair value | Price >= 15% below the lower of a two-stage DDM and a P/E value, see below | Cache: dividends, EPS, P/E history | Built, needs cache |
| 9 | Valuation multiples | P/S < 1.5; P/B <= 3; earnings yield > 10-yr Treasury; cash >= 5% of market cap (skipped for banks and insurers); P/E below its own 10-yr median. Fail if any evaluable sub-test fails; pass with 3+ evaluable and all passed. Not built: P/B below the market's | Screener; FRED; Finnhub P/E history | Built |
| **D** | **Fundamentals and momentum** | | | |
| 10 | Better fundamentals | P/E below own 10-yr median; ROE and ROIC rising (3-yr average above the prior 3-yr, or latest >= 90% of the 10-yr high); next-year consensus EPS growth >= max(3%, CPI). Fail if any evaluable test fails; pass with 2+ evaluable | Finnhub annual series; yfinance estimates | Built, needs cache |
| 11 | Cash growth | Cash and equivalents up year over year | EDGAR | Built, needs cache |
| 12 | Insider buying | At least 2 different open-market buyers (Finnhub code P) in the last 183 days and net shares positive | Finnhub insider transactions | Built, needs cache |
| 13 | Beat market next 6-12 months | StarMine ESS Bullish or Very Bullish, or Neutral with a Moderate or Large Increase in its 1-month change. With no ESS, the revision proxy decides (pass at 7.0 of 10); with an ESS the proxy is shown beside it | Screener ESS; cache: yfinance revisions | Built |
| **E** | **Portfolio and manual checks** | | | |
| 14 | Diversification cut | Drop candidates already owned; optional sector-share cap | Holdings file | Built; na without holdings |
| 15 | Rating agreement | At least 3 votes and (positives - negatives) / votes >= 0.25 across Jefferson, Zacks, McLean, Argus, I/B/E/S and Morningstar (StarMine is criterion 13's, so it does not vote); optional manual yes/no override | Screener; Morningstar pick lists | Built |

### Financial Strength proxy score (criterion 1)
0-100, tiers A >= 80, B 65-79, C 50-64, D < 50; shown as "proxy tier", never as a named rating; pass at B or better.
Components and weights: debt / market cap < 50% (20), interest coverage >= 3x (20), debt / EBITDA (15; <= 3x full credit, <= 4.5x partial; utilities and REITs <= 6x and 7.5x, REITs on net debt), payout (20; <= 60% on the higher of earnings payout and dividends paid / FCF; REITs use dividends paid / FFO <= 85%; utilities exempt), FCF margin positive in 4 of the last 5 years (10), cash growing (5). Missing components are skipped and the weights re-scaled; at least 3 components are needed. Altman Z (10 points in the first design) is dropped: the statements it needs are not fetched. Banks and insurers are scored separately in the design; that is not built, so they are unknown.
REIT FFO proxy = net income + D&A + real-estate impairments - property-sale gains, validated within about 3% for O (PLD runs 4.8% high because its gains sit on custom tags): `../research/reit_ffo_validation_2026-10-26.md`. Mortgage REITs are not covered.

### Quality composite (criteria 2, 3 and 15)
A collective, proxy-labelled quality view built from the Fidelity screener (added 2026-10-25, because Stewardship, the Jefferson grades and Ford have no source). Defaults, to calibrate on known tickers later. Inputs are the Search Criteria and Analyst Opinions fields in `../research/fidelity_screener.md`; missing inputs are skipped and the rest re-weighted. Coverage on the 681 CCC names in the screener is given in brackets.
- **Criterion 2, management (600):** MSCI Governance score, Leader 100, Average 60, Laggard 0. Pass at Average or better. It mostly removes Laggards (25 of 2,883 stocks). It measures governance, not capital allocation, so it stays a weak proxy; unknown when MSCI has no score.
- **Criterion 3, quality score 0-100:** average of four sub-scores, each the average of its available inputs, with at least 3 of the 4 present; pass at 70 or more (calibrated 2026-10-25 on 24 known tickers: KO 89, JNJ 82, PG 85, ADP 95 pass; PEP 65, VZ 61, ABBV 56 fail; the universe median is about 75, CCC about 80). Debt to capital is skipped for financials and its ladder has a 20 step for 65-75%.
  - Balance sheet (673): interest coverage (8x or more 100, 5-8 80, 3-5 60, 1.5-3 30, below 1.5 0); debt to capital (35% or less 100, up to 50 70, up to 65 40, above 0); current ratio (1.5 or more 100, 1.0-1.5 70, below 1.0 40; skipped for financials, utilities and REITs).
  - Cash flow quality (681): free cash flow positive (100) or negative (0); 5-year cash flow growth (5% or more 100, 0-5 70, negative 20). Cash flow to net income from the statements is not built.
  - Earnings quality (681): EPS growth 3-year and 5-year (both positive 100, one 50, none 0); operating margin TTM vs 5-year average (0.95 or more 100, 0.85-0.95 60, below 20); dividend coverage EPS/dividend (1.5x or more 100, 1.0-1.5 60, below 1.0 0; REITs use the FFO-proxy payout).
  - Operating efficiency (680): SG&A / net sales (20% or less 100, up to 35 60, above 20; skipped for financials, REITs, utilities); 5-year operating margin (15% or more 100, 8-15 60, below 8 20); return on investment (10% or more 100, 5-10 60, below 5 20).
  - Valuation risk, the fifth Jefferson grade, is covered by criteria 8 and 9 and not repeated here. Balance sheet overlaps the criterion 1 proxy by design.
  - The S&P Quality and Financial Health scores are not used (no relation to credit ratings, checked 2026-10-25).
- **Criterion 15, rating agreement (576 of 632 US-scope CCC names have at least 3 votes; 628 of 681 when StarMine still voted):** each available third-party rating votes positive, neutral or negative: Jefferson Research (Buy / Hold / Sell, 58% of CCC names), Zacks (Outperform / Neutral / Underperform, 93%), McLean (Buy / Neutral / Sell, 89%), Argus Analyst Opinions (Buy / Hold, 33%), I/B/E/S mean (2.0 or lower positive, 3.0 or higher negative, 96%), plus the Morningstar star rating for pick-list names (4-5 positive, 1-2 negative). Agreement score = (positives - negatives) / sources available. Pass: at least 3 sources and a score of 0.25 or more. Ford is not available, so this replaces the Jefferson-and-Ford check with a wider panel; the manual yes/no override stays. Trading Central is a technical signal and is not used.

### Revision proxy (criterion 13, second signal)
0-10 from one yfinance snapshot per ticker, missing components skipped and the weights re-scaled (at least 2 needed): 40% 90-day EPS estimate change (+/-10% maps to 10/0), 20% up/down estimate revision balance, 20% upgrade/downgrade balance (90 days), 10% mean recommendation level (the 4-month Finnhub trend is too short), 10% price-target upside (+/-20% maps to 10/0). The screener ESS and the proxy are only weakly related (Spearman 0.25 with the 90-day change), so they stay separate. yfinance revision data is point-in-time: a snapshot is stored each day.

### Fair value (criterion 8)
Two-stage DDM: the current annual dividend grows at the 5-yr dividend CAGR (capped at 8%, floored at 0) for 5 years, then 4% for good, discounted at the 10-yr Treasury + 3.5%. P/E value: median of the last 3 fiscal-year EPS x median 10-yr P/E (not for REITs). Fair value is the lower of the two; pass at 15% below. The median is used for P/E history everywhere because one-off GAAP charges create P/Es of 40 to 150. The calibration, the pass rates at other premiums, and the deferred yield-trap guard are in `decisions_log.md` (2026-10-26).

## Exit rules
The exit report shows which trigger fired for each holding, plus current price, target sell price, % upside.
1. **Fair-value ceiling:** price > fair value + 15%.
2. **Yield compression:** current yield <= 50% of the 5-yr average yield (yfinance `fiveYearAvgDividendYield`).
3. **Fundamental break ("review now"):** dividend cut or freeze, payout ratio over the limit, falling earnings.
Morningstar "Pick List Deletions" are shown as an informational note, not a trigger.

## Inputs
- Holdings file: Excel or CSV (not yet supplied). Ticker required, shares optional, no cost basis. Without it the entry list runs with criterion 14 n/a and no exit report.
- Monthly reference files (manual drops): `../guides/monthly_drop.md`. Screener fields and how they map to criteria: `../research/fidelity_screener.md`.
- Cached market data (yfinance, Finnhub, EDGAR, FRED): `../plan/PLAN.md` (Slice 2) and `../research/data_sources.md`.
