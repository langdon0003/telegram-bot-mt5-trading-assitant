"""
Conversation Handler Utilities

Shared utilities for managing conversation states across the bot.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

logger = logging.getLogger(__name__)


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Cancel the current conversation.

    Used when user explicitly sends /cancel command.
    """
    await update.message.reply_text(
        "❌ Operation cancelled.\n\n"
        "Use /start to see available commands."
    )
    # Clear any stored context data
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_and_process_new_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Cancel current conversation when user sends a different command.

    This handler is used as a fallback to automatically end conversations
    when the user switches to a different command without completing the current one.

    The new command will be processed by its respective handler after this returns END.
    """
    command = update.message.text
    logger.info(f"User switched from conversation to new command: {command}")

    await update.message.reply_text(
        f"⚠️ Previous operation cancelled.\n"
        f"Processing {command} instead..."
    )

    # Clear any stored context data
    context.user_data.clear()

    # Return END to allow the new command to be processed by other handlers
    return ConversationHandler.END
