"""Tests for normalizer.py — normalization, aliases, and name matching."""

import unittest

from src.collectors.harvesters.normalizer import (
    LEAGUE_ALIASES,
    american_to_decimal,
    get_alias,
    make_slug,
    name_match_score,
    normalize,
    normalize_slug,
    token_set,
)


class TestNormalize(unittest.TestCase):
    def test_lowercases_and_strips_accents(self):
        self.assertEqual(normalize("São Paulo FC"), "sao paulo")

    def test_strips_club_suffixes(self):
        self.assertEqual(normalize("Manchester United FC"), "manchester")

    def test_preserves_short_names(self):
        """'FC Barcelona' → 'barcelona' — 'fc' stripped as suffix."""
        self.assertEqual(normalize("FC Barcelona"), "barcelona")

    def test_removes_non_alphanumeric(self):
        """'C.D. FAS' → 'c d fas' — dots become spaces, 'fas' is not a suffix."""
        self.assertEqual(normalize("C.D. FAS"), "c d fas")

    def test_empty_returns_empty(self):
        self.assertEqual(normalize(""), "")

    def test_handles_special_characters(self):
        self.assertEqual(normalize("Bayer 04 Leverkusen"), "bayer 04 leverkusen")


class TestNormalizeSlug(unittest.TestCase):
    def test_converts_hyphens_to_spaces(self):
        self.assertEqual(normalize_slug("england-premier-league"), "england premier league")

    def test_handles_underscores(self):
        self.assertEqual(normalize_slug("serie_a"), "serie a")

    def test_strips_suffixes(self):
        self.assertEqual(normalize_slug("real-madrid-cf"), "real madrid")


class TestTokenSet(unittest.TestCase):
    def test_basic_split(self):
        self.assertEqual(token_set("Manchester United"), {"manchester"})

    def test_empty_string(self):
        self.assertEqual(token_set(""), set())


class TestNameMatchScore(unittest.TestCase):
    def test_exact_match(self):
        self.assertEqual(name_match_score("FC Barcelona", "Barcelona FC"), 1.0)

    def test_partial_match(self):
        """'Liverpool' vs 'Liverpool U21' — 'u21' not a suffix, so ratio = 1/2 = 0.5."""
        score = name_match_score("Liverpool", "Liverpool U21")
        self.assertAlmostEqual(score, 0.5)

    def test_no_match(self):
        self.assertEqual(name_match_score("Barcelona", "Liverpool"), 0.0)

    def test_both_empty(self):
        self.assertEqual(name_match_score("", ""), 0.0)


class TestAmericanToDecimal(unittest.TestCase):
    def test_positive_american(self):
        self.assertEqual(american_to_decimal(200), 3.0)

    def test_negative_american(self):
        self.assertEqual(american_to_decimal(-110), 1.9091)

    def test_even_money(self):
        self.assertEqual(american_to_decimal(100), 2.0)

    def test_large_positive(self):
        self.assertEqual(american_to_decimal(500), 6.0)

    def test_large_negative(self):
        self.assertEqual(american_to_decimal(-500), 1.2)


class TestGetAlias(unittest.TestCase):
    def test_known_alias_betexplorer(self):
        alias = get_alias("international-friendly-games", "world")
        self.assertIsNotNone(alias)
        self.assertEqual(alias["betexplorer_search"], "Friendly International")
        self.assertEqual(alias["pinnacle_name"], "International - Friendlies")

    def test_ligapro_serie_a_has_both_fields(self):
        """Regression: duplicate key bug — betexplorer_search was overwritten by pinnacle_name."""
        alias = get_alias("ligapro-serie-a", "ecuador")
        self.assertIsNotNone(alias)
        self.assertEqual(alias["betexplorer_search"], "Liga Pro")
        self.assertEqual(alias["pinnacle_name"], "Ecuador - Serie A")

    def test_ii_liga_poland_has_both_fields(self):
        """Regression: duplicate key bug — missing betexplorer_search."""
        alias = get_alias("ii-liga", "poland")
        self.assertIsNotNone(alias)
        self.assertEqual(alias["betexplorer_search"], "2 Liga")
        self.assertEqual(alias["pinnacle_name"], "Poland - 2nd Liga")

    def test_v_league_2_vietnam_has_both_fields(self):
        """Regression: duplicate key bug — missing betexplorer_search."""
        alias = get_alias("v-league-2", "vietnam")
        self.assertIsNotNone(alias)
        self.assertEqual(alias["betexplorer_search"], "V League 2")
        self.assertEqual(alias["pinnacle_name"], "Vietnam - V League 2")

    def test_unknown_alias_returns_none(self):
        self.assertIsNone(get_alias("nonexistent-league", "mars"))

    def test_alias_with_only_betexplorer(self):
        alias = get_alias("brasileiro-serie-a", "brazil")
        self.assertIsNotNone(alias)
        self.assertEqual(alias["betexplorer_search"], "Serie A Betano")
        self.assertNotIn("pinnacle_name", alias)

    def test_alias_with_only_pinnacle(self):
        alias = get_alias("primera-b", "chile")
        self.assertIsNotNone(alias)
        self.assertEqual(alias["pinnacle_name"], "Chile - Primera B")


class TestMakeSlug(unittest.TestCase):
    def test_basic_slug(self):
        self.assertEqual(make_slug("Premier League"), "premier-league")

    def test_handles_special_chars(self):
        self.assertEqual(make_slug("Copa do Brasil!"), "copa-do-brasil")

    def test_removes_extra_whitespace(self):
        self.assertEqual(make_slug("  Liga   MX  "), "liga-mx")


class TestLeagueAliasesDict(unittest.TestCase):
    def test_no_duplicate_keys(self):
        """Ensure no duplicate keys in LEAGUE_ALIASES (would silently overwrite)."""
        seen = set()
        for key in LEAGUE_ALIASES:
            self.assertNotIn(key, seen, f"Duplicate key: {key}")
            seen.add(key)

    def test_world_entries_exist(self):
        self.assertIn(("international-friendly-games", "world"), LEAGUE_ALIASES)
        self.assertIn(("world-cup-2026", "world"), LEAGUE_ALIASES)

    def test_no_empty_values(self):
        """Every alias must have at least one useful mapping."""
        for key, val in LEAGUE_ALIASES.items():
            self.assertTrue(
                val.get("betexplorer_search") or val.get("pinnacle_name"),
                f"Empty alias for {key}",
            )


if __name__ == "__main__":
    unittest.main()
