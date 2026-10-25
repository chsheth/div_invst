# div-invst

Personal dividend-investing screener: ranked top-50 entry list with per-criterion pass/fail, and an exit list for holdings.
Start with `docs/sessions/session_resume.md` (state, open items, next steps). `docs/criteria/ideas_v2.md` is the source of
truth for criteria, thresholds and the decisions log; `docs/plan/PLAN.md` has the build slices.

## Commands
- `uv run --python 3.13 scripts/<name>.py`: scripts carry PEP 723 dependency headers (see README "Scripts").
- `uv run python -m unittest discover -s tests`: unit tests (stdlib unittest, no pandas dependency).
- Monthly flow: `docs/guides/monthly_drop.md` (merge_screener, check_month, build_dataset, run_screen).

## Code map
- `src/div_invst/reference/`: loaders for the monthly files in `docs/reference/<YYYY-MM>/` and the combined per-ticker dataset.
- `src/div_invst/criteria/`: one function per criterion, registered with `@criterion`; `engine.py` ranks.
- `config/criteria.toml`: all thresholds and macro inputs. Change numbers there, not in code.
- Reports go to `data/reports/<month>/` (gitignored).

## Rules
- Percent fields are fractions in every loader; screener cash/FCF/revenue are $ millions (`_m`), market cap is dollars.
- Criteria return pass / fail / unknown / na; missing data is unknown, never a fail.
- Free data sources first; paid only if inadequate.
- `docs/reference/` (licensed vendor files), `data/` and `.env` are gitignored: never commit them or any API key.
- Dividend Vision is dropped (terms prohibit automated extraction): do not scrape it.
- Commit and push only when asked. Commit messages end with the attribution line from the session reminder.
- Update the docs (PLAN, session_resume, ideas_v2 decisions log) when a decision or a threshold changes.
- Use they/them for anyone whose pronouns are not stated.
