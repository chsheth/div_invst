# Documentation index

One home per topic: each fact lives in exactly one file and the others link to it.

| Folder | File | What it holds | Changes when |
|--------|------|---------------|--------------|
| `criteria/` | `ideas_v1.md` | The original notes, untouched | Never |
| | `ideas_v2.md` | **The spec:** universe, scoring and ranking, the 15 criteria with thresholds, proxy scores, exit rules | A rule or threshold changes |
| | `decisions_log.md` | Why: dated decisions, calibration findings, superseded options (newest last) | Every decision |
| `plan/` | `PLAN.md` | Design, build slices and their status, verification | A slice moves |
| `guides/` | `monthly_drop.md` | The monthly routine: files to download, commands, checks, what each file feeds | The process changes |
| `research/` | `data_sources.md` | What each data source can supply, current status, refresh cadence | A source is re-tested |
| | `coverage_spike_2026-10-19.md`, `revision_spike_2026-10-21.md` | Spike results (21 tickers): source verdicts, revision data coverage | Never (dated records) |
| | `fidelity_screener.md` | The Fidelity screener download: layout, units, columns, fill rates, mapping to criteria | The screen changes |
| | `reit_ffo_validation_2026-10-26.md` | REIT FFO proxy checked against reported FFO | Never (dated record) |
| `sessions/` | `session_resume.md` | Live state: open items and next steps (start here) | Every session |
| | `session_log.md` | History of each session | Every session (new entry on top) |
| `reference/` | `<YYYY-MM>/` | Monthly vendor files (gitignored) and a short README per month | Monthly |

Rules:
- The spec (`ideas_v2.md`) states the current rule only; the reasoning and the old versions go in `decisions_log.md`.
- `session_resume.md` holds open items and next steps only, never a rule; finished work moves to `session_log.md`.
- Numbers live in `config/criteria.toml`; the docs describe them and name the config key, they do not restate every value elsewhere.
- The root `README.md` stays high level and links here; `CLAUDE.md` holds the working rules and code map for the assistant.
