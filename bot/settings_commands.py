"""
Settings Management Commands

Handles /setsymbol and /setrisk commands for user configuration.
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

# Conversation states
SYMBOL_BASE, SYMBOL_PREFIX, SYMBOL_SUFFIX = range(3)
RISK_TYPE, RISK_VALUE = range(3, 5)
PREFIX_INPUT = 5
SUFFIX_INPUT = 6
RISKTYPE_SELECT = 7


# ==================== SET SYMBOL ====================

async def setsymbol_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start /setsymbol conversation"""
    from database.db_manager import DatabaseManager

    telegram_id = update.effective_user.id
    db = DatabaseManager()
    db.connect()

    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("❌ Please use /start first")
        db.close()
        return ConversationHandler.END

    settings = db.get_user_settings(user['id'])
    db.close()

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
    from database.db_manager import DatabaseManager
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
    db = DatabaseManager()
    db.connect()

    user = db.get_user_by_telegram_id(telegram_id)

    # Update settings
    db.update_user_settings(
        user_id=user['id'],
        default_symbol_base=context.user_data['symbol_base'],
        symbol_prefix=context.user_data['symbol_prefix'],
        symbol_suffix=context.user_data['symbol_suffix']
    )

    db.close()

    await update.message.reply_text(
        f"✅ Symbol settings saved!\n\n"
        f"Base: {context.user_data['symbol_base']}\n"
        f"Prefix: {context.user_data['symbol_prefix'] or 'None'}\n"
        f"Suffix: {context.user_data['symbol_suffix'] or 'None'}\n\n"
        f"Preview: {preview_symbol}\n\n"
        f"This will be used as default for /limitbuy and /limitsell"
    )

    return ConversationHandler.END


async def cancel_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel settings change"""
    await update.message.reply_text("❌ Settings change cancelled")
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
        fallbacks=[CommandHandler("cancel", cancel_settings)]
    )


# ==================== SET RISK ====================

async def setrisk_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start /setrisk conversation"""
    from database.db_manager import DatabaseManager

    telegram_id = update.effective_user.id
    db = DatabaseManager()
    db.connect()

    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("❌ Please use /start first")
        db.close()
        return ConversationHandler.END

    settings = db.get_user_settings(user['id'])
    db.close()

    keyboard = [
        [InlineKeyboardButton("💵 Fixed USD", callback_data="risk_fixed_usd")],
        [InlineKeyboardButton("📊 Percent of Balance", callback_data="risk_percent")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"⚙️ Risk Configuration\n\n"
        f"Current settings:\n"
        f"Type: {settings['risk_type']}\n"
        f"Value: {settings['risk_value']}\n\n"
        f"Select risk type:",
        reply_markup=reply_markup
    )

    return RISK_TYPE


async def ask_risk_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for risk value"""
    query = update.callback_query
    await query.answer()

    risk_type = query.data.replace("risk_", "")
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

    return RISK_VALUE


async def save_risk_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save risk settings"""
    from database.db_manager import DatabaseManager

    try:
        risk_value = float(update.message.text)

        if risk_value <= 0:
            await update.message.reply_text(
                "❌ Risk value must be positive.\n\n"
                "Try again:"
            )
            return RISK_VALUE

        risk_type = context.user_data['risk_type']

        # Validate percent range
        if risk_type == "percent" and risk_value > 100:
            await update.message.reply_text(
                "❌ Percentage cannot exceed 100%.\n\n"
                "Try again:"
            )
            return RISK_VALUE

        # Convert percent to decimal if needed
        if risk_type == "percent":
            risk_value_display = risk_value
            risk_value = risk_value / 100.0  # Store as decimal (e.g., 0.01 for 1%)
        else:
            risk_value_display = risk_value

        telegram_id = update.effective_user.id
        db = DatabaseManager()
        db.connect()

        user = db.get_user_by_telegram_id(telegram_id)

        # Update settings
        db.update_user_settings(
            user_id=user['id'],
            risk_type=risk_type,
            risk_value=risk_value
        )

        db.close()

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
        return RISK_VALUE


def get_setrisk_handler():
    """Get the /setrisk conversation handler"""
    return ConversationHandler(
        entry_points=[CommandHandler("setrisk", setrisk_start)],
        states={
            RISK_TYPE: [CallbackQueryHandler(ask_risk_value)],
            RISK_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_risk_settings)]
        },
        fallbacks=[CommandHandler("cancel", cancel_settings)]
    )


