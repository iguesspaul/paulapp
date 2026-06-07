import unittest

from src.core.results_checker import evaluate_selection


def parse_period_scores(score_str: str, partial_str: str | None) -> tuple[int, int, int, int]:  # noqa: ARG001
    """Parse BetExplorer score format into (h1, a1, h2, a2) period scores.

    Formats handled:
      - "3:2" with "(1:0, 2:2)" → (1, 0, 2, 2)
      - "0:0" with None → (0, 0, 0, 0)
    """
    if not partial_str:
        return (0, 0, 0, 0)
    stripped = partial_str.strip("()")
    halves = stripped.split(",")
    if len(halves) == 2:
        h1, a1 = map(int, halves[0].strip().split(":"))
        h2, a2 = map(int, halves[1].strip().split(":"))
        return (h1, a1, h2, a2)
    return (0, 0, 0, 0)


class TestResultsChecker(unittest.TestCase):
    def test_score_parser(self):
        """Test parse_period_scores handles standard BetExplorer formats."""
        # 3-2 with partial (1:0, 2:2)
        h1, a1, h2, a2 = parse_period_scores("3:2", "(1:0, 2:2)")
        self.assertEqual((h1, a1, h2, a2), (1, 0, 2, 2))

        # 0-0 with missing partial (should default to all zeros)
        h1, a1, h2, a2 = parse_period_scores("0:0", None)
        self.assertEqual((h1, a1, h2, a2), (0, 0, 0, 0))

    def test_evaluate_correct_score(self):
        # 3-2 (HT 1-0, 2H 2-2)
        h1, a1, h2, a2 = 1, 0, 2, 2

        self.assertTrue(evaluate_selection("Correct Score", "3:2", h1, a1, h2, a2))
        self.assertFalse(evaluate_selection("Correct Score", "2:1", h1, a1, h2, a2))

        # 1H Correct Score
        self.assertTrue(evaluate_selection("1H Correct Score", "1:0", h1, a1, h2, a2))
        self.assertFalse(evaluate_selection("1H Correct Score", "0:0", h1, a1, h2, a2))

        # 2H Correct Score
        self.assertTrue(evaluate_selection("2H Correct Score", "2:2", h1, a1, h2, a2))
        self.assertFalse(evaluate_selection("2H Correct Score", "1:1", h1, a1, h2, a2))

    def test_evaluate_totals(self):
        # 3-2 (HT 1-0, 2H 2-2) -> Match total 5, 1H total 1, 2H total 4
        h1, a1, h2, a2 = 1, 0, 2, 2

        self.assertTrue(evaluate_selection("Total Goals", "Over 2.5", h1, a1, h2, a2))
        self.assertFalse(evaluate_selection("Total Goals", "Under 4.5", h1, a1, h2, a2))

        # 1H Totals
        self.assertTrue(evaluate_selection("1H Total Goals", "Over 0.5", h1, a1, h2, a2))
        self.assertTrue(evaluate_selection("1H Total Goals", "Under 1.5", h1, a1, h2, a2))
        self.assertFalse(evaluate_selection("1H Total Goals", "Over 1.5", h1, a1, h2, a2))

        # 2H Totals
        self.assertTrue(evaluate_selection("2H Total Goals", "Over 3.5", h1, a1, h2, a2))
        self.assertFalse(evaluate_selection("2H Total Goals", "Under 2.5", h1, a1, h2, a2))

    def test_evaluate_btts(self):
        # 3-2 (HT 1-0, 2H 2-2)
        h1, a1, h2, a2 = 1, 0, 2, 2

        self.assertTrue(evaluate_selection("BTTS", "Yes", h1, a1, h2, a2))
        self.assertFalse(evaluate_selection("BTTS", "No", h1, a1, h2, a2))

        # 1H BTTS (1-0 -> No)
        self.assertTrue(evaluate_selection("1H BTTS", "No", h1, a1, h2, a2))
        self.assertFalse(evaluate_selection("1H BTTS", "Yes", h1, a1, h2, a2))

        # 2H BTTS (2-2 -> Yes)
        self.assertTrue(evaluate_selection("2H BTTS", "Yes", h1, a1, h2, a2))
        self.assertFalse(evaluate_selection("2H BTTS", "No", h1, a1, h2, a2))

    def test_evaluate_htft(self):
        # 3-2 (HT 1-0, 2H 2-2) -> HT: Home, FT: Home
        h1, a1, h2, a2 = 1, 0, 2, 2

        self.assertTrue(evaluate_selection("HT/FT Result", "Home/Home", h1, a1, h2, a2))
        self.assertFalse(evaluate_selection("HT/FT Result", "Draw/Home", h1, a1, h2, a2))

        # HT/FT Correct Score
        self.assertTrue(evaluate_selection("HT/FT Correct Score", "1:0 3:2", h1, a1, h2, a2))
        self.assertFalse(evaluate_selection("HT/FT Correct Score", "0:0 3:2", h1, a1, h2, a2))

    def test_evaluate_double_chance_and_combos(self):
        # 3-2 (HT 1-0, 2H 2-2)
        h1, a1, h2, a2 = 1, 0, 2, 2

        # Double Chance & Total
        self.assertTrue(
            evaluate_selection("Double Chance & Total", "1X & under 5.5", h1, a1, h2, a2)
        )
        self.assertFalse(
            evaluate_selection("Double Chance & Total", "X2 & over 2.5", h1, a1, h2, a2)
        )

        # Double Chance & BTTS
        self.assertTrue(evaluate_selection("Double Chance & BTTS", "1X & yes", h1, a1, h2, a2))
        self.assertFalse(evaluate_selection("Double Chance & BTTS", "X2 & yes", h1, a1, h2, a2))

        # 1H Double Chance & BTTS (HT: 1-0 -> 1X & no)
        self.assertTrue(evaluate_selection("1H Double Chance & BTTS", "1X & no", h1, a1, h2, a2))

        # 2H 1x2 & BTTS (2H: 2-2 -> Draw & yes)
        self.assertTrue(evaluate_selection("2H 1x2 & BTTS", "Draw & yes", h1, a1, h2, a2))

    def test_evaluate_1x2_and_total_compound(self):
        """1X2 & Total must evaluate BOTH components — Atlanta & over 3.5 with
        final score 3-0 (total=3) should LOSE because 3 is NOT over 3.5."""
        h1, a1, h2, a2 = 0, 0, 3, 0  # 3-0 (HT 0-0, 2H 3-0)
        # Selection: "Atlanta & over 3.5" — Atlanta wins but total is exactly 3 (not over 3.5)
        result = evaluate_selection(
            "1x2 & Total",
            "Atlanta & over 3.5",
            h1,
            a1,
            h2,
            a2,
            home_team="Atlanta",
            away_team="Gimnasia",
        )
        self.assertFalse(result, "Over 3.5 with total=3 should be LOST")

    def test_evaluate_1x2_and_total_correct(self):
        """1X2 & Total — both components win: home team wins AND over 2.5."""
        h1, a1, h2, a2 = 1, 0, 2, 0  # 3-0 (HT 1-0, 2H 2-0), total=3
        result = evaluate_selection(
            "1x2 & Total",
            "Atlanta & over 2.5",
            h1,
            a1,
            h2,
            a2,
            home_team="Atlanta",
            away_team="Gimnasia",
        )
        self.assertTrue(result, "Atlanta wins AND total=3 is over 2.5")

    def test_evaluate_1x2_and_total_loses_on_1x2(self):
        """1X2 & Total — lose if the team loses even if total qualifies."""
        h1, a1, h2, a2 = 0, 1, 0, 2  # 0-3 (HT 0-1, 2H 0-2), total=3
        result = evaluate_selection(
            "1x2 & Total",
            "Atlanta & over 2.5",
            h1,
            a1,
            h2,
            a2,
            home_team="Atlanta",
            away_team="Gimnasia",
        )
        self.assertFalse(result, "Atlanta loses even though total=3 is over 2.5")

    def test_plain_1x2_still_works_with_team_name(self):
        """Plain 1x2 with team name in selection still evaluates correctly."""
        h1, a1, h2, a2 = 1, 0, 2, 2  # 3-2
        result = evaluate_selection(
            "1x2 (Match Result)",
            "Atlanta",
            h1,
            a1,
            h2,
            a2,
            home_team="Atlanta",
            away_team="Gimnasia",
        )
        self.assertTrue(result, "Atlanta wins 3-2")

    def test_evaluate_multiscores(self):
        # 3-2 (HT 1-0, 2H 2-2)
        h1, a1, h2, a2 = 1, 0, 2, 2

        self.assertFalse(evaluate_selection("Multiscores", "0:1, 0:2 or 0:3", h1, a1, h2, a2))
        self.assertFalse(evaluate_selection("Multiscores", "Draw", h1, a1, h2, a2))
        self.assertTrue(evaluate_selection("Multiscores", "3:1, 3:2 or 3:3", h1, a1, h2, a2))


if __name__ == "__main__":
    unittest.main()
