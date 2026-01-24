"""
Unit tests for Trade Validator (TDD - Phase 2)

These tests MUST be written BEFORE implementation.
They define validation rules for LIMIT BUY/SELL orders.

Critical Rules:
- LIMIT BUY: Stop Loss MUST be < Entry Price
- LIMIT SELL: Stop Loss MUST be > Entry Price
"""

import pytest


class TestTradeValidator:
    """Test suite for trade validation logic"""

    def test_validate_limit_buy_valid_sl(self):
        """
        GIVEN: LIMIT BUY with entry=2000, SL=1995
        WHEN: SL < Entry (valid for BUY)
        THEN: Validation should pass
        """
        from engine.trade_validator import TradeValidator

        validator = TradeValidator()

        is_valid = validator.validate_sl_position(
            order_type="LIMIT_BUY",
            entry_price=2000.00,
            sl_price=1995.00
        )

        assert is_valid is True

    def test_validate_limit_buy_invalid_sl_above_entry(self):
        """
        GIVEN: LIMIT BUY with entry=2000, SL=2005
        WHEN: SL > Entry (INVALID for BUY)
        THEN: Validation should fail
        """
        from engine.trade_validator import TradeValidator

        validator = TradeValidator()

        is_valid = validator.validate_sl_position(
            order_type="LIMIT_BUY",
            entry_price=2000.00,
            sl_price=2005.00  # Invalid!
        )

        assert is_valid is False

    def test_validate_limit_buy_sl_equals_entry(self):
        """
        GIVEN: LIMIT BUY with entry=2000, SL=2000
        WHEN: SL == Entry
        THEN: Validation should fail (no risk management)
        """
        from engine.trade_validator import TradeValidator

        validator = TradeValidator()

        is_valid = validator.validate_sl_position(
            order_type="LIMIT_BUY",
            entry_price=2000.00,
            sl_price=2000.00  # Same as entry!
        )

        assert is_valid is False

    def test_validate_limit_sell_valid_sl(self):
        """
        GIVEN: LIMIT SELL with entry=2000, SL=2005
        WHEN: SL > Entry (valid for SELL)
        THEN: Validation should pass
        """
        from engine.trade_validator import TradeValidator

        validator = TradeValidator()

        is_valid = validator.validate_sl_position(
            order_type="LIMIT_SELL",
            entry_price=2000.00,
            sl_price=2005.00
        )

        assert is_valid is True

    def test_validate_limit_sell_invalid_sl_below_entry(self):
        """
        GIVEN: LIMIT SELL with entry=2000, SL=1995
        WHEN: SL < Entry (INVALID for SELL)
        THEN: Validation should fail
        """
        from engine.trade_validator import TradeValidator

        validator = TradeValidator()

        is_valid = validator.validate_sl_position(
            order_type="LIMIT_SELL",
            entry_price=2000.00,
            sl_price=1995.00  # Invalid!
        )

        assert is_valid is False

    def test_validate_limit_sell_sl_equals_entry(self):
        """
        GIVEN: LIMIT SELL with entry=2000, SL=2000
        WHEN: SL == Entry
        THEN: Validation should fail
        """
        from engine.trade_validator import TradeValidator

        validator = TradeValidator()

        is_valid = validator.validate_sl_position(
            order_type="LIMIT_SELL",
            entry_price=2000.00,
            sl_price=2000.00
        )

        assert is_valid is False

    def test_calculate_rr_ratio_buy(self):
        """
        GIVEN: LIMIT BUY entry=2000, SL=1995, TP=2015
        WHEN: Risk=5, Reward=15
        THEN: R:R should be 3.0 (15/5)
        """
        from engine.trade_validator import TradeValidator

        validator = TradeValidator()

        rr_ratio = validator.calculate_rr_ratio(
            order_type="LIMIT_BUY",
            entry_price=2000.00,
            sl_price=1995.00,
            tp_price=2015.00
        )

        assert rr_ratio == 3.0

    def test_calculate_rr_ratio_sell(self):
        """
        GIVEN: LIMIT SELL entry=2000, SL=2010, TP=1980
        WHEN: Risk=10, Reward=20
        THEN: R:R should be 2.0 (20/10)
        """
        from engine.trade_validator import TradeValidator

        validator = TradeValidator()

        rr_ratio = validator.calculate_rr_ratio(
            order_type="LIMIT_SELL",
            entry_price=2000.00,
            sl_price=2010.00,
            tp_price=1980.00
        )

        assert rr_ratio == 2.0

    def test_calculate_rr_ratio_buy_negative_reward(self):
        """
        GIVEN: LIMIT BUY entry=2000, SL=1995, TP=1990
        WHEN: TP is below entry (negative reward for BUY)
        THEN: R:R should be negative
        """
        from engine.trade_validator import TradeValidator

        validator = TradeValidator()

        rr_ratio = validator.calculate_rr_ratio(
            order_type="LIMIT_BUY",
            entry_price=2000.00,
            sl_price=1995.00,
            tp_price=1990.00  # Below entry!
        )

        assert rr_ratio < 0

    def test_validate_full_trade_buy_success(self):
        """
        GIVEN: Complete LIMIT BUY trade with valid prices
        THEN: Full validation should pass and return trade details
        """
        from engine.trade_validator import TradeValidator

        validator = TradeValidator()

        result = validator.validate_trade(
            order_type="LIMIT_BUY",
            entry_price=2000.00,
            sl_price=1995.00,
            tp_price=2015.00
        )

        assert result["is_valid"] is True
        assert result["sl_valid"] is True
        assert result["rr_ratio"] == 3.0
        assert result["risk_pips"] == 5.0
        assert result["reward_pips"] == 15.0

    def test_validate_full_trade_sell_success(self):
        """
        GIVEN: Complete LIMIT SELL trade with valid prices
        THEN: Full validation should pass
        """
        from engine.trade_validator import TradeValidator

        validator = TradeValidator()

        result = validator.validate_trade(
            order_type="LIMIT_SELL",
            entry_price=2000.00,
            sl_price=2010.00,
            tp_price=1980.00
        )

        assert result["is_valid"] is True
        assert result["sl_valid"] is True
        assert result["rr_ratio"] == 2.0

    def test_validate_full_trade_invalid_sl(self):
        """
        GIVEN: LIMIT BUY with SL above entry
        THEN: Validation should fail with clear error
        """
        from engine.trade_validator import TradeValidator

        validator = TradeValidator()

        result = validator.validate_trade(
            order_type="LIMIT_BUY",
            entry_price=2000.00,
            sl_price=2005.00,  # Invalid!
            tp_price=2015.00
        )

        assert result["is_valid"] is False
        assert result["sl_valid"] is False
        assert "error" in result