# ==================== SET PREFIX ====================

async def setprefix_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start /setprefix conversation"""
    from database.db_manager import DatabaseManager

    telegram_id = update.effective_user.id
    db = DatabaseManager()
    db.connect()

    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("❌ Please use /start first")
        db.close()
        return ConversationHandler.END

    settings = db.get_user_settings(user['id'])
    db.close()

    await update.message.reply_text(
        f"⚙️ Configure Symbol Prefix\n\n"
        f"Current prefix: {settings['symbol_prefix'] or 'None'}\n\n"
        f"Enter new prefix (e.g., 'BROKER.' or type 'skip' to clear):"
    )

    return PREFIX_INPUT


async def save_prefix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save prefix setting"""
    from database.db_manager import DatabaseManager
    from engine.symbol_resolver import SymbolResolver

    prefix = update.message.text.strip()

    if prefix.lower() == 'skip':
        prefix = ''

    telegram_id = update.effective_user.id
    db = DatabaseManager()
    db.connect()

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

    db.close()

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
        fallbacks=[CommandHandler("cancel", cancel_settings)]
    )


# ==================== SET SUFFIX ====================

async def setsuffix_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start /setsuffix conversation"""
    from database.db_manager import DatabaseManager

    telegram_id = update.effective_user.id
    db = DatabaseManager()
    db.connect()

    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("❌ Please use /start first")
        db.close()
        return ConversationHandler.END

    settings = db.get_user_settings(user['id'])
    db.close()

    await update.message.reply_text(
        f"⚙️ Configure Symbol Suffix\n\n"
        f"Current suffix: {settings['symbol_suffix'] or 'None'}\n\n"
        f"Enter new suffix (e.g., 'm', '.pro' or type 'skip' to clear):"
    )

    return SUFFIX_INPUT


async def save_suffix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save suffix setting"""
    from database.db_manager import DatabaseManager
    from engine.symbol_resolver import SymbolResolver

    suffix = update.message.text.strip()

    if suffix.lower() == 'skip':
        suffix = ''

    telegram_id = update.effective_user.id
    db = DatabaseManager()
    db.connect()

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

    db.close()

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
        fallbacks=[CommandHandler("cancel", cancel_settings)]
    )


# ==================== SET RISK TYPE ====================

async def setrisktype_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start /setrisktype conversation"""
    from database.db_manager import DatabaseManager

    telegram_id = update.effective_user.id
    db = DatabaseManager()
    db.connect()

    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("❌ Please use /start first")
        db.close()
        return ConversationHandler.END

    settings = db.get_user_settings(user['id'])
    db.close()

    keyboard = [
        [InlineKeyboardButton("💵 Fixed USD", callback_data="risktype_fixed_usd")],
        [InlineKeyboardButton("📊 Percent of Balance", callback_data="risktype_percent")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"⚙️ Configure Risk Type\n\n"
        f"Current type: {settings['risk_type']}\n"
        f"Current value: {settings['risk_value']}\n\n"
        f"Select new risk type:",
        reply_markup=reply_markup
    )

    return RISKTYPE_SELECT


async def save_risktype(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save risk type setting"""
    from database.db_manager import DatabaseManager

    query = update.callback_query
    await query.answer()

    risk_type = query.data.replace("risktype_", "")

    telegram_id = update.effective_user.id
    db = DatabaseManager()
    db.connect()

    user = db.get_user_by_telegram_id(telegram_id)
    settings = db.get_user_settings(user['id'])

    # Update risk type only (keep existing value)
    db.update_user_settings(
        user_id=user['id'],
        risk_type=risk_type
    )

    db.close()

    type_label = "Fixed USD" if risk_type == "fixed_usd" else "Percent of Balance"

    await query.edit_message_text(
        f"✅ Risk type updated!\n\n"
        f"Type: {type_label}\n"
        f"Value: {settings['risk_value']} (unchanged)\n\n"
        f"Use /setrisk to change both type and value."
    )

    return ConversationHandler.END


def get_setrisktype_handler():
    """Get the /setrisktype conversation handler"""
    return ConversationHandler(
        entry_points=[CommandHandler("setrisktype", setrisktype_start)],
        states={
            RISKTYPE_SELECT: [CallbackQueryHandler(save_risktype)]
        },
        fallbacks=[CommandHandler("cancel", cancel_settings)]
    )
