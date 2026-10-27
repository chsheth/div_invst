# Coverage spike results (2026-10-19)

Script: `scripts/coverage_spike.py`. Raw output (gitignored): `data/spike_out/report.md`, `results.json`.
Tickers (21): JNJ KO PG MCD ABBV XOM CVX MMM CAT MSFT AAPL T MO O PLD NEE DUK ED JPM USB WMB. Python 3.13.9, yfinance 1.7.0 (also imports and returns data on 3.14.0).

## Verdict per source

| Source | Verdict | Evidence |
|---|---|---|
| **yfinance** | Backbone for prices, yield, multiples, dividend history, analyst and insider data | `info`: only freeCashflow, operatingCashflow, returnOnEquity (4 of 21 each) and EBITDA (2) missing. Dividend history 1962+ for old payers. Insider (72-150 rows), recommendations, upgrades, estimates, EPS revisions, price targets present for all 21. Statements are **4 years only**. Operating Income and EBITDA absent for 2 tickers (banks: JPM, USB). Interest Expense missing for 2 tickers (2-4 years elsewhere) |
| **SEC EDGAR** | Backbone for long EPS and fundamentals history, with caveats below | 10-13 annual years of EPS, net income, revenue, operating cash flow for 20 of 21 tickers. No HTTP errors |
| **Finnhub** (free) | Strong surprise: use it | `stock/metric` works for all 21: 133 metrics, including dividendYield, payoutRatioTTM, dividendGrowthRate5Y, peTTM, pbAnnual, roeTTM. **Annual series back to 1985 (up to 41 years)** for eps, roe, roic, payoutRatio, netMargin, debt ratios, FCF margin; pe/pb/ps back to 1999. roicTTM missing but the annual `roic` series exists. `recommendation` (4 rows) and `insider-transactions` (263 rows) work. **403 (premium): `price-target` and `dividend`** |
| **FMP** (free) | Usable only with `limit=5` | `limit=10` returns 402 ("limit must be between 0 and 5") for statements, ratios, key-metrics. Retest with `limit=5` returned 5 annual years (2021-2025) for KO, so FMP is no deeper than yfinance. `dividends` (228 rows back to 1970) and `price-target-consensus` work for only 6 of 10 tickers; 402 "symbol not available" for PG, MCD and others. `profile` works. 233 live calls used this run (80 on FMP) |
| **Alpha Vantage** (free) | Minor: `INCOME_STATEMENT` gives 20 annual years, `DIVIDENDS` 112 rows | `OVERVIEW` is premium. 25 calls/day makes it unusable for a universe; at most a gap filler |
| **FRED** | Works, no key | DGS10 = 5.09% (2026-10-16); CPIAUCSL 336.298 (2026-09-01) |
| **SPY yield** | yfinance gives 0.99 (percent) in `dividendYield` and 0.0099 in `yield`. Units differ by field | Convert carefully in the data layer |

## Findings that change the design

1. **Finnhub annual series replace most of the EDGAR tag work for the history-based criteria.** EPS history for criterion 7 (7 of 10 years), ROE/ROIC trend and payout history for criterion 10, and historical P/E for the P/E-vs-history test are all in one call per ticker. Keep EDGAR for audit and gaps. Caveat: Finnhub series are derived values; spot-check them against EDGAR for a few tickers before trusting them.
2. **ticker-to-CIK mapping can break after a corporate reorganization.** `company_tickers.json` now maps XOM to a new entity, ExxonMobil Holdings Corp (CIK 2115436), whose facts have no history, so all 10 XOM EDGAR fields came back empty. The old CIK is 34088 (EPS 2025 = 6.70). **Fixed in the script:** `CIK_OVERRIDES` maps XOM to 34088 (XOM now returns 11-12 years), and a warning prints when a CIK has no 10-K facts.
3. **EDGAR tag gaps: closed by extending the chains** (in `EDGAR_FIELDS`, `scripts/coverage_spike.py`). Found by listing every us-gaap tag with 8+ annual values per ticker and picking what each company actually uses. Before to after, years of data:
   - long_term_debt: ABBV 7 to 12, XOM 4 to 12, T 7 to 12, O 3 to 11, JPM 0 to 12, WMB 0 to 12, KO, CVX, USB up to 12. New tags: `LongTermDebtAndCapitalLeaseObligations` (ABBV), `...IncludingCurrentMaturities` (JPM), `NotesPayable` (O), plus `LongTermNotesPayable`, `SeniorNotes`, `UnsecuredDebt`.
   - dividends_paid: JNJ 0 to 12 (`PaymentsOfOrdinaryDividends`), DUK 9 to 12. Chain now prefers common-stock-only tags before the generic `PaymentsOfDividends`, which can include preferred.
   - cash: USB 7 to 12, JPM and CAT 11 to 12 (`CashAndDueFromBanks`, `CashCashEquivalentsAndShortTermInvestments`, `Cash`).
   - interest_expense: MMM 11 to 12 (`InterestExpenseDebt`, `InterestExpenseDebtExcludingAmortization`, `InterestPaid` added).
   - Every field now has 8+ years for all 21 tickers except `dps_declared` for CVX (7): CVX tags dividends per share only from 2019 in XBRL. Take per-share dividends from yfinance or Finnhub history instead.
   - JNJ's 10 to 12 on most fields is the 52/53-week fix, not the new tags.
   - **Caveat:** the merge takes the first tag that has a value for each year. A company that switches from `LongTermDebtNoncurrent` to a "including current" tag mid-history can give a series that mixes definitions. Fine for coverage; check debt-ratio trends before relying on them. Banks' `long_term_debt` is not comparable to industrials'.
