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


def fund(sector="Industrials", market_cap=1e10, screener=None, **cache):
    r = rec(**(screener or {}))
    r["sector"], r["market_cap"], r["cache"] = sector, market_cap, cache
    return r


def yrs(values, start=2015):
    return {start + i: v for i, v in enumerate(values)}


class FundamentalsCriteriaTest(unittest.TestCase):
    def test_criterion_10(self):
        good = {"pe": yrs([20] * 8), "roe": yrs([0.10, 0.10, 0.10, 0.12, 0.12, 0.12]), "roic": yrs([0.05, 0.05, 0.05, 0.06, 0.06, 0.06]),
                "eps_growth_next_year": 0.08}
        r = fund(screener={"pe": 15.0}, fundamentals=good)
        res = evaluate(r, CFG)[10]
        self.assertEqual(res.status, PASS)
        self.assertEqual(evaluate(fund(screener={"pe": 25.0}, fundamentals=good), CFG)[10].status, FAIL)          # above own average
        falling = {**good, "roe": yrs([0.20, 0.20, 0.20, 0.10, 0.10, 0.10])}
        self.assertEqual(evaluate(fund(screener={"pe": 15.0}, fundamentals=falling), CFG)[10].status, FAIL)       # neither rising nor near the high
        near_high = {**good, "roe": yrs([0.20, 0.10, 0.10, 0.10, 0.10, 0.19])}
        self.assertEqual(evaluate(fund(screener={"pe": 15.0}, fundamentals=near_high), CFG)[10].status, PASS)     # latest >= 90% of the high
        low_growth = {**good, "eps_growth_next_year": 0.035}                                                      # inflation 3.72% in the config
        self.assertEqual(evaluate(fund(screener={"pe": 15.0}, fundamentals=low_growth), CFG)[10].status, FAIL)
        self.assertEqual(evaluate(fund(), CFG)[10].status, UNKNOWN)

    def test_criterion_1_score_and_exemptions(self):
        strong = {"total_debt": 2e9, "ebitda": 1e9, "fcf_margin": yrs([0.1] * 5), "free_cash_flow": 5e8, "payout": 0.5}
        edgar = {"cash": 12, "cash_prev": 10, "dividends_paid": 2e8}
        r = fund(screener={"interest_coverage": 9.0}, fundamentals=strong, edgar=edgar, payout=0.5)
        res = evaluate(r, CFG)[1]
        self.assertEqual((res.status, res.value, res.detail["tier"]), (PASS, 100.0, "A"))
        weak = {**strong, "total_debt": 9e9, "ebitda": 1e9, "fcf_margin": yrs([0.1, -0.1, 0.1, 0.1, 0.1])}
        r = fund(screener={"interest_coverage": 1.0}, fundamentals=weak, edgar={**edgar, "cash": 5}, payout=0.9)
        self.assertEqual(evaluate(r, CFG)[1].status, FAIL)
        util = fund("Utilities", screener={"interest_coverage": 9.0}, fundamentals=strong, edgar=edgar, payout=0.95)
        res = evaluate(util, CFG)[1]
        self.assertEqual((res.status, res.detail["payout"]), (PASS, None))           # payout exempt, re-weighted
        self.assertEqual(evaluate(fund(), CFG)[1].status, UNKNOWN)                    # nothing cached
        bank = fund("Financials", fundamentals=strong, edgar=edgar)
        bank["industry"] = "Banks"
        self.assertEqual(evaluate(bank, CFG)[1].status, UNKNOWN)

    def test_criterion_1_reit_uses_net_debt_and_ffo_payout(self):
        f = {"total_debt": 5e9, "ebitda": 1e9, "fcf_margin": yrs([0.1] * 5), "free_cash_flow": None}
        r = fund("Real Estate", market_cap=2e10, screener={"interest_coverage": 4.0}, fundamentals=f,
                 edgar={"cash": 1.5e9, "cash_prev": 1e9, "ffo_payout": 0.80, "dividends_paid": 1})
        res = evaluate(r, CFG)[1]
        self.assertEqual(res.detail["debt_to_ebitda"], 100)  # net debt 3.5x is within the 6x REIT limit (4.5x would be partial for others)
        self.assertEqual((res.status, res.detail["payout"]), (PASS, 100))
        r["cache"]["edgar"]["ffo_payout"] = 0.90
        self.assertEqual(evaluate(r, CFG)[1].detail["payout"], 0)

    def test_criterion_9_gets_the_own_pe_test(self):
        r = fund(screener={"ps": 1.0, "pb": 2.0, "pe": 30.0, "earnings_yield": 0.06}, fundamentals={"pe": yrs([20] * 6)})
        res = evaluate(r, CFG)[9]
        self.assertEqual((res.status, res.detail["pe_below_history"]), (FAIL, False))


