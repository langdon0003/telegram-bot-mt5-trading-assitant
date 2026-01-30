"""
Order Management Commands

Handles /orders, /orderdetail, /closeorder commands
for managing pending LIMIT orders on MT5.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from datetime import datetime


# Conversation states
ORDER_DETAIL_SELECT = 0
ORDER_CLOSE_CONFIRM = 1


async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /orders command - Show all pending orders.
    """
    telegram_id = update.effective_user.id

    # Get shared MT5 adapter from bot context
    adapter = context.bot_data.get('mt5_adapter')

    if not adapter:
        await update.message.reply_text(
            "❌ MT5 adapter not available\n\n"
            "Please restart the bot."
        )
        return

    # Get pending orders - adapter handles connection automatically
    pending_orders = adapter.get_pending_orders()

    if not pending_orders:
        await update.message.reply_text(
            "📋 No pending orders\n\n"
            "You don't have any LIMIT BUY or LIMIT SELL orders pending.\n\n"
            "Use /limitbuy or /limitsell to place new orders."
        )
        return

    # Build message with order list
    message = "📋 Pending Orders\n\n"

    for order in pending_orders:
        # Format time
        time_setup = datetime.fromtimestamp(order['time_setup'])
        time_str = time_setup.strftime("%Y-%m-%d %H:%M")

        # Calculate distance from current price
        distance = abs(order['price_current'] - order['price_open'])

        message += (
            f"🎫 MT5 Ticket: `{order['ticket']}`\n"
            f"📊 {order['type']}: {order['symbol']}\n"
            f"💰 Volume: {order['volume']} lots\n"
            f"📍 ET: {order['price_open']}\n"
            f"🛑 SL: {order['sl']}\n"
            f"🎯 TP: {order['tp']}\n"
            f"📈 Current: {order['price_current']} (±{distance:.1f})\n"
            f"🕐 Time: {time_str}\n"
            f"💬 Comment: {order['comment'] or 'None'}\n"
            f"\n"
        )

    message += f"Total: {len(pending_orders)} order(s)\n\n"
    message += "Use /orderdetail <ticket> to see details\n"
    message += "Use /closeorder <ticket> to close an order"

    await update.message.reply_text(message, parse_mode='Markdown')


