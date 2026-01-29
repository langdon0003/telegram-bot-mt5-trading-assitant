"""
Tests for Menu Handler

Test main menu display and callback routing.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, CallbackQuery, Message, User, Chat
from telegram.ext import ContextTypes


class TestShowMainMenu:
    """Test main menu display"""

    @pytest.mark.asyncio
    async def test_show_menu_on_start(self):
        """
        GIVEN: User sends /start command
        WHEN: show_main_menu is called
        THEN: Should display menu with 4 buttons
        """
        from bot.menu_handler import show_main_menu

        # Mock update with message
        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()
        update.callback_query = None

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        await show_main_menu(update, context)

        # Verify menu was sent
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args

        # Check message text
        message_text = call_args[0][0]
        assert "MT5 Trading Assistant Menu" in message_text
        assert "Vui lòng chọn menu" in message_text

        # Check keyboard markup
        reply_markup = call_args[1]['reply_markup']
        assert reply_markup is not None

        # Should have 3 rows of buttons
        keyboard = reply_markup.inline_keyboard
        assert len(keyboard) == 3

        # Row 1: Place Order
        assert len(keyboard[0]) == 1
        assert keyboard[0][0].text == "📊 Place Order"
        assert keyboard[0][0].callback_data == "menu_place_order"

        # Row 2: View Orders, Settings
        assert len(keyboard[1]) == 2
        assert keyboard[1][0].text == "📋 View Orders"
        assert keyboard[1][1].text == "⚙️ Settings"

        # Row 3: More Commands
        assert len(keyboard[2]) == 1
        assert keyboard[2][0].text == "🔧 More Commands"

    @pytest.mark.asyncio
    async def test_show_menu_from_callback(self):
        """
        GIVEN: User clicks "Back to Menu" button
        WHEN: show_main_menu is called with callback_query
        THEN: Should edit message instead of sending new one
        """
        from bot.menu_handler import show_main_menu

        # Mock update with callback query
        update = MagicMock(spec=Update)
        update.callback_query = MagicMock(spec=CallbackQuery)
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.message = None

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        await show_main_menu(update, context)

        # Verify callback was answered
        update.callback_query.answer.assert_called_once()

        # Verify message was edited
        update.callback_query.edit_message_text.assert_called_once()


class TestMenuCallbacks:
    """Test menu button callbacks"""

    @pytest.mark.asyncio
    async def test_place_order_submenu(self):
        """
        GIVEN: User clicks "Place Order" button
        WHEN: handle_menu_callback is called
        THEN: Should show trading submenu with Limit Buy/Sell
        """
        from bot.menu_handler import handle_menu_callback

        update = MagicMock(spec=Update)
        update.callback_query = MagicMock(spec=CallbackQuery)
        update.callback_query.data = "menu_place_order"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        await handle_menu_callback(update, context)

        # Verify submenu was shown
        update.callback_query.edit_message_text.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args

        # Check message
        message = call_args[0][0]
        assert "Trading Menu" in message

        # Check keyboard has Limit Buy, Limit Sell, Back
        reply_markup = call_args[1]['reply_markup']
        keyboard = reply_markup.inline_keyboard

        assert len(keyboard) == 3
        assert keyboard[0][0].text == "🟢 Limit Buy"
        assert keyboard[0][0].callback_data == "action_limitbuy"
        assert keyboard[1][0].text == "🔴 Limit Sell"
        assert keyboard[1][0].callback_data == "action_limitsell"
        assert keyboard[2][0].text == "« Back to Menu"
        assert keyboard[2][0].callback_data == "menu_back"

    @pytest.mark.asyncio
    async def test_settings_submenu(self):
        """
        GIVEN: User clicks "Settings" button
        WHEN: handle_menu_callback is called
        THEN: Should show settings submenu
        """
        from bot.menu_handler import handle_menu_callback

        update = MagicMock(spec=Update)
        update.callback_query = MagicMock(spec=CallbackQuery)
        update.callback_query.data = "menu_settings"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        await handle_menu_callback(update, context)

        # Verify settings menu was shown
        call_args = update.callback_query.edit_message_text.call_args
        message = call_args[0][0]
        assert "Settings Menu" in message

        # Check keyboard has settings options
        reply_markup = call_args[1]['reply_markup']
        keyboard = reply_markup.inline_keyboard

        # Should have: Risk Settings, R:R Ratio, Symbol Config, View Settings, Back
        assert len(keyboard) == 5
        assert "Risk Settings" in keyboard[0][0].text
        assert "R:R Ratio" in keyboard[1][0].text
        assert "Symbol Config" in keyboard[2][0].text
        assert "View Settings" in keyboard[3][0].text
        assert "Back to Menu" in keyboard[4][0].text

    @pytest.mark.asyncio
    async def test_back_to_menu(self):
        """
        GIVEN: User clicks "Back to Menu" button
        WHEN: handle_menu_callback is called
        THEN: Should return to main menu
        """
        from bot.menu_handler import handle_menu_callback

        update = MagicMock(spec=Update)
        update.callback_query = MagicMock(spec=CallbackQuery)
        update.callback_query.data = "menu_back"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        await handle_menu_callback(update, context)

        # Verify main menu was shown
        call_args = update.callback_query.edit_message_text.call_args
        message = call_args[0][0]
        assert "MT5 Trading Assistant Menu" in message

    @pytest.mark.asyncio
    async def test_action_routing(self):
        """
        GIVEN: User clicks action button (e.g., action_limitbuy)
        WHEN: handle_menu_callback is called
        THEN: Should show instruction to use command
        """
        from bot.menu_handler import handle_menu_callback

        update = MagicMock(spec=Update)
        update.callback_query = MagicMock(spec=CallbackQuery)
        update.callback_query.data = "action_limitbuy"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        await handle_menu_callback(update, context)

        # Verify instruction was shown
        call_args = update.callback_query.edit_message_text.call_args
        message = call_args[0][0]
        assert "/limitbuy" in message
        assert "/start" in message


class TestMenuIntegration:
    """Test menu integration with other commands"""

    @pytest.mark.asyncio
    async def test_view_orders_callback(self):
        """
        GIVEN: User clicks "View Orders" from menu
        WHEN: handle_menu_callback is called
        THEN: Should provide orders command info and return to menu
        """
        from bot.menu_handler import handle_menu_callback

        update = MagicMock(spec=Update)
        update.callback_query = MagicMock(spec=CallbackQuery)
        update.callback_query.data = "menu_view_orders"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.message = MagicMock(spec=Message)
        update.callback_query.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}

        await handle_menu_callback(update, context)

        # Should show orders command info
        update.callback_query.message.reply_text.assert_called()
        call_args = update.callback_query.message.reply_text.call_args[0][0]
        assert "/orders" in call_args
        assert "/orderdetail" in call_args
        assert "/closeorder" in call_args

    @pytest.mark.asyncio
    async def test_more_commands_shows_all(self):
        """
        GIVEN: User clicks "More Commands"
        WHEN: handle_menu_callback is called
        THEN: Should show complete command list
        """
        from bot.menu_handler import handle_menu_callback

        update = MagicMock(spec=Update)
        update.callback_query = MagicMock(spec=CallbackQuery)
        update.callback_query.data = "menu_more_commands"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.message = MagicMock(spec=Message)
        update.callback_query.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        await handle_menu_callback(update, context)

        # Should show all commands
        call_args = update.callback_query.edit_message_text.call_args[0][0]
        assert "/limitbuy" in call_args
        assert "/limitsell" in call_args
        assert "/addsetup" in call_args
        assert "/settings" in call_args
        assert "/orders" in call_args
        assert "/mt5connection" in call_args
