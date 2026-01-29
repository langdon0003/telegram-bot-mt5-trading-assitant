"""
Tests for Settings Commands

Test risk value formatting and display logic used in /setrisktype command.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, CallbackQuery, Message, User, Chat
from telegram.ext import ContextTypes


def format_risk_value_display(risk_type: str, risk_value: float) -> str:
    """
    Format risk value for display based on risk type.

    This is the core logic used in /setrisktype to display the current value.

    Args:
        risk_type: "fixed_usd" or "percent"
        risk_value: Raw value from database
                   - For fixed_usd: actual USD amount (e.g., 100.0)
                   - For percent: decimal value (e.g., 0.01 for 1%)

    Returns:
        Formatted string for display (e.g., "$100" or "1%")
    """
    if risk_type == "fixed_usd":
        return f"${risk_value}"
    else:  # percent
        # Convert from decimal to percentage (0.01 -> 1%)
        return f"{risk_value * 100}%"


class TestRiskValueFormatting:
    """Test risk value formatting for display"""

    def test_format_fixed_usd(self):
        """
        GIVEN: Risk type is "fixed_usd" with value 100.0
        WHEN: Format for display
        THEN: Should show "$100.0"
        """
        result = format_risk_value_display("fixed_usd", 100.0)
        assert result == "$100.0"

    def test_format_fixed_usd_decimal(self):
        """
        GIVEN: Risk type is "fixed_usd" with value 50.5
        WHEN: Format for display
        THEN: Should show "$50.5"
        """
        result = format_risk_value_display("fixed_usd", 50.5)
        assert result == "$50.5"

    def test_format_percent_one(self):
        """
        GIVEN: Risk type is "percent" with value 0.01 (stored as decimal)
        WHEN: Format for display
        THEN: Should show "1%" (converted from decimal to percentage)
        """
        result = format_risk_value_display("percent", 0.01)
        assert result == "1.0%"

    def test_format_percent_half(self):
        """
        GIVEN: Risk type is "percent" with value 0.005 (0.5% stored as decimal)
        WHEN: Format for display
        THEN: Should show "0.5%"
        """
        result = format_risk_value_display("percent", 0.005)
        assert result == "0.5%"

    def test_format_percent_two(self):
        """
        GIVEN: Risk type is "percent" with value 0.02 (2% stored as decimal)
        WHEN: Format for display
        THEN: Should show "2.0%"
        """
        result = format_risk_value_display("percent", 0.02)
        assert result == "2.0%"

    def test_format_percent_large(self):
        """
        GIVEN: Risk type is "percent" with value 0.1 (10% stored as decimal)
        WHEN: Format for display
        THEN: Should show "10.0%"
        """
        result = format_risk_value_display("percent", 0.1)
        assert result == "10.0%"


class TestRiskTypeScenarios:
    """Test real-world scenarios for /setrisktype command"""

    def test_setrisktype_fixed_usd_to_percent(self):
        """
        GIVEN: User has risk_type="fixed_usd", risk_value=100.0
        WHEN: Change to "percent" via /setrisktype
        THEN: Should display old value as "$100.0 (unchanged)"
        """
        # Current settings
        current_type = "fixed_usd"
        current_value = 100.0

        # User clicks "Percent" button but value doesn't change
        display = format_risk_value_display(current_type, current_value)
        assert display == "$100.0"

    def test_setrisktype_percent_to_fixed_usd(self):
        """
        GIVEN: User has risk_type="percent", risk_value=0.01 (1%)
        WHEN: Change to "fixed_usd" via /setrisktype
        THEN: Should display old value as "1.0% (unchanged)"
        """
        # Current settings (before change)
        current_type = "percent"
        current_value = 0.01  # Stored as decimal

        # Display current value before type change
        display = format_risk_value_display(current_type, current_value)
        assert display == "1.0%"

    def test_setrisktype_preserves_value_format(self):
        """
        GIVEN: Multiple users with different risk settings
        WHEN: They use /setrisktype
        THEN: Each should see their value formatted correctly
        """
        # User A: Fixed $50
        user_a_type = "fixed_usd"
        user_a_value = 50.0
        assert format_risk_value_display(user_a_type, user_a_value) == "$50.0"

        # User B: 2% of balance
        user_b_type = "percent"
        user_b_value = 0.02
        assert format_risk_value_display(user_b_type, user_b_value) == "2.0%"

        # User C: Fixed $200
        user_c_type = "fixed_usd"
        user_c_value = 200.0
        assert format_risk_value_display(user_c_type, user_c_value) == "$200.0"


class TestEdgeCases:
    """Test edge cases for risk value formatting"""

    def test_format_very_small_percent(self):
        """
        GIVEN: Risk type is "percent" with value 0.001 (0.1%)
        WHEN: Format for display
        THEN: Should show "0.1%"
        """
        result = format_risk_value_display("percent", 0.001)
        assert result == "0.1%"

    def test_format_zero_value(self):
        """
        GIVEN: Risk value is 0 (edge case, shouldn't happen in production)
        WHEN: Format for display
        THEN: Should handle gracefully
        """
        # Fixed USD
        result_usd = format_risk_value_display("fixed_usd", 0.0)
        assert result_usd == "$0.0"

        # Percent
        result_pct = format_risk_value_display("percent", 0.0)
        assert result_pct == "0.0%"

    def test_format_large_usd_value(self):
        """
        GIVEN: Risk type is "fixed_usd" with value 10000.0
        WHEN: Format for display
        THEN: Should show "$10000.0"
        """
        result = format_risk_value_display("fixed_usd", 10000.0)
        assert result == "$10000.0"


class TestRiskTypeUpdate:
    """Test the /setrisktype command full flow (type + value)"""

    def test_convert_percent_input_to_decimal(self):
        """
        GIVEN: User enters "1" for 1% risk
        WHEN: Convert to decimal for storage
        THEN: Should store as 0.01 in database
        """
        user_input = 1.0  # User types "1" for 1%
        stored_value = user_input / 100.0
        assert stored_value == 0.01

    def test_convert_half_percent_to_decimal(self):
        """
        GIVEN: User enters "0.5" for 0.5% risk
        WHEN: Convert to decimal for storage
        THEN: Should store as 0.005 in database
        """
        user_input = 0.5  # User types "0.5" for 0.5%
        stored_value = user_input / 100.0
        assert stored_value == 0.005

    def test_fixed_usd_no_conversion(self):
        """
        GIVEN: User enters "100" for $100 risk
        WHEN: Store fixed USD value
        THEN: Should store as 100.0 (no conversion needed)
        """
        user_input = 100.0  # User types "100"
        stored_value = user_input  # No conversion for fixed_usd
        assert stored_value == 100.0


class TestSetRiskTypeFlow:
    """Test the complete /setrisktype command flow"""

    @pytest.mark.asyncio
    async def test_setrisktype_fixed_usd_flow(self):
        """
        GIVEN: User runs /setrisktype
        WHEN: Selects Fixed USD and enters 100
        THEN: Should save risk_type="fixed_usd", risk_value=100.0
        """
        from bot.settings_commands import save_risktype_settings

        # Mock update with user input "100"
        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.text = "100"
        update.message.reply_text = AsyncMock()
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 12345

        # Mock context with risk_type set to fixed_usd
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {'risk_type': 'fixed_usd'}

        # Mock database from bot_data
        mock_db = MagicMock()
        mock_db.get_user_by_telegram_id.return_value = {'id': 1}
        mock_db.update_user_settings = MagicMock()
        context.application.bot_data = {'db': mock_db}

        result = await save_risktype_settings(update, context)

        # Verify database was updated correctly
        mock_db.update_user_settings.assert_called_once_with(
            user_id=1,
            risk_type='fixed_usd',
            risk_value=100.0  # No conversion for fixed_usd
        )

        # Verify success message sent
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args[0][0]
        assert "✅ Risk settings saved!" in call_args
        assert "$100" in call_args

    @pytest.mark.asyncio
    async def test_setrisktype_percent_flow(self):
        """
        GIVEN: User runs /setrisktype
        WHEN: Selects Percent and enters 1 (for 1%)
        THEN: Should save risk_type="percent", risk_value=0.01
        """
        from bot.settings_commands import save_risktype_settings

        # Mock update with user input "1"
        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.text = "1"
        update.message.reply_text = AsyncMock()
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 12345

        # Mock context with risk_type set to percent
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {'risk_type': 'percent'}

        # Mock database from bot_data
        mock_db = MagicMock()
        mock_db.get_user_by_telegram_id.return_value = {'id': 1}
        mock_db.update_user_settings = MagicMock()
        context.application.bot_data = {'db': mock_db}

        result = await save_risktype_settings(update, context)

        # Verify database was updated correctly
        mock_db.update_user_settings.assert_called_once_with(
            user_id=1,
            risk_type='percent',
            risk_value=0.01  # Converted from 1% to 0.01
        )

        # Verify success message sent
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args[0][0]
        assert "✅ Risk settings saved!" in call_args
        assert "1.0%" in call_args  # Python formats as 1.0, not 1

    @pytest.mark.asyncio
    async def test_setrisktype_percent_half_percent(self):
        """
        GIVEN: User runs /setrisktype
        WHEN: Selects Percent and enters 0.5 (for 0.5%)
        THEN: Should save risk_type="percent", risk_value=0.005
        """
        from bot.settings_commands import save_risktype_settings

        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.text = "0.5"
        update.message.reply_text = AsyncMock()
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 12345

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {'risk_type': 'percent'}

        # Mock database from bot_data
        mock_db = MagicMock()
        mock_db.get_user_by_telegram_id.return_value = {'id': 1}
        mock_db.update_user_settings = MagicMock()
        context.application.bot_data = {'db': mock_db}

        await save_risktype_settings(update, context)

        # Verify 0.5% converted to 0.005
        mock_db.update_user_settings.assert_called_once_with(
            user_id=1,
            risk_type='percent',
            risk_value=0.005
        )

    @pytest.mark.asyncio
    async def test_setrisktype_validates_positive_value(self):
        """
        GIVEN: User enters negative or zero value
        WHEN: Save risk settings
        THEN: Should reject and ask to try again
        """
        from bot.settings_commands import save_risktype_settings

        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.text = "-10"
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {'risk_type': 'fixed_usd'}

        result = await save_risktype_settings(update, context)

        # Should ask to try again (returns RISKTYPE_VALUE state)
        from bot.settings_commands import RISKTYPE_VALUE
        assert result == RISKTYPE_VALUE

        # Should show error message
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args[0][0]
        assert "❌" in call_args
        assert "positive" in call_args.lower()

    @pytest.mark.asyncio
    async def test_setrisktype_validates_percent_max_100(self):
        """
        GIVEN: User enters percentage > 100
        WHEN: Save risk settings
        THEN: Should reject and ask to try again
        """
        from bot.settings_commands import save_risktype_settings

        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.text = "150"
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {'risk_type': 'percent'}

        result = await save_risktype_settings(update, context)

        # Should ask to try again
        from bot.settings_commands import RISKTYPE_VALUE
        assert result == RISKTYPE_VALUE

        # Should show error message
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args[0][0]
        assert "❌" in call_args
        assert "100" in call_args

    @pytest.mark.asyncio
    async def test_setrisktype_validates_numeric_input(self):
        """
        GIVEN: User enters non-numeric text
        WHEN: Save risk settings
        THEN: Should reject and ask to try again
        """
        from bot.settings_commands import save_risktype_settings

        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.text = "abc"
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {'risk_type': 'fixed_usd'}

        result = await save_risktype_settings(update, context)

        # Should ask to try again
        from bot.settings_commands import RISKTYPE_VALUE
        assert result == RISKTYPE_VALUE

        # Should show error message
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args[0][0]
        assert "❌" in call_args
        assert "Invalid number" in call_args
