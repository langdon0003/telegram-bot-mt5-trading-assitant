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

        # Calculate stop distance
        sl_distance = abs(entry_price - sl_price)

        if sl_distance == 0:
            return None

        # Calculate raw volume
        # Volume = Risk / (Distance * Pip Value)
        raw_volume = risk_usd / (sl_distance * pip_value)

        # Round down to volume step
        volume = self._round_to_step(raw_volume, volume_step)

        # Enforce min/max limits
        if volume < min_volume:
            volume = min_volume

        if volume > max_volume:
            volume = max_volume

        return volume

    def _round_to_step(self, value: float, step: float) -> float:
        """
        Round value down to nearest step.

        Example: value=0.237, step=0.01 -> 0.23
        """
        import math
        return math.floor(value / step) * step
