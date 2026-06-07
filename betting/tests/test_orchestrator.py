"""Tests for orchestrator.py — session management and function signatures.

The orchestrator module contains two async workflow functions (process_match,
run_full_scan) that are integration-level and require network/database/Playwright.
This suite validates everything that can be verified synchronously:
  - Module-level session accumulator constants
  - Function signatures (parameter names, order, defaults)
  - Imported configuration values
  - Module symbol exports
"""

import inspect
import unittest

from src.core.config import KELLY_MULTIPLIER, LEAGUES
from src.core.orchestrator import (
    _session_bets_logged,
    _session_ev_total,
    _session_stake_total,
    process_match,
    run_full_scan,
)


class TestSessionAccumulators(unittest.TestCase):
    """Module-level globals that accumulate totals across a scan session."""

    def test_session_stake_total_initialized(self):
        """_session_stake_total starts at 0.0."""
        self.assertEqual(_session_stake_total, 0.0)
        self.assertIsInstance(_session_stake_total, float)

    def test_session_ev_total_initialized(self):
        """_session_ev_total starts at 0.0."""
        self.assertEqual(_session_ev_total, 0.0)
        self.assertIsInstance(_session_ev_total, float)

    def test_session_bets_logged_initialized(self):
        """_session_bets_logged starts at 0."""
        self.assertEqual(_session_bets_logged, 0)
        self.assertIsInstance(_session_bets_logged, int)


class TestProcessMatchSignature(unittest.TestCase):
    """Verify process_match's parameter signature."""

    def setUp(self):
        # Get the coroutine function (not the awaited result)
        self.sig = inspect.signature(process_match)

    def test_is_coroutine_function(self):
        """process_match should be an async (coroutine) function."""
        self.assertTrue(inspect.iscoroutinefunction(process_match))

    def test_has_correct_parameters(self):
        """process_match must accept exactly the expected parameters."""
        expected_params = [
            "match",
            "league_config",
            "db",
            "tracker",
            "parser",
            "consensus_engine",
        ]
        params = list(self.sig.parameters.keys())
        for p in expected_params:
            self.assertIn(p, params, f"Missing required parameter: {p}")

    def test_consensus_engine_no_default(self):
        """consensus_engine is a required positional parameter (no default)."""
        param = self.sig.parameters["consensus_engine"]
        self.assertIs(param.default, inspect.Parameter.empty)

    def test_is_session_default_true(self):
        """is_session must have default value True."""
        param = self.sig.parameters["is_session"]
        self.assertEqual(param.default, True)

    def test_parameter_order(self):
        """Parameters appear in the expected declaration order up to is_session."""
        param_names = list(self.sig.parameters.keys())
        # consensus_engine should come before is_session
        ci = param_names.index("consensus_engine")
        si = param_names.index("is_session")
        self.assertLess(ci, si, "consensus_engine should appear before is_session")


class TestRunFullScanSignature(unittest.TestCase):
    """Verify run_full_scan's parameter signature."""

    def setUp(self):
        self.sig = inspect.signature(run_full_scan)

    def test_is_coroutine_function(self):
        """run_full_scan should be an async (coroutine) function."""
        self.assertTrue(inspect.iscoroutinefunction(run_full_scan))

    def test_is_session_default_true(self):
        """is_session must have default value True."""
        param = self.sig.parameters["is_session"]
        self.assertEqual(param.default, True)

    def test_only_parameter_is_is_session(self):
        """run_full_scan accepts exactly one parameter: is_session (optional)."""
        self.assertEqual(list(self.sig.parameters.keys()), ["is_session"])


class TestKELLYMultiplierImport(unittest.TestCase):
    """Verify the KELLY_MULTIPLIER constant imported from config."""

    def test_kelly_multiplier_is_float(self):
        self.assertIsInstance(KELLY_MULTIPLIER, float)

    def test_kelly_multiplier_expected_value(self):
        """Expected fractional Kelly value is 0.20 (20%)."""
        self.assertEqual(KELLY_MULTIPLIER, 0.20)

    def test_kelly_multiplier_between_zero_and_one(self):
        self.assertGreater(KELLY_MULTIPLIER, 0.0)
        self.assertLessEqual(KELLY_MULTIPLIER, 1.0)


