"""
Unit tests for Trade Command Builder (TDD - Phase 2)

These tests MUST be written BEFORE implementation.
They define the JSON structure for trade commands sent from Bot to Trade Engine.
"""

import pytest
import json


class TestTradeCommandBuilder:
    """Test suite for building valid trade command JSON"""

    def test_build_limit_buy_command(self):
        """
        GIVEN: All required parameters for LIMIT BUY
        THEN: Should build valid JSON command
        """
        from bot.trade_command_builder import TradeCommandBuilder

        builder = TradeCommandBuilder()

        command = builder.build_command(
            user_id=12345,
            account_id=1,
            order_type="LIMIT_BUY",
            symbol="XAUUSD",
            entry_price=2000.00,
            sl_price=1995.00,
            tp_price=2015.00,
            volume=0.10,
            risk_usd=50.00,
            emotion="calm",
            setup_code="FZ1",
            chart_url="https://www.tradingview.com/x/abc123/"
        )

        assert command["user_id"] == 12345
        assert command["account_id"] == 1
        assert command["order_type"] == "LIMIT_BUY"
        assert command["symbol"] == "XAUUSD"
        assert command["entry"] == 2000.00
        assert command["sl"] == 1995.00
        assert command["tp"] == 2015.00
        assert command["volume"] == 0.10
        assert command["risk_usd"] == 50.00
        assert command["emotion"] == "calm"
        assert command["setup_code"] == "FZ1"
        assert command["chart_url"] == "https://www.tradingview.com/x/abc123/"

    def test_build_limit_sell_command(self):
        """
        GIVEN: All required parameters for LIMIT SELL
        THEN: Should build valid JSON command
        """
        from bot.trade_command_builder import TradeCommandBuilder

        builder = TradeCommandBuilder()

        command = builder.build_command(
            user_id=12345,
            account_id=1,
            order_type="LIMIT_SELL",
            symbol="EURUSD",
            entry_price=1.1000,
            sl_price=1.1050,
            tp_price=1.0900,
            volume=0.20,
            risk_usd=100.00,
            emotion="confident",
            setup_code="TLP1",
            chart_url=None  # Optional
        )

        assert command["order_type"] == "LIMIT_SELL"
        assert command["symbol"] == "EURUSD"
        assert command["chart_url"] is None

    def test_build_command_optional_chart_url(self):
        """
        GIVEN: Chart URL is None
        THEN: Command should still be valid
        """
        from bot.trade_command_builder import TradeCommandBuilder

        builder = TradeCommandBuilder()

        command = builder.build_command(
            user_id=12345,
            account_id=1,
            order_type="LIMIT_BUY",
            symbol="XAUUSD",
            entry_price=2000.00,
            sl_price=1995.00,
            tp_price=2015.00,
            volume=0.10,
            risk_usd=50.00,
            emotion="calm",
            setup_code="FZ1",
            chart_url=None
        )

        assert command["chart_url"] is None
        assert "chart_url" in command  # Key should exist

    def test_build_command_validates_emotion(self):
        """
        GIVEN: Invalid emotion value
        THEN: Should raise ValueError
        """
        from bot.trade_command_builder import TradeCommandBuilder

        builder = TradeCommandBuilder()

        with pytest.raises(ValueError, match="Invalid emotion"):
            builder.build_command(
                user_id=12345,
                account_id=1,
                order_type="LIMIT_BUY",
                symbol="XAUUSD",
                entry_price=2000.00,
                sl_price=1995.00,
                tp_price=2015.00,
                volume=0.10,
                risk_usd=50.00,
                emotion="happy",  # Invalid!
                setup_code="FZ1",
                chart_url=None
            )

    def test_build_command_validates_order_type(self):
        """
        GIVEN: Invalid order type
        THEN: Should raise ValueError
        """
        from bot.trade_command_builder import TradeCommandBuilder

        builder = TradeCommandBuilder()

        with pytest.raises(ValueError, match="Invalid order_type"):
            builder.build_command(
                user_id=12345,
                account_id=1,
                order_type="MARKET_BUY",  # Invalid!
                symbol="XAUUSD",
                entry_price=2000.00,
                sl_price=1995.00,
                tp_price=2015.00,
                volume=0.10,
                risk_usd=50.00,
                emotion="calm",
                setup_code="FZ1",
                chart_url=None
            )

    def test_build_command_to_json_serializable(self):
        """
        GIVEN: Valid trade command
        THEN: Should be JSON serializable
        """
        from bot.trade_command_builder import TradeCommandBuilder

        builder = TradeCommandBuilder()

        command = builder.build_command(
            user_id=12345,
            account_id=1,
            order_type="LIMIT_BUY",
            symbol="XAUUSD",
            entry_price=2000.00,
            sl_price=1995.00,
            tp_price=2015.00,
            volume=0.10,
            risk_usd=50.00,
            emotion="calm",
            setup_code="FZ1",
            chart_url="https://www.tradingview.com/x/abc/"
        )

        # Should not raise exception
        json_str = json.dumps(command)
        assert isinstance(json_str, str)

        # Should be able to parse back
        parsed = json.loads(json_str)
        assert parsed["user_id"] == 12345

    def test_build_command_includes_timestamp(self):
        """
        GIVEN: Valid trade command
        THEN: Should include created_at timestamp
        """
        from bot.trade_command_builder import TradeCommandBuilder

        builder = TradeCommandBuilder()

        command = builder.build_command(
            user_id=12345,
            account_id=1,
            order_type="LIMIT_BUY",
            symbol="XAUUSD",
            entry_price=2000.00,
            sl_price=1995.00,
            tp_price=2015.00,
            volume=0.10,
            risk_usd=50.00,
            emotion="calm",
            setup_code="FZ1",
            chart_url=None
        )

        assert "created_at" in command
        assert isinstance(command["created_at"], str)

    def test_build_command_validates_positive_volume(self):
        """
        GIVEN: Volume <= 0
        THEN: Should raise ValueError
        """
        from bot.trade_command_builder import TradeCommandBuilder

        builder = TradeCommandBuilder()

        with pytest.raises(ValueError, match="Volume must be positive"):
            builder.build_command(
                user_id=12345,
                account_id=1,
                order_type="LIMIT_BUY",
                symbol="XAUUSD",
                entry_price=2000.00,
                sl_price=1995.00,
                tp_price=2015.00,
                volume=0.0,  # Invalid!
                risk_usd=50.00,
                emotion="calm",
                setup_code="FZ1",
                chart_url=None
            )

    def test_build_command_validates_positive_risk(self):
        """
        GIVEN: Risk USD <= 0
        THEN: Should raise ValueError
        """
        from bot.trade_command_builder import TradeCommandBuilder

        builder = TradeCommandBuilder()

        with pytest.raises(ValueError, match="Risk must be positive"):
            builder.build_command(
                user_id=12345,
                account_id=1,
                order_type="LIMIT_BUY",
                symbol="XAUUSD",
                entry_price=2000.00,
                sl_price=1995.00,
                tp_price=2015.00,
                volume=0.10,
                risk_usd=-50.00,  # Invalid!
                emotion="calm",
                setup_code="FZ1",
                chart_url=None
            )
