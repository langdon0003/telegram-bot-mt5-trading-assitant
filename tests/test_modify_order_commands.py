"""
Tests for Modify Order Commands

Test /modifyorder command for modifying pending orders.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, User, Chat, CallbackQuery, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler


class TestModifyOrderStart:
    """Test modifyorder_start function"""

    @pytest.mark.asyncio
    async def test_modifyorder_without_ticket_shows_order_list(self):
        """
        GIVEN: User sends /modifyorder without ticket number
        WHEN: modifyorder_start is called
        THEN: Should show list of pending orders
        """
        from bot.modify_order_commands import modifyorder_start, MODIFY_SELECT_ORDER

        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 12345
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = []  # No arguments

        # Mock bot_data
        mt5_adapter = MagicMock()
        mt5_adapter.connected = True
        mt5_adapter.get_pending_orders.return_value = [
            {
                'ticket': 111,
                'symbol': 'XAUUSD',
                'type': 'BUY LIMIT',
                'price_open': 2050.50,
                'volume': 0.01
            }
        ]
        context.bot_data = {'mt5_adapter': mt5_adapter}

        with patch('database.db_manager.DatabaseManager') as MockDB:
            mock_db = MockDB.return_value
            mock_db.get_user_by_telegram_id.return_value = {'id': 1}

            result = await modifyorder_start(update, context)

            # Verify order list shown
            update.message.reply_text.assert_called_once()
            call_args = update.message.reply_text.call_args

            # Check message
            assert "Modify Pending Order" in call_args[0][0]
            assert "Select an order" in call_args[0][0]

            # Check keyboard
            reply_markup = call_args[1]['reply_markup']
            assert reply_markup is not None
            assert len(reply_markup.inline_keyboard) > 0

            # Verify returns MODIFY_SELECT_ORDER state
            assert result == MODIFY_SELECT_ORDER

    @pytest.mark.asyncio
    async def test_modifyorder_with_ticket_shows_modification_menu(self):
        """
        GIVEN: User sends /modifyorder 12345
        WHEN: modifyorder_start is called
        THEN: Should show modification menu for that order
        """
        from bot.modify_order_commands import modifyorder_start, MODIFY_SELECT_FIELD

        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 12345
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = ['111']  # Ticket number provided
        context.user_data = {}

        # Mock MT5 adapter
        mt5_adapter = MagicMock()
        mt5_adapter.connected = True
        mt5_adapter.get_order_detail.return_value = {
            'ticket': 111,
            'symbol': 'XAUUSD',
            'type': 'BUY LIMIT',
            'price_open': 2050.50,
            'sl': 2048.00,
            'tp': 2055.00
        }
        context.bot_data = {'mt5_adapter': mt5_adapter}

        with patch('database.db_manager.DatabaseManager') as MockDB:
            mock_db = MockDB.return_value
            mock_db.get_user_by_telegram_id.return_value = {'id': 1}

            result = await modifyorder_start(update, context)

            # Verify modification menu shown
            update.message.reply_text.assert_called_once()
            call_args = update.message.reply_text.call_args

            # Check message contains order details
            message_text = call_args[0][0]
            assert "Modify Order" in message_text
            assert "111" in message_text  # Ticket number
            assert "XAUUSD" in message_text

            # Check keyboard has modification options
            reply_markup = call_args[1]['reply_markup']
            assert reply_markup is not None

            # Verify ticket stored in context
            assert context.user_data['modify_ticket'] == 111

            # Verify returns MODIFY_SELECT_FIELD state
            assert result == MODIFY_SELECT_FIELD

    @pytest.mark.asyncio
    async def test_modifyorder_with_invalid_ticket(self):
        """
        GIVEN: User sends /modifyorder with invalid ticket
        WHEN: modifyorder_start is called
        THEN: Should show error and return END
        """
        from bot.modify_order_commands import modifyorder_start

        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 12345
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = ['abc']  # Invalid ticket
        context.user_data = {}

        context.bot_data = {'mt5_adapter': MagicMock(connected=True)}

        with patch('database.db_manager.DatabaseManager') as MockDB:
            mock_db = MockDB.return_value
            mock_db.get_user_by_telegram_id.return_value = {'id': 1}

            result = await modifyorder_start(update, context)

            # Verify error message
            update.message.reply_text.assert_called_once()
            call_args = update.message.reply_text.call_args[0][0]
            assert "Invalid ticket" in call_args

            # Verify returns END
            assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_modifyorder_no_mt5_connection(self):
        """
        GIVEN: MT5 is not connected
        WHEN: modifyorder_start is called
        THEN: Should show error and return END
        """
        from bot.modify_order_commands import modifyorder_start

        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 12345
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = []

        # MT5 not connected
        mt5_adapter = MagicMock()
        mt5_adapter.connected = False
        context.bot_data = {'mt5_adapter': mt5_adapter}

        with patch('database.db_manager.DatabaseManager') as MockDB:
            mock_db = MockDB.return_value
            mock_db.get_user_by_telegram_id.return_value = {'id': 1}

            result = await modifyorder_start(update, context)

            # Verify error message about MT5
            update.message.reply_text.assert_called_once()
            call_args = update.message.reply_text.call_args[0][0]
            assert "MT5" in call_args
            assert "not connected" in call_args.lower()

            # Verify returns END
            assert result == ConversationHandler.END


class TestReceiveModificationValues:
    """Test receiving new values for modification"""

    @pytest.mark.asyncio
    async def test_receive_entry_valid_number(self):
        """
        GIVEN: User enters valid entry price
        WHEN: receive_entry is called
        THEN: Should store value and proceed
        """
        from bot.modify_order_commands import receive_entry

        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.text = "2051.50"
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {
            'modify_field': 'entry',
            'modify_order': {'sl': 2048.00}
        }

        result = await receive_entry(update, context)

        # Verify value stored
        assert context.user_data['new_entry'] == 2051.50

        # Should proceed to confirmation
        assert result is not None

    @pytest.mark.asyncio
    async def test_receive_entry_invalid_number(self):
        """
        GIVEN: User enters invalid price
        WHEN: receive_entry is called
        THEN: Should ask again
        """
        from bot.modify_order_commands import receive_entry, MODIFY_ENTRY

        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.text = "invalid"
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {'modify_field': 'entry'}

        result = await receive_entry(update, context)

        # Verify error message
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args[0][0]
        assert "Invalid" in call_args or "number" in call_args.lower()

        # Verify stays in same state
        assert result == MODIFY_ENTRY


class TestExecuteModification:
    """Test execute_modification function"""

    @pytest.mark.asyncio
    async def test_execute_modification_success(self):
        """
        GIVEN: User confirmed modification
        WHEN: execute_modification is called
        THEN: Should call MT5 and show success
        """
        from bot.modify_order_commands import execute_modification

        query = MagicMock(spec=CallbackQuery)
        query.data = "modify_confirm_yes"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        query.message = MagicMock(spec=Message)
        query.message.reply_text = AsyncMock()

        update = MagicMock(spec=Update)
        update.callback_query = query

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {
            'modify_ticket': 111,
            'modify_field': 'entry',
            'modify_order': {'symbol': 'XAUUSD'},
            'new_entry': 2051.50
        }

        # Mock MT5 adapter
        mt5_adapter = MagicMock()
        mt5_adapter.modify_order.return_value = {
            'success': True,
            'new_price': 2051.50,
            'new_sl': 2048.00,
            'new_tp': 2055.00
        }
        context.bot_data = {'mt5_adapter': mt5_adapter}

        result = await execute_modification(update, context)

        # Verify MT5 called
        mt5_adapter.modify_order.assert_called_once_with(
            ticket=111,
            price=2051.50,
            sl=None,
            tp=None
        )

        # Verify success message shown
        query.message.reply_text.assert_called_once()
        call_args = query.message.reply_text.call_args[0][0]
        assert "Modified Successfully" in call_args or "success" in call_args.lower()

        # Verify context cleared
        assert len(context.user_data) == 0

        # Verify returns END
        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_execute_modification_failure(self):
        """
        GIVEN: MT5 modification fails
        WHEN: execute_modification is called
        THEN: Should show error message
        """
        from bot.modify_order_commands import execute_modification

        query = MagicMock(spec=CallbackQuery)
        query.data = "modify_confirm_yes"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        query.message = MagicMock(spec=Message)
        query.message.reply_text = AsyncMock()

        update = MagicMock(spec=Update)
        update.callback_query = query

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {
            'modify_ticket': 111,
            'modify_field': 'entry',
            'modify_order': {'symbol': 'XAUUSD'},
            'new_entry': 2051.50
        }

        # Mock MT5 failure
        mt5_adapter = MagicMock()
        mt5_adapter.modify_order.return_value = {
            'success': False,
            'error': 'Invalid price'
        }
        context.bot_data = {'mt5_adapter': mt5_adapter}

        result = await execute_modification(update, context)

        # Verify error message shown
        query.message.reply_text.assert_called_once()
        call_args = query.message.reply_text.call_args[0][0]
        assert "Failed" in call_args or "error" in call_args.lower()
        assert "Invalid price" in call_args

        # Verify returns END
        assert result == ConversationHandler.END