4. **Banks (JPM, USB)** lack operating income and EBITDA in yfinance, as the plan predicted. They need the separate bank scoring in the Financial Strength proxy.
5. **Dividend streak: fixed the payment-count bug, residual errors remain.** Calendar-year totals broke when a payment slipped across Dec 31 (O had 11 payments in 2024 and 13 in 2025; KO, PG, XOM, CAT show the same in older years). `dividend_stats()` now skips those ambiguous years and compares the clean years on either side. Results vs known streaks: JNJ 63 (63), KO 63 (63), MCD 48 (49), CVX 38 (38), CAT 32 (31), NEE 30 (30), JPM 15, MSFT 21, O 26, MMM 0 and T 0 (both cut). Still off: **XOM 53 (about 43), PG 42 (about 69), ED 44 (about 51), AAPL 13 (14)**. Bridging can hide a real freeze in an ambiguous year (XOM overshoots), and PG/ED likely hit data quirks in old split-adjusted history. Use yfinance streaks only as a screen; cross-check against Dividend Vision before trusting a number.
6. **FMP adds little**: no more history than yfinance, and symbol coverage on the free tier is partial. Drop it from the primary plan unless a specific gap appears. Do not build on it.
7. **Price-target data** (StarMine proxy): yfinance has it for all 21 tickers; Finnhub's is premium. Use yfinance.

## Updated criteria sources (these replaced the element-to-source map of the first draft; the current mapping is the Inputs column of `../criteria/ideas_v2.md`)

- Criterion 7 earnings streak, 10 PE history, ROE/ROIC trend: Finnhub annual series (primary), EDGAR (cross-check), not yfinance statements.
- Criterion 12 insider buying: yfinance insider transactions or Finnhub `insider-transactions` (both work); EDGAR Form 4 not needed.
- Criterion 13 proxy: yfinance price targets, recommendations, estimate revisions.
- FMP and Alpha Vantage: not used.

## Finnhub vs EDGAR spot-check (JNJ, KO; `scripts/finnhub_vs_edgar.py`)

- **EPS:** 20 of 20 years (2016-2025) within 0.7% of EDGAR diluted EPS. Finnhub reports GAAP EPS, not adjusted: it includes one-offs such as JNJ 2017 (0.47, tax reform) and 2023 (13.73, Kenvue gain), and KO 2017 (0.29). The earnings-up-7-of-10-years test will see those spikes and dips.
- **ROE:** Finnhub = net income / ending equity, exactly (JNJ 2025 32.9%, KO 2025 40.7%). Series are fractions, not percents.
- **Payout ratio:** Finnhub is within 1.5 points of declared DPS / EPS (KO 2025 67.0 vs 67.1; JNJ 2025 46.2 vs 46.6). Also a fraction.
- **Bug found in my EDGAR extraction:** JNJ uses a 52/53-week fiscal year ending in early January, so two fiscal years keyed to the same calendar year and one overwrote the other (fake 1162% EPS gap for 2017). Fixed in `edgar_annual` (an end date in Jan 1-7 counts as the prior year). The coverage numbers above for 52/53-week filers were slightly understated before this fix.
- **Conclusion for JNJ and KO:** Finnhub annual series match reported figures.

### Second spot-check: JPM (bank), O (REIT), NEE (utility)

- **Banks have no annual EPS series in Finnhub.** JPM and USB return 31 annual series but no `eps` (ROE, payoutRatio and PE series are present). EPS history for banks must come from EDGAR (JPM has 12 years). Any bank criterion that needs EPS history (7, 10) uses EDGAR, not Finnhub.
- **NEE: Finnhub is split-adjusted, EDGAR is not.** The 4-for-1 split in 2020 makes 2016 and 2017 differ by exactly -75% (Finnhub 1.56 vs EDGAR 6.24 as originally reported). All 2018-2025 years match within 0.3%. Anything built on EDGAR EPS or DPS history must split-adjust it; Finnhub already has.
- **O: EPS matches in 8 of 10 years**; 2016 (+9.2%) and 2017 (+5.8%) differ from EDGAR (1.23 vs 1.13, 1.16 vs 1.10), cause not investigated. ROE exact. GAAP payout is 195-325% of EPS, so a REIT needs the FFO-based payout the proxy score already specifies; Finnhub's payout series for O has only 14 years.
- **Utility (NEE) and REIT (O) ROE match EDGAR exactly**; payout within 1.5 points for NEE.

**Net:** Finnhub is the right primary for industrials, staples and utilities. Banks need EDGAR for EPS; REITs need FFO from elsewhere (not tested; EDGAR has `FundsFromOperations` only in some filings); split-adjust any EDGAR history.

## Not tested yet

- Finnhub accuracy on small caps, and a REIT FFO source.
- Finnhub rate limit under a full-universe run. The script paced calls at 1.1 s and got no 429s on 21 tickers.
- Whether the free-tier symbol restriction on FMP also applies to Finnhub for small caps or less-liquid tickers; the 21 test tickers are all large caps.
