# Fidelity screener: reference

What the monthly Fidelity stock screener download contains, how to read it, and what to watch for. Written from the 2026-10-25 download (7 yield bands, 2,883 stocks). Criteria mapping and decisions live in `../criteria/ideas_v2.md` ("Fidelity screener"); the monthly steps are in `../guides/monthly_drop.md`. Where a unit or meaning below is marked **unverified**, it is inferred from the values and has not been checked against Fidelity's field help.

## 1. How the file is produced
- Fidelity caps an export at 500 rows, so the screen is downloaded as yield bands, each saved as `screener_results*.xls` in `docs/reference/<YYYY-MM>/`.
- `scripts/merge_screener.py` stacks the bands tab by tab into `screener_results.xlsx` (the monthly file), dropping footer rows and the stock repeated on a band edge, and refusing a file that is a copy of another.
- October bands: 6% and up (401 stocks), 4–6% (442), 3–4% (437), 2.25–3% (425), 1.5–2.25% (443), 0.75–1.5% (466), 0.07–0.75% (273); 4 symbols on band edges appeared twice. Total 2,883.
- Snapshot time is in the raw files' footer: "AS OF 02:04 AM ET 10/25/2026, quotes delayed at least 15 minutes" (bands were downloaded within about 12 hours of each other).

## 2. Layout and parsing rules
- Five tabs, each with one header row and one row per stock. Join tabs on `Symbol` (unique after the merge). `Company Name` is the second column on every tab.
- The raw files end with disclaimer lines (Fidelity address, "All data is historical and is subject to revision", the as-of line, and a note that highlighted cells are user-added). They have no Company Name and are removed by the merge. Raw files also carry a few blank rows before the footer.
- Missing values appear as an empty cell, or as the text `--` (seen in `P/E (Price/TTM Earnings)`, `Sector`, `Industry`, `Market Capitalization`, `Jefferson Research`, `Trading Central`, `McLean Capital Management`, and some others). Treat `--` as unknown, never as zero. `P/E` is stored as text for this reason; convert with a coercing parser.
- `Market Capitalization` is text with a suffix: `$580.84K`, `$105.25M`, `$2.83B`, `$1.5T`; `-` or `--` for 11 stocks. Suffix counts: B 2,246, M 615, T 9, K 2.
- Some columns repeat across tabs (`Security Price`, `Dividend Yield`, `Company Name`; `EPS Growth (Proj This Yr vs. Last Yr)` is on both Search Criteria and Valuation, Growth & Ownership). Use the Search Criteria copy and ignore the duplicates.
- Stocks with a blank in a field Fidelity filters on are dropped by Fidelity, so add fields as display columns only.

## 3. What is in the universe
| Security Type | Stocks | Notes |
|---|---|---|
| Common Stock | 1,764 | |
| Depository Receipt | 935 | ADRs; out of scope for v1; only 1 has a US headquarters |
| Common Stock (REIT) | 124 | |
| Unit Trust Fund | 56 | MLPs and royalty trusts |
| Unit Trust Fund (REIT) | 4 | |

- Headquarters: 1,677 United States, then Japan 186, United Kingdom 113, Canada 97, China 72, Germany 66, France 56. Filtering on `Company Headquarters Location == United States of America` removes 935 ADRs and most foreign names in one step (1,499 common, 124 REIT, 53 unit trusts, 1 depository receipt remain).
- `Sector` (GICS names): Financials 796, Industrials 460, Consumer Discretionary 297, Materials 229, Energy 193, Real Estate 180, Consumer Staples 175, Information Technology 162, Utilities 132, Health Care 127, Communication Services 122, `--` 10. `Industry` has 75 values (Banks 444, Oil Gas & Consumable Fuels 157, Capital Markets 146, Insurance 110, Machinery 106, Metals & Mining 100, Chemicals 87, and others). These differ from yfinance sector names (Healthcare, Technology), so map them for criterion 14.
- Outliers: 71 stocks yield over 15% and 30 over 20%; one shows 117,452% (a worthless microcap). 429 yield under 1%.
- CCC coverage: 681 of the 684 DRIP CCC names are present. XOM (2.44%), CABO and TGLS are absent; XOM is inside a band, so Fidelity omitted it.
- Fill rates below: all stocks / DRIP CCC names. CCC names are covered much better than ADRs and microcaps.

