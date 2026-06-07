"""Unit tests for betexplorer.py — non-network parser functions only.

Tests use static data matching the BetExplorer JSON odds response schema.
The API returns dicts with "odds" key containing a list of bookmaker entries.
"""

import unittest

from src.collectors.harvesters.betexplorer import _be_path_to_url, _parse_json_1x2, _parse_json_ou


class TestBePathToUrl(unittest.TestCase):
    def test_normal_path(self):
        result = _be_path_to_url("/football/england/premier-league/")
        self.assertEqual(result, "https://www.betexplorer.com/football/england/premier-league/")

    def test_path_without_trailing_slash(self):
        result = _be_path_to_url("/football/england/premier-league")
        self.assertEqual(result, "https://www.betexplorer.com/football/england/premier-league/")

    def test_soccer_mapped_to_football(self):
        result = _be_path_to_url("soccer/england/premier-league")
        self.assertEqual(result, "https://www.betexplorer.com/football/england/premier-league/")

    def test_deep_path(self):
        result = _be_path_to_url("/football/europe/uefa-champions-league/")
        self.assertEqual(
            result, "https://www.betexplorer.com/football/europe/uefa-champions-league/"
        )


class TestParseJson1x2(unittest.TestCase):
    def test_happy_path_decimal_odds(self):
        """odds field has list of 3 decimal odds (the actual format)."""
        data = {
            "odds": [
                {"n": "Pinnacle", "odds": [1.95, 3.40, 4.00]},
            ]
        }
        result = _parse_json_1x2(data)
        self.assertIn("Pinnacle", result)
        self.assertAlmostEqual(result["Pinnacle"]["1"], 1.95)
        self.assertAlmostEqual(result["Pinnacle"]["X"], 3.40)
        self.assertAlmostEqual(result["Pinnacle"]["2"], 4.00)

    def test_picks_pinnacle_over_other_books(self):
        data = {
            "odds": [
                {"n": "Bet365", "odds": [1.90, 3.30, 3.80]},
                {"n": "Pinnacle", "odds": [1.95, 3.40, 4.00]},
            ]
        }
        result = _parse_json_1x2(data)
        # Only Pinnacle should be in result (_TARGET_BOOKS includes it)
        self.assertIn("Pinnacle", result)
        self.assertAlmostEqual(result["Pinnacle"]["1"], 1.95)

    def test_dict_style_odds(self):
        """odds can also be a dict with 1/X/2 keys."""
        data = {
            "odds": [
                {"n": "Pinnacle", "odds": {"1": 1.95, "X": 3.40, "2": 4.00}},
            ]
        }
        result = _parse_json_1x2(data)
        self.assertAlmostEqual(result["Pinnacle"]["1"], 1.95)
        self.assertAlmostEqual(result["Pinnacle"]["X"], 3.40)
        self.assertAlmostEqual(result["Pinnacle"]["2"], 4.00)

    def test_empty_data(self):
        self.assertEqual(_parse_json_1x2({}), {})

    def test_none_data(self):
        self.assertEqual(_parse_json_1x2(None), {})

    def test_missing_odds_key(self):
        self.assertEqual(_parse_json_1x2({"other": "data"}), {})

    def test_empty_odds_list(self):
        self.assertEqual(_parse_json_1x2({"odds": []}), {})

    def test_odds_too_short(self):
        data = {"odds": [{"n": "Pinnacle", "odds": [1.95, 3.40]}]}
        result = _parse_json_1x2(data)
        self.assertEqual(result, {})

    def test_uses_data_key_fallback(self):
        data = {
            "data": [
                {"n": "Pinnacle", "odds": [1.95, 3.40, 4.00]},
            ]
        }
        result = _parse_json_1x2(data)
        self.assertIn("Pinnacle", result)

    def test_uses_rows_key_fallback(self):
        data = {
            "rows": [
                {"n": "Pinnacle", "odds": [1.95, 3.40, 4.00]},
            ]
        }
        result = _parse_json_1x2(data)
        self.assertIn("Pinnacle", result)


class TestParseJsonOu(unittest.TestCase):
    def test_happy_path(self):
        data = {
            "odds": [
                {"n": "Pinnacle", "handicap": "2.5", "odds": [1.85, 1.95]},
            ]
        }
        result = _parse_json_ou(data)
        self.assertIn("Pinnacle", result)
        self.assertAlmostEqual(result["Pinnacle"]["Over2.5"], 1.85)
        self.assertAlmostEqual(result["Pinnacle"]["Under2.5"], 1.95)

    def test_wrong_handicap_skipped(self):
        """Only handicap containing '2.5' should be used."""
        data = {
            "odds": [
                {"n": "Pinnacle", "handicap": "3.5", "odds": [1.85, 1.95]},
                {"n": "Pinnacle", "handicap": "2.5", "odds": [1.80, 2.00]},
            ]
        }
        result = _parse_json_ou(data)
        self.assertAlmostEqual(result["Pinnacle"]["Over2.5"], 1.80)

    def test_uses_points_fallback(self):
        data = {
            "odds": [
                {"n": "Pinnacle", "points": "2.5", "odds": [1.85, 1.95]},
            ]
        }
        result = _parse_json_ou(data)
        self.assertIn("Pinnacle", result)

    def test_uses_line_fallback(self):
        data = {
            "odds": [
                {"n": "Pinnacle", "line": "2.5", "odds": [1.85, 1.95]},
            ]
        }
        result = _parse_json_ou(data)
        self.assertIn("Pinnacle", result)

    def test_non_pinnacle_book_skipped(self):
        data = {
            "odds": [
                {"n": "Some Random Book", "handicap": "2.5", "odds": [1.85, 1.95]},
            ]
        }
        result = _parse_json_ou(data)
        self.assertEqual(result, {})

    def test_empty_data(self):
        self.assertEqual(_parse_json_ou({}), {})

    def test_none_data(self):
        self.assertEqual(_parse_json_ou(None), {})

    def test_odds_too_short(self):
        data = {"odds": [{"n": "Pinnacle", "handicap": "2.5", "odds": [1.85]}]}
        result = _parse_json_ou(data)
        self.assertEqual(result, {})

    def test_uses_name_fallback(self):
        data = {
            "odds": [
                {"name": "Pinnacle", "handicap": "2.5", "odds": [1.85, 1.95]},
            ]
        }
        result = _parse_json_ou(data)
        self.assertIn("Pinnacle", result)


if __name__ == "__main__":
    unittest.main()
