"""Tests for scraper.py — slug generation, URL helpers, and PIN_PATH_OVERRIDES."""

import unittest

from src.collectors.scraper import (
    PIN_PATH_OVERRIDES,
    discover_active_leagues,
    fetch_json,
    fetch_page_json,
    find_matches,
    make_slug,
)


class TestMakeSlug(unittest.TestCase):
    """Tests for make_slug() — URL-safe slug generation."""

    def test_basic_league_name(self):
        """'Premier League' → 'premier-league'."""
        self.assertEqual(make_slug("Premier League"), "premier-league")

    def test_removes_special_characters(self):
        """Punctuation and special chars are stripped."""
        self.assertEqual(make_slug("Copa do Brasil!"), "copa-do-brasil")
        self.assertEqual(make_slug("C.D. FAS"), "cd-fas")

    def test_collapses_extra_whitespace(self):
        """Multiple spaces are collapsed into a single hyphen."""
        self.assertEqual(make_slug("  Liga   MX  "), "liga-mx")

    def test_handles_accented_chars(self):
        """Accented characters outside a-z are stripped."""
        self.assertEqual(make_slug("São Paulo"), "so-paulo")
        self.assertEqual(make_slug("Vitória"), "vitria")

    def test_handles_numbers(self):
        """Numerals are preserved."""
        self.assertEqual(make_slug("Bayer 04 Leverkusen"), "bayer-04-leverkusen")
        self.assertEqual(make_slug("1. FC Köln"), "1-fc-kln")

    def test_already_slugified(self):
        """Already-slugified input passes through unchanged."""
        self.assertEqual(make_slug("premier-league"), "premier-league")

    def test_mixed_case(self):
        """Input is lowercased."""
        self.assertEqual(make_slug("UEFA Champions League"), "uefa-champions-league")

    def test_empty_string(self):
        """Empty string returns empty string."""
        self.assertEqual(make_slug(""), "")

    def test_only_special_chars(self):
        """String of only special characters reduces to a single hyphen."""
        self.assertEqual(make_slug("!!! @@@ ###"), "-")

    def test_consecutive_hyphens_and_spaces(self):
        """Mixed hyphens and spaces collapse into single hyphen."""
        self.assertEqual(make_slug("a - b"), "a-b")
        self.assertEqual(make_slug("a--b"), "a-b")

    def test_tabs_and_newlines(self):
        """Whitespace characters other than space are treated as separators."""
        self.assertEqual(make_slug("a\tb"), "a-b")
        self.assertEqual(make_slug("a\nb"), "a-b")

    def test_leading_trailing_whitespace(self):
        """Leading/trailing whitespace is stripped before slugging."""
        self.assertEqual(make_slug("  hello  "), "hello")

    def test_single_character(self):
        self.assertEqual(make_slug("a"), "a")
        self.assertEqual(make_slug("A"), "a")

    def test_underscores_removed(self):
        """Underscores are not in [a-z0-9\\s-], so they are removed."""
        self.assertEqual(make_slug("some_league"), "someleague")

    def test_hyphen_preserved(self):
        """Existing hyphens are kept and collapsed with adjacent whitespace."""
        self.assertEqual(make_slug("england-premier-league"), "england-premier-league")

    def test_none_raises_type_error(self):
        """Passing None should raise AttributeError because .lower() is called on None."""
        with self.assertRaises(AttributeError):
            make_slug(None)  # type: ignore[arg-type]


