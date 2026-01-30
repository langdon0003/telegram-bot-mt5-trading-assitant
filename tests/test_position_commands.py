"""
Tests for Position Commands

Test /positions command for viewing and closing open positions.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, User, Chat, CallbackQuery
from telegram.ext import ContextTypes


class TestPositionsCommand:
    """Test positions_command function"""

    @pytest.mark.asyncio
    async def test_positions_shows_open_positions(self):
        """
        GIVEN: User has 2 open positions
        WHEN: positions_command is called
        THEN: Should display both positions with close buttons
        """
        from bot.position_commands import positions_command

        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 12345
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        # Mock MT5 adapter with 2 positions
        mt5_adapter = MagicMock()
        mt5_adapter.connected = True
        mt5_adapter.get_open_positions.return_value = [
            {
                'ticket': 111,
                'symbol': 'XAUUSD',
                'type': 'BUY',
                'volume': 0.01,
                'price_open': 2050.50,
                'price_current': 2055.25,
                'sl': 2048.00,
                'tp': 2060.00,
                'profit': 47.50,
                'swap': 0.0
            },
            {
                'ticket': 222,
                'symbol': 'EURUSD',
                'type': 'SELL',
                'volume': 0.1,
                'price_open': 1.0850,
                'price_current': 1.0845,
                'sl': 1.0860,
                'tp': 1.0840,
                'profit': 50.00,
                'swap': -2.50
            }
        ]
        context.bot_data = {'mt5_adapter': mt5_adapter}

        with patch('database.db_manager.DatabaseManager') as MockDB:
            mock_db = MockDB.return_value
            mock_db.get_user_by_telegram_id.return_value = {'id': 1}

            await positions_command(update, context)

            # Verify positions displayed
            update.message.reply_text.assert_called_once()
            call_args = update.message.reply_text.call_args

            # Check message content
            message_text = call_args[0][0]
            assert "Open Positions" in message_text
            assert "(2)" in message_text  # 2 positions
            assert "111" in message_text  # Ticket 1
            assert "222" in message_text  # Ticket 2
            assert "XAUUSD" in message_text
            assert "EURUSD" in message_text
            assert "47.50" in message_text  # Profit 1
            assert "50.00" in message_text  # Profit 2

            # Check total P&L
            assert "97.50" in message_text  # Total profit

            # Check keyboard
            reply_markup = call_args[1]['reply_markup']
            assert reply_markup is not None
            keyboard = reply_markup.inline_keyboard

            # Should have 2 close buttons + 1 refresh button
            assert len(keyboard) == 3

            # Check close buttons
            assert "Close #111" in keyboard[0][0].text
            assert "Close #222" in keyboard[1][0].text
            assert "Refresh" in keyboard[2][0].text

    @pytest.mark.asyncio
    async def test_positions_no_positions(self):
        """
        GIVEN: User has no open positions
        WHEN: positions_command is called
        THEN: Should show empty message
        """
        from bot.position_commands import positions_command

        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 12345
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        # Mock MT5 adapter with no positions
        mt5_adapter = MagicMock()
        mt5_adapter.connected = True
        mt5_adapter.get_open_positions.return_value = []
        context.bot_data = {'mt5_adapter': mt5_adapter}

        with patch('database.db_manager.DatabaseManager') as MockDB:
            mock_db = MockDB.return_value
            mock_db.get_user_by_telegram_id.return_value = {'id': 1}

            await positions_command(update, context)

            # Verify empty message
            update.message.reply_text.assert_called_once()
            call_args = update.message.reply_text.call_args[0][0]
            assert "No Open Positions" in call_args

    @pytest.mark.asyncio
    async def test_positions_mt5_not_connected(self):
        """
        GIVEN: MT5 is not connected
        WHEN: positions_command is called
        THEN: Should show error message
        """
        from bot.position_commands import positions_command

        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 12345
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        # MT5 not connected
        mt5_adapter = MagicMock()
        mt5_adapter.connected = False
        context.bot_data = {'mt5_adapter': mt5_adapter}

        with patch('database.db_manager.DatabaseManager') as MockDB:
            mock_db = MockDB.return_value
            mock_db.get_user_by_telegram_id.return_value = {'id': 1}

            await positions_command(update, context)

            # Verify error message
            update.message.reply_text.assert_called_once()
            call_args = update.message.reply_text.call_args[0][0]
            assert "MT5" in call_args
            assert "not connected" in call_args.lower()

    @pytest.mark.asyncio
    async def test_positions_shows_profit_loss_colors(self):
        """
        GIVEN: User has profitable and losing positions
        WHEN: positions_command is called
        THEN: Should show green for profit, red for loss
        """
        from bot.position_commands import positions_command

        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 12345
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        # Mock positions with profit and loss
        mt5_adapter = MagicMock()
        mt5_adapter.connected = True
        mt5_adapter.get_open_positions.return_value = [
            {
                'ticket': 111,
                'symbol': 'XAUUSD',
                'type': 'BUY',
                'volume': 0.01,
                'price_open': 2050.50,
                'price_current': 2055.25,
                'sl': 2048.00,
                'tp': 2060.00,
                'profit': 47.50,  # Positive
                'swap': 0.0
            },
            {
                'ticket': 222,
                'symbol': 'EURUSD',
                'type': 'SELL',
                'volume': 0.1,
                'price_open': 1.0850,
                'price_current': 1.0860,
                'sl': 1.0870,
                'tp': 1.0840,
                'profit': -100.00,  # Negative
                'swap': 0.0
            }
        ]
        context.bot_data = {'mt5_adapter': mt5_adapter}

        with patch('database.db_manager.DatabaseManager') as MockDB:
            mock_db = MockDB.return_value
            mock_db.get_user_by_telegram_id.return_value = {'id': 1}

            await positions_command(update, context)

            call_args = update.message.reply_text.call_args[0][0]

            # Check for emoji indicators
            assert "🟢" in call_args  # Green for profit
            assert "🔴" in call_args  # Red for loss


class TestHandlePositionAction:
    """Test handle_position_action callback handler"""

    @pytest.mark.asyncio
    async def test_refresh_positions_updates_display(self):
        """
        GIVEN: User clicks Refresh button
        WHEN: handle_position_action is called
        THEN: Should update position display with fresh data
        """
        from bot.position_commands import handle_position_action

        query = MagicMock(spec=CallbackQuery)
        query.data = "refresh_positions"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()

        update = MagicMock(spec=Update)
        update.callback_query = query

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        # Mock MT5 adapter
        mt5_adapter = MagicMock()
        mt5_adapter.get_open_positions.return_value = [
            {
                'ticket': 111,
                'symbol': 'XAUUSD',
                'type': 'BUY',
                'volume': 0.01,
                'price_open': 2050.50,
                'price_current': 2056.00,  # Updated price
                'sl': 2048.00,
                'tp': 2060.00,
                'profit': 55.00,  # Updated profit
                'swap': 0.0
            }
        ]
        context.bot_data = {'mt5_adapter': mt5_adapter}

        await handle_position_action(update, context)

        # Verify callback answered
        query.answer.assert_called_once()

        # Verify message edited with new data
        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args[0][0]

        # Check updated values
        assert "2056.00" in call_args  # New current price
        assert "55.00" in call_args  # New profit

    @pytest.mark.asyncio
    async def test_close_position_shows_confirmation(self):
        """
        GIVEN: User clicks Close button
        WHEN: handle_position_action is called
        THEN: Should show confirmation dialog
        """
        from bot.position_commands import handle_position_action

        query = MagicMock(spec=CallbackQuery)
        query.data = "close_pos_111"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()

        update = MagicMock(spec=Update)
        update.callback_query = query

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        # Mock MT5 adapter
        mt5_adapter = MagicMock()
        mt5_adapter.get_position_detail.return_value = {
            'ticket': 111,
            'symbol': 'XAUUSD',
            'type': 'BUY',
            'volume': 0.01,
            'price_open': 2050.50,
            'price_current': 2055.25,
            'profit': 47.50
        }
        context.bot_data = {'mt5_adapter': mt5_adapter}

        await handle_position_action(update, context)

        # Verify confirmation shown
        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args

        message_text = call_args[0][0]
        assert "Confirm Close Position" in message_text
        assert "111" in message_text
        assert "47.50" in message_text

        # Check keyboard has Yes/Cancel
        reply_markup = call_args[1]['reply_markup']
        keyboard = reply_markup.inline_keyboard
        assert len(keyboard) == 1
        assert len(keyboard[0]) == 2  # Yes and Cancel buttons

    @pytest.mark.asyncio
    async def test_confirm_close_position_success(self):
        """
        GIVEN: User confirms close position
        WHEN: handle_position_action is called
        THEN: Should close position and show success
        """
        from bot.position_commands import handle_position_action

        query = MagicMock(spec=CallbackQuery)
        query.data = "confirm_close_pos_111"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        query.message = MagicMock(spec=Message)
        query.message.reply_text = AsyncMock()

        update = MagicMock(spec=Update)
        update.callback_query = query

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        # Mock MT5 adapter
        mt5_adapter = MagicMock()
        mt5_adapter.close_position.return_value = {
            'success': True,
            'close_price': 2055.30,
            'profit': 48.00
        }
        context.bot_data = {'mt5_adapter': mt5_adapter}

        await handle_position_action(update, context)

        # Verify position closed
        mt5_adapter.close_position.assert_called_once_with(111)

        # Verify success message
        query.message.reply_text.assert_called_once()
        call_args = query.message.reply_text.call_args[0][0]
        assert "Position Closed" in call_args
        assert "2055.30" in call_args  # Close price
        assert "48.00" in call_args  # Final profit

    @pytest.mark.asyncio
    async def test_confirm_close_position_failure(self):
        """
        GIVEN: Position close fails
        WHEN: handle_position_action is called
        THEN: Should show error message
        """
        from bot.position_commands import handle_position_action

        query = MagicMock(spec=CallbackQuery)
        query.data = "confirm_close_pos_111"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        query.message = MagicMock(spec=Message)
        query.message.reply_text = AsyncMock()

        update = MagicMock(spec=Update)
        update.callback_query = query

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        # Mock MT5 failure
        mt5_adapter = MagicMock()
        mt5_adapter.close_position.return_value = {
            'success': False,
            'error': 'Market closed'
        }
        context.bot_data = {'mt5_adapter': mt5_adapter}

        await handle_position_action(update, context)

        # Verify error message
        query.message.reply_text.assert_called_once()
        call_args = query.message.reply_text.call_args[0][0]
        assert "Failed" in call_args
        assert "Market closed" in call_args

    @pytest.mark.asyncio
    async def test_cancel_close_position(self):
        """
        GIVEN: User clicks Cancel on close confirmation
        WHEN: handle_position_action is called
        THEN: Should cancel and show message
        """
        from bot.position_commands import handle_position_action

        query = MagicMock(spec=CallbackQuery)
        query.data = "cancel_close_pos"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()

        update = MagicMock(spec=Update)
        update.callback_query = query

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.bot_data = {'mt5_adapter': MagicMock()}

        await handle_position_action(update, context)

        # Verify cancel message
        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args[0][0]
        assert "cancelled" in call_args.lower()
