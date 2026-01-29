"""
Settings Management Commands

Handles /setsymbol and /setrisktype commands for user configuration.
"""

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

# Conversation states
SYMBOL_BASE, SYMBOL_PREFIX, SYMBOL_SUFFIX = range(3)
PREFIX_INPUT = 5
SUFFIX_INPUT = 6
RISKTYPE_TYPE = 7
RISKTYPE_VALUE = 8
RR_INPUT = 9


# ==================== SET SYMBOL ====================

async def setsymbol_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start /setsymbol conversation"""
    telegram_id = update.effective_user.id
    db = context.application.bot_data['db']

    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("❌ Please use /start first")
        return ConversationHandler.END

    settings = db.get_user_settings(user['id'])
    await update.message.reply_text(
        f"⚙️ Symbol Configuration\n\n"
        f"Current settings:\n"
        f"Base: {settings['default_symbol_base']}\n"
        f"Prefix: {settings['symbol_prefix'] or 'None'}\n"
        f"Suffix: {settings['symbol_suffix'] or 'None'}\n\n"
        f"Enter new symbol base (e.g., XAU, EUR, GBP):"
    )

    return SYMBOL_BASE


async def ask_symbol_prefix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for symbol prefix"""
    symbol_base = update.message.text.strip().upper()

    if len(symbol_base) < 2 or len(symbol_base) > 6:
        await update.message.reply_text(
            "❌ Symbol base must be 2-6 characters.\n\n"
            "Try again:"
        )
        return SYMBOL_BASE

    context.user_data['symbol_base'] = symbol_base

    await update.message.reply_text(
        f"Base: {symbol_base}\n\n"
        f"Enter symbol prefix (e.g., 'BROKER.' or type 'skip'):"
    )

    return SYMBOL_PREFIX


async def ask_symbol_suffix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for symbol suffix"""
    prefix = update.message.text.strip()

    if prefix.lower() == 'skip':
        prefix = ''

    context.user_data['symbol_prefix'] = prefix

    await update.message.reply_text(
        f"Prefix: {prefix or 'None'}\n\n"
        f"Enter symbol suffix (e.g., 'm', '.pro' or type 'skip'):"
    )

    return SYMBOL_SUFFIX


async def save_symbol_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save symbol settings"""
    from engine.symbol_resolver import SymbolResolver

    suffix = update.message.text.strip()

    if suffix.lower() == 'skip':
        suffix = ''

    context.user_data['symbol_suffix'] = suffix

    # Preview symbol
    resolver = SymbolResolver()
    preview_symbol = resolver.resolve(
        base=context.user_data['symbol_base'],
        prefix=context.user_data['symbol_prefix'],
        suffix=context.user_data['symbol_suffix']
    )

    telegram_id = update.effective_user.id
    db = context.application.bot_data['db']

    user = db.get_user_by_telegram_id(telegram_id)

    # Update settings
    db.update_user_settings(
        user_id=user['id'],
        default_symbol_base=context.user_data['symbol_base'],
        symbol_prefix=context.user_data['symbol_prefix'],
        symbol_suffix=context.user_data['symbol_suffix']
    )
    await update.message.reply_text(
        f"✅ Symbol settings saved!\n\n"
        f"Base: {context.user_data['symbol_base']}\n"
        f"Prefix: {context.user_data['symbol_prefix'] or 'None'}\n"
        f"Suffix: {context.user_data['symbol_suffix'] or 'None'}\n\n"
        f"Preview: {preview_symbol}\n\n"
        f"This will be used as default for /limitbuy and /limitsell"
    )

    return ConversationHandler.END



def get_setsymbol_handler():
    """Get the /setsymbol conversation handler"""
    return ConversationHandler(
        entry_points=[CommandHandler("setsymbol", setsymbol_start)],
        states={
            SYMBOL_BASE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_symbol_prefix)],
            SYMBOL_PREFIX: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_symbol_suffix)],
            SYMBOL_SUFFIX: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_symbol_settings)]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            MessageHandler(filters.COMMAND, cancel_and_process_new_command)
        ],
        per_message=False  # Track per user+chat, not per message
    )


# ==================== SET PREFIX ====================

async def setprefix_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start /setprefix conversation"""
    telegram_id = update.effective_user.id
    db = context.application.bot_data['db']

    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("❌ Please use /start first")
        return ConversationHandler.END

    settings = db.get_user_settings(user['id'])
    await update.message.reply_text(
        f"⚙️ Configure Symbol Prefix\n\n"
        f"Current prefix: {settings['symbol_prefix'] or 'None'}\n\n"
        f"Enter new prefix (e.g., 'BROKER.' or type 'skip' to clear):"
    )

    return PREFIX_INPUT


async def save_prefix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save prefix setting"""
    from engine.symbol_resolver import SymbolResolver

    prefix = update.message.text.strip()

    if prefix.lower() == 'skip':
        prefix = ''

    telegram_id = update.effective_user.id
    db = context.application.bot_data['db']

    user = db.get_user_by_telegram_id(telegram_id)
    settings = db.get_user_settings(user['id'])

    # Update prefix only
    db.update_user_settings(
        user_id=user['id'],
        symbol_prefix=prefix
    )

    # Show preview
    resolver = SymbolResolver()
    preview_symbol = resolver.resolve(
        base=settings['default_symbol_base'],
        prefix=prefix,
        suffix=settings['symbol_suffix']
    )
    await update.message.reply_text(
        f"✅ Prefix updated!\n\n"
        f"Prefix: {prefix or 'None'}\n"
        f"Preview: {preview_symbol}"
    )

    return ConversationHandler.END


