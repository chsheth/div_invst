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
- Use the same saved screen every month, with all five tabs/views: Search Criteria, Basic Facts, Performance & Volatility, Valuation Growth & Ownership, Analyst Opinions. The Search Criteria view must carry the full 62 columns (listed in `docs/research/fidelity_screener.md` section 5). Do not add, remove or rename columns, because the merge stops if the files disagree.
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

## 5. Refresh the market data cache
```
uv run --python 3.13 scripts/refresh_data.py                  # the rankable pool plus anything already cached
uv run --python 3.13 scripts/refresh_data.py --scope ccc      # CCC names only; --scope top50, --tickers JNJ,KO, --kinds edgar,yf_splits also work
```
Fills `data/cache/div_invst.sqlite` from yfinance, Finnhub, EDGAR and FRED. Only snapshots older than their max age (`[refresh]` in `config/criteria.toml`) are fetched, so a rerun is cheap and an interrupted run resumes. The first full pass takes hours (Finnhub allows about one call per second); load `.env` keys first (`FINNHUB_API_KEY`, `EDGAR_USER_AGENT`). Criteria 1, 7, 8, 10, 11, 12 and the 13 fallback stay unknown for tickers that are not cached.

## 6. Run the screen
`uv run --python 3.13 scripts/run_screen.py` writes `data/reports/<YYYY-MM>/top50.md` and `top50.csv`. The 10-yr Treasury and inflation come from the cached FRED series when the cache exists; the S&P yield is still a manual input in `config/criteria.toml` (`[macro]`): update it monthly.

## 7. Follow-up
- Update the folder's own `README.md` if a file's source or format changed.

## What each file feeds
| File | Used for |
|------|----------|
| `drip_ccc.csv` | CCC universe, tier and streak band (Stock Type: Challenger 5-9, Contender 10-24, Champion 25-49, King 50+ years; criterion 7). Also yield, 5Y average yield, DGR 1/3/5/10Y, Chowder number (equals yield + DGR 5Y, not independent), Peter Lynch fair value, ROE, debt/capital, P/E, P/BV, PEG |
| `screener_results.xlsx` | StarMine ESS (13), Zacks, McLean, Jefferson and I/B/E/S ratings (15), interest coverage and debt to capital (1, 3), 5-yr dividend, EPS and revenue growth (5, 6), ROI, margins and SG&A (3), multiples (9), MSCI governance (2), sector (14), dividend cut check (exit rule 3). Field-by-field mapping: `docs/research/fidelity_screener.md` section 8 |
| Morningstar PDFs | Rating and moat, fair value cross-check (8), star rating in the agreement panel (15). Names are picks only, so absence says nothing; the "Pick List Deletions" table gives status `deleted`, shown as an informational note, not an exit trigger |
| Argus PDF | Financial Strength grade, Analyst Opinions (15), target-style cross-checks. PDFs are read with PyMuPDF sorted-text extraction (its table finder splits decimals) |

Detail on each source's columns and verdicts: `docs/research/fidelity_screener.md` (screener), `docs/research/data_sources.md` (all sources). The code map is in the root `CLAUDE.md`; loaders live in `src/div_invst/reference/`.
