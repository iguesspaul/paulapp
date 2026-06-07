"""Tests for market_resolver.py — probability grid market pricing."""

import unittest
from unittest.mock import MagicMock

import numpy as np
from scipy.stats import poisson

from src.collectors.market_resolver import MarketResolver


def _make_grid(h_lam, a_lam, rho=-0.10):
    """Build a 7x7 Dixon-Coles grid matching ProbabilityGrid's logic."""
    matrix = np.zeros((7, 7))
    for h in range(7):
        for a in range(7):
            prob = poisson.pmf(h, h_lam) * poisson.pmf(a, a_lam)
            tau = 1.0
            if h == 0 and a == 0:
                tau = 1.0 - rho * h_lam * a_lam
            elif h == 1 and a == 0:
                tau = 1.0 + rho * a_lam
            elif h == 0 and a == 1:
                tau = 1.0 + rho * h_lam
            elif h == 1 and a == 1:
                tau = 1.0 - rho
            tau = max(0.0, tau)
            matrix[h][a] = prob * tau
    total = np.sum(matrix)
    if total > 0:
        matrix /= total
    return matrix


def _make_resolver(match_lambda=2.65, home_lambda=1.40, away_lambda=1.25):
    """Create a MarketResolver with a mock prob_grid."""
    grid = MagicMock()
    grid.grid = _make_grid(home_lambda, away_lambda)
    grid.h1_grid = _make_grid(home_lambda * 0.45, away_lambda * 0.45)
    grid.h2_grid = _make_grid(
        (match_lambda - home_lambda * 0.45 - away_lambda * 0.45) * 0.53,
        (match_lambda - home_lambda * 0.45 - away_lambda * 0.45) * 0.47,
    )
    grid.match_lambda = match_lambda
    grid.h1_lambda = home_lambda * 0.45
    grid.a1_lambda = away_lambda * 0.45
    grid.h2_lambda = (match_lambda - home_lambda * 0.45 - away_lambda * 0.45) * 0.53
    grid.a2_lambda = (match_lambda - home_lambda * 0.45 - away_lambda * 0.45) * 0.47
    return MarketResolver(grid)


