# div-invst: Data Source Research (draft for review)

Written 2026-10-18. Purpose: for every data element behind the criteria in `../criteria/ideas_v2.md`, record the original source from `../criteria/ideas_v1.md`, whether it can be pulled programmatically, and the best alternative. Nothing is built yet.

**Status legend**
- **Tested**: I called it from this machine on 2026-10-18 and it returned data.
- **Docs only**: found in documentation or web search, not called. Treat as unconfirmed.
- **Needs key**: free signup required; not tested because I have no key.
- **Blocked**: no programmatic access found, or access is sales-gated or against site terms.

**Updated 2026-10-19:** the full coverage spike (21 tickers) ran after this draft. FMP and Finnhub are now tested, the CCC route and key questions are answered, and the per-criterion source choices changed. Results and the superseding source list: `coverage_spike_2026-10-19.md`. Where this file and the spike doc differ, the spike doc wins; sections 1 and 4 are unchanged.

**Updated 2026-10-25 (Dividend Vision):** dropped, its terms of use prohibit scraping and automated extraction; mentions of it below are historical.

**Updated 2026-10-25:** the Fidelity stock screener download (manual, monthly) supplies the LSEG StarMine Equity Summary Score, interest coverage, 5-yr growth rates and more, so the "Fidelity StarMine" row below is no longer fully blocked: it is available as a manual monthly file. See `fidelity_screener.md`; the table below is left as the original 2026-10-18 findings.

Original 2026-10-18 spike scope: yfinance 1.7.0 on 4 tickers (JNJ, KO, O, XOM); SEC EDGAR company facts for JNJ only; FRED CSV; the DRIP Investing and Dividend Vision pages. Four tickers is a sanity check, not coverage proof. The real coverage spike is still the next step.

## 1. Original sources from ideas_v1.md: can they be used programmatically?

