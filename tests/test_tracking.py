import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from div_invst.tracking import dividend_cut, group_stats, horizon_end, split_by_criterion, total_return  # noqa: E402

SERIES = [("2026-10-26", 100.0), ("2026-10-27", 100.0), ("2026-11-02", 110.0), ("2026-11-06", 120.0)]


class ReturnTest(unittest.TestCase):
    def test_total_return_window(self):
        self.assertAlmostEqual(total_return(SERIES, "2026-10-26", "2026-11-06"), 0.20)
        self.assertIsNone(total_return(SERIES, "2026-10-28", "2026-11-03"))   # enters 11-02, exits 11-02: no span, so no return
        self.assertAlmostEqual(total_return(SERIES, "2026-10-27", "2026-11-04"), 0.10)  # exits on the last close on or before

    def test_start_on_weekend_uses_next_close(self):
        self.assertAlmostEqual(total_return(SERIES, "2026-10-31", "2026-11-06"), 120 / 110 - 1)

    def test_not_covered_is_none_never_zero(self):
        self.assertIsNone(total_return(SERIES, "2026-10-26", "2026-12-01"))   # series stops weeks before the end
        self.assertIsNone(total_return(SERIES, "2026-11-07", "2026-11-08"))   # nothing on or after the start
        self.assertIsNone(total_return([], "2026-10-26", "2026-11-06"))
        self.assertIsNone(total_return(SERIES, "2026-10-01", "2026-10-10"))   # nothing on or before the end

    def test_horizon_end(self):
        self.assertEqual(horizon_end("2026-10-26", 30), "2026-11-25")


class StatsTest(unittest.TestCase):
    def test_group_stats_counts_unpriced(self):
        s = group_stats({"A": 0.10, "B": -0.05, "C": None, "D": 0.30}, 0.02)
        self.assertEqual((s["n"], s["priced"]), (4, 3))
        self.assertAlmostEqual(s["mean"], 0.35 / 3)
        self.assertAlmostEqual(s["median"], 0.10)
        self.assertAlmostEqual(s["hit"], 2 / 3)
        self.assertAlmostEqual(s["excess"], 0.35 / 3 - 0.02)

    def test_group_stats_empty(self):
        s = group_stats({"A": None}, 0.02)
        self.assertEqual((s["n"], s["priced"], s["mean"], s["hit"]), (1, 0, None, None))

    def test_split_by_criterion_skips_unknown_and_unpriced(self):
        rows = [{"ticker": "A", "c1": "pass"}, {"ticker": "B", "c1": "fail"}, {"ticker": "C", "c1": "unknown"},
                {"ticker": "D", "c1": "pass"}]
        out = split_by_criterion(rows, {"A": 0.10, "B": -0.10, "C": 0.5, "D": None}, ["c1"])
        self.assertEqual(out["c1"]["pass"], (1, 0.10))
        self.assertEqual(out["c1"]["fail"], (1, -0.10))


class CutTest(unittest.TestCase):
    PAY = [["2026-01-15", 1.0], ["2026-04-15", 1.0], ["2026-07-15", 1.0], ["2026-10-15", 1.0]]

    def test_cut_detected(self):
        self.assertTrue(dividend_cut(self.PAY + [["2026-11-15", 0.5]], "2026-10-26"))

    def test_small_trim_and_raise_are_not_cuts(self):
        self.assertFalse(dividend_cut(self.PAY + [["2026-11-15", 0.95], ["2027-02-15", 1.2]], "2026-10-26"))

    def test_no_payment_after_or_before(self):
        self.assertFalse(dividend_cut(self.PAY, "2026-10-26"))
        self.assertIsNone(dividend_cut([["2026-11-15", 1.0]], "2026-10-26"))


if __name__ == "__main__":
    unittest.main()
