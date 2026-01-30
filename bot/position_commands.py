"""
Position Commands

Handles /positions command for viewing and closing open positions.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


async def positions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show all open positions with close buttons.

    Usage: /positions
    """
    telegram_id = update.effective_user.id
    db = DatabaseManager()
    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("Please use /start first")
        return

    # Get MT5 adapter from context
    mt5_adapter = context.bot_data.get('mt5_adapter')
    if not mt5_adapter or not mt5_adapter.connected:
        await update.message.reply_text(
            "❌ MT5 not connected\n\n"
            "Use /mt5connection to check status"
        )
        return

    # Get open positions
    positions = mt5_adapter.get_open_positions()

    if not positions:
        await update.message.reply_text(
            "📭 *No Open Positions*\n\n"
            "You don't have any active trades right now.\n\n"
            "Use /limitbuy or /limitsell to place new orders.",
            parse_mode='Markdown'
        )
        return

    # Calculate total profit
    total_profit = sum(pos['profit'] for pos in positions)

    # Build message header
    message = (
        f"💼 *Open Positions* ({len(positions)})\n\n"
        f"Total P&L: {total_profit:+.2f} USD\n"
        f"━━━━━━━\n\n"
    )

    # Create keyboard with close buttons
    keyboard = []

    for position in positions:
        # Position info
        profit_emoji = "🟢" if position['profit'] >= 0 else "🔴"
        profit_str = f"{position['profit']:+.2f}"

        pos_text = (
            f"{profit_emoji} *#{position['ticket']}* - {position['symbol']}\n"
            f"Type: {position['type']}\n"
            f"Volume: {position['volume']}\n"
            f"Entry: {position['price_open']}\n"
            f"Current: {position['price_current']}\n"
            f"P&L: {profit_str} USD\n"
        )

        if position['sl'] > 0:
            pos_text += f"SL: {position['sl']}\n"
        if position['tp'] > 0:
            pos_text += f"TP: {position['tp']}\n"

        message += pos_text + "\n"

        # Add close button for this position
        button_text = f"❌ Close #{position['ticket']}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"close_pos_{position['ticket']}")])

    # Add refresh button
    keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="refresh_positions")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def handle_position_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle position-related callback queries"""
    query = update.callback_query
    await query.answer()

    data = query.data

    # Get MT5 adapter
    mt5_adapter = context.bot_data.get('mt5_adapter')

    if data == "refresh_positions":
        # Refresh position list
        positions = mt5_adapter.get_open_positions()

        if not positions:
            await query.edit_message_text(
                "📭 *No Open Positions*\n\n"
                "All positions have been closed.",
                parse_mode='Markdown'
            )
            return

        # Rebuild message
        total_profit = sum(pos['profit'] for pos in positions)
        message = (
            f"💼 *Open Positions* ({len(positions)})\n\n"
            f"Total P&L: {total_profit:+.2f} USD\n"
            f"━━━━━━━\n\n"
        )

        keyboard = []
        for position in positions:
            profit_emoji = "🟢" if position['profit'] >= 0 else "🔴"
            profit_str = f"{position['profit']:+.2f}"

            pos_text = (
                f"{profit_emoji} *#{position['ticket']}* - {position['symbol']}\n"
                f"Type: {position['type']}\n"
                f"Volume: {position['volume']}\n"
                f"Entry: {position['price_open']}\n"
                f"Current: {position['price_current']}\n"
                f"P&L: {profit_str} USD\n"
            )

            if position['sl'] > 0:
                pos_text += f"SL: {position['sl']}\n"
            if position['tp'] > 0:
                pos_text += f"TP: {position['tp']}\n"

            message += pos_text + "\n"

            button_text = f"❌ Close #{position['ticket']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"close_pos_{position['ticket']}")])

        keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="refresh_positions")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    elif data.startswith("close_pos_"):
        # Extract ticket number
        ticket = int(data.replace("close_pos_", ""))

        # Get position details
        position = mt5_adapter.get_position_detail(ticket)

        if not position:
            await query.edit_message_text(
                f"❌ Position #{ticket} not found or already closed"
            )
            return

        # Show confirmation
        profit_emoji = "🟢" if position['profit'] >= 0 else "🔴"
        profit_str = f"{position['profit']:+.2f}"

        confirm_message = (
            f"⚠️ *Confirm Close Position*\n\n"
            f"Ticket: #{ticket}\n"
            f"Symbol: {position['symbol']}\n"
            f"Type: {position['type']}\n"
            f"Volume: {position['volume']}\n"
            f"Entry: {position['price_open']}\n"
            f"Current: {position['price_current']}\n"
            f"Current P&L: {profit_emoji} {profit_str} USD\n\n"
            f"Are you sure you want to close this position?"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Yes, Close", callback_data=f"confirm_close_pos_{ticket}"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_close_pos")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            confirm_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    elif data.startswith("confirm_close_pos_"):
        # Extract ticket number
        ticket = int(data.replace("confirm_close_pos_", ""))

        await query.edit_message_text(
            f"⏳ Closing position #{ticket}..."
        )

        # Close position
        result = mt5_adapter.close_position(ticket)

        if result['success']:
            profit_emoji = "🟢" if result['profit'] >= 0 else "🔴"
            profit_str = f"{result['profit']:+.2f}"

            success_message = (
                f"✅ *Position Closed*\n\n"
                f"Ticket: #{ticket}\n"
                f"Close Price: {result['close_price']}\n"
                f"Final P&L: {profit_emoji} {profit_str} USD\n\n"
                f"Use /positions to view remaining positions"
            )

            await query.message.reply_text(success_message, parse_mode='Markdown')
        else:
            await query.message.reply_text(
                f"❌ *Failed to Close Position*\n\n"
                f"Ticket: #{ticket}\n"
                f"Error: {result['error']}",
                parse_mode='Markdown'
            )

    elif data == "cancel_close_pos":
        await query.edit_message_text(
            "❌ Close cancelled\n\n"
            "Use /positions to view positions"
        )
