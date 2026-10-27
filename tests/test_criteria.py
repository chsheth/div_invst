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


def cached(tier=None, **cache):
    r = rec()
    r["ccc_tier"] = tier
    r["cache"] = cache
    return r


def eps_years(values, start=2014):
    return {"years": {start + i: v for i, v in enumerate(values)}}


class CachedCriteriaTest(unittest.TestCase):
    def test_eps_up_years_and_one_off(self):
        from div_invst.criteria.history import eps_up_years
        ups, flagged = eps_up_years(dict(zip(range(2014, 2019), [1.0, 1.1, 1.2, 1.3, 1.4])), 0.4)
        self.assertEqual((ups, flagged), ([True] * 4, []))
        # 2016 is a spike (+100%, then -50%): judged by 2017 vs 2015, and 2017 is compared with 2015
        ups, flagged = eps_up_years(dict(zip(range(2014, 2019), [1.0, 1.1, 2.2, 1.2, 1.3])), 0.4)
        self.assertEqual(flagged, [2016])
        self.assertEqual(ups, [True, True, True, True])
        # spike where the next year falls below the pre-spike level: the spike year is not an up year
        ups, flagged = eps_up_years(dict(zip(range(2014, 2018), [1.0, 1.1, 2.2, 1.0])), 0.4)
        self.assertEqual((flagged, ups), ([2016], [True, False, False]))

    def test_criterion_7(self):
        rising = [1.0 + 0.1 * i for i in range(11)]
        self.assertEqual(evaluate(cached("Champion", eps=eps_years(rising)), CFG)[7].status, PASS)
        self.assertEqual(evaluate(cached(None, eps=eps_years(rising), dividends={"streak_years": 3}), CFG)[7].status, FAIL)
        self.assertEqual(evaluate(cached(None, eps=eps_years(rising), dividends={"streak_years": 6}), CFG)[7].status, PASS)
        flat = [1.0, 1.1, 1.0, 1.1, 1.0, 1.1, 1.0, 1.1, 1.0, 1.1, 1.0]  # 5 up of 10
        self.assertEqual(evaluate(cached("King", eps=eps_years(flat)), CFG)[7].status, FAIL)
        self.assertEqual(evaluate(cached("King", eps=eps_years(rising[:5])), CFG)[7].status, UNKNOWN)  # 4 comparisons
        self.assertEqual(evaluate(cached(None, eps=eps_years(rising)), CFG)[7].status, UNKNOWN)       # no streak data
        self.assertEqual(evaluate(rec(), CFG)[7].status, UNKNOWN)                                      # nothing cached

    def test_criteria_11_and_12(self):
        self.assertEqual(evaluate(cached(edgar={"cash": 12, "cash_prev": 10}), CFG)[11].status, PASS)
        self.assertEqual(evaluate(cached(edgar={"cash": 9, "cash_prev": 10}), CFG)[11].status, FAIL)
        self.assertEqual(evaluate(cached(edgar={"cash": 9, "cash_prev": None}), CFG)[11].status, UNKNOWN)
        buy = lambda buyers, net: {"insider": {"buyers": buyers, "buys": buyers, "sellers": 0, "net_shares": net}}  # noqa: E731
        self.assertEqual(evaluate(cached(**buy(2, 500)), CFG)[12].status, PASS)
        self.assertEqual(evaluate(cached(**buy(1, 500)), CFG)[12].status, FAIL)
        self.assertEqual(evaluate(cached(**buy(2, -5)), CFG)[12].status, FAIL)
        self.assertEqual(evaluate(rec(), CFG)[12].status, UNKNOWN)

    def test_revision_proxy_second_signal(self):
        from div_invst.criteria.analysts import revision_score
        strong = {"eps_rev_90d": 0.10, "eps_up_30d": 4, "eps_down_30d": 0, "upgrades_90d": 2, "downgrades_90d": 0,
                  "recommendation_mean": 1.0, "target_upside": 0.20}
        self.assertAlmostEqual(revision_score(strong, CFG)[0], 10.0)
        weak = {"eps_rev_90d": -0.10, "target_upside": -0.20}
        self.assertAlmostEqual(revision_score(weak, CFG)[0], 0.0)
        self.assertIsNone(revision_score({"eps_rev_90d": 0.05}, CFG)[0])  # one component is not enough
        # no ESS: the proxy decides; with an ESS the ESS decides and the proxy is only shown
        self.assertEqual(evaluate(cached(revision=strong), CFG)[13].status, PASS)
        self.assertEqual(evaluate(cached(revision=weak), CFG)[13].status, FAIL)
        r = rec(ess="Bearish")
        r["cache"] = {"revision": strong}
        res = evaluate(r, CFG)[13]
        self.assertEqual((res.status, res.detail["proxy"]), (FAIL, 10.0))


class ReitPayoutTest(unittest.TestCase):
    def reit(self, payout):
        r = rec(div_yield=0.05)
        r["sector"] = "Real Estate"
        r["cache"] = {"edgar": {"ffo_payout": payout}}
        return r

    def test_criterion_3_scores_reit_payout(self):
        from div_invst.criteria.quality import subscores
        cuts = [0.76, 0.85, 0.95, 1.2, None]
        got = [subscores(self.reit(p), CFG)["earnings_quality"] for p in cuts]
        self.assertEqual(got, [100, 100, 60, 0, None])
        self.assertIsNone(subscores(self.reit(0.5))["earnings_quality"])  # no cfg: not scored


class FfoReaderTest(unittest.TestCase):
    def test_impairment_added_and_known_flags(self):
        from div_invst.data.readers import edgar_latest
        row = lambda v: {"2025": [v, "t", "x"]}  # noqa: E731
        f = {"fields": {"net_income": row(1058.59e6), "depreciation": row(2524.2e6), "impairment": row(471.335e6),
                        "property_sale_gain": row(177.64e6), "dividends_paid": row(2920.895e6)}}
        r = edgar_latest(f)
        self.assertAlmostEqual(r["ffo"], 3876.485e6, delta=1e3)  # reported Nareit FFO 3,860.3M (+0.4%)
        self.assertAlmostEqual(r["ffo_payout"], 2920.895 / 3876.485, places=4)
        self.assertTrue(r["ffo_impairment_known"] and r["ffo_gain_known"])
        del f["fields"]["property_sale_gain"]
        self.assertFalse(edgar_latest(f)["ffo_gain_known"])


if __name__ == "__main__":
    unittest.main()
