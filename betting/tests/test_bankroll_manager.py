"""Tests for bankroll_manager.py — Kelly Criterion stake sizing."""

import unittest

from src.math.bankroll_manager import calculate_kelly_stake


class TestCalculateKellyStake(unittest.TestCase):
    def test_positive_ev_stake(self):
        """Fair prob 0.55 at odds 2.0 with $1000 bankroll → 20% Kelly = 20.0."""
        stake = calculate_kelly_stake(2.0, 0.55, 1000.0, multiplier=0.2)
        self.assertAlmostEqual(stake, 20.0, places=2)

    def test_negative_ev_returns_zero(self):
        """Fair prob 0.40 at odds 2.0 → negative EV, zero stake."""
        stake = calculate_kelly_stake(2.0, 0.40, 1000.0)
        self.assertEqual(stake, 0.0)

    def test_odds_one_or_less_returns_zero(self):
        """Odds <= 1.0 are invalid."""
        self.assertEqual(calculate_kelly_stake(1.0, 0.9, 1000.0), 0.0)
        self.assertEqual(calculate_kelly_stake(0.5, 0.9, 1000.0), 0.0)

    def test_zero_bankroll_returns_zero(self):
        self.assertEqual(calculate_kelly_stake(2.0, 0.55, 0.0), 0.0)
        self.assertEqual(calculate_kelly_stake(2.0, 0.55, -1.0), 0.0)

    def test_multiplier_reduces_stake(self):
        full_kelly = calculate_kelly_stake(2.0, 0.55, 1000.0, multiplier=1.0)
        quarter_kelly = calculate_kelly_stake(2.0, 0.55, 1000.0, multiplier=0.25)
        self.assertAlmostEqual(quarter_kelly, full_kelly * 0.25, places=2)

    def test_default_multiplier_is_0_2(self):
        """b=1.0, p=0.55, q=0.45: kelly_f = (0.55-0.45)/1.0 = 0.10. 20% of 0.10 * 1000 = 20.0."""
        stake = calculate_kelly_stake(2.0, 0.55, 1000.0)
        self.assertAlmostEqual(stake, 20.0, places=2)

    def test_high_conviction_bet(self):
        """Very high edge (fair prob 0.8 at 1.5 odds).
        b = 0.5, p = 0.8, q = 0.2
        kelly_f = (0.5*0.8 - 0.2) / 0.5 = (0.4 - 0.2) / 0.5 = 0.4
        20% fractional = 0.4 * 0.2 = 0.08
        stake = 0.08 * 5000 = 400
        """
        stake = calculate_kelly_stake(1.5, 0.8, 5000.0, multiplier=0.2)
        self.assertAlmostEqual(stake, 400.0, places=2)

    def test_rounds_to_two_decimals(self):
        stake = calculate_kelly_stake(1.91, 0.55, 1000.0)
        self.assertAlmostEqual(stake, round(stake, 2), places=2)

    def test_break_even_no_stake(self):
        """Fair prob exactly equals implied prob → zero EV → zero stake."""
        stake = calculate_kelly_stake(2.0, 0.5, 1000.0)
        self.assertEqual(stake, 0.0)


if __name__ == "__main__":
    unittest.main()
