# Monthly reference drop: what to download, where it goes

Do this once a month. Everything lands in one folder, `docs/reference/<YYYY-MM>/`, where `<YYYY-MM>` is the month the lists are published (the data inside is as of the prior month-end). The folder is gitignored because the files are licensed vendor material. If you skip a month, the loaders fall back to the latest earlier folder and mark the data stale.

Run every command from the repo root.

## 1. Create the folder
```
mkdir docs/reference/2026-11
```
Use the exact `YYYY-MM` name. Use the file names below exactly; the loaders look for them by name.

## 2. Drop the files

| Step | File name | Required | Where it comes from | How |
|------|-----------|----------|---------------------|-----|
| a | `drip_ccc.csv` | yes | DRIP Investing "All CCC" export, sent by email | Save the attachment into the folder and rename it. Keep the original columns untouched. |
| b | `screener_results*.xls` files, then `screener_results.xlsx` | yes | Fidelity stock screener | Download one `.xls` per yield band (see below), save them all in the folder with their default names, then run `uv run --python 3.13 scripts/merge_screener.py`. The merged `screener_results.xlsx` is the monthly file, saved in the folder like `drip_ccc.csv`. |
| c | `morningstar_large_cap.pdf` | optional | Morningstar US Large Cap Pick List (monthly PDF) | Save and rename. |
| d | `morningstar_mid_cap.pdf` | optional | Morningstar US Mid Cap Pick List (monthly PDF) | Save and rename. |
| e | `argus_top30.pdf` | optional | Argus Portfolio Selector, the issue with the Top 30 and the Stock Screen | Save and rename. |
| f | `ratings.csv` | optional | Your own notes | Columns `as_of, ticker, source, rating, target_price`. |

### Fidelity screener (step b)
Column reference, units and parsing rules: `docs/research/fidelity_screener.md`.
- Use the same saved screen every month, with all five tabs/views: Search Criteria, Basic Facts, Performance & Volatility, Valuation Growth & Ownership, Analyst Opinions. The Search Criteria view must carry the full 62 columns (listed in `ideas_v2.md`, "Fidelity screener"). Do not add, remove or rename columns, because the merge stops if the files disagree.
- Add fields as display columns only. Do not set criteria on margins, ROI, SG&A, insider activity or similar fields: Fidelity drops every stock with a blank value in a field it filters on.
- Split the download into yield bands, because Fidelity caps an export at 500 rows. October used seven: 6% and up, 4–6%, 3–4%, 2.25–3%, 1.5–2.25%, 0.75–1.5% and 0.07–0.75%. Check each band's count before downloading and move an edge if it is over 500. Bands may touch at an edge; the merge removes the duplicate.
- Do not filter on Security Type in Fidelity. ADRs (about a third of the rows) are removed later in code, and that keeps the files comparable month to month.
- Download all bands on the same day. The snapshot date is printed in the footer of each file.
- The merge never edits the raw `.xls` files. Once `screener_results.xlsx` looks right, keep only that file and delete the raw downloads (they can be downloaded again); only that file is read afterwards. Rerunning the merge needs the raw files back in the folder.
- Run the merge. It prints each file's row count and yield range: check that the ranges line up with no gap and no overlap beyond a shared edge. It refuses to run if two files share more than 5% of their symbols (a copy; delete one and rerun).
- Known gap: XOM was missing from the October download (2.44% yield, inside a band), so after each merge compare the DRIP CCC list with the screener and look up any missing names by hand.

## 3. Check the folder
```
uv run --python 3.13 scripts/check_month.py                 # newest month
uv run --python 3.13 scripts/check_month.py --month 2026-11
```
It prints one line per file: found or missing, whether it loads, and a count. Typical October result:

```
ok  drip_ccc.csv                 684 stocks
ok  screener_results.xlsx        2883 stocks, 5 tabs
ok  morningstar_large_cap.pdf    60 picks, 7 deletions, as of 2026-09-30
ok  morningstar_mid_cap.pdf      30 picks, 7 deletions, as of 2026-09-30
ok  argus_top30.pdf              30 top 30, 30 screen
```
What to look at:
- **Counts far from last month** (for example 684 CCC stocks dropping to 400, or 30 Argus rows dropping to 0) mean a wrong file or a changed layout.
- **`FAILED` on a PDF** means the layout changed. The parser raises on any row it cannot read rather than skipping it. Send the file or the error and the parser gets adjusted.
- **A missing optional file** is fine; criteria that use it stay unknown for that month.
- **The "raw .xls newer than the .xlsx" note:** rerun the merge in step b.

## 4. Build the combined dataset
```
uv run --python 3.13 scripts/build_dataset.py
```
Joins DRIP, the screener, Morningstar and Argus into one row per ticker and writes `data/dataset/<YYYY-MM>.csv` (columns prefixed `drip_`, `scr_`, `ms_`, `argus_`; percent fields are fractions). It prints the join summary: tickers per source, Morningstar and Argus names missing from the screener, CCC names missing from the screener (October: CABO, TGLS, XOM) and how complete the key fields are for CCC names. Look at the missing-CCC list each month.

## 5. Follow-up
- Update the folder's own `README.md` if a file's source or format changed.

## What each file feeds
| File | Used for |
|------|----------|
| `drip_ccc.csv` | CCC universe, tier and streak band (criterion 7) |
| `screener_results.xlsx` | StarMine score and Zacks (13), interest coverage, debt to capital and S&P scores (1), 5-yr EPS and revenue growth (ACN, 6), ROI and next-year EPS growth (10), SG&A and margins (3 proxy), insider buying (12, partial), multiples (9), sector (14), dividend cut check (exit rule 3) |
| Morningstar PDFs | Fair value cross-check (8), rating, moat, uncertainty (2, 3); "deleted" status is a possible exit signal |
| Argus PDF | Financial Strength grade (1), target-style cross-checks |

Detail on each source's columns and verdicts: `docs/criteria/ideas_v2.md` ("Monthly reference inputs", "Fidelity screener"). The loaders live in `src/div_invst/reference/` (one module per source).

## Code map
| Piece | File |
|-------|------|
| CCC universe loaders | `src/div_invst/reference/ccc.py` |
| Morningstar pick-list loader | `src/div_invst/reference/morningstar.py` |
| Argus loader | `src/div_invst/reference/argus.py` |
| Shared helpers (month folder lookup, cell cleaning, PDF text) | `src/div_invst/reference/common.py` |
| Screener merge | `scripts/merge_screener.py` |
| Folder check | `scripts/check_month.py` |
| Screener loader (5 tabs joined, units converted) | `src/div_invst/reference/screener.py` |
| Combined dataset (one record per ticker, sources side by side) | `src/div_invst/reference/dataset.py`, `scripts/build_dataset.py` |

