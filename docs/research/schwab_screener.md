# Schwab stock screener export

Second manual monthly screener, next to Fidelity's. Evaluated 2026-11-06 on the November export. Loader: `src/div_invst/reference/schwab.py`;
merge: `scripts/merge_schwab.py`; how to download it: `../guides/monthly_drop.md`. The decision and its reasons: `../criteria/decisions_log.md` (2026-11-06).

## Layout
- One CSV per yield band (`Results (N).csv`, UTF-8 with a BOM). The November export had 22 columns; the loader reads six. Schwab caps an export at **1,000 rows** and cuts
  the list off alphabetically (the first November try, 0 to 1.98%, ended at "BCGWW" and lost 255 of the 257 CCC names that were missing), so split
  a band that returns exactly 1,000 rows. November used six bands: 6%+, 4-6%, 3-4%, 2-3%, 0.75-2%, 0.07-0.75%.
- Columns the loader needs (it stops if one is missing): Symbol, Description, CFRA Star Ranking, Morningstar Rating, Morningstar Fair Value Estimate,
  Morningstar Economic Moat. Select only these when downloading; Add `Annual Dividend Yield` too if you want `merge_schwab.py` to print each band's yield range (it is optional). Percents come as text ("3.1%"), "--" is blank.
- Symbols follow Fidelity's spelling (CIG/C), so the join is on the ticker. Tickers are sometimes reused or renamed, and the Description can then name a different company (BEPC, JBTC). `same_company` ignores a Schwab row whose description shares no significant word with the
  screener's company name; `build_dataset` lists the ignored tickers (November: ARRPY, BEPC, JBTC, JILL, LRLCY, MGYOY, SSREY).
- Schwab adds no tickers to the dataset (3,666 in the file, 2,866 join): it only enriches names the other sources already have.

## Columns used
| Field | Fill, CCC names | Used for |
|-------|----------------|----------|
| CFRA Star Ranking (`cfra_stars`, 1-5) | 95% | A vote in criterion 15: 4-5 stars +1, 3 neutral, 1-2 -1 (`cfra_buy_at_least`, `cfra_sell_at_most`) |
| Morningstar Fair Value Estimate (`ms_fair_value`) | 46% | Criterion 8 cross-check: shown beside our fair value, flagged when below the price, never decides |
| Morningstar Rating, Economic Moat (`ms_stars`, `ms_moat`) | 46% | Carried in the dataset, not used by a criterion (the PDF pick-list star vote in criterion 15 is unchanged) |

"dropping coverage", "Rating Drop" and "notrated" rows (43 CCC names) get no rating and no fair value; `ms_status` says why.

## Columns checked and not used
Agreement of each rating (as +1 / 0 / -1) with the mean of the five votes already in criterion 15, on CCC names (r): CFRA 0.17, Market Edge 0.11, Schwab Equity Rating 0.14,
Morningstar -0.12 (stars measure cheapness, so it is a contrarian vote). For comparison the existing votes against the other four: Argus 0.19, I/B/E/S 0.05, Zacks 0.05,
McLean 0.02, Jefferson 0.01. Low agreement among raters is normal, and none of this says which one predicts returns (backtest: `../sessions/session_resume.md`).
- **Argus 12 Month Rating:** equals Fidelity's Argus opinion in every shared name (155 of 155); redundant.
- **I/B/E/S mean over 30, 60 and 90 days:** direction words only ("No Change" for 94%), no numbers; Fidelity has the numeric mean.
- **Dividend growth, payout, coverage, yield columns:** Fidelity already supplies them.
- **Market Edge Second Opinion Weekly:** 36% "Avoid" against 29% "Long" on CCC names, weakest agreement of the new raters; skipped.
- **Schwab Equity Rating:** fully filled, mostly "NC" (not covered) overall; skipped as a third rating from the same family as the others.

## Morningstar here against the PDF
On 29 tickers in both the mid cap PDF and the Schwab export, fair values match on 24 and differ by 2-9% on four (ALB, LPLA, ZBH, CRH); star ratings differ by a star on
several because Schwab's are priced live while the PDF is as of 2026-10-30. Criterion 15 still votes the PDF's stars for pick-list names only.