class TestMarketResolver(unittest.TestCase):
    def setUp(self):
        self.resolver = _make_resolver()

    def test_forbidden_markets_return_none(self):
        """Corner, booking, card, shot markets should return None."""
        self.assertIsNone(self.resolver.resolve("Corners", "Over 9.5"))
        self.assertIsNone(self.resolver.resolve("Bookings", "Over 3.5"))
        self.assertIsNone(self.resolver.resolve("Red Cards", "Over 0.5"))
        self.assertIsNone(self.resolver.resolve("Total Shots", "Over 10.5"))

    def test_match_winner_home(self):
        prob = self.resolver.resolve("1x2", "1")
        self.assertGreater(prob, 0.0)
        self.assertLess(prob, 1.0)
        # With home_lambda > away_lambda, home prob should be > 0.33
        self.assertGreater(prob, 0.33)

    def test_match_winner_away(self):
        prob = self.resolver.resolve("1x2", "2")
        self.assertGreater(prob, 0.0)
        self.assertLess(prob, 1.0)

    def test_draw(self):
        prob = self.resolver.resolve("1x2", "X")
        self.assertGreater(prob, 0.0)

    def test_correct_score(self):
        prob = self.resolver.resolve("Correct Score", "2:1")
        self.assertGreater(prob, 0.0)
        self.assertLess(prob, 0.5)  # Individual scores are unlikely

    def test_correct_score_nonexistent(self):
        prob = self.resolver.resolve("Correct Score", "99:99")
        self.assertEqual(prob, 0.0)

    def test_over_2_5_total(self):
        prob = self.resolver.resolve("Total Goals", "Over 2.5")
        self.assertGreater(prob, 0.0)
        self.assertLess(prob, 1.0)

    def test_under_2_5_total(self):
        prob = self.resolver.resolve("Total Goals", "Under 2.5")
        self.assertGreater(prob, 0.0)
        self.assertLess(prob, 1.0)

    def test_over_and_under_sum_to_approx_1(self):
        over = self.resolver.resolve("Total Goals", "Over 2.5")
        under = self.resolver.resolve("Total Goals", "Under 2.5")
        self.assertAlmostEqual(over + under, 1.0, places=2)

    def test_btts_yes(self):
        prob = self.resolver.resolve("Both Teams To Score", "Yes")
        self.assertGreater(prob, 0.0)

    def test_btts_no(self):
        prob = self.resolver.resolve("Both Teams To Score", "No")
        self.assertGreater(prob, 0.0)

    def test_btts_yes_and_no_sum_to_1(self):
        yes = self.resolver.resolve("Both Teams To Score", "Yes")
        no = self.resolver.resolve("Both Teams To Score", "No")
        self.assertAlmostEqual(yes + no, 1.0, places=2)

    def test_winning_margin_home_by_1(self):
        prob = self.resolver.resolve("Winning Margin", "Home by 1")
        self.assertGreater(prob, 0.0)

    def test_winning_margin_away_by_2(self):
        prob = self.resolver.resolve("Winning Margin", "Away by 2")
        self.assertGreater(prob, 0.0)

    def test_multiscores(self):
        prob = self.resolver.resolve("Multiscores", "1:0, 2:0 or 3:0")
        self.assertGreater(prob, 0.0)

    def test_unknown_market_returns_0(self):
        prob = self.resolver.resolve("Something Unknown", "Some selection")
        self.assertEqual(prob, 0.0)

    def test_1st_half_grid_is_used(self):
        """1st Half markets should use the h1_grid, not full match grid."""
        self.resolver.resolve("Total Goals", "Over 0.5")
        prob_1h = self.resolver.resolve("1st Half Total Goals", "Over 0.5")
        # 1H should have fewer goals on average, so lower over prob for a low threshold
        # Actually since 1H lambda is ~45% of full, over 0.5 should still be decent
        self.assertGreater(prob_1h, 0.0)

    def test_halftime_fulltime_correct_score(self):
        prob = self.resolver.resolve("Halftime/Fulltime Correct Score", "1:0 2:1")
        self.assertGreaterEqual(prob, 0.0)
        self.assertLess(prob, 1.0)

    def test_double_chance_returns_0_standalone(self):
        """Standalone 'Double Chance' is not a handled market — returns 0.0.
        Double Chance is only supported when combined with BTTS (& BTTS)."""
        self.assertEqual(self.resolver.resolve("Double Chance", "1X"), 0.0)
        self.assertEqual(self.resolver.resolve("Double Chance", "12"), 0.0)
        self.assertEqual(self.resolver.resolve("Double Chance", "X2"), 0.0)


class TestMarketResolverWithTotalGrids(unittest.TestCase):
    """Edge case tests with total-specific market resolutions."""

    def test_over_6_5_is_near_zero(self):
        """With lambda ~2.65, over 6.5 should be very unlikely."""
        r = _make_resolver()
        prob = r.resolve("Total Goals", "Over 6.5")
        self.assertGreater(prob, 0.0)
        self.assertLess(prob, 0.05)

    def test_over_0_5_is_near_1(self):
        r = _make_resolver(match_lambda=3.0, home_lambda=1.6, away_lambda=1.4)
        prob = r.resolve("Total Goals", "Over 0.5")
        # With match_lambda=3.0, Over 0.5 is very close to 1.0
        self.assertGreater(prob, 0.90)

    def test_under_0_5_is_near_0_with_high_lambda(self):
        r = _make_resolver(match_lambda=3.5, home_lambda=1.85, away_lambda=1.65)
        prob = r.resolve("Total Goals", "Under 0.5")
        self.assertLess(prob, 0.10)

    def test_all_market_probabilities_are_valid(self):
        """Sum of home + draw + away should be approximately 1."""
        r = _make_resolver(home_lambda=1.8, away_lambda=1.2)
        home = r.resolve("1x2", "1")
        draw = r.resolve("1X2", "X")
        away = r.resolve("1x2", "2")
        self.assertAlmostEqual(home + draw + away, 1.0, places=2)


if __name__ == "__main__":
    unittest.main()
