"""
Unit tests for Risk Calculator (TDD - Phase 2)

These tests MUST be written BEFORE implementation.
They define the expected behavior of the risk calculation engine.
"""

import pytest


class TestRiskCalculator:
    """Test suite for volume calculation based on risk management"""

    def test_calculate_volume_fixed_usd_forex(self):
        """
        GIVEN: User risks $100 USD on EUR/USD trade
        WHEN: Entry=1.1000, SL=1.0950 (50 pips), pip_value=$10/lot
        THEN: Volume should be 0.20 lots (100 / (50 * 10))
        """
        from engine.risk_calculator import RiskCalculator

        calculator = RiskCalculator()

        volume = calculator.calculate_volume(
            risk_usd=100.0,
            entry_price=1.1000,
            sl_price=1.0950,
            pip_value=10.0,  # Standard lot forex
            tick_size=0.00001,
            volume_step=0.01
        )

        assert volume == 0.20

    def test_calculate_volume_fixed_usd_gold(self):
        """
        GIVEN: User risks $50 USD on XAU/USD trade
        WHEN: Entry=2000.00, SL=1995.00 ($5 distance), contract_size=100
        THEN: Volume should be 0.1 lots (50 / (5 × 100))

        Gold contract = 100 oz
        Formula: Volume = Risk / (Distance × Contract Size)
        """
        from engine.risk_calculator import RiskCalculator

        calculator = RiskCalculator()

        volume = calculator.calculate_volume(
            risk_usd=50.0,
            entry_price=2000.00,
            sl_price=1995.00,
            pip_value=1.0,  # Gold: $1 per lot per $1 move
            tick_size=0.01,
            volume_step=0.01
        )

        assert volume == 0.1

    def test_calculate_volume_percent_balance(self):
        """
        GIVEN: User risks 1% of $10,000 balance ($100)
        WHEN: Entry=1.2000, SL=1.1950 (50 pips), pip_value=$10/lot
        THEN: Volume should be 0.20 lots
        """
        from engine.risk_calculator import RiskCalculator

        calculator = RiskCalculator()

        # First calculate risk from balance
        balance = 10000.0
        risk_percent = 0.01  # 1%
        risk_usd = balance * risk_percent  # $100

        volume = calculator.calculate_volume(
            risk_usd=risk_usd,
            entry_price=1.2000,
            sl_price=1.1950,
            pip_value=10.0,
            tick_size=0.00001,
            volume_step=0.01
        )

        assert volume == 0.20

    def test_calculate_volume_respects_min_volume(self):
        """
        GIVEN: Calculated volume is 0.005 lots
        WHEN: Broker minimum is 0.01 lots
        THEN: Volume should be rounded up to 0.01
        """
        from engine.risk_calculator import RiskCalculator

        calculator = RiskCalculator()

        volume = calculator.calculate_volume(
            risk_usd=5.0,  # Very small risk
            entry_price=1.1000,
            sl_price=1.0950,
            pip_value=10.0,
            tick_size=0.00001,
            volume_step=0.01,
            min_volume=0.01
        )

        assert volume == 0.01

    def test_calculate_volume_respects_max_volume(self):
        """
        GIVEN: Calculated volume is 150 lots
        WHEN: Broker maximum is 100 lots
        THEN: Volume should be capped at 100
        """
        from engine.risk_calculator import RiskCalculator

        calculator = RiskCalculator()

        volume = calculator.calculate_volume(
            risk_usd=75000.0,  # Very large risk (75000 / (50 * 10) = 150 lots)
            entry_price=1.1000,
            sl_price=1.0950,
            pip_value=10.0,
            tick_size=0.00001,
            volume_step=0.01,
            max_volume=100.0
        )

        assert volume == 100.0

    def test_calculate_volume_respects_step_size(self):
        """
        GIVEN: Calculated volume is 0.237 lots
        WHEN: Broker step is 0.01 lots
        THEN: Volume should be rounded down to 0.23
        """
        from engine.risk_calculator import RiskCalculator

        calculator = RiskCalculator()

        volume = calculator.calculate_volume(
            risk_usd=118.5,
            entry_price=1.1000,
            sl_price=1.0950,
            pip_value=10.0,
            tick_size=0.00001,
            volume_step=0.01
        )

        # 118.5 / (50 pips * 10) = 0.237, rounded to 0.23
        assert volume == 0.23

    def test_calculate_volume_zero_sl_distance_returns_none(self):
        """
        GIVEN: Entry and SL are the same price
        WHEN: SL distance is zero
        THEN: Should return None (invalid trade)
        """
        from engine.risk_calculator import RiskCalculator

        calculator = RiskCalculator()

        volume = calculator.calculate_volume(
            risk_usd=100.0,
            entry_price=1.1000,
            sl_price=1.1000,  # Same as entry!
            pip_value=10.0,
            tick_size=0.00001,
            volume_step=0.01
        )

        assert volume is None

    def test_calculate_volume_negative_risk_returns_none(self):
        """
        GIVEN: Risk amount is negative
        THEN: Should return None (invalid input)
        """
        from engine.risk_calculator import RiskCalculator

        calculator = RiskCalculator()

        volume = calculator.calculate_volume(
            risk_usd=-100.0,  # Invalid!
            entry_price=1.1000,
            sl_price=1.0950,
            pip_value=10.0,
            tick_size=0.00001,
            volume_step=0.01
        )

        assert volume is None
