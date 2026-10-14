# div-invst

A personal dividend-investing screener. It aggregates dividend stock data and history, applies a fixed set of
criteria, and produces:

- a **ranked entry list** (what to buy) with per-criterion pass/fail, and
- an **exit list** for your current holdings (what to sell or review) showing which trigger fired.

Focus is on dividend Aristocrats, Champions and Contenders, but all US dividend payers are screened.

## Status
Planning complete, no code built yet. See `session_resume.md` for the current state and next steps.

## Documents
| File | Purpose |
|------|---------|
| `ideas_v1.md` | Original notes (untouched) |
| `ideas_v2.md` | Structured criteria, exit rules, decisions log |
| `PLAN.md` | Build plan, data sources, phases |
| `session_resume.md` | Session summary and next steps |

## Planned usage
```
uv run main.py                          # entry list only (no holdings)
uv run main.py --holdings holdings.csv  # entry list + exit report
```
(CLI is not implemented yet.)

## Inputs
- Optional holdings file (Excel or CSV): `ticker` required, `shares` optional. No cost basis needed.

## Outputs
- Ranked entry list (top 50): per-criterion pass/fail, coverage count.
- Exit report: price, target sell price, % upside, trigger(s) fired.

## Data
Free sources first (Dividend Radar / DRIP Investing lists, yfinance, FMP free tier, SEC EDGAR). See `PLAN.md`.