def get_setprefix_handler():
    """Get the /setprefix conversation handler"""
    return ConversationHandler(
        entry_points=[CommandHandler("setprefix", setprefix_start)],
        states={
            PREFIX_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_prefix)]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            MessageHandler(filters.COMMAND, cancel_and_process_new_command)
        ],
        per_message=False  # Track per user+chat, not per message
    )


# ==================== SET SUFFIX ====================

async def setsuffix_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start /setsuffix conversation"""
    telegram_id = update.effective_user.id
    db = context.application.bot_data['db']

    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("❌ Please use /start first")
        return ConversationHandler.END

    settings = db.get_user_settings(user['id'])
    await update.message.reply_text(
        f"⚙️ Configure Symbol Suffix\n\n"
        f"Current suffix: {settings['symbol_suffix'] or 'None'}\n\n"
        f"Enter new suffix (e.g., 'm', '.pro' or type 'skip' to clear):"
    )

    return SUFFIX_INPUT


async def save_suffix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save suffix setting"""
    from engine.symbol_resolver import SymbolResolver

    suffix = update.message.text.strip()

    if suffix.lower() == 'skip':
        suffix = ''

    telegram_id = update.effective_user.id
    db = context.application.bot_data['db']

    user = db.get_user_by_telegram_id(telegram_id)
    settings = db.get_user_settings(user['id'])

    # Update suffix only
    db.update_user_settings(
        user_id=user['id'],
        symbol_suffix=suffix
    )

    # Show preview
    resolver = SymbolResolver()
    preview_symbol = resolver.resolve(
        base=settings['default_symbol_base'],
        prefix=settings['symbol_prefix'],
        suffix=suffix
    )
    await update.message.reply_text(
        f"✅ Suffix updated!\n\n"
        f"Suffix: {suffix or 'None'}\n"
        f"Preview: {preview_symbol}"
    )

    return ConversationHandler.END


def get_setsuffix_handler():
    """Get the /setsuffix conversation handler"""
    return ConversationHandler(
        entry_points=[CommandHandler("setsuffix", setsuffix_start)],
        states={
            SUFFIX_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_suffix)]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            MessageHandler(filters.COMMAND, cancel_and_process_new_command)
        ],
        per_message=False  # Track per user+chat, not per message
    )


# ==================== SET RISK TYPE ====================

async def setrisktype_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start /setrisktype conversation - Configure risk type and value"""
    telegram_id = update.effective_user.id
    db = context.application.bot_data['db']

    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("❌ Please use /start first")
        return ConversationHandler.END

    settings = db.get_user_settings(user['id'])
    # Format current value for display
    if settings['risk_type'] == "fixed_usd":
        current_value_display = f"${settings['risk_value']}"
    else:  # percent
        current_value_display = f"{settings['risk_value'] * 100}%"

    keyboard = [
        [InlineKeyboardButton("💵 Fixed USD", callback_data="risktype_fixed_usd")],
        [InlineKeyboardButton("📊 Percent of Balance", callback_data="risktype_percent")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"⚙️ Risk Configuration\n\n"
        f"Current settings:\n"
        f"Type: {settings['risk_type']}\n"
        f"Value: {current_value_display}\n\n"
        f"Select risk type:",
        reply_markup=reply_markup
    )

    return RISKTYPE_TYPE


async def ask_risktype_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for risk value based on selected type"""
    query = update.callback_query
    await query.answer()

    risk_type = query.data.replace("risktype_", "")
    context.user_data['risk_type'] = risk_type

    if risk_type == "fixed_usd":
        await query.edit_message_text(
            f"Risk Type: Fixed USD\n\n"
            f"Enter risk amount in USD (e.g., 100):"
        )
    else:  # percent
        await query.edit_message_text(
            f"Risk Type: Percent of Balance\n\n"
            f"Enter risk percentage (e.g., 1 for 1%, 0.5 for 0.5%):"
        )

    return RISKTYPE_VALUE