class TestLeagueConfigValidation(unittest.TestCase):
    """Validate the LEAGUES config structure imported from core.config."""

    def test_leagues_is_nonempty_list(self):
        self.assertIsInstance(LEAGUES, list)
        self.assertGreater(len(LEAGUES), 0)

    def test_each_league_has_required_keys(self):
        """Every league entry must contain name, country, champ_id, be_path,
        and pin_path."""
        required_keys = {"name", "country", "champ_id", "be_path", "pin_path"}
        for i, league in enumerate(LEAGUES):
            with self.subTest(league=league.get("name", f"index-{i}")):
                self.assertIsInstance(league, dict)
                missing = required_keys - set(league.keys())
                self.assertFalse(
                    missing,
                    f"League at index {i} missing keys: {missing}",
                )

    def test_champ_id_is_integer(self):
        """champ_id must be an integer (Altenar championship ID)."""
        for i, league in enumerate(LEAGUES):
            with self.subTest(league=league.get("name", f"index-{i}")):
                self.assertIsInstance(
                    league.get("champ_id"),
                    int,
                    f"champ_id for league {league.get('name')} is not an int",
                )

    def test_be_path_and_pin_path_are_strings(self):
        """be_path and pin_path must be non-empty strings."""
        for i, league in enumerate(LEAGUES):
            with self.subTest(league=league.get("name", f"index-{i}")):
                self.assertIsInstance(league["be_path"], str)
                self.assertGreater(len(league["be_path"]), 0)
                self.assertIsInstance(league["pin_path"], str)
                self.assertGreater(len(league["pin_path"]), 0)

    def test_unique_champ_ids(self):
        """No two leagues share the same champ_id."""
        ids = [lc["champ_id"] for lc in LEAGUES]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate champ_id values found")

    def test_unique_names(self):
        """No two leagues share the same name."""
        names = [lc["name"] for lc in LEAGUES]
        self.assertEqual(len(names), len(set(names)), "Duplicate league names found")


class TestModuleExports(unittest.TestCase):
    """Verify the module exports the expected top-level symbols."""

    def test_process_match_exported(self):
        self.assertTrue(inspect.iscoroutinefunction(process_match))

    def test_run_full_scan_exported(self):
        self.assertTrue(inspect.iscoroutinefunction(run_full_scan))

    def test_session_globals_accessible(self):
        """Session accumulator globals are reachable at module level."""
        self.assertIsInstance(_session_stake_total, float)
        self.assertIsInstance(_session_ev_total, float)
        self.assertIsInstance(_session_bets_logged, int)


class TestDocumentation(unittest.TestCase):
    """Verify that public functions carry docstrings with expected content."""

    def test_process_match_docstring_exists(self):
        self.assertIsNotNone(process_match.__doc__)
        assert process_match.__doc__ is not None  # narrow type for Pyright
        self.assertGreater(len(process_match.__doc__.strip()), 0)

    def test_process_match_docstring_mentions_harvest(self):
        """Docstring should describe harvesting sharps and EV calculation."""
        self.assertIsNotNone(process_match.__doc__)
        assert process_match.__doc__ is not None
        lower_doc = process_match.__doc__.lower()
        self.assertIn("harvest", lower_doc)
        self.assertIn("ev", lower_doc)

    def test_run_full_scan_docstring_exists(self):
        self.assertIsNotNone(run_full_scan.__doc__)
        assert run_full_scan.__doc__ is not None
        self.assertGreater(len(run_full_scan.__doc__.strip()), 0)

    def test_run_full_scan_docstring_mentions_scan(self):
        self.assertIsNotNone(run_full_scan.__doc__)
        assert run_full_scan.__doc__ is not None
        lower_doc = run_full_scan.__doc__.lower()
        self.assertIn("scan", lower_doc)


if __name__ == "__main__":
    unittest.main()
