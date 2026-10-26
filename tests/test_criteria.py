import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from div_invst.criteria import FAIL, NA, PASS, UNKNOWN, evaluate, load_config, rank  # noqa: E402

CFG = load_config()


def rec(**screener):
    return {"ticker": "T", "sector": "Industrials", "industry": "", "security_type": "Common Stock", "market_cap": 1e10,
            "screener": {"ticker": "T", **screener}, "drip": None, "morningstar": None, "argus": None}


class CriteriaTest(unittest.TestCase):
    def test_yield_bands(self):
        self.assertEqual(evaluate(rec(div_yield=0.01), CFG)[4].status, FAIL)
        self.assertEqual(evaluate(rec(div_yield=0.02), CFG)[4].status, PASS)
        r = evaluate(rec(div_yield=0.04), CFG)[4]
        self.assertEqual((r.status, r.flags), (PASS, ["yield trap?"]))

    def test_chowder_tier_and_unknown(self):
        self.assertEqual(evaluate(rec(div_yield=0.03, dgr_5y=0.10), CFG)[5].status, PASS)
        self.assertEqual(evaluate(rec(div_yield=0.03, dgr_5y=0.05), CFG)[5].status, FAIL)
        self.assertEqual(evaluate(rec(div_yield=0.03), CFG)[5].status, UNKNOWN)

    def test_acn_needs_two_terms(self):
        self.assertEqual(evaluate(rec(div_yield=0.03, dgr_5y=0.2), CFG)[6].status, UNKNOWN)
        self.assertEqual(evaluate(rec(div_yield=0.03, dgr_5y=0.2, eps_growth_5y=0.2), CFG)[6].status, PASS)

    def test_starmine_and_portfolio(self):
        self.assertEqual(evaluate(rec(ess="Neutral", ess_change="Large Increase"), CFG)[13].status, PASS)
        self.assertEqual(evaluate(rec(ess="Neutral", ess_change="Unchanged"), CFG)[13].status, FAIL)
        self.assertEqual(evaluate(rec(), CFG)[14].status, NA)

    def test_agreement_ignores_starmine(self):
        r = evaluate(rec(ess="Very Bullish", zacks="OUTPERFORM", mclean="Buy"), CFG)[15]
        self.assertEqual(r.status, UNKNOWN)

    def test_rank_penalises_missing_criteria(self):
        def row(t, passes, acn=0.1):
            # 9 applicable criteria for everyone; FEW evaluated only 3 of them but passed all 3
            return {"ticker": t, "passes": passes, "applicable": 9, "evaluated": 9, "coverage": 1.0, "score": 1.0,
                    "rank_score": passes / 9, "acn": acn, "yield": 0.03}
        rows = [row("FEW", 3), row("MANY", 8), row("TIE", 8, acn=0.2)]
        self.assertEqual([x["ticker"] for x in rank(rows, CFG)], ["TIE", "MANY", "FEW"])


if __name__ == "__main__":
    unittest.main()