class FairValueTest(unittest.TestCase):
    def rec(self, price=100.0, dividend=3.0, cagr=0.06, eps=(4.0, 5.0, 6.0), pe=15.0, sector="Industrials"):
        return fund(sector, price=price, forward_yield=dividend / price, dividends={"cagr5": cagr},
                    eps={"years": {2023 + i: v for i, v in enumerate(eps)}}, fundamentals={"pe": yrs([pe] * 8)})

    def test_both_estimates_and_lower_wins(self):
        from div_invst.criteria.valuation import fair_values
        r = CFG["macro"]["treasury_10y"] + CFG["fair_value"]["equity_premium"]
        d, ddm = 3.0, 0.0
        for t in range(1, 6):                                  # 6% CAGR (under the 8% cap) for 5 years
            d *= 1.06
            ddm += d / (1 + r) ** t
        ddm += d * 1.04 / (r - 0.04) / (1 + r) ** 5            # then 4% for good
        fv = fair_values(self.rec(), CFG)
        self.assertAlmostEqual(fv["ddm"], ddm)
        self.assertAlmostEqual(fv["pe"], 5.0 * 15.0)          # median EPS 5 x median P/E 15
        self.assertGreater(ddm, 3.0 * 1.04 / (r - 0.04))                 # more than the single-stage value at 4% growth
        fair = min(ddm, 75.0)
        res = evaluate(self.rec(price=fair * 0.80), CFG)[8]   # 20% below the lower value
        self.assertEqual((res.status, round(res.detail["fair"], 2)), (PASS, round(fair, 2)))
        self.assertEqual(evaluate(self.rec(price=fair * 0.95), CFG)[8].status, FAIL)

    def test_reit_uses_ddm_only_and_missing_is_unknown(self):
        res = evaluate(self.rec(price=40.0, sector="Real Estate"), CFG)[8]   # dividend 3.0 on a 40 price: well below the DDM value
        self.assertEqual((res.status, res.flags), (PASS, ["ddm estimate only"]))
        self.assertEqual(evaluate(fund(), CFG)[8].status, UNKNOWN)
        no_div = self.rec()
        no_div["cache"]["dividends"] = None
        res = evaluate(no_div, CFG)[8]
        self.assertEqual((res.detail["pe"], res.flags), (75.0, ["pe estimate only"]))   # P/E estimate still works

    def test_stage1_growth_is_capped_and_floored(self):
        from div_invst.criteria.valuation import fair_values
        capped = fair_values(self.rec(cagr=0.30), CFG)["ddm"]
        at_cap = fair_values(self.rec(cagr=0.08), CFG)["ddm"]
        self.assertAlmostEqual(capped, at_cap)                          # a 30% CAGR is treated as 8%
        self.assertAlmostEqual(fair_values(self.rec(cagr=-0.05), CFG)["ddm"], fair_values(self.rec(cagr=0.0), CFG)["ddm"])


if __name__ == "__main__":
    unittest.main()
