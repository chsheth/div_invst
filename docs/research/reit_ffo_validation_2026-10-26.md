# REIT FFO proxy: validation against reported FFO (2026-10-26)

Proxy as decided 2026-10-25: net income + D&A - gains on property sales, from EDGAR (`data/edgar.py`, `edgar_latest` in
`data/readers.py`). Reported figures: Realty Income Q4 2025 supplemental (FFO reconciliation, p. 10-11) and the Prologis
Q4 and full-year 2025 release (Nareit FFO reconciliation). $ millions.

| | Reported Nareit FFO | Proxy now | Gap | Proxy + impairment | Gap |
|---|---|---|---|---|---|
| O 2025 | 3,860.3 | 3,405.2 | -11.8% | 3,876.5 | +0.4% |
| O 2024 | 3,467.7 | 3,139.1 | -9.5% | 3,564.9 | +2.8% |
| PLD 2025 | 5,679.5 | 5,954.3 | +4.8% | n/a | |
| PLD 2024 | 5,794.6 | 6,312.2 | +8.9% | n/a | |

Why the gaps:
- **O:** Nareit FFO adds back real-estate impairments (434.5 in 2025, 319.0 in 2024), which the proxy omitted. EDGAR's
  `ImpairmentOfRealEstate` (471.3 and 425.8, slightly wider than the real-estate-only line) closes the gap to within 3%.
- **PLD:** the proxy found no property-sale gain tag for Prologis (reported gains 684.9 and 899.3 are not subtracted), so it
  overstates FFO. Prologis also adds the share of unconsolidated co-investment ventures (+551.0 in 2025), which no
  us-gaap tag gives us; that part stays missing. Its dividends in EDGAR (`PaymentsOfDividends`) are 3,764.7 and 3,570.5
  against 3,866 and 3,667 reported including LP units.
- Payout on reported FFO: O 75.7% (2025), 77.6% (2024); PLD 68.1% (2025). Dividends paid from EDGAR match O's reported
  distributions exactly (2,920.9).

Conclusion: the proxy lands within about +/-10% of reported FFO. Add the impairment add-back and a wider gain tag chain;
expect the payout to carry about 10% relative error, so the cutoff needs margin.

## Applied 2026-10-26
- Impairment add-back: `impairment` field in `data/edgar.py` (`ImpairmentOfRealEstate`, then `AssetImpairmentCharges`); `edgar_latest`
  now computes FFO = net income + D&A + impairment - gains. Live check: O 2025 FFO 3,876.5 vs reported 3,860.3 (+0.4%), payout 75.3%.
- Gain tags: added `GainLossOnSaleOfPropertiesBeforeApplicableIncomeTaxes`. Prologis has no us-gaap gain tag in company facts
  (checked every gain and disposal tag; its gains are on custom tags the facts endpoint does not carry), so PLD stays 4.8% high
  (payout 63.2% vs 68.1% reported). `ffo_gain_known` and `ffo_impairment_known` on the cache record show when a tag was missing.
- Cutoff: `[reit] max_ffo_payout = 0.85` in `config/criteria.toml`; criterion 3's earnings-quality sub-score now uses it for REITs
  (100 at or below 85%, 60 up to 100%, 0 above). Criterion 1 will use the same value when it is built.