| Original source (v1) | What v1 used it for | Programmatic access? | Status | Evidence | Alternative |
|---|---|---|---|---|---|
| Morningstar credit rating (via Austin library) | Credit quality BBB+ | No. Morningstar's credit-rating data (DBRS Morningstar RatingsNow) is API/SFTP but contact-sales only; developer-portal credentials are sales-gated. Whether it covers dividend-stock issuers is unclear | Blocked | Search: [DBRS RatingsNow](https://go-dbrs.morningstar.com/RatingsNow), [Morningstar API profile](https://providers.apievangelist.com/providers/morningstar/) (secondary source) | Computed Financial Strength proxy score from statements; optional manual rating column |
| Morningstar Stewardship | Management quality | Not found in any API listing | Blocked | Search found nothing on Stewardship | Manual column only. No free equivalent |
| Morningstar fair value / star rating | Discount to fair value | Marketed in Morningstar's paid Agent API only | Blocked | [Morningstar Agent API](https://www.morningstar.com/business/products/agent-api) (marketing page) | Own fair value: DDM and PE-vs-historical-PE |
| Value Line (library) Safety rank / Timeliness | Credit quality 1 or 2 | No public API or export found. Library edition is web pages only | Blocked | Search: library guides describe web reports and ranks; no API listed | Proxy score; manual column from the library if wanted |
| S&P Capital IQ Quality Rank (via TD Ameritrade) | Quality B+ or better | No. The TD Ameritrade API is shut down. Schwab's Trader API needs a Schwab account and no fundamentals or ratings endpoint was confirmed | Blocked | Search: [TD API status](https://blog.traderspost.io/article/does-td-ameritrade-have-api) (third-party) | Proxy score. S&P Quality Rank is built from 10 yrs of earnings and dividend growth and stability, so the dividend and EPS history checks approximate it |
| Fidelity StarMine (0 to 10) | Beat market 6-12 months | No API. Fidelity's Equity Summary Score is built with StarMine, so this is probably what v1 means; confirm in your Fidelity account. Login required; scraping would breach Fidelity terms | Blocked | [Fidelity help glossary](https://www.fidelity.com/quick-content/etf/help/research/learn_er_opinions.shtml) | Analyst-consensus proxy (target-price upside, recommendation mean, estimate revisions); manual column for the real score |
| Jefferson Research (via fidelity.com) | Accuracy calls; quality grades | No API. Jefferson Research did not appear in Fidelity's help pages or search | Blocked | Search: no hits | Manual on finalists, or drop. Proxy score covers the grade topics roughly |
| Ford Equity Research (via fidelity.com) | Accuracy calls | No API. Listed as a Fidelity provider in a 2021 help page; current availability unconfirmed | Blocked | [Fidelity help, 2021 snapshot](https://www.fidelity.com/webcontent/ap010098-etf-content/21.01.0/help/research/learn_er_opinions.shtml) | Manual on finalists, or drop |
| dividendinvestor.com | Current yield and CAGR inputs, rising dividend and earnings strings | Could not verify. The site returned HTTP 403 to my fetch | Not verified | WebFetch 403 | Dividend streak from dividend history (yfinance); EPS streak from SEC EDGAR; CCC lists for streak |
| Seeking Alpha | Source of Aristocrat lists; Quant and Dividend grades | No official public API found. A RapidAPI listing and an Apify scraper exist (third-party; scraping is a terms-of-service risk). Premium subscription is about $299/yr for the website | Blocked | Search: [Apify scraper](https://apify.com/bovi/seeking-alpha-scraper), [RapidAPI blog](https://blog-proxy.rapidapi.com/seeking-alpha-api-with-python-php-ruby-javascript-examples) | CCC lists from DRIP Investing / Dividend Vision |
| Austin public library databases | Access route for Morningstar and Value Line | Human login only | Blocked | n/a | n/a |

Summary: **every rating-agency source in v1 is a human-only source.** Credit rating, Stewardship, Value Line, S&P Quality Rank, StarMine, Jefferson and Ford cannot be refreshed automatically. They become either computed proxies or manual columns.

## 2. Free sources: what they actually return

| Source | Access | Status | What I found |
|---|---|---|---|
| **yfinance** (Yahoo, unofficial) | No key | Tested | Worked for all 4 tickers. `info`: 21-23 of 24 fields I asked for were present. Missing: returnOnEquity (JNJ), freeCashflow (JNJ), interestExpense (all 4). Dividend history back to 1962 (JNJ, KO, XOM) and 1994 (O). Price history 10 yrs. Annual statements only 4-5 yrs (income, balance sheet, cash flow). Analyst data present: recommendations (4 summary rows), upgrades/downgrades (213-415 rows), earnings estimate and EPS revisions (4 rows), insider transactions (41-95 rows). A raw, unauthenticated call to Yahoo's chart URL returned 429, so rate limiting is real. Yahoo has no official API and reports of 429s in 2026 are anecdotal ([search](https://usahousinginformation.com/yahoo-finance-too-many-requests/)). It can break without notice |
| **SEC EDGAR** (data.sec.gov) | No key; descriptive User-Agent required | Tested | JNJ company facts returned (4 MB). Diluted EPS has annual values 2009-2025, net income 2010-2025, cash 2009-2025, operating cash flow 2009-2025. **XBRL tags vary by company and year**: JNJ revenue appears only under the newer tag (2018-2025), interest expense switches tag after 2023, and operating income and dividends-paid tags came back empty or sparse. Needs a tag fallback chain per field. Stockholders' equity returned no rows in my quick filter; not resolved. Company Facts, Frames and Submissions APIs; bulk `companyfacts.zip` rebuilt nightly about 3:00 a.m. ET ([SEC docs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)). The page did not state the rate limit; I recall 10 requests/second from SEC fair-access policy but did not confirm it here. Form 4 filings feed returned HTTP 200 per company; XML parsing not tried |
| **FRED** | CSV endpoint needs no key; API needs a free key | Tested (CSV) | `fredgraph.csv?id=DGS10` returned 10-yr Treasury 5.10% (2026-10-15). `CPIAUCSL` returned 336.298 (2026-09-01) |
| **US Treasury daily yield CSV** | No key | Not working in my test | My call returned nothing; use FRED instead |
| **DRIP Investing CCC workbook** | Email-gated | Blocked for automation | The page says the full, current Champions list is **delivered by email**. The spreadsheet link I downloaded (`/spreadsheets/dividend-spreadsheet.xlsx`) is a portfolio tracker, not the list. Older monthly lists (2008-2021) are downloadable `.xls`. The on-page preview shows streak-related columns plus Chowder number, DGR 1/3/5/10Y, 5Y avg yield, Peter Lynch fair value, ROE, debt/capital, P/E, P/BV. Page says "Updated on November 18, 2025", so freshness is unclear ([page](https://www.dripinvesting.org/dividend-champions/)) |
| **Dividend Vision** CCC tables | No key; HTML | Tested (page loads) | Public tables of Kings, Aristocrats, Champions, Contenders, Challengers with ticker, sector, streak, yield, Distribution Safety Score, forward P/E, market cap, price. robots.txt allows crawling except `/admin`. Terms of use not checked. 2026 counts: 127 Champions, 108 Contenders, 42 Challengers ([search](https://www.dividendvision.com/lists/dividend-champions)) |
| **Financial Modeling Prep** | Free key | Tested 2026-10-19 | Free plan caps statements, ratios and key-metrics at `limit=5` (limit 10 returns 402), so history is 5 annual years, no deeper than yfinance. `dividends` (back to 1970) and `price-target-consensus` work for only some symbols (PG, MCD refused as "symbol not available"). 250 calls/day. **Dropped** |
| **Finnhub** | Free key | Tested 2026-10-19 | `stock/metric` works for all 21 tickers: 133 metrics and annual series back to 1985 (eps, roe, roic, payoutRatio, margins, debt ratios; pe/pb/ps from 1999). Matches EDGAR for JNJ, KO, NEE, O (EPS, ROE; split-adjusted; GAAP not adjusted). No annual EPS series for banks (JPM, USB). `recommendation` and `insider-transactions` work. `price-target` and `dividend` are premium (403). About 60 calls/min, no 429s on 21 tickers. **Primary history source** |
| **Alpha Vantage** | Free key | Tested 2026-10-19 | `INCOME_STATEMENT` gives 20 annual years, `DIVIDENDS` 112 rows, `OVERVIEW` is premium. 25 calls/day. **Dropped** (unusable for a universe) |
| **OpenInsider** (HTML) | None | Page loads | Scraping candidate for insider buys; not parsed; terms not checked. EDGAR Form 4 is the sanctioned route |

## 3. Data element to source map (one row per computed value)

"Computed value" is what gets compared with the threshold in `../criteria/ideas_v2.md`. Primary source is the first choice; the status column reflects the spike above.

| # | Criterion | Computed value | Threshold | Primary source | Status | Fallback | Manual input needed |
|---|---|---|---|---|---|---|---|
| 1 | Credit quality | Financial Strength proxy score (0-100) and tier | Tier B or better (cutoff to confirm) | EDGAR statements + yfinance info (debt, market cap, payout) | Partly tested: debt, market cap, payout present; interest expense needs EDGAR or statements | FMP statements | Optional rating column |
| 1 | Debt / market cap | totalDebt / marketCap | < 50% | yfinance info | Tested | EDGAR + price | No |
| 1 | Interest coverage | Operating cash flow after tax / interest paid | >= 3x | EDGAR (tag chain) | Tag gaps seen | yfinance statements ("Interest Expense" row, not tested) | No |
| 1 | Payout ratio | payoutRatio (earnings), also FCF-based | <= 60%, REIT/utility/MLP exempt | yfinance info | Tested (present for all 4) | EDGAR dividends / net income | No |
| 1 | Annual earnings growth | YoY diluted EPS growth | 5-10% | EDGAR EPS | Tested (JNJ) | yfinance statements (4-5 yrs) | No |
| 1 | Altman Z, FCF positive 5 yrs, cash growth | Computed | Per proxy weights | yfinance statements | Statements tested for shape, not all rows | EDGAR | No |
| 2 | Management quality | Stewardship rating | Per Morningstar | None | Blocked | none | **Yes** |
| 3 | Jefferson quality grades | 5 grades | Strongest / Strong / Low risk | None | Blocked | proxy score | **Yes** |
| 4 | Current yield vs market | dividendYield / SPY yield | 1.5 to 2.5x (flag above) | yfinance (stock and SPY) | Stock tested; SPY not tested | any quote source | No |
| 5 | Chowder rule | yield + 5-yr dividend CAGR; yield / SPY yield | 12 / 15 / 8% by sector; >= 50% of SPY | yfinance dividend history + price | Tested (history present) | FMP dividends | No |
| 5 | Inflation floor | CPI YoY + margin | Growth >= floor | FRED CPI | Tested | none needed | Margin of safety value |
| 6 | ACN | min(10%,Y) + min(30%, avg/median of D,E,R) | Same sector tiers as 5 | yfinance (Y, dividends) + EDGAR (E, R, 5-yr) | EPS tested; revenue tag varies | yfinance statements | No |
| 7 | Dividend streak | Consecutive years of increase | >= 5 | yfinance dividend history (compute) or Dividend Vision streak | Tested (history). Needs special-dividend handling | CCC list | No |
| 7 | Earnings streak | Years with EPS up in last 10 | >= 7 of 10 | EDGAR diluted EPS | Tested (JNJ 2009-2025) | none (yfinance only 4-5 yrs) | No |
| 8 | Fair value | Lower of DDM and PE-vs-hist-PE; discount % | >= 15% below | Computed | Inputs available (dividends, price, EPS history) | n/a | Discount rate and growth assumptions |
| 9 | P/S, P/E, P/B | priceToSales, trailingPE, priceToBook | P/S < 1.5; P/E below average and below 1/bond rate; P/B near 1 and below market | yfinance info | Tested (present) | FMP ratios | No |
| 9 | Bond rate | 10-yr Treasury | Input to P/E test | FRED | Tested | none | No |
| 9 | Price / cash | marketCap / totalCash | Low (no numeric threshold given) | yfinance info | Tested | EDGAR | **Threshold needed** |
| 10 | PE vs historical PE | trailing PE / avg of historical PE | Current below normal | yfinance prices + EDGAR EPS | Inputs tested | FMP | No |
| 10 | ROE, ROIC trend | Net income / equity; NOPAT / invested capital, direction over years | Rising | Statements (yfinance 4-5 yrs, EDGAR longer) | ROE missing from info for JNJ; compute instead | FMP | No |
| 10 | Est. earnings growth | earningsGrowth; estimate table | Positive (threshold to define) | yfinance | Tested (present) | Finnhub estimates | **Threshold needed** |
| 11 | Cash growth | Cash YoY change | > 0 | EDGAR or yfinance balance sheet | Tested | none | No |
| 12 | Insider buying | Net insider purchases over trailing period | Increasing | yfinance insider transactions or EDGAR Form 4 | yfinance tested; EDGAR feed reachable, parse not tried | OpenInsider | **Threshold needed** |
| 13 | Beat-market proxy | Target-price upside, recommendation mean, estimate revisions | 7+ equivalent (proxy scale to define) | yfinance | Tested 2026-10-21 (21/21; see `revision_spike_2026-10-21.md`) | Finnhub recommendations (4 months) | StarMine score optional |
| 14 | Diversification | Sector vs holdings | Not already owned; optional sector cap | yfinance sector + your holdings file | Tested (sector present) | none | Holdings file |
| 15 | Accuracy calls | Jefferson / Ford agree | Yes | None | Blocked | none | **Yes** |
| Exit | Yield compression | yield / 5-yr average yield | <= 50% | yfinance fiveYearAvgDividendYield | Tested (present) | computed from history | No |
| Exit | Fair-value ceiling | price / fair value | > +15% | Computed | See criterion 8 | n/a | No |
| Exit | Fundamental break | Dividend cut/freeze, payout over limit, falling EPS | Any | Dividend history, payout, EPS | Tested | n/a | No |
| Universe | CCC membership and tier | Streak years, tier | Primary tier flag | Dividend Vision tables or emailed DRIP workbook | Dividend Vision page loads; workbook email-gated | Compute streak from history | Drop the emailed file in a folder, if used |

## 4. Proposed refresh cadence (for discussion)

| Data | Cadence | Reason |
|---|---|---|
| Prices, yield, valuation multiples | Daily after close | Cheap, moves daily; also feeds exit triggers |
| Treasury yield, CPI | Daily / monthly | FRED updates at that rate |
| Analyst data, estimates | Weekly | Changes slowly; Yahoo rate limits |
| Insider transactions | Daily or weekly | Form 4 due within 2 business days |
| Financial statements, EPS history | After each 10-Q / 10-K, checked weekly | EDGAR updates within minutes of filing |
| CCC list and streaks | Monthly or weekly | Lists update monthly or weekly depending on source |
| Rating-agency columns | Manual, when you update them | No automated source |

## 5. Gaps and decisions for you

1. **Blocked sources.** Morningstar, Value Line, S&P Quality Rank, StarMine, Jefferson, Ford and Stewardship cannot be fetched. Confirm the plan: proxy scores for credit quality and StarMine, and manual columns for Stewardship, Jefferson and Ford. Criteria 2, 3 and 15 will stay "unknown" unless you fill them.
2. **CCC list source.** The DRIP Investing workbook is emailed. Options: (a) you subscribe and drop the file in a folder, (b) scrape Dividend Vision's public tables, (c) compute streaks from yfinance dividend history. I lean to (c) as the base with (b) as a cross-check. Status 2026-10-19: yfinance-computed streaks work for most tickers but show errors (XOM, PG, ED); still need the Dividend Vision cross-check. User confirmation of the route is pending. Update 2026-10-22: settled differently: the user supplied the DRIP "All CCC" export (684 stocks) and `scripts/fetch_ccc.py` pulls Dividend Vision (288); the streak is the conservative lower claim of the two (see `ideas_v2.md` decisions log).
3. **API keys.** Answered 2026-10-19: keys supplied in `.env`, FMP and Finnhub and Alpha Vantage tested. Finnhub kept; FMP and Alpha Vantage dropped.
4. **Reliability.** yfinance is unofficial and rate limited. Plan: cache everything locally, back off on 429s, and use EDGAR as the backbone for fundamentals history.
5. **Thresholds.** Resolved 2026-10-21: all defaults accepted; see the decisions log in `../criteria/ideas_v2.md`.
6. **dividendinvestor.com** returned 403 to my fetch, so I could not assess it. If you use it manually, tell me what you pull from it.
