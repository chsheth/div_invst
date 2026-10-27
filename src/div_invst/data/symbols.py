"""Vendor ticker symbols. The dataset writes class shares as BF/B (DRIP, screener) or BRK.B; Yahoo and the SEC ticker map
spell them BF-B and BRK-B, and Finnhub accepts the dash too (a slash returns nothing). The store keeps the dataset's own ticker."""


def vendor(symbol: str) -> str:
    return symbol.upper().replace("/", "-").replace(".", "-")
