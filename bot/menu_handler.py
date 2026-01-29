"""
Main Menu Handler

Handles the main menu shown after /start command.
Provides quick access to common trading actions.
"""

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
from telegram.ext import ContextTypes, ConversationHandler


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Display main menu with quick actions and trading options.

    Called by /start command or "Back to Menu" buttons.
    """
    # Use either message or callback query
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        send_func = query.edit_message_text
    else:
        send_func = update.message.reply_text

    keyboard = [
        [InlineKeyboardButton("📊 Place Order", callback_data="menu_place_order")],
        [
            InlineKeyboardButton("📋 View Orders", callback_data="menu_view_orders"),
            InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")
        ],
        [InlineKeyboardButton("🔧 More Commands", callback_data="menu_more_commands")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = (
        "📱 *MT5 Trading Assistant Menu*\n\n"
        "👋 Vui lòng chọn menu:\n\n"
        "• *Place Order* - Open new trade\n"
        "• *View Orders* - Check pending orders\n"
        "• *Settings* - Configure bot settings\n"
        "• *More Commands* - View all commands"
    )

    await send_func(
        message_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle menu button callbacks"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "menu_place_order":
        # Show trading submenu
        keyboard = [
            [InlineKeyboardButton("🟢 Limit Buy", callback_data="action_limitbuy")],
            [InlineKeyboardButton("🔴 Limit Sell", callback_data="action_limitsell")],
            [InlineKeyboardButton("« Back to Menu", callback_data="menu_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "📊 *Trading Menu*\n\n"
            "Select order type:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    elif data == "menu_view_orders":
        # Trigger /orders command
        await query.edit_message_text("Loading pending orders...")
        # Import here to avoid circular dependency
        from bot.order_commands import orders_command
        # Create a fake message update to trigger orders_command
        context.user_data['menu_return'] = True
        # Send orders command output
        await query.message.reply_text(
            "Use /orders command to view all pending orders.\n\n"
            "Quick commands:\n"
            "/orderdetail <ticket> - View details\n"
            "/closeorder <ticket> - Close order"
        )
        await show_main_menu(update, context)

    elif data == "menu_settings":
        # Show settings menu
        keyboard = [
            [InlineKeyboardButton("📈 Risk Settings", callback_data="action_setrisktype")],
            [InlineKeyboardButton("🎯 R:R Ratio", callback_data="action_setrr")],
            [InlineKeyboardButton("📊 Symbol Config", callback_data="action_setsymbol")],
            [InlineKeyboardButton("📋 View Settings", callback_data="action_settings")],
            [InlineKeyboardButton("« Back to Menu", callback_data="menu_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "⚙️ *Settings Menu*\n\n"
            "Configure your trading settings:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    elif data == "menu_more_commands":
        # Show all commands
        await query.edit_message_text(
            "📋 *All Commands*\n\n"
            "📈 *Trading:*\n"
            "/limitbuy - Place LIMIT BUY order\n"
            "/limitsell - Place LIMIT SELL order\n\n"
            "📝 *Setup Management:*\n"
            "/addsetup - Add new trade setup\n"
            "/editsetup - Edit existing setup\n"
            "/deletesetup - Delete a setup\n"
            "/setups - View all setups\n\n"
            "⚙️ *Configuration:*\n"
            "/setsymbol - Configure symbol settings\n"
            "/setprefix - Configure prefix only\n"
            "/setsuffix - Configure suffix only\n"
            "/setrisktype - Configure risk settings\n"
            "/setrr - Configure R:R ratio\n"
            "/settings - View current settings\n\n"
            "📋 *Order Management:*\n"
            "/orders - View all pending orders\n"
            "/orderdetail <ticket> - View order details\n"
            "/closeorder <ticket> - Close pending order\n\n"
            "🔧 *MT5 Connection:*\n"
            "/mt5connection - Check MT5 status\n"
            "/reconnectmt5 - Reconnect to MT5\n\n"
            "/cancel - Cancel current operation",
            parse_mode='Markdown'
        )
        # Add back button
        keyboard = [[InlineKeyboardButton("« Back to Menu", callback_data="menu_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "Use /start to return to menu",
            reply_markup=reply_markup
        )

    elif data == "menu_back":
        # Return to main menu
        await show_main_menu(update, context)

    # Action callbacks - route to commands
    elif data.startswith("action_"):
        command = data.replace("action_", "")

        # Get friendly command name
        command_names = {
            "limitbuy": "🟢 Limit Buy Order",
            "limitsell": "🔴 Limit Sell Order",
            "setrisktype": "📈 Risk Settings",
            "setrr": "🎯 R:R Ratio",
            "setsymbol": "📊 Symbol Config",
            "settings": "⚙️ View Settings"
        }
        friendly_name = command_names.get(command, command.title())

        # Create reply keyboard with command button
        keyboard = [[KeyboardButton(f"/{command}")]]
        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            one_time_keyboard=True,  # Auto-hide after use
            resize_keyboard=True,     # Compact size
            input_field_placeholder=f"Tap to send /{command}"
        )

        # Edit menu message
        await query.edit_message_text(
            f"*{friendly_name}*\n\n"
            f"👇 Tap the button below to start:",
            parse_mode='Markdown'
        )

        # Send keyboard
        await query.message.reply_text(
            f"Quick action:",
            reply_markup=reply_markup
        )


async def handle_command_with_menu(command_name: str):
    """
    Decorator to add 'Back to Menu' button after command execution.

    Usage:
        After a command completes, show a button to return to menu.
    """
    keyboard = [[InlineKeyboardButton("« Back to Menu", callback_data="menu_back")]]
    return InlineKeyboardMarkup(keyboard)
