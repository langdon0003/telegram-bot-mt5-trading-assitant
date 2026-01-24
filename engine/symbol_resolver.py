"""
Symbol Resolver - PHASE 4 Implementation

Builds MT5 symbol from user configuration (prefix + base + "USD" + suffix).
This implementation satisfies all test cases in test_symbol_resolver.py.
"""


class SymbolResolver:
    """
    Resolves MT5 symbol from components.

    Formula: symbol = prefix + base + "USD" + suffix

    Examples:
    - base="XAU", prefix="", suffix="" -> "XAUUSD"
    - base="XAU", prefix="BROKER.", suffix="m" -> "BROKER.XAUUSDm"
    """

    def resolve(
        self,
        base: str,
        prefix: str | None = None,
        suffix: str | None = None
    ) -> str | None:
        """
        Build MT5 symbol from components.

        Args:
            base: Base currency (e.g., "XAU", "EUR", "GBP")
            prefix: Optional prefix (e.g., "BROKER.")
            suffix: Optional suffix (e.g., "m", ".pro")

        Returns:
            Complete MT5 symbol, or None if base is empty
        """
        # Validate base
        if not base or base == "":
            return None

        # Treat None as empty string
        prefix = prefix or ""
        suffix = suffix or ""

        # Build symbol: prefix + base + "USD" + suffix
        symbol = f"{prefix}{base}USD{suffix}"

        return symbol
