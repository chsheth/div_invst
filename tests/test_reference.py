import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from div_invst.reference import load_schwab, same_company  # noqa: E402
from div_invst.reference.schwab import parse_row  # noqa: E402

HEADER = ["Symbol", "Description", "CFRA Star Ranking", "Morningstar Rating", "Morningstar Fair Value Estimate",
          "Morningstar Economic Moat", "Annual Dividend Yield"]


def write(path, rows, header=HEADER):
    lines = [",".join(f'"{c}"' for c in header)] + [",".join(f'"{c}"' for c in r) for r in rows]
    path.write_text("﻿" + "\n".join(lines) + "\n", encoding="utf-8")


class SchwabLoaderTest(unittest.TestCase):
    def test_parse_row_conversions_and_unusable_morningstar(self):
        row = dict(zip(HEADER, ["KO", "Coca-Cola Co", "4 Stars", "2 stars", "1,080.50", "Wide", "3.1%"]))
        out = parse_row(row)
        self.assertEqual((out["cfra_stars"], out["ms_stars"], out["ms_fair_value"], out["ms_moat"], out["ms_status"]),
                         (4, 2, 1080.5, "Wide", None))
        row.update({"CFRA Star Ranking": "--", "Morningstar Rating": "dropping coverage"})
        out = parse_row(row)
        self.assertEqual((out["cfra_stars"], out["ms_stars"], out["ms_fair_value"], out["ms_status"]),
                         (None, None, None, "dropping coverage"))    # a stale rating and its fair value are not used
        row["CFRA Star Ranking"] = "1 Star"
        self.assertEqual(parse_row(row)["cfra_stars"], 1)

    def test_load_reads_bom_first_row_wins_and_checks_columns(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "schwab_results.csv"
            write(p, [["KO", "Coca-Cola Co", "3 Stars", "5 stars", "80", "Wide", "3%"], ["KO", "dup", "1 Star", "--", "--", "--", "--"]])
            self.assertEqual(load_schwab(p)["KO"]["cfra_stars"], 3)
            write(p, [["KO", "x", "3 Stars"]], header=["Symbol", "Description", "CFRA Star Ranking"])
            with self.assertRaisesRegex(ValueError, "lacks column"):
                load_schwab(p)

    def test_same_company_guards_reused_tickers(self):
        self.assertTrue(same_company("The Hershey Company", "Hershey Co (The)"))
        self.assertTrue(same_company("Centerspace", "Centrespace"))
        self.assertTrue(same_company("Energy of Minas Gerais Co", "Companhia Energetica de Minas Gerais CEMIG"))
        self.assertFalse(same_company("Brhc Holdings Ltd", "Brookfield Renewable Corp"))
        self.assertTrue(same_company(None, "Anything Inc"))              # nothing to contradict


class MergeSchwabTest(unittest.TestCase):
    def test_merge_dedupes_and_stops_on_cap_copy_and_layout(self):
        import merge_schwab as ms
        with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(io.StringIO()):
            d = Path(d)
            a, b, c = d / "Results (1).csv", d / "Results (2).csv", d / "Results (3).csv"
            ys = lambda n, start: [[f"T{i}", "n", "--", "--", "--", "--", f"{i}%"] for i in range(start, start + n)]  # noqa: E731
            write(a, ys(30, 0))
            write(b, ys(30, 29))                       # shares T29 with a: a band edge, kept once
            cols, rows = ms.merge([a, b])
            self.assertEqual((cols, len(rows)), (HEADER, 59))
            write(c, ys(30, 0))                        # a copy of a
            with self.assertRaises(SystemExit):
                ms.merge([a, c])
            write(c, ys(ms.EXPORT_CAP, 100))
            with self.assertRaisesRegex(SystemExit, "export cap"):
                ms.merge([a, c])
            write(c, ys(5, 200), header=HEADER[:-1] + ["Other"])
            with self.assertRaisesRegex(SystemExit, "different columns"):
                ms.merge([a, c])


if __name__ == "__main__":
    unittest.main()
