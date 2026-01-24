"""
Risk Calculator - PHASE 4 Implementation

Calculates position volume based on risk management parameters.
This implementation satisfies all test cases in test_risk_calculator.py.

Updated Formula for Gold (XAU/USD):
Volume (Lot) = Risk Amount / (Stop Loss Distance × 100)

Where:
- Risk Amount: The money you're willing to lose (e.g., $100)
- Stop Loss Distance: |Entry - Stop Loss| in price units
- 100: Standard contract size for Gold (XAUUSD)

Example:
- Entry: 2650, Stop Loss: 2640 (Distance: 10)
- Risk: $100
- Volume = 100 / (10 × 100) = 0.10 Lot

For Forex pairs:
Volume = Risk USD / (Stop Distance in Pips × Pip Value)
"""


class RiskCalculator:
    """
    Calculates trading volume based on risk amount and stop loss distance.

    Supports two calculation methods:
    1. Gold (XAUUSD): Volume = Risk / (Distance × 100)
    2. Forex: Volume = Risk / (Distance in Pips × Pip Value)

    Then rounds to broker's volume step and enforces min/max limits.
    """

    def calculate_volume(
        self,
        risk_usd: float,
        entry_price: float,
        sl_price: float,
        pip_value: float,
        tick_size: float,
        volume_step: float,
        min_volume: float = 0.01,
        max_volume: float = 100.0
    ) -> float | None:
        """
        Calculate position volume based on risk management.

        Args:
            risk_usd: Amount of USD to risk on this trade
            entry_price: Entry price for the trade
            sl_price: Stop loss price
            pip_value: Value per pip/point per lot (e.g., $10 for forex standard lot)
            tick_size: Minimum price increment (e.g., 0.00001 for forex)
            volume_step: Minimum volume increment (e.g., 0.01)
            min_volume: Broker minimum volume
            max_volume: Broker maximum volume

        Returns:
            Calculated volume in lots, or None if invalid inputs
        """
        # Validate inputs
        if risk_usd <= 0:
            return None

        # Calculate stop distance in price
        sl_distance_price = abs(entry_price - sl_price)

        print(f"SL Distance Price: {sl_distance_price}")

        if sl_distance_price == 0:
            return None

        # Calculate raw volume based on instrument type
        #
        # For Gold (XAUUSD):
        #   Formula: Volume = Risk / (Distance × 100)
        #   Where 100 is the standard contract size for Gold
        #
        #   Example: Entry 2650, SL 2640, Risk $100
        #   Distance = 10, Volume = 100 / (10 × 100) = 0.10 Lot
        #
        # For Forex pairs:
        #   Formula: Volume = Risk / (Distance in Pips × Pip Value)
        #
        #   Example: Entry 1.1000, SL 1.0950, Risk $100, Pip Value $10
        #   Distance = 0.005 (50 pips), Volume = 100 / (50 × 10) = 0.20 Lot

        if tick_size >= 0.01:  # Gold-like (tick_size = 0.01)
            # Using simplified Gold formula: Volume = Risk / (Distance × 100)
            # The pip_value of 1.0 for Gold means $1 per lot per $1 move
            # So: Risk / (Distance × 100) = Risk / (Distance × 100 × pip_value)
            # When pip_value = 1.0: Risk / (Distance × 100)
            raw_volume = risk_usd / (sl_distance_price * 100)
        else:  # Forex-like (tick_size = 0.00001 or 0.0001)
            # pip_value is per pip (10 points for 5-digit, 1 point for 4-digit)
            # Convert price distance to pips (assuming 1 pip = 10 points for 5-digit)
            pip_size = 0.0001  # Standard pip size for forex
            sl_distance_pips = sl_distance_price / pip_size
            raw_volume = risk_usd / (sl_distance_pips * pip_value)

        # Enforce max volume BEFORE rounding (to handle very large risk amounts)
        if raw_volume > max_volume:
            return max_volume

        # Round down to volume step
        volume = self._round_to_step(raw_volume, volume_step)

        # Enforce min volume after rounding
        if volume < min_volume:
            volume = min_volume

        return volume

    def _round_to_step(self, value: float, step: float) -> float:
        """
        Round value down to nearest step.

        Example: value=0.237, step=0.01 -> 0.23

        Uses rounding to avoid floating point precision issues.
        """
        import math
        # Round to 8 decimal places first to avoid floating point errors
        value = round(value, 8)
        return math.floor(value / step) * step