async def save_risktype_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save risk type and value settings"""
    try:
        risk_value = float(update.message.text)

        if risk_value <= 0:
            await update.message.reply_text(
                "❌ Risk value must be positive.\n\n"
                "Try again:"
            )
            return RISKTYPE_VALUE

        risk_type = context.user_data['risk_type']

        # Validate percent range
        if risk_type == "percent" and risk_value > 100:
            await update.message.reply_text(
                "❌ Percentage cannot exceed 100%.\n\n"
                "Try again:"
            )
            return RISKTYPE_VALUE

        # Convert percent to decimal if needed
        if risk_type == "percent":
            risk_value_display = risk_value
            risk_value = risk_value / 100.0  # Store as decimal (e.g., 0.01 for 1%)
        else:
            risk_value_display = risk_value

        telegram_id = update.effective_user.id
        db = context.application.bot_data['db']

        user = db.get_user_by_telegram_id(telegram_id)

        # Update settings
        db.update_user_settings(
            user_id=user['id'],
            risk_type=risk_type,
            risk_value=risk_value
        )
        if risk_type == "fixed_usd":
            await update.message.reply_text(
                f"✅ Risk settings saved!\n\n"
                f"Type: Fixed USD\n"
                f"Amount: ${risk_value_display}\n\n"
                f"Every trade will risk ${risk_value_display} USD"
            )
        else:
            await update.message.reply_text(
                f"✅ Risk settings saved!\n\n"
                f"Type: Percent of Balance\n"
                f"Percentage: {risk_value_display}%\n\n"
                f"Every trade will risk {risk_value_display}% of your account balance"
            )

        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(
            "❌ Invalid number.\n\n"
            "Try again:"
        )
        return RISKTYPE_VALUE


def get_setrisktype_handler():
    """Get the /setrisktype conversation handler"""
    return ConversationHandler(
        entry_points=[CommandHandler("setrisktype", setrisktype_start)],
        states={
            RISKTYPE_TYPE: [CallbackQueryHandler(ask_risktype_value, pattern="^risktype_(fixed_usd|percent)$")],
            RISKTYPE_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_risktype_settings)]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            MessageHandler(filters.COMMAND, cancel_and_process_new_command)
        ],
        per_message=False  # Track per user+chat, not per message
    )


# ==================== SET RR RATIO ====================

async def setrr_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start /setrr conversation"""
    telegram_id = update.effective_user.id
    db = context.application.bot_data['db']

    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("❌ Please use /start first")
        return ConversationHandler.END

    settings = db.get_user_settings(user['id'])
    # Handle sqlite3.Row object - check if column exists first
    column_missing = False
    try:
        current_rr = settings['default_rr_ratio'] if settings['default_rr_ratio'] is not None else 2.0
    except (KeyError, TypeError):
        # Column doesn't exist yet - user needs to run migration
        current_rr = 2.0
        column_missing = True

    if column_missing:
        await update.message.reply_text(
            "⚠️ Database migration required!\n\n"
            "The R:R ratio feature requires a database update.\n\n"
            "Please ask your admin to run:\n"
            "```\npython migrate_add_rr_ratio.py\n```\n\n"
            "Using default R:R ratio: 2.0:1 for now."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"⚙️ Configure R:R Ratio (Risk:Reward)\n\n"
        f"Current R:R: {current_rr}:1\n\n"
        f"📊 Examples:\n"
        f"• 2 = 2:1 (default) - TP is 2x SL distance\n"
        f"• 3 = 3:1 - TP is 3x SL distance\n"
        f"• 1.5 = 1.5:1 - TP is 1.5x SL distance\n\n"
        f"💡 How it works:\n"
        f"If Entry=2000, SL=1995 (risk=5 points)\n"
        f"• R:R 2:1 → TP=2010 (reward=10 points)\n"
        f"• R:R 3:1 → TP=2015 (reward=15 points)\n\n"
        f"Enter new R:R ratio (e.g., 2, 2.5, 3):"
    )

    return RR_INPUT


async def save_rr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save R:R ratio setting"""
    try:
        rr_ratio = float(update.message.text)

        # Validate R:R ratio
        if rr_ratio <= 0:
            await update.message.reply_text(
                "❌ R:R ratio must be positive!\n\n"
                "Enter a valid R:R ratio (e.g., 2, 2.5, 3):"
            )
            return RR_INPUT

        if rr_ratio > 10:
            await update.message.reply_text(
                "❌ R:R ratio too high (max 10)!\n\n"
                "Enter a realistic R:R ratio (e.g., 2, 2.5, 3):"
            )
            return RR_INPUT

        telegram_id = update.effective_user.id
        db = context.application.bot_data['db']

        user = db.get_user_by_telegram_id(telegram_id)

        # Update RR ratio
        db.update_user_settings(
            user_id=user['id'],
            default_rr_ratio=rr_ratio
        )
        await update.message.reply_text(
            f"✅ R:R ratio updated!\n\n"
            f"New R:R: {rr_ratio}:1\n\n"
            f"📊 Example:\n"
            f"If Entry=2000, SL=1995 (risk=5 points)\n"
            f"→ TP will be auto-calculated: 2000 + (5 × {rr_ratio}) = {2000 + (5 * rr_ratio)}\n\n"
            f"Now when you place trades, TP will be calculated automatically!"
        )

        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(
            "❌ Invalid number!\n\n"
            "Enter a valid R:R ratio (e.g., 2, 2.5, 3):"
        )
        return RR_INPUT


def get_setrr_handler():
    """Get the /setrr conversation handler"""
    return ConversationHandler(
        entry_points=[CommandHandler("setrr", setrr_start)],
        states={
            RR_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_rr)]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            MessageHandler(filters.COMMAND, cancel_and_process_new_command)
        ],
        per_message=False  # Track per user+chat, not per message
    )
