"""Unit tests for pinnacle.py — non-network parser functions only.

All tests use static data matching the Arcadia API schema where the
`price` field is the American odds integer (e.g. -110, +200).
"""

import unittest

from src.collectors.harvesters.pinnacle import (
    _build_participant_map,
    _find_league,
    _find_matchup,
    _parse_markets,
)


class TestFindLeague(unittest.TestCase):
    def setUp(self):
        self.leagues = [
            {"id": 1, "name": "Sweden - Allsvenskan", "parent": {"id": 123, "name": "Sweden"}},
            {"id": 2, "name": "England - Premier League", "parent": {"id": 456, "name": "England"}},
        ]

    def test_known_name_exact_match(self):
        result = _find_league(self.leagues, "sweden-allsvenskan", known_name="Sweden - Allsvenskan")
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 1)

    def test_known_name_not_found_falls_back_to_token_scoring(self):
        result = _find_league(self.leagues, "sweden-allsvenskan")
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 1)

    def test_england_premier_match(self):
        result = _find_league(self.leagues, "england-premier-league")
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 2)

    def test_no_match_returns_none(self):
        result = _find_league(self.leagues, "unrelated-league")
        self.assertIsNone(result)

    def test_empty_league_list(self):
        result = _find_league([], "anything")
        self.assertIsNone(result)


class TestFindMatchup(unittest.TestCase):
    def setUp(self):
        self.matchups = [
            {"id": 100, "participants": [{"id": 1, "name": "Malmo FF"}, {"id": 2, "name": "AIK"}]},
            {
                "id": 101,
                "participants": [{"id": 3, "name": "Djurgarden"}, {"id": 4, "name": "Hammarby"}],
            },
        ]

    def test_direct_order_match(self):
        result = _find_matchup(self.matchups, "Malmo FF", "AIK")
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 100)

    def test_swapped_order_match(self):
        result = _find_matchup(self.matchups, "AIK", "Malmo FF")
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 100)

    def test_no_match_returns_none(self):
        result = _find_matchup(self.matchups, "Barcelona", "Real Madrid")
        self.assertIsNone(result)

    def test_empty_matchups(self):
        result = _find_matchup([], "Team A", "Team B")
        self.assertIsNone(result)


class TestBuildParticipantMap(unittest.TestCase):
    def test_3way_home_away_draw(self):
        participants = [
            {"id": 10, "name": "Home Team", "alignment": "home", "order": 0},
            {"id": 11, "name": "Away Team", "alignment": "away", "order": 1},
            {"id": 12, "name": "Draw", "alignment": "draw", "order": 2},
        ]
        pmap = _build_participant_map(participants)
        self.assertEqual(pmap[10]["role"], "home")
        self.assertEqual(pmap[11]["role"], "away")
        self.assertEqual(pmap[12]["role"], "draw")

    def test_2way_no_draw(self):
        participants = [
            {"id": 10, "name": "Home", "alignment": "home", "order": 0},
            {"id": 11, "name": "Away", "alignment": "away", "order": 1},
        ]
        pmap = _build_participant_map(participants)
        self.assertEqual(pmap[10]["role"], "home")
        self.assertEqual(pmap[11]["role"], "away")

    def test_empty_returns_empty(self):
        self.assertEqual(_build_participant_map([]), {})


