"""
Modify Order Command

Handles /modifyorder command for modifying pending orders (Entry, SL, TP).
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from bot.conversation_utils import cancel_conversation, cancel_and_process_new_command
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

# Conversation states
MODIFY_SELECT_ORDER, MODIFY_SELECT_FIELD, MODIFY_ENTRY, MODIFY_SL, MODIFY_TP, MODIFY_CONFIRM = range(6)


async def modifyorder_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start /modifyorder conversation.

    Can be called as:
    - /modifyorder          -> Show list of pending orders
    - /modifyorder <ticket> -> Directly modify specific order
    """
    telegram_id = update.effective_user.id
    db = DatabaseManager()
    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("Please use /start first")
        return ConversationHandler.END

    # Get MT5 adapter from context
    mt5_adapter = context.bot_data.get('mt5_adapter')
    if not mt5_adapter or not mt5_adapter.connected:
        await update.message.reply_text(
            "❌ MT5 not connected\n\n"
            "Use /mt5connection to check status"
        )
        return ConversationHandler.END

    # Check if ticket number provided
    args = context.args
    if args and len(args) > 0:
        try:
            ticket = int(args[0])
            # Get order details
            order = mt5_adapter.get_order_detail(ticket)

            if not order:
                await update.message.reply_text(f"❌ Order {ticket} not found")
                return ConversationHandler.END

            # Store ticket in context and show modification menu
            context.user_data['modify_ticket'] = ticket
            context.user_data['modify_order'] = order
            return await show_modification_menu(update, context, order)

        except ValueError:
            await update.message.reply_text("❌ Invalid ticket number")
            return ConversationHandler.END

    # No ticket provided - show list of pending orders
    pending_orders = mt5_adapter.get_pending_orders()

    if not pending_orders:
        await update.message.reply_text(
            "📭 No pending orders found\n\n"
            "Use /limitbuy or /limitsell to create orders"
        )
        return ConversationHandler.END

    # Create keyboard with pending orders
    keyboard = []
    for order in pending_orders[:10]:  # Limit to 10 orders
        button_text = f"#{order['ticket']} - {order['symbol']} {order['type']} @ {order['price_open']}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"modify_order_{order['ticket']}")])

    keyboard.append([InlineKeyboardButton("« Cancel", callback_data="modify_cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🔧 *Modify Pending Order*\n\n"
        "Select an order to modify:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    return MODIFY_SELECT_ORDER


async def select_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User selected an order to modify"""
    query = update.callback_query
    await query.answer()

    if query.data == "modify_cancel":
        await query.edit_message_text("❌ Modification cancelled")
        return ConversationHandler.END

    # Extract ticket number
    ticket = int(query.data.replace("modify_order_", ""))

    # Get order details
    mt5_adapter = context.bot_data.get('mt5_adapter')
    order = mt5_adapter.get_order_detail(ticket)

    if not order:
        await query.edit_message_text(f"❌ Order {ticket} not found or already filled")
        return ConversationHandler.END

    # Store in context
    context.user_data['modify_ticket'] = ticket
    context.user_data['modify_order'] = order

    return await show_modification_menu(update, context, order)


async def show_modification_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, order: dict):
    """Show menu to select which field to modify"""

    message_text = (
        f"🔧 *Modify Order #{order['ticket']}*\n\n"
        f"Symbol: {order['symbol']}\n"
        f"Type: {order['type']}\n"
        f"Current Entry: {order['price_open']}\n"
        f"Current SL: {order['sl']}\n"
        f"Current TP: {order['tp']}\n\n"
        f"What would you like to modify?"
    )

    keyboard = [
        [InlineKeyboardButton("📍 Entry Price", callback_data="modify_field_entry")],
        [InlineKeyboardButton("🛑 Stop Loss", callback_data="modify_field_sl")],
        [InlineKeyboardButton("🎯 Take Profit", callback_data="modify_field_tp")],
        [InlineKeyboardButton("✏️ Modify All", callback_data="modify_field_all")],
        [InlineKeyboardButton("« Cancel", callback_data="modify_cancel")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Edit message if from callback, otherwise send new
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    return MODIFY_SELECT_FIELD


async def select_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User selected which field to modify"""
    query = update.callback_query
    await query.answer()

    if query.data == "modify_cancel":
        await query.edit_message_text("❌ Modification cancelled")
        context.user_data.clear()
        return ConversationHandler.END

    field = query.data.replace("modify_field_", "")
    context.user_data['modify_field'] = field

    order = context.user_data['modify_order']

    if field == "all":
        # Modify all fields - ask for entry first
        await query.edit_message_text(
            f"🔧 *Modify All Fields*\n\n"
            f"Current Entry: {order['price_open']}\n\n"
            f"Enter new *Entry Price*:",
            parse_mode='Markdown'
        )
        context.user_data['modify_step'] = 'entry'
        return MODIFY_ENTRY

    elif field == "entry":
        await query.edit_message_text(
            f"📍 *Modify Entry Price*\n\n"
            f"Current: {order['price_open']}\n\n"
            f"Enter new entry price:",
            parse_mode='Markdown'
        )
        return MODIFY_ENTRY

    elif field == "sl":
        await query.edit_message_text(
            f"🛑 *Modify Stop Loss*\n\n"
            f"Current: {order['sl']}\n\n"
            f"Enter new stop loss:",
            parse_mode='Markdown'
        )
        return MODIFY_SL

    elif field == "tp":
        await query.edit_message_text(
            f"🎯 *Modify Take Profit*\n\n"
            f"Current: {order['tp']}\n\n"
            f"Enter new take profit:",
            parse_mode='Markdown'
        )
        return MODIFY_TP


async def receive_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive new entry price"""
    try:
        new_entry = float(update.message.text)
        context.user_data['new_entry'] = new_entry

        # If modifying all, ask for SL next
        if context.user_data.get('modify_field') == 'all':
            order = context.user_data['modify_order']
            await update.message.reply_text(
                f"✅ Entry: {new_entry}\n\n"
                f"Current SL: {order['sl']}\n\n"
                f"Enter new *Stop Loss*:",
                parse_mode='Markdown'
            )
            context.user_data['modify_step'] = 'sl'
            return MODIFY_SL

        # Single field modification - confirm
        return await show_confirmation(update, context)

    except ValueError:
        await update.message.reply_text("❌ Invalid price. Please enter a number:")
        return MODIFY_ENTRY


async def receive_sl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive new stop loss"""
    try:
        new_sl = float(update.message.text)
        context.user_data['new_sl'] = new_sl

        # If modifying all, ask for TP next
        if context.user_data.get('modify_field') == 'all':
            order = context.user_data['modify_order']
            await update.message.reply_text(
                f"✅ Entry: {context.user_data['new_entry']}\n"
                f"✅ SL: {new_sl}\n\n"
                f"Current TP: {order['tp']}\n\n"
                f"Enter new *Take Profit*:",
                parse_mode='Markdown'
            )
            context.user_data['modify_step'] = 'tp'
            return MODIFY_TP

        # Single field modification - confirm
        return await show_confirmation(update, context)

    except ValueError:
        await update.message.reply_text("❌ Invalid price. Please enter a number:")
        return MODIFY_SL


async def receive_tp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive new take profit"""
    try:
        new_tp = float(update.message.text)
        context.user_data['new_tp'] = new_tp

        # Show confirmation
        return await show_confirmation(update, context)

    except ValueError:
        await update.message.reply_text("❌ Invalid price. Please enter a number:")
        return MODIFY_TP


async def show_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirmation before modifying order"""
    order = context.user_data['modify_order']
    ticket = context.user_data['modify_ticket']
    field = context.user_data['modify_field']

    # Build summary
    summary = f"🔧 *Confirm Modification*\n\n"
    summary += f"Order: #{ticket}\n"
    summary += f"Symbol: {order['symbol']}\n"
    summary += f"Type: {order['type']}\n\n"

    summary += "*Changes:*\n"

    if field == 'all' or field == 'entry':
        new_entry = context.user_data.get('new_entry')
        if new_entry:
            summary += f"Entry: {order['price_open']} → {new_entry}\n"

    if field == 'all' or field == 'sl':
        new_sl = context.user_data.get('new_sl')
        if new_sl:
            summary += f"SL: {order['sl']} → {new_sl}\n"

    if field == 'all' or field == 'tp':
        new_tp = context.user_data.get('new_tp')
        if new_tp:
            summary += f"TP: {order['tp']} → {new_tp}\n"

    summary += "\nProceed with modification?"

    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data="modify_confirm_yes"),
            InlineKeyboardButton("❌ Cancel", callback_data="modify_confirm_no")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        summary,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    return MODIFY_CONFIRM


async def execute_modification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the order modification"""
    query = update.callback_query
    await query.answer()

    if query.data == "modify_confirm_no":
        await query.edit_message_text("❌ Modification cancelled")
        context.user_data.clear()
        return ConversationHandler.END

    # Get stored data
    ticket = context.user_data['modify_ticket']
    field = context.user_data['modify_field']
    order = context.user_data['modify_order']

    # Prepare modification parameters
    new_price = context.user_data.get('new_entry')
    new_sl = context.user_data.get('new_sl')
    new_tp = context.user_data.get('new_tp')

    # Get MT5 adapter
    mt5_adapter = context.bot_data.get('mt5_adapter')

    await query.edit_message_text("⏳ Modifying order...")

    # Execute modification
    result = mt5_adapter.modify_order(
        ticket=ticket,
        price=new_price,
        sl=new_sl,
        tp=new_tp
    )

    if result['success']:
        success_msg = (
            f"✅ *Order Modified Successfully*\n\n"
            f"Order: #{ticket}\n"
            f"Symbol: {order['symbol']}\n\n"
        )

        if new_price:
            success_msg += f"Entry: {result['new_price']}\n"
        if new_sl:
            success_msg += f"SL: {result['new_sl']}\n"
        if new_tp:
            success_msg += f"TP: {result['new_tp']}\n"

        await query.message.reply_text(success_msg, parse_mode='Markdown')
    else:
        await query.message.reply_text(
            f"❌ *Modification Failed*\n\n"
            f"Error: {result['error']}",
            parse_mode='Markdown'
        )

    context.user_data.clear()
    return ConversationHandler.END


def get_modifyorder_handler():
    """Get the ConversationHandler for /modifyorder command"""
    return ConversationHandler(
        entry_points=[CommandHandler("modifyorder", modifyorder_start)],
        states={
            MODIFY_SELECT_ORDER: [
                CallbackQueryHandler(select_order, pattern="^modify_order_|modify_cancel$")
            ],
            MODIFY_SELECT_FIELD: [
                CallbackQueryHandler(select_field, pattern="^modify_field_|modify_cancel$")
            ],
            MODIFY_ENTRY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_entry)
            ],
            MODIFY_SL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_sl)
            ],
            MODIFY_TP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_tp)
            ],
            MODIFY_CONFIRM: [
                CallbackQueryHandler(execute_modification, pattern="^modify_confirm_(yes|no)$")
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            MessageHandler(filters.COMMAND, cancel_and_process_new_command)
        ],
        per_message=False
    )
