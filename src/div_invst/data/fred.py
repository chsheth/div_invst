"""FRED series as [[date, value], ...] (market-wide, no ticker)."""
import csv
import io

from . import http

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
SERIES = {"DGS10": 400, "CPIAUCSL": 40}  # series id -> rows kept (about 1.5 years daily, 3+ years monthly)


def fetch(series_id: str) -> list[list]:
    text = http.get(URL, params={"id": series_id}, parse="text", sleep=0.3)
    rows = []
    for date, value in list(csv.reader(io.StringIO(text)))[1:]:
        try:
            rows.append([date, float(value)])
        except ValueError:
            continue  # FRED marks holidays with "." or blank
    return rows[-SERIES.get(series_id, 400):]
