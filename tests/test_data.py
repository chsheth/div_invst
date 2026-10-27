import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from div_invst.criteria import load_config  # noqa: E402
from div_invst.data.refresh import refresh  # noqa: E402
from div_invst.data.store import Store  # noqa: E402

T0 = datetime(2026, 10, 26, tzinfo=timezone.utc)


class StoreTest(unittest.TestCase):
    def test_latest_history_and_age(self):
        s = Store(":memory:")
        s.put("yahoo", "yf_info", "KO", {"p": 1}, T0)
        s.put("yahoo", "yf_info", "KO", {"p": 2}, T0 + timedelta(days=2))
        self.assertEqual(s.latest("yahoo", "yf_info", "KO")[1], {"p": 2})
        self.assertEqual([p for _, p in s.history("yahoo", "yf_info", "KO")], [{"p": 1}, {"p": 2}])
        self.assertIsNone(s.latest("yahoo", "yf_info", "KO", 1, T0 + timedelta(days=4)))
        self.assertIsNotNone(s.latest("yahoo", "yf_info", "KO", 3, T0 + timedelta(days=4)))
        self.assertIsNone(s.latest("yahoo", "yf_info", "PG"))
        self.assertEqual(s.tickers("yf_info"), {"KO"})


class RefreshTest(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()
        self.calls = []

        def info(t):
            self.calls.append(t)
            if t == "BAD":
                raise RuntimeError("boom")
            return {"t": t}

        self.fetchers = {"yf_info": ("yahoo", info, True)}

    def test_skips_fresh_retries_errors_and_keeps_going(self):
        s = Store(":memory:")
        a = refresh(s, ["JNJ", "BAD", "KO"], self.cfg, fetchers=self.fetchers, now=T0, log=lambda m: None)
        self.assertEqual((a["fetched"], a["fresh"], len(a["errors"])), (2, 0, 1))
        self.calls.clear()
        b = refresh(s, ["JNJ", "BAD", "KO"], self.cfg, fetchers=self.fetchers, now=T0 + timedelta(hours=1), log=lambda m: None)
        self.assertEqual((b["fetched"], b["fresh"]), (0, 2))
        self.assertEqual(self.calls, ["BAD"])  # failed fetch was not stored, so it is retried
        c = refresh(s, ["JNJ"], self.cfg, fetchers=self.fetchers, now=T0 + timedelta(days=2), log=lambda m: None)
        self.assertEqual(c["fetched"], 1)
        self.assertEqual(len(s.history("yahoo", "yf_info", "JNJ")), 2)  # snapshots accumulate

    def test_every_fetcher_has_a_max_age(self):
        from div_invst.data.refresh import FETCHERS
        self.assertTrue(set(FETCHERS) <= set(self.cfg["refresh"]))


class EdgarTest(unittest.TestCase):
    def test_annual_picks_latest_filing_and_filters(self):
        from div_invst.data import edgar
        e = lambda start, end, val, filed, form="10-K": {"start": start, "end": end, "val": val, "filed": filed, "form": form}
        facts = {"facts": {"us-gaap": {
            "EarningsPerShareDiluted": {"units": {"USD/shares": [
                e("2017-01-01", "2017-12-31", 6.24, "2018-02-20"),
                e("2017-01-01", "2017-12-31", 1.56, "2021-02-20"),       # later 10-K, restated for the split
                e("2017-04-01", "2017-06-30", 9.99, "2017-08-01"),       # quarter, dropped
                e("2018-01-01", "2018-12-31", 7.0, "2019-02-20", "10-Q"),  # not a 10-K, dropped
            ]}},
            "EarningsPerShareBasicAndDiluted": {"units": {"USD/shares": [e("2017-01-01", "2017-12-31", 5.0, "2018-02-20"),
                                                                        e("2016-01-01", "2016-12-31", 1.2, "2017-02-20")]}}}}}
        got = edgar.annual(facts, "USD/shares", "flow", edgar.FIELDS["eps_diluted"][2])
        self.assertEqual(got[2017][:2], [1.56, "EarningsPerShareDiluted"])
        self.assertEqual(got[2016][1], "EarningsPerShareBasicAndDiluted")  # falls back to the next tag
        self.assertNotIn(2018, got)

    def test_fiscal_year_and_split_adjust(self):
        from div_invst.data import edgar
        self.assertEqual((edgar.fiscal_year("2023-12-31"), edgar.fiscal_year("2023-01-01"), edgar.fiscal_year("2023-01-20")), (2023, 2022, 2023))
        self.assertAlmostEqual(edgar.split_adjust(6.24, "2018-02-20", [["2020-10-27", 4.0]]), 1.56)
        self.assertEqual(edgar.split_adjust(1.56, "2021-02-20", [["2020-10-27", 4.0]]), 1.56)


class ReaderTest(unittest.TestCase):
    def test_dividend_streak_special_and_ambiguous_year(self):
        from div_invst.data.readers import dividend_stats
        pays = []
        for y in range(2012, 2025):
            amt = 1.0 + 0.1 * (y - 2012)
            pays += [[f"{y}-{m:02d}-15", amt / 4] for m in (2, 5, 8, 11)]
        pays.append(["2018-12-20", 5.0])                       # special, dropped
        r = dividend_stats(pays, 2026)
        self.assertEqual(r["streak_years"], 12)
        self.assertAlmostEqual(r["cagr5"], (2.2 / 1.7) ** (1 / 5) - 1, places=6)
        cut = [p for p in pays if not p[0].startswith("2024")] + [[f"2024-{m:02d}-15", 0.1] for m in (2, 5, 8, 11)]
        self.assertEqual(dividend_stats(cut, 2026)["streak_years"], 0)  # 2024 cut breaks the streak

    def test_eps_history_prefers_finnhub_then_edgar_split_adjusted(self):
        from div_invst.data.readers import eps_history
        metric = {"series": {"annual": {"eps": [{"period": "2025-12-31", "v": 3.0}, {"period": "2024-12-29", "v": 2.0}]}}}
        edg = {"fields": {"eps_diluted": {"2025": [9.9, "t", "2026-02-01"], "2016": [6.24, "t", "2018-02-15"]}}}
        r = eps_history(metric, edg, [["2020-10-27", 4.0]])
        self.assertEqual(r["years"], {2016: 1.56, 2024: 2.0, 2025: 3.0})
        self.assertEqual(r["source"][2016], "edgar")
        self.assertEqual(r["source"][2025], "finnhub")

    def test_insider_activity_window_and_codes(self):
        from datetime import date
        from div_invst.data.readers import insider_activity
        tx = [{"name": "A", "transactionCode": "P", "transactionDate": "2026-09-01", "change": 100},
              {"name": "B", "transactionCode": "P", "transactionDate": "2026-08-01", "change": 50},
              {"name": "B", "transactionCode": "P", "transactionDate": "2026-07-01", "change": 50},
              {"name": "C", "transactionCode": "S", "transactionDate": "2026-09-05", "change": -30},
              {"name": "D", "transactionCode": "A", "transactionDate": "2026-09-05", "change": 999},
              {"name": "E", "transactionCode": "P", "transactionDate": "2025-01-01", "change": 999}]
        r = insider_activity(tx, date(2026, 10, 26))
        self.assertEqual((r["buys"], r["buyers"], r["sells"], r["net_shares"]), (3, 2, 1, 170))
        self.assertIsNone(insider_activity(None, date(2026, 10, 26)))

    def test_revision_metrics(self):
        from datetime import date
        from div_invst.data.readers import revision_metrics
        rev = {"eps_trend": {"columns": ["period", "current", "30daysAgo", "90daysAgo"], "rows": [["0y", 11.0, 10.0, 12.0]]},
               "eps_revisions": {"columns": ["period", "upLast30days", "downLast30days"], "rows": [["0y", 3, 1]]},
               "upgrades_downgrades": {"columns": ["GradeDate", "Action"], "rows": [["2026-10-01 10:00:00", "up"], ["2026-09-01 10:00:00", "down"], ["2026-01-01 10:00:00", "up"]]},
               "price_targets": {"mean": 120.0}}
        r = revision_metrics(rev, 100.0, 2.0, date(2026, 10, 26))
        self.assertAlmostEqual(r["eps_rev_30d"], 0.1)
        self.assertAlmostEqual(r["eps_rev_90d"], -1 / 12)
        self.assertEqual((r["eps_up_30d"], r["upgrades_90d"], r["downgrades_90d"]), (3, 1, 1))
        self.assertAlmostEqual(r["target_upside"], 0.2)

    def test_edgar_latest_ffo_and_missing_inputs(self):
        from div_invst.data.readers import edgar_latest
        f = {"fields": {"net_income": {"2024": [1.0e9, "t", "x"], "2025": [1.1e9, "t", "x"]},
                        "depreciation": {"2025": [2.5e9, "t", "x"]}, "property_sale_gain": {"2025": [0.2e9, "t", "x"]},
                        "dividends_paid": {"2025": [3.0e9, "t", "x"]}}}
        r = edgar_latest(f)
        self.assertAlmostEqual(r["ffo"], 3.4e9)
        self.assertAlmostEqual(r["ffo_payout"], 3.0 / 3.4)
        self.assertIsNone(r["ebitda"])
        self.assertIsNone(edgar_latest({"fields": {"net_income": {"2025": [1.0, "t", "x"]}}})["ffo"])
        self.assertIsNone(edgar_latest(None))

    def test_macro_and_read_ticker(self):
        from datetime import date
        from div_invst.data.readers import apply_macro, read_macro, read_ticker
        s = Store(":memory:")
        s.put("fred", "fred:DGS10", "", [["2026-10-22", 4.9], ["2026-10-23", 5.0]])
        s.put("fred", "fred:CPIAUCSL", "", [["2025-09-01", 100.0], ["2026-09-01", 103.0]])
        m = read_macro(s)
        self.assertAlmostEqual(m["treasury_10y"], 0.05)
        self.assertAlmostEqual(m["inflation"], 0.03)
        cfg = apply_macro({"macro": {"sp_yield": 0.01, "treasury_10y": 0.04, "inflation": 0.02}}, m)
        self.assertEqual((cfg["macro"]["sp_yield"], cfg["macro"]["treasury_10y"]), (0.01, 0.05))
        self.assertIsNone(read_ticker(s, "ZZZ", date(2026, 10, 26)))
        s.put("yahoo", "yf_info", "KO", {"currentPrice": 50.0, "dividendRate": 2.0, "dividendYield": 4.1, "fiveYearAvgDividendYield": 3.0})
        r = read_ticker(s, "KO", date(2026, 10, 26))
        self.assertAlmostEqual(r["forward_yield"], 0.04)
        self.assertAlmostEqual(r["avg_yield_5y"], 0.03)
        self.assertIsNone(r["dividends"])


if __name__ == "__main__":
    unittest.main()
