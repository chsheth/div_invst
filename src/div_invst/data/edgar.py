"""SEC EDGAR XBRL company facts, reduced to annual series per field.

The full facts file is several MB per company, so only the fields below are kept: {field: {fiscal_year: [value, tag,
filed]}}. Each field is a fallback chain of us-gaap tags (earlier tags win per year). Per fiscal year the value from the
most recently filed 10-K is used, so figures restated for a split are picked up where a later 10-K shows the year.
Older years can still be as originally reported: `split_adjust` fixes per-share values with the split history.
EDGAR_USER_AGENT (name and email) is required by the SEC.
"""
import os
from datetime import date, datetime
from functools import lru_cache

from . import http
from .symbols import vendor

PAUSE = 0.2  # SEC allows 10 requests/second
YEARS = 15

# The SEC ticker map points some tickers at a successor entity with no filing history: ticker -> CIK with the 10-K facts.
CIK_OVERRIDES = {
    "XOM": "0000034088",  # ExxonMobil Holdings Corp (2115436) has no history yet; Exxon Mobil Corp does
}

# field -> (unit, kind, tag chain); kind is flow (about one year) or instant
FIELDS = {
    "eps_diluted": ("USD/shares", "flow", ["EarningsPerShareDiluted", "EarningsPerShareBasicAndDiluted"]),
    "net_income": ("USD", "flow", ["NetIncomeLoss", "ProfitLoss"]),
    "revenue": ("USD", "flow", ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet",
                                "RevenuesNetOfInterestExpense",
                                "RevenueFromContractWithCustomerIncludingAssessedTax"]),
    "operating_income": ("USD", "flow", ["OperatingIncomeLoss"]),
    "interest_expense": ("USD", "flow", ["InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt",
                                         "InterestExpenseDebtExcludingAmortization", "InterestPaidNet", "InterestPaid"]),
    "op_cash_flow": ("USD", "flow", ["NetCashProvidedByUsedInOperatingActivities"]),
    "dividends_paid": ("USD", "flow", ["PaymentsOfDividendsCommonStock", "PaymentsOfDividends",
                                       "PaymentsOfOrdinaryDividends", "DividendsCommonStockCash", "DividendsCash",
                                       "DividendsCommonStock"]),
    "dps_declared": ("USD/shares", "flow", ["CommonStockDividendsPerShareDeclared",
                                            "CommonStockDividendsPerShareCashPaid"]),
    "equity": ("USD", "instant", ["StockholdersEquity",
                                  "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"]),
    "cash": ("USD", "instant", ["CashAndCashEquivalentsAtCarryingValue",
                                "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents", "CashAndDueFromBanks",
                                "CashCashEquivalentsAndShortTermInvestments", "Cash"]),
    "long_term_debt": ("USD", "instant", ["LongTermDebt", "LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations",
                                          "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities",
                                          "LongTermNotesPayable", "NotesPayable", "SeniorNotes", "UnsecuredDebt"]),
    # REIT FFO proxy: net income + D&A + real-estate impairments - gains on property sales (validated 2026-10-26, docs/research/reit_ffo_validation_2026-10-26.md).
    # Some REITs (PLD) report their gains on custom tags that company facts do not carry: the proxy then overstates FFO.
    "depreciation": ("USD", "flow", ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization",
                                     "DepreciationAmortizationAndAccretionNet", "Depreciation", "RealEstateDepreciation"]),
    "impairment": ("USD", "flow", ["ImpairmentOfRealEstate", "AssetImpairmentCharges"]),
    "property_sale_gain": ("USD", "flow", ["GainLossOnSaleOfPropertiesNetOfApplicableIncomeTaxes",
                                           "GainLossOnSaleOfProperties", "GainLossOnSaleOfPropertiesBeforeApplicableIncomeTaxes",
                                           "GainLossOnSaleOfRealEstateInvestmentPropertyNetOfTax",
                                           "GainLossOnSaleOfPropertyPlantEquipment"]),
}
PER_SHARE = ("eps_diluted", "dps_declared")


def _headers() -> dict:
    ua = os.environ.get("EDGAR_USER_AGENT")
    if not ua:
        raise RuntimeError("EDGAR_USER_AGENT is not set")
    return {"User-Agent": ua}


@lru_cache(maxsize=1)
def ticker_map() -> dict[str, str]:
    body = http.get("https://www.sec.gov/files/company_tickers.json", headers=_headers(), sleep=PAUSE)
    return {v["ticker"].upper(): str(v["cik_str"]).zfill(10) for v in body.values()}


def fiscal_year(end: str) -> int:
    """52/53-week filers (JNJ) end in the first days of January: count that as the prior year."""
    return int(end[:4]) - (1 if end[5:7] == "01" and int(end[8:10]) <= 7 else 0)


def annual(facts: dict, unit: str, kind: str, tags: list[str]) -> dict[int, list]:
    """{fiscal_year: [value, tag, filed]} from 10-K entries; earlier tags win, the latest filing wins within a tag."""
    merged: dict[int, list] = {}
    gaap = facts.get("facts", {}).get("us-gaap", {})
    for tag in tags:
        per_tag: dict[int, list] = {}
        for e in gaap.get(tag, {}).get("units", {}).get(unit, []):
            end = e.get("end")
            if not str(e.get("form", "")).startswith("10-K") or not end:
                continue
            if kind == "flow":
                start = e.get("start")
                if not start or not 340 <= (datetime.fromisoformat(end) - datetime.fromisoformat(start)).days <= 380:
                    continue
            year, filed = fiscal_year(end), e.get("filed", "")
            if year not in per_tag or filed >= per_tag[year][2]:
                per_tag[year] = [e["val"], tag, filed]
        for year, row in per_tag.items():
            merged.setdefault(year, row)
    return merged


def fetch(symbol: str) -> dict:
    cik = CIK_OVERRIDES.get(symbol) or ticker_map().get(vendor(symbol))
    if not cik:
        raise RuntimeError(f"{symbol} is not in the SEC ticker map")
    facts = http.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json", headers=_headers(), sleep=PAUSE)
    floor = date.today().year - YEARS
    fields = {}
    for name, (unit, kind, tags) in FIELDS.items():
        rows = {y: r for y, r in annual(facts, unit, kind, tags).items() if y >= floor}
        if rows:
            fields[name] = rows
    out = {"cik": cik, "entity": facts.get("entityName"), "fields": fields}
    if not fields:
        out["warning"] = "no 10-K facts; likely a successor entity, add the old CIK to CIK_OVERRIDES"
    return out


def split_adjust(value: float, filed: str, splits: list[list]) -> float:
    """Per-share value as filed on `filed` (YYYY-MM-DD), restated for splits after that date.
    splits: [[ex_date, ratio], ...] with ratio new shares per old share (4:1 is 4.0)."""
    factor = 1.0
    for ex_date, ratio in splits:
        if ex_date > filed:
            factor *= ratio
    return value / factor