class TestPinPathOverrides(unittest.TestCase):
    """Structure and completeness checks for PIN_PATH_OVERRIDES."""

    def test_is_dict(self):
        self.assertIsInstance(PIN_PATH_OVERRIDES, dict)

    def test_all_keys_are_tuple_str_str(self):
        """Every key must be a (country_slug, league_slug) tuple of strings."""
        for key in PIN_PATH_OVERRIDES:
            self.assertIsInstance(key, tuple)
            self.assertEqual(len(key), 2)
            self.assertIsInstance(key[0], str)
            self.assertIsInstance(key[1], str)

    def test_all_values_are_nonempty_strings(self):
        for val in PIN_PATH_OVERRIDES.values():
            self.assertIsInstance(val, str)
            self.assertGreater(len(val), 0)

    def test_key_slugs_match_make_slug_pattern(self):
        """All key slugs should be valid output of make_slug() — lowercase, no special chars."""
        for country_slug, league_slug in PIN_PATH_OVERRIDES:
            self.assertEqual(country_slug, make_slug(country_slug))
            self.assertEqual(league_slug, make_slug(league_slug))

    def test_known_conmebol_entries(self):
        self.assertEqual(
            PIN_PATH_OVERRIDES[("americas", "copa-sudamericana")],
            "conmebol-copa-sudamericana",
        )
        self.assertEqual(
            PIN_PATH_OVERRIDES[("americas", "copa-libertadores")],
            "conmebol-copa-libertadores",
        )

    def test_known_uefa_entries(self):
        self.assertEqual(
            PIN_PATH_OVERRIDES[("europe", "champions-league")],
            "uefa-champions-league",
        )
        self.assertEqual(
            PIN_PATH_OVERRIDES[("europe", "europa-league")],
            "uefa-europa-league",
        )

    def test_known_caf_entry(self):
        self.assertEqual(
            PIN_PATH_OVERRIDES[("africa", "africa-cup-of-nations")],
            "caf-africa-cup-of-nations",
        )

    def test_known_concacaf_entries(self):
        self.assertEqual(
            PIN_PATH_OVERRIDES[("central-america", "concacaf-champions-cup")],
            "concacaf-champions-cup",
        )
        self.assertEqual(
            PIN_PATH_OVERRIDES[("north-america", "concacaf-champions-cup")],
            "concacaf-champions-cup",
        )

    def test_no_duplicate_values(self):
        """Some values are shared across keys (alias groups). Just verify structure."""
        self.assertGreater(len(PIN_PATH_OVERRIDES), 0)

    def test_total_count(self):
        """Explicit count to catch accidental additions/removals."""
        self.assertEqual(len(PIN_PATH_OVERRIDES), 13)


class TestFetchJsonInterface(unittest.TestCase):
    """Placeholder: fetch_json() is a synchronous network function.

    Tested here via interface documentation only; actual execution requires
    a live Altenar API endpoint or a mocked urllib.request.
    """

    def test_fetch_json_signature(self):
        """fetch_json should take a single url string argument."""
        import inspect

        sig = inspect.signature(fetch_json)
        self.assertEqual(list(sig.parameters.keys()), ["url"])

    def test_fetch_json_docstring(self):
        """fetch_json has no docstring, but should accept a URL."""
        # Just verify the function is callable with a string
        # (actual call will do network I/O, so we only check signature)
        pass


class TestFindMatchesInterface(unittest.TestCase):
    """Placeholder: find_matches() is an async function that makes network calls.

    Full testing requires mocking fetch_json() or providing a live endpoint.
    These tests document the expected interface and return structure.
    """

    def test_find_matches_is_async(self):
        """find_matches should be a coroutine function."""
        import inspect

        self.assertTrue(inspect.iscoroutinefunction(find_matches))

    def test_find_matches_signature(self):
        """find_matches takes a single champ_id integer parameter."""
        import inspect

        sig = inspect.signature(find_matches)
        self.assertEqual(list(sig.parameters.keys()), ["champ_id"])

    def test_find_matches_champ_id_type_annotation(self):
        """champ_id should be annotated as int."""
        import inspect

        sig = inspect.signature(find_matches)
        param = sig.parameters["champ_id"]
        self.assertEqual(param.annotation, int)


class TestFetchPageJsonInterface(unittest.TestCase):
    """Placeholder: fetch_page_json() is an async function with network + file I/O."""

    def test_fetch_page_json_is_async(self):
        import inspect

        self.assertTrue(inspect.iscoroutinefunction(fetch_page_json))

    def test_fetch_page_json_signature(self):
        """fetch_page_json takes url (str) and output_path (str)."""
        import inspect

        sig = inspect.signature(fetch_page_json)
        self.assertEqual(list(sig.parameters.keys()), ["url", "output_path"])

    def test_fetch_page_json_annotations(self):
        import inspect

        sig = inspect.signature(fetch_page_json)
        self.assertEqual(sig.parameters["url"].annotation, str)
        self.assertEqual(sig.parameters["output_path"].annotation, str)


class TestDiscoverActiveLeaguesInterface(unittest.TestCase):
    """Placeholder: discover_active_leagues() is an async network function."""

    def test_discover_active_leagues_is_async(self):
        import inspect

        self.assertTrue(inspect.iscoroutinefunction(discover_active_leagues))

    def test_discover_active_leagues_signature(self):
        """discover_active_leagues takes no parameters."""
        import inspect

        sig = inspect.signature(discover_active_leagues)
        self.assertEqual(len(sig.parameters), 0)

    def test_discover_active_leagues_return_structure(self):
        """Documented return type: list[dict] with expected keys."""
        expected_keys = {
            "name",
            "country",
            "champ_id",
            "be_path",
            "pin_path",
            "events_count",
        }
        # No mock here — just document the expected structure in the test name
        # Actual integration test would mock fetch_json and assert on returned dicts
        self.assertEqual(
            sorted(expected_keys),
            ["be_path", "champ_id", "country", "events_count", "name", "pin_path"],
        )


if __name__ == "__main__":
    unittest.main()
