"""
Unit tests for Symbol Resolver (TDD - Phase 2)

These tests MUST be written BEFORE implementation.
They define how symbols are built from prefix + base + "USD" + suffix.
"""

import pytest


class TestSymbolResolver:
    """Test suite for dynamic symbol resolution"""

    def test_resolve_symbol_no_prefix_no_suffix(self):
        """
        GIVEN: base="XAU", prefix="", suffix=""
        THEN: Symbol should be "XAUUSD"
        """
        from engine.symbol_resolver import SymbolResolver

        resolver = SymbolResolver()

        symbol = resolver.resolve(
            base="XAU",
            prefix="",
            suffix=""
        )

        assert symbol == "XAUUSD"

    def test_resolve_symbol_with_prefix_only(self):
        """
        GIVEN: base="XAU", prefix="BROKER.", suffix=""
        THEN: Symbol should be "BROKER.XAUUSD"
        """
        from engine.symbol_resolver import SymbolResolver

        resolver = SymbolResolver()

        symbol = resolver.resolve(
            base="XAU",
            prefix="BROKER.",
            suffix=""
        )

        assert symbol == "BROKER.XAUUSD"

    def test_resolve_symbol_with_suffix_only(self):
        """
        GIVEN: base="XAU", prefix="", suffix="m"
        THEN: Symbol should be "XAUUSDm"
        """
        from engine.symbol_resolver import SymbolResolver

        resolver = SymbolResolver()

        symbol = resolver.resolve(
            base="XAU",
            prefix="",
            suffix="m"
        )

        assert symbol == "XAUUSDm"

    def test_resolve_symbol_with_both_prefix_and_suffix(self):
        """
        GIVEN: base="XAU", prefix="BROKER.", suffix=".pro"
        THEN: Symbol should be "BROKER.XAUUSD.pro"
        """
        from engine.symbol_resolver import SymbolResolver

        resolver = SymbolResolver()

        symbol = resolver.resolve(
            base="XAU",
            prefix="BROKER.",
            suffix=".pro"
        )

        assert symbol == "BROKER.XAUUSD.pro"

    def test_resolve_symbol_eur(self):
        """
        GIVEN: base="EUR", prefix="", suffix=""
        THEN: Symbol should be "EURUSD"
        """
        from engine.symbol_resolver import SymbolResolver

        resolver = SymbolResolver()

        symbol = resolver.resolve(
            base="EUR",
            prefix="",
            suffix=""
        )

        assert symbol == "EURUSD"

    def test_resolve_symbol_gbp_with_suffix(self):
        """
        GIVEN: base="GBP", prefix="", suffix=".a"
        THEN: Symbol should be "GBPUSD.a"
        """
        from engine.symbol_resolver import SymbolResolver

        resolver = SymbolResolver()

        symbol = resolver.resolve(
            base="GBP",
            prefix="",
            suffix=".a"
        )

        assert symbol == "GBPUSD.a"

    def test_resolve_symbol_none_values_treated_as_empty(self):
        """
        GIVEN: base="XAU", prefix=None, suffix=None
        THEN: Symbol should be "XAUUSD" (None treated as empty string)
        """
        from engine.symbol_resolver import SymbolResolver

        resolver = SymbolResolver()

        symbol = resolver.resolve(
            base="XAU",
            prefix=None,
            suffix=None
        )

        assert symbol == "XAUUSD"

    def test_resolve_symbol_case_preserved(self):
        """
        GIVEN: base="xau" (lowercase)
        THEN: Symbol should preserve case: "xauUSD"
        """
        from engine.symbol_resolver import SymbolResolver

        resolver = SymbolResolver()

        symbol = resolver.resolve(
            base="xau",
            prefix="",
            suffix=""
        )

        assert symbol == "xauUSD"

    def test_resolve_symbol_empty_base_returns_none(self):
        """
        GIVEN: base="" (empty string)
        THEN: Should return None (invalid)
        """
        from engine.symbol_resolver import SymbolResolver

        resolver = SymbolResolver()

        symbol = resolver.resolve(
            base="",
            prefix="BROKER.",
            suffix="m"
        )

        assert symbol is None