class TestParseMarkets(unittest.TestCase):
    """Price field is American odds integer (e.g. -110, +200).
    _parse_markets converts to decimal via american_to_decimal()."""

    def test_full_3way_with_participants(self):
        """Home=-110→1.9091, Away=+200→3.0, Draw=+240→3.4"""
        participants = [
            {"id": 10, "name": "Malmo FF", "alignment": "home", "order": 0},
            {"id": 11, "name": "AIK", "alignment": "away", "order": 1},
            {"id": 12, "name": "Draw", "alignment": "draw", "order": 2},
        ]
        markets = [
            {
                "key": "s;0;m",
                "prices": [
                    {"participantId": 10, "price": -110},
                    {"participantId": 11, "price": 200},
                    {"participantId": 12, "price": 240},
                ],
            }
        ]
        odds = _parse_markets(markets, participants)
        self.assertAlmostEqual(odds["1"], 1.9091, places=3)
        self.assertAlmostEqual(odds["2"], 3.0, places=3)
        self.assertAlmostEqual(odds["X"], 3.4, places=3)

    def test_ordinal_fallback_no_participants(self):
        """Without participants, ordinal position determines home/away/draw."""
        markets = [
            {
                "key": "s;0;m",
                "prices": [
                    {"price": -110},
                    {"price": 200},
                    {"price": 240},
                ],
            }
        ]
        odds = _parse_markets(markets)
        self.assertAlmostEqual(odds["1"], 1.9091, places=3)
        self.assertAlmostEqual(odds["2"], 3.0, places=3)
        self.assertAlmostEqual(odds["X"], 3.4, places=3)

    def test_over_under_2_5_with_participant_ids(self):
        """O/U market with designation and points=2.5."""
        markets = [
            {
                "key": "s;0;ou",
                "prices": [
                    {"participantId": 20, "price": -110, "designation": "over", "points": 2.5},
                    {"participantId": 21, "price": -115, "designation": "under", "points": 2.5},
                ],
            }
        ]
        odds = _parse_markets(markets)
        self.assertAlmostEqual(odds["Over2.5"], 1.9091, places=3)
        self.assertAlmostEqual(odds["Under2.5"], 1.8696, places=3)

    def test_over_under_position_fallback(self):
        """O/U without designation uses position: first=over, second=under."""
        markets = [
            {
                "key": "s;0;ou",
                "prices": [
                    {"price": -110, "points": 2.5},
                    {"price": -115, "points": 2.5},
                ],
            }
        ]
        odds = _parse_markets(markets)
        self.assertAlmostEqual(odds["Over2.5"], 1.9091, places=3)
        self.assertAlmostEqual(odds["Under2.5"], 1.8696, places=3)

    def test_half_time_market_is_skipped(self):
        """First-half moneyline (s;1;m) should be skipped."""
        markets = [{"key": "s;1;m", "prices": [{"price": -110}]}]
        odds = _parse_markets(markets)
        self.assertEqual(odds, {})

    def test_empty_markets(self):
        self.assertEqual(_parse_markets([]), {})

    def test_market_with_none_price_is_skipped(self):
        """Prices with null price value in participant-resolved path are skipped."""
        participants = [
            {"id": 10, "name": "Home", "alignment": "home", "order": 0},
            {"id": 11, "name": "Away", "alignment": "away", "order": 1},
        ]
        markets = [
            {
                "key": "s;0;m",
                "prices": [
                    {"participantId": 10, "price": -110},
                    {"participantId": 11, "price": None},
                ],
            }
        ]
        odds = _parse_markets(markets, participants)
        # Home resolved via participantId, away None is skipped
        self.assertAlmostEqual(odds["1"], 1.9091, places=3)
        self.assertNotIn("2", odds)

    def test_2way_moneyline_only(self):
        """2-way matchup without draw participant."""
        participants = [
            {"id": 10, "name": "Home", "alignment": "home", "order": 0},
            {"id": 11, "name": "Away", "alignment": "away", "order": 1},
        ]
        markets = [
            {
                "key": "s;0;m",
                "prices": [
                    {"participantId": 10, "price": -110},
                    {"participantId": 11, "price": 200},
                ],
            }
        ]
        odds = _parse_markets(markets, participants)
        self.assertAlmostEqual(odds["1"], 1.9091, places=3)
        self.assertAlmostEqual(odds["2"], 3.0, places=3)
        self.assertNotIn("X", odds)

    def test_full_match_1x2_and_ou(self):
        """Both 1x2 and O/U 2.5 from the same market list."""
        participants = [
            {"id": 10, "alignment": "home", "name": "Malmo", "order": 0},
            {"id": 11, "alignment": "away", "name": "AIK", "order": 1},
            {"id": 12, "alignment": "draw", "name": "Draw", "order": 2},
        ]
        markets = [
            {
                "key": "s;0;m",
                "prices": [
                    {"participantId": 10, "price": -110},
                    {"participantId": 12, "price": 240},
                    {"participantId": 11, "price": 200},
                ],
            },
            {
                "key": "s;0;ou",
                "prices": [
                    {"price": -110, "points": 2.5},
                    {"price": -115, "points": 2.5},
                ],
            },
        ]
        odds = _parse_markets(markets, participants)
        self.assertAlmostEqual(odds["1"], 1.9091, places=3)
        self.assertAlmostEqual(odds["X"], 3.4, places=3)
        self.assertAlmostEqual(odds["2"], 3.0, places=3)
        self.assertAlmostEqual(odds["Over2.5"], 1.9091, places=3)
        self.assertAlmostEqual(odds["Under2.5"], 1.8696, places=3)


if __name__ == "__main__":
    unittest.main()
