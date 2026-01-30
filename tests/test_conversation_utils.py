"""
Tests for Conversation Utilities

Test conversation helpers used across all command handlers.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes, ConversationHandler


class TestCancelConversation:
    """Test cancel_conversation function"""

    @pytest.mark.asyncio
    async def test_cancel_conversation_clears_user_data(self):
        """
        GIVEN: User has data stored in context.user_data
        WHEN: cancel_conversation is called
        THEN: Should clear user_data and return END
        """
        from bot.conversation_utils import cancel_conversation

        # Mock update with message
        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()

        # Mock context with user_data
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {'key1': 'value1', 'key2': 'value2'}

        result = await cancel_conversation(update, context)

        # Verify user_data was cleared
        assert len(context.user_data) == 0

        # Verify message sent
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args[0][0]
        assert "cancelled" in call_args.lower()

        # Verify returns END
        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_cancel_conversation_message_content(self):
        """
        GIVEN: User in active conversation
        WHEN: cancel_conversation is called
        THEN: Should show helpful message with /start reference
        """
        from bot.conversation_utils import cancel_conversation

        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}

        await cancel_conversation(update, context)

        call_args = update.message.reply_text.call_args[0][0]
        assert "Operation cancelled" in call_args or "cancelled" in call_args
        assert "/start" in call_args


class TestCancelAndProcessNewCommand:
    """Test cancel_and_process_new_command function"""

    @pytest.mark.asyncio
    async def test_cancel_and_process_new_command_clears_data(self):
        """
        GIVEN: User has data in context and sends new command
        WHEN: cancel_and_process_new_command is called
        THEN: Should clear user_data and return END
        """
        from bot.conversation_utils import cancel_and_process_new_command

        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.text = "/settings"
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {'old_data': 'should_be_cleared'}

        result = await cancel_and_process_new_command(update, context)

        # Verify user_data cleared
        assert len(context.user_data) == 0

        # Verify returns END
        assert result == ConversationHandler.END

    @pytest.mark.asyncio
    async def test_cancel_and_process_shows_command_being_processed(self):
        """
        GIVEN: User sends /settings while in /limitbuy conversation
        WHEN: cancel_and_process_new_command is called
        THEN: Should mention the new command in message
        """
        from bot.conversation_utils import cancel_and_process_new_command

        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.text = "/settings"
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}

        await cancel_and_process_new_command(update, context)

        call_args = update.message.reply_text.call_args[0][0]
        assert "cancelled" in call_args.lower()
        assert "/settings" in call_args

    @pytest.mark.asyncio
    async def test_cancel_and_process_returns_end(self):
        """
        GIVEN: User switches from one command to another
        WHEN: cancel_and_process_new_command is called
        THEN: Should return ConversationHandler.END
        """
        from bot.conversation_utils import cancel_and_process_new_command

        update = MagicMock(spec=Update)
        update.message = MagicMock(spec=Message)
        update.message.text = "/orders"
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {'some_key': 'some_value'}

        result = await cancel_and_process_new_command(update, context)

        # Verify returns END
        assert result == ConversationHandler.END

        # Verify user_data cleared
        assert len(context.user_data) == 0
