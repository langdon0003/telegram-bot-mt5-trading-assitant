"""
Risk Calculator - PHASE 4 Implementation

Calculates position volume based on risk management parameters.
This implementation satisfies all test cases in test_risk_calculator.py.
"""


class RiskCalculator:
    """
    Calculates trading volume based on risk amount and stop loss distance.

    Formula:
    Volume = Risk USD / (Stop Distance in Pips * Pip Value)

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

        if sl_distance_price == 0:
            return None

        # Calculate raw volume based on price distance and pip value
        # For Gold: pip_value = $ per lot per $1 move
        #   Example: Risk $50, Distance $5, pip_value $1/lot → Volume = 50/5 = 10 lots
        # For Forex: pip_value = $ per lot per point move
        #   Example: Risk $100, Distance 0.005 (50 pips), pip_value $10/lot per pip
        #   → Need to calculate pips first: 0.005 / 0.0001 = 50 pips → Volume = 100/(50*10) = 0.2

        # Check if pip_value represents value per unit price move (like Gold)
        # or value per pip (like Forex)
        if tick_size >= 0.01:  # Gold-like (tick_size = 0.01)
            # pip_value is per $ move, direct calculation
            raw_volume = risk_usd / (sl_distance_price * pip_value)
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
