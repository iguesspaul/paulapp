import unittest

from src.math.bankroll_manager import calculate_kelly_stake
from src.math.ev import calculate_ev
from src.math.sharp_consensus import get_consensus_lambda


class TestQuantEngine(unittest.TestCase):
    def test_lambda_derivation(self):
        """
        TEST 1: The 'Pinnacle 1.93/1.95' Benchmark.
        If Over 2.5 is 1.934 and Under 2.5 is 1.952, the true lambda MUST be ~2.678.
        """
        lambda_val = get_consensus_lambda(
            [{"book": "Pinnacle", "odds": {"Under2.5": 1.952, "Over2.5": 1.934}}]
        )

        self.assertAlmostEqual(
            lambda_val,
            2.68,
            places=2,
            msg=f"Lambda Solver failed! Expected ~2.68, got {lambda_val}",
        )

    def test_ev_calculation(self):
        """
        TEST 2: The 'Coin Flip' EV Check.
        If true probability is 50% (0.5), and casino offers 2.50 (+150) odds:
        Profit if win = $1.50. Loss if lose = $1.00.
        EV = (0.5 * 1.5) - (0.5 * 1.0) = +0.25 (25%).
        """
        ev = calculate_ev(0.5, 2.5)

        self.assertAlmostEqual(
            ev, 0.25, places=3, msg=f"EV Math is broken! Expected 0.25, got {ev}"
        )

    def test_negative_ev_calculation(self):
        """
        TEST 3: The 'House Edge' EV Check.
        If true prob is 50% (0.5), and casino offers 1.80 (-125) odds:
        EV = (0.5 * 0.8) - (0.5 * 1.0) = -0.10 (-10%).
        """
        ev = calculate_ev(0.5, 1.8)

        self.assertAlmostEqual(ev, -0.10, places=3, msg="Negative EV not properly handled!")

    def test_kelly_stake_sizing(self):
        """
        TEST 4: The 'Bankroll Protection' Check.
        Bankroll = $40. Prob = 0.5. Odds = 2.5. Edge = 25%.
        Full Kelly = 16.66%. Quarter Kelly = 4.16% = $1.66 bet.
        """
        stake = calculate_kelly_stake(odds=2.5, fair_prob=0.5, bankroll=40.0, multiplier=0.25)

        self.assertAlmostEqual(
            stake, 1.66, places=1, msg=f"Stake sizing is reckless! Expected ~1.66, got {stake}"
        )

    def test_htft_lambda_split(self):
        """
        TEST 5: The 'Half-Time Independence' Check.
        If Match Lambda is 3.0, 1st Half Home Lambda MUST be exactly:
        3.0 * 0.45 (HT Split) * 0.53 (Home Split) = 0.7155
        """
        match_lambda = 3.0
        expected_ht_home_lambda = match_lambda * 0.45 * 0.53

        self.assertAlmostEqual(
            expected_ht_home_lambda,
            0.7155,
            places=4,
            msg="HT/FT Split is leaking or using wrong constants!",
        )

    def test_constraint_solver(self):
        """
        TEST 6: Top-Down Market Implied Constraint Solver.
        Test that we can perfectly solve home and away lambdas from Pinnacle odds.
        """
        from src.math.sharp_consensus import solve_implied_lambdas_from_consensus

        sharp_data = [
            {
                "book": "Pinnacle",
                "odds": {"1": 2.0, "X": 3.4, "2": 3.8, "Over2.5": 1.90, "Under2.5": 1.90},
            }
        ]

        L_h, L_a = solve_implied_lambdas_from_consensus(sharp_data)

        self.assertIsNotNone(L_h)
        self.assertIsNotNone(L_a)
        self.assertTrue(L_h > 0)
        self.assertTrue(L_a > 0)
        # Check that they represent realistic lambdas for these odds
        self.assertAlmostEqual(L_h, 1.580, places=2)
        self.assertAlmostEqual(L_a, 1.092, places=2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
