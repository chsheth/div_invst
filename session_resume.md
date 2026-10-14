# Session Resume

_Last updated: 2026-10-13 (session 1)_

## How to resume
Read `ideas_v2.md` (criteria + decisions log), then `PLAN.md` (build plan and data sources). This file lists where we stopped.
`ideas_v1.md` is the untouched original notes.

## Session 1 summary (2026-10-13)
- Reviewed `ideas_v1.md` (8 criteria + SBI factors + ACN formula).
- Interviewed user; all decisions are recorded in the `ideas_v2.md` Decisions log.
- Researched free data sources (CCC lists, yfinance, FMP, SEC EDGAR, Finnhub candidates); added to `PLAN.md`.
- Designed the Financial Strength proxy score for the credit-quality criterion.
- Plan approved. Created `PLAN.md`, `ideas_v2.md`, `README.md`, `session_resume.md`. `ideas_v1.md` left untouched.

## Key decisions
- Free data first; paid only if inadequate.
- Universe: all US dividend payers, CCC flagged primary.
- Output: ranked entry list (top 50) + exit list showing which trigger fired.
- Exit triggers: fair-value ceiling (+15%), yield <= 50% of 5-yr avg, fundamental break.
- Equal-weighted pass/fail; coverage-aware ranking (70% min).
- CLI + SQLite cache with run snapshots.
- Holdings: Excel/CSV, no cost basis. Works without a holdings file.

## Repo state
- `main.py`: hello-world stub. `pyproject.toml`: requires-python >=3.14 (may need lowering), no deps.
- No commits yet; all files untracked.

## Next steps (ordered)
1. Data spike: ~20 tickers, check per-criterion field coverage across yfinance, FMP, Finnhub, SEC EDGAR; verify CCC file URLs; confirm Python version.
2. Update the criteria data map in `PLAN.md` and `ideas_v2.md` with spike results.
3. Build data layer + SQLite cache (`src/div_invst/`).
4. Criteria engine + Financial Strength proxy + TOML config.
5. Holdings loader + diversification cut.
6. Fair value, ranking, entry report; exit triggers + exit report.
7. Tests and CLI.

## Open questions
- User to provide holdings file (layout TBD).
- Is the 15% exit margin right?
- ADRs/foreign listings after v1?
