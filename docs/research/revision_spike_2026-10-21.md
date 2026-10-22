# Revision data spike results (2026-10-21)

Script: `scripts/revision_spike.py`. Raw output (gitignored): `data/revision_out/report.md`, `results.json`, daily snapshots in `data/revision_out/snapshots/`.
Tickers (21): same as the coverage spike. Purpose: can free sources supply a StarMine-style analyst-revision proxy for criterion 13?

## Verdict
- **Yes.** yfinance covers 21/21 for `eps_trend` (consensus now vs 7/30/60/90 days ago), `eps_revisions` (up/down counts), analyst counts, price targets, 4-quarter earnings history, and dated `upgrades_downgrades` (back to about 2012).
- Finnhub free: recommendations only 4 months deep (enough for a 3-month trend); earnings surprises 21/21; price targets gated (premium).
- yfinance revision data is point-in-time, so store a snapshot every run to build longer revision history.
- Caveat: thin coverage on some names (PLD shows 2 analysts). Calibrate the proxy against a few Fidelity StarMine scores looked up by hand (MCD, XOM, CVX, ED sit at the extremes).
- Proxy weights and pass cutoff (0-10, pass at 7+): see criterion 13 in `../criteria/ideas_v2.md`.

## Coverage

| Field | Tickers with data |
|---|---|
| yfinance eps_trend complete (now/7/30/60/90d) | 21/21 |
| yfinance eps_revisions up/down counts | 21/21 |
| yfinance analyst count | 21/21 |
| yfinance price target | 21/21 |
| yfinance earnings history (4 qtrs) | 21/21 |
| yfinance dated rating changes | 21/21 |
| Finnhub recommendation history (12+ months) | 0/21 |
| Finnhub earnings surprises | 21/21 |
| Finnhub price target (free tier) | 0/21 |

## Revision signals

FY = current fiscal year consensus EPS now vs 30/90 days ago. Rating changes are dated up/down actions in the last 90 days.

| Ticker | Analysts | FY EPS 30d | FY EPS 90d | Up/Down 30d | Target upside | Beats (yf) | Rating chg 90d up/down | Rec score | 3m delta |
|---|---|---|---|---|---|---|---|---|---|
| JNJ | 21 | +0.4% | -4.6% | 0/2 | +8.4% | 3/4 | 0/0 | 0.97 | 0.06 |
| KO | 25 | +0.1% | +1.1% | 3/0 | +2.6% | 4/4 | 0/0 | 1.03 | -0.06 |
| PG | 24 | -0.1% | -0.8% | 3/3 | +3.4% | 4/4 | 1/2 | 0.66 | -0.13 |
| MCD | 31 | -0.3% | -0.4% | 4/17 | +18.5% | 3/4 | 0/0 | 0.78 | 0.02 |
| ABBV | 27 | -0.4% | -1.5% | 0/10 | -0.5% | 3/4 | 2/0 | 1.08 | 0.05 |
| XOM | 17 | +13.1% | +19.9% | 7/0 | +0.7% | 3/4 | 1/2 | 0.61 | -0.12 |
| CVX | 24 | +8.0% | +19.7% | 12/2 | +1.7% | 4/4 | 0/0 | 1.03 | 0.07 |
| MMM | 14 | +2.0% | +2.2% | 4/3 | +8.3% | 4/4 | 1/0 | 0.64 | 0.03 |
| CAT | 27 | +0.5% | +10.5% | 1/1 | +27.8% | 4/4 | 1/1 | 0.79 | 0.03 |
| MSFT | 34 | +0.0% | +1.8% | 5/0 | +12.9% | 4/4 | 1/0 | 1.29 | 0.03 |
| AAPL | 39 | +0.0% | +0.6% | 2/2 | -4.5% | 4/4 | 1/3 | 0.76 | -0.12 |
| T | 18 | +0.8% | +1.1% | 3/4 | +30.5% | 4/4 | 2/0 | 0.85 | 0.05 |
| MO | 12 | +0.0% | -0.1% | 3/6 | -5.2% | 2/4 | 0/0 | 0.52 | -0.09 |
| O | 9 | -0.2% | -3.7% | 0/1 | +16.8% | 0/4 | 0/1 | 0.48 | 0.00 |
| PLD | 2 | -7.7% | +0.0% | 1/0 | +20.1% | 4/4 | 3/0 | 0.86 | -0.06 |
| NEE | 20 | -0.6% | -0.2% | 0/1 | +21.8% | 4/4 | 0/0 | 0.85 | -0.05 |
| DUK | 21 | +0.1% | +0.2% | 1/1 | +10.1% | 4/4 | 1/0 | 0.73 | 0.12 |
| ED | 15 | +0.0% | -0.1% | 1/0 | -2.8% | 3/4 | 1/0 | -0.42 | 0.00 |
| JPM | 14 | -0.2% | +0.3% | 5/0 | +11.2% | 2/4 | 0/0 | 0.70 | 0.03 |
| USB | 21 | +1.2% | +1.2% | 11/3 | +15.9% | 4/4 | 0/0 | 0.81 | 0.18 |
| WMB | 14 | -0.0% | +0.4% | 0/2 | +17.3% | 2/4 | 0/0 | 1.10 | 0.07 |

## Depth

| Ticker | yf rating-change span | yf rec buckets | Finnhub rec span | Finnhub earnings qtrs |
|---|---|---|---|---|
| JNJ | 390 (2012-04-16 .. 2026-10-16) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
| KO | 303 (2012-02-08 .. 2026-10-16) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
| PG | 347 (2012-02-28 .. 2026-10-20) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
| MCD | 691 (2012-03-06 .. 2026-10-20) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
| ABBV | 421 (2013-03-11 .. 2026-10-21) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
| XOM | 416 (2012-03-22 .. 2026-10-19) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
| CVX | 450 (2011-12-08 .. 2026-10-15) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
| MMM | 433 (2012-02-09 .. 2026-10-21) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
| CAT | 380 (2012-03-21 .. 2026-10-14) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
| MSFT | 949 (2012-03-16 .. 2026-10-21) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
| AAPL | 971 (2012-09-12 .. 2026-10-20) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
| T | 343 (2012-04-12 .. 2026-10-09) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
| MO | 162 (2012-07-24 .. 2026-08-11) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
| O | 216 (2012-04-05 .. 2026-10-20) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
| PLD | 327 (2012-02-24 .. 2026-10-21) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
| NEE | 353 (2012-03-20 .. 2026-10-21) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
| DUK | 362 (2012-05-24 .. 2026-10-21) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
| ED | 343 (2012-03-26 .. 2026-10-13) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
| JPM | 451 (2012-02-29 .. 2026-10-15) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
| USB | 509 (2012-03-30 .. 2026-10-16) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
| WMB | 286 (2012-04-26 .. 2026-10-14) | 4 | 4 (2026-07-01 .. 2026-10-01) | 4 |