## 4. Units cheat sheet
| Kind | Convention (observed unless noted) |
|---|---|
| Percent columns (yield, payout, growth rates, margins, ROE, ROA, ROI, returns, institutional ownership, debt/equity, debt to capital) | In percent units: 2.29 means 2.29%. Do not divide again. |
| Dollar amounts (Total Cash, Revenue, Free Cash Flow) | Millions of dollars: KO cash 16,371 and revenue 50,129. |
| Shares Outstanding, Volume (90 Day Avg) | Millions of shares: KO shares 4,302.5 and volume 16.96. |
| Standard Deviation (all periods) | Fraction: 0.18 means 18% annualised. |
| Beta | Plain number. |
| Coverage and liquidity ratios, price multiples | Plain multiples (x). |
| Exceptions to check | `Cash Flow Growth Rate (TTM vs. Prior TTM)` looks like a fraction (KO 0.098; median 0.06) while the 3 and 5-year versions are percents (KO 9.4 and 8.8). `Operating Margin (TTM/5 Year Avg.)` is a ratio near 1.0. `Net Insider Shares Bought` is tiny (median 0, 95th percentile 0.011), probably millions of shares; unverified. |

## 5. Column dictionary

### Search Criteria (62 columns)
| Column | Meaning | Fill | Notes |
|---|---|---|---|
| Symbol, Company Name | Ticker and name | 100 / 100 | |
| Security Type | See section 3 | 100 / 100 | |
| Security Price | Last price | 100 / 100 | Delayed |
| Dividend Yield | Indicated annual dividend / price, % | 100 / 100 | Differs from DRIP's by a median 0.16 points |
| Dividend | Current periodic dividend per share | 99 / 100 | Per payment, not annual |
| Dividend Payout % (Last Quarter) | Dividend / EPS, % | 61 / 85 | GAAP; REITs show 200%+ (O 220%); negative when EPS is negative |
| Dividend Growth Rate (5 Year Avg) | 5-year dividend growth, % | 65 / 100 | Within 1 point of DRIP's 5-yr DGR for 64% of names (median gap 0.5) |
| Dividend Growth Rate (IAD to Prior Yr) | Indicated annual dividend vs the prior year's, % | 73 / 100 | 0 or negative flags a freeze or cut (exit rule 3). IAD = indicated annual dividend |
| Dividend Coverage (EPS TTM/IAD) | Trailing EPS / annual dividend, x | 74 / 99 | Inverse of payout; below 1 means the dividend exceeds earnings |
| Dividend Coverage (EPS Next Yr/IAD) | Next-year EPS estimate / annual dividend, x | 63 / 96 | |
| Earnings Yield (TTM) | Trailing EPS / price, % | 67 / 95 | |
| Total Cash | Cash and equivalents, $M | 73 / 98 | One point in time |
| Revenue (TTM) | Trailing revenue, $M | 75 / 100 | |
| Jefferson Research | Jefferson Research rating: Buy, Hold, Sell, `--` | 100 / 100 | Overall rating, not the quality grades; filled for only 29% of stocks |
| Price/Book Ratio | Price / book value, x | 71 / 95 | Blank for some names (MCD, PG, JNJ); reason not stated, negative equity is one cause |
| Price/Sales Ratio | x | 70 / 99 | |
| Price/Cash Flow Ratio | x | 67 / 97 | |
| Total Debt/Equity (TTM) | %, KO 136.7 | 67 / 94 | Blank for some names (PG, JNJ); hugely negative when equity is negative (MCD about -3,514) |
| Free Cash Flow | $M, trailing | 64 / 86 | |
| Return on Equity (TTM) | % | 71 / 99 | |
| Return on Assets (TTM) | % | 71 / 99 | |
| EBITD Margin (TTM) | EBITDA margin, % | 61 / 87 | Spelled "EBITD" in the source |
| Gross Profit Margin (TTM) | % | 69 / 97 | |
| Forward EPS Long Term Growth (3-5 Yrs) | Analyst long-term EPS growth, % | 31 / 57 | Sparse |
| Book Value Growth (5 Yr average) | % | 70 / 98 | |
| P/E (Next Year's Estimate) | Price / next-year EPS estimate, x | 66 / 96 | |
| Current Ratio (Most Recent Qtr) | x | 47 / 65 | |
| Quick Ratio (Most Recent Qtr) | x | 46 / 64 | |
| Debt to Capital Ratio (Most Recent Qtr) | Debt / (debt + equity), % | 74 / 99 | Criterion 1 |
| Interest Coverage (Most Recent Qtr) | Earnings / interest expense, x | 55 / 74 | Criterion 1 |
| % Revenue to RD (Last FY) | R&D as % of revenue | 29 / 42 | Informational |
| Net Insider Shares Bought | Insider buying, units and period unverified | 62 / 97 | Never negative, so it cannot show net selling; criterion 12 only partly covered |
| Revenue Growth (5 Yrs / 3 Yrs / TTM vs. Prior TTM) | Revenue growth, % | 75 / 100 each (TTM 70 / 99) | 5-yr is the R term of ACN |
| Cash Flow Growth Rate (3 Yr / 5 Yr / TTM vs. Prior TTM) | Operating cash flow growth | 74 to 75 / 100 | TTM unit differs, see section 4. Cash flow, not cash balance (criterion 11 partial) |
| EPS Growth (3 Year History / 5 Year Historical) | Historical EPS growth, % | 63 / 93; 59 / 90 | 5-yr is the E term of ACN; annualised vs point-to-point is unchecked |
| EPS Growth (Proj Next Yr vs. This Yr) | Consensus growth, % | 66 / 96 | Criterion 10 (next-year EPS growth) |
| EPS Growth (Proj This Yr vs. Last Yr) | % | 64 / 95 | Duplicate of the Valuation tab column |
| Beta (3 / 5 / 10 Yr Annualized) | Beta | 90 / 86 / 76 | Informational |
| Total Return (3 / 5 / 10 Yr Annualized) | % | 92 / 89 / 77 | Informational |
| Standard Deviation (3 / 5 / 10 Yr Annualized) | Fraction | 91 / 88 / 76 | Informational |
| Zacks Investment Research | Zacks rating: OUTPERFORM, NEUTRAL, UNDERPERFORM | 71 / 93 | 2,040 rated: 1,706 neutral, 170 outperform, 164 underperform. Second analyst signal for criterion 13 |
| Trading Central | Technical signal: Buy, Sell, `--` | 100 / 100 | Technical pattern call, not used |
| Argus Analyst Opinions | Argus rating: Buy, Hold | 14 / 33 | Sparse |
| McLean Capital Management | Buy, Neutral, Sell, `--` | 100 / 100 | Mostly Neutral or `--`; low information |
| Shares Outstanding | Millions of shares | 100 / 100 | |
| Profit Margin (TTM) | Net margin, % | 70 / 98 | |
| Return on Investment (TTM) | % | 70 / 98 | Nearest to ROIC (criterion 10), current value only |
| Operating Margin (5 Year Avg) | % | 73 / 100 | |
| Operating Margin (TTM/5 Year Avg.) | Current operating margin / 5-yr average, ratio | 65 / 95 | Above 1.0 means margins are rising |
| SG&A Expense / Net Sales | % | 55 / 79 | Proxy for Jefferson's Operating Efficiency (criterion 3) |

### Basic Facts
| Column | Meaning | Fill | Notes |
|---|---|---|---|
| Volume (90 Day Avg) | Average daily shares, millions | 75 / 100 | Liquidity screen |
| Market Capitalization | Text with K/M/B/T suffix | 100 / 100 | Parse, see section 2 |
| Company Headquarters Location | Country name | 100 / 100 | Use "United States of America" to drop ADRs |
| Sector, Industry | GICS sector and industry | 100 / 100 | Criterion 14; `--` for 10 stocks |
| Optionable | Yes (Option Chain) or No | 100 / 100 | 1,705 yes, 1,178 no |

### Performance & Volatility
| Column | Meaning | Fill | Notes |
|---|---|---|---|
| Price Performance (52 Weeks) | Price change, % | 96 / 100 | |
| Total Return (1 Yr Annualized) | % | 96 / 100 | |
| Beta (1 Year Annualized) | Beta | 89 / 100 | Noisy (KO -0.06) |
| Standard Deviation (1 Yr Annualized) | Fraction | 88 / 100 | |

### Valuation, Growth & Ownership
| Column | Meaning | Fill | Notes |
|---|---|---|---|
| S&P Global Market Intelligence Valuation / Quality / Growth Stability / Financial Health | Scores 0 to 100, apparently percentile ranks | 66 to 69 / 96 to 100 | **Direction and scale unverified.** Spot values: JNJ Quality 89 and Financial Health 91, KO 45 and 26, PG 74 and 48, NEE Quality 31. Criterion 1 candidates once calibrated on known tickers |
| P/E (Price/TTM Earnings) | x, stored as text | 100 / 100 | `--` when negative or missing |
| PEG Ratio | x | 27 / 53 | Sparse |
| EPS Growth (Proj This Yr vs. Last Yr) | %, duplicate of Search Criteria | 64 / 95 | |
| Institutional Ownership | % of shares | 91 / 97 | Not insider activity |
| Institutional Ownership (Last vs. Prior Qtr) | Change, % | 94 / 100 | |

### Analyst Opinions
| Column | Meaning | Fill | Notes |
|---|---|---|---|
| Equity Summary Score (ESS) from LSEG StarMine | Very Bearish, Bearish, Neutral, Bullish, Very Bullish | 47 / 92 | Criterion 13. Counts: Neutral 463, Bearish 352, Bullish 311, Very Bearish 118, Very Bullish 111. Not the 0 to 10 StarMine scale in the original notes |
| Equity Summary Score Change (1 Month) | Stable, Moderate or Large Increase or Decrease | 47 / 92 | |
| LSEG I/B/E/S Estimates | Mean analyst recommendation, 1.5 to 3.1 in the middle 90% | 68 / 96 | Scale direction unverified (1 is probably strong buy; O is 2.68 with a Very Bearish ESS) |
| MSCI Overall ESG Rating, Environmental, Social, Governance | Leader, Average, Laggard | 47 / 88 to 90 | Governance is a weak stand-in for Morningstar Stewardship (criterion 2); informational |

## 6. Spot values for calibration (October snapshot)
| Ticker | Yield | Div growth 5-yr | Payout | ESS | S&P Quality | S&P Fin. Health | Debt/capital | Interest coverage |
|---|---|---|---|---|---|---|---|---|
| KO | 2.29 | 4.76 | 51.5 | Neutral | 45 | 26 | 52.8 | 12.7 |
| JNJ | 2.03 | 4.80 | blank | Neutral | 89 | 91 | blank | blank |
| PG | 2.70 | 4.59 | 55.9 | Neutral | 74 | 48 | 38.8 | 27.1 |
| O | 5.71 | 2.77 | 220.0 | Very Bearish | 53 | 26 | 44.1 | 2.2 |

## 7. Open checks
1. Why XOM (and CABO, TGLS) are missing, and whether the same happens in other months. Compare the DRIP CCC list with the screener after every merge.
2. Definition of Net Insider Shares Bought (period, units, sells).
3. Direction and scale of the four S&P scores and of the I/B/E/S estimate.
4. Whether Fidelity's 5-yr EPS and revenue growth are annualised or point-to-point, versus Finnhub CAGRs on a sample.
5. Unit of Cash Flow Growth (TTM vs. Prior TTM).
6. Whether the stocks with a blank for a given field are consistently the same ones (banks, REITs, small caps) so that "unknown" can be handled by sector.