async def orderdetail_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /orderdetail <ticket> command - Show order details.
    """
    # Check if ticket provided
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "❌ Usage: /orderdetail <ticket>\n\n"
            "Example: /orderdetail 123456789\n\n"
            "Use /orders to see all pending orders"
        )
        return

    try:
        ticket = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid ticket number\n\n"
            "Ticket must be a number.\n"
            "Example: /orderdetail 123456789"
        )
        return

    # Get shared MT5 adapter
    adapter = context.bot_data.get('mt5_adapter')

    if not adapter:
        await update.message.reply_text(
            "❌ MT5 adapter not available\n\n"
            "Please restart the bot."
        )
        return

    order_detail = adapter.get_order_detail(ticket)

    if not order_detail:
        await update.message.reply_text(
            f"❌ Order {ticket} not found\n\n"
            "Possible reasons:\n"
            "- Order already executed\n"
            "- Order already closed\n"
            "- Wrong ticket number\n\n"
            "Use /orders to see current pending orders"
        )
        return

    # Format time
    time_setup = datetime.fromtimestamp(order_detail['time_setup'])
    time_str = time_setup.strftime("%Y-%m-%d %H:%M:%S")

    # Calculate R:R
    entry = order_detail['price_open']
    sl = order_detail['sl']
    tp = order_detail['tp']

    risk = abs(entry - sl)
    reward = abs(tp - entry)
    rr_ratio = reward / risk if risk > 0 else 0

    # Calculate distance from current price
    distance = order_detail['price_current'] - entry
    distance_pct = (distance / entry) * 100 if entry > 0 else 0

    # Build detailed message
    message = f"🎫 Order Detail #{ticket}\n\n"

    message += f"📊 Symbol & Type:\n"
    message += f"  Symbol: {order_detail['symbol']}\n"
    message += f"  Type: {order_detail['type']}\n\n"

    message += f"💰 Volume & Prices:\n"
    message += f"  Volume: {order_detail['volume']} lots\n"
    message += f"  Entry: {entry}\n"
    message += f"  Stop Loss: {sl}\n"
    message += f"  Take Profit: {tp}\n\n"

    message += f"📈 Market Info:\n"
    message += f"  Current Price: {order_detail['price_current']}\n"
    message += f"  Distance: {distance:+.1f} ({distance_pct:+.2f}%)\n\n"

    message += f"📊 Risk/Reward:\n"
    message += f"  Risk: {risk:.1f} points\n"
    message += f"  Reward: {reward:.1f} points\n"
    message += f"  R:R Ratio: {rr_ratio:.2f}:1\n\n"

    message += f"🕐 Time & Info:\n"
    message += f"  Setup Time: {time_str}\n"
    message += f"  Comment: {order_detail['comment'] or 'None'}\n"
    message += f"  Magic: {order_detail['magic']}\n\n"

    # Action buttons
    keyboard = [
        [InlineKeyboardButton("🗑️ Close Order", callback_data=f"close_order_{ticket}")],
        [InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_order_{ticket}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_order_action")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message += "Choose an action:"

    await update.message.reply_text(message, reply_markup=reply_markup)


async def closeorder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /closeorder <ticket> command - Close pending order.
    """
    # Check if ticket provided
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "❌ Usage: /closeorder <ticket>\n\n"
            "Example: /closeorder 123456789\n\n"
            "Use /orders to see all pending orders"
        )
        return

    try:
        ticket = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid ticket number\n\n"
            "Ticket must be a number.\n"
            "Example: /closeorder 123456789"
        )
        return

    # Get shared MT5 adapter
    adapter = context.bot_data.get('mt5_adapter')

    if not adapter:
        await update.message.reply_text(
            "❌ MT5 adapter not available\n\n"
            "Please restart the bot."
        )
        return

    order_detail = adapter.get_order_detail(ticket)

    if not order_detail:
        await update.message.reply_text(
            f"❌ Order {ticket} not found\n\n"
            "Use /orders to see current pending orders"
        )
        return

    # Show confirmation
    message = (
        f"⚠️ Confirm Close Order\n\n"
        f"Ticket: {ticket}\n"
        f"Symbol: {order_detail['symbol']}\n"
        f"Type: {order_detail['type']}\n"
        f"Volume: {order_detail['volume']} lots\n"
        f"Entry: {order_detail['price_open']}\n\n"
        f"Are you sure you want to close this order?"
    )

    keyboard = [
        [InlineKeyboardButton("✅ Yes, Close", callback_data=f"confirm_close_order_{ticket}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_close_order")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(message, reply_markup=reply_markup)


async def handle_order_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks for order actions"""
    query = update.callback_query
    await query.answer()

    data = query.data

    # Get shared MT5 adapter
    adapter = context.bot_data.get('mt5_adapter')

    if not adapter:
        await query.edit_message_text("❌ MT5 adapter not available")
        return ConversationHandler.END

    # Cancel actions
    if data in ("cancel_order_action", "cancel_close_order"):
        await query.edit_message_text("❌ Action cancelled")
        return ConversationHandler.END

    # Refresh order detail
    if data.startswith("refresh_order_"):
        ticket = int(data.replace("refresh_order_", ""))

        order_detail = adapter.get_order_detail(ticket)

        if not order_detail:
            await query.edit_message_text(f"❌ Order {ticket} not found")
            return ConversationHandler.END

        # Rebuild message (same as orderdetail_command)
        time_setup = datetime.fromtimestamp(order_detail['time_setup'])
        time_str = time_setup.strftime("%Y-%m-%d %H:%M:%S")

        entry = order_detail['price_open']
        sl = order_detail['sl']
        tp = order_detail['tp']
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        rr_ratio = reward / risk if risk > 0 else 0
        distance = order_detail['price_current'] - entry
        distance_pct = (distance / entry) * 100 if entry > 0 else 0

        message = f"🎫 Order Detail #{ticket}\n\n"
        message += f"📊 Symbol & Type:\n"
        message += f"  Symbol: {order_detail['symbol']}\n"
        message += f"  Type: {order_detail['type']}\n\n"
        message += f"💰 Volume & Prices:\n"
        message += f"  Volume: {order_detail['volume']} lots\n"
        message += f"  Entry: {entry}\n"
        message += f"  Stop Loss: {sl}\n"
        message += f"  Take Profit: {tp}\n\n"
        message += f"📈 Market Info:\n"
        message += f"  Current Price: {order_detail['price_current']}\n"
        message += f"  Distance: {distance:+.1f} ({distance_pct:+.2f}%)\n\n"
        message += f"📊 Risk/Reward:\n"
        message += f"  Risk: {risk:.1f} points\n"
        message += f"  Reward: {reward:.1f} points\n"
        message += f"  R:R Ratio: {rr_ratio:.2f}:1\n\n"
        message += f"🕐 Time & Info:\n"
        message += f"  Setup Time: {time_str}\n"
        message += f"  Comment: {order_detail['comment'] or 'None'}\n"
        message += f"  Magic: {order_detail['magic']}\n\n"
        message += "Choose an action:"

        keyboard = [
            [InlineKeyboardButton("🗑️ Close Order", callback_data=f"close_order_{ticket}")],
            [InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_order_{ticket}")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_order_action")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(message, reply_markup=reply_markup)
        return ConversationHandler.END

    # Close order confirmation from orderdetail
    if data.startswith("close_order_"):
        ticket = int(data.replace("close_order_", ""))

        order_detail = adapter.get_order_detail(ticket)

        if not order_detail:
            await query.edit_message_text(f"❌ Order {ticket} not found")
            return ConversationHandler.END

        message = (
            f"⚠️ Confirm Close Order\n\n"
            f"Ticket: {ticket}\n"
            f"Symbol: {order_detail['symbol']}\n"
            f"Type: {order_detail['type']}\n"
            f"Volume: {order_detail['volume']} lots\n"
            f"Entry: {order_detail['price_open']}\n\n"
            f"Are you sure?"
        )

        keyboard = [
            [InlineKeyboardButton("✅ Yes, Close", callback_data=f"confirm_close_order_{ticket}")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_close_order")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(message, reply_markup=reply_markup)
        return ConversationHandler.END

    # Confirm close
    if data.startswith("confirm_close_order_"):
        ticket = int(data.replace("confirm_close_order_", ""))

        # Close the order
        result = adapter.close_pending_order(ticket)

        if result['success']:
            await query.edit_message_text(
                f"✅ Order Closed\n\n"
                f"Ticket: {ticket}\n"
                f"Status: Successfully closed\n\n"
                f"Use /orders to see remaining orders"
            )
        else:
            await query.edit_message_text(
                f"❌ Failed to Close Order\n\n"
                f"Ticket: {ticket}\n"
                f"Error: {result['error']}\n\n"
                f"Please try again or check MT5"
            )

        return ConversationHandler.END

    return ConversationHandler.END
