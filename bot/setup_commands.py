"""
Setup Management Commands

Handles /addsetup, /editsetup, /deletesetup commands for managing trade setups.
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

# Conversation states for /addsetup
SETUP_CODE, SETUP_NAME, SETUP_DESCRIPTION = range(3)

# Conversation states for /editsetup
EDIT_SELECT, EDIT_FIELD, EDIT_VALUE = range(3, 6)

# Conversation states for /deletesetup
DELETE_SELECT, DELETE_CONFIRM = range(6, 8)


async def addsetup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start /addsetup conversation"""
    await update.message.reply_text(
        "📝 Add New Trade Setup\n\n"
        "Enter setup code (e.g., FZ1, TLP1, OB):\n"
        "(Use /cancel to abort)"
    )
    return SETUP_CODE


async def ask_setup_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for setup name"""
    setup_code = update.message.text.strip().upper()

    if len(setup_code) < 2 or len(setup_code) > 10:
        await update.message.reply_text(
            "❌ Setup code must be 2-10 characters.\n\n"
            "Try again:"
        )
        return SETUP_CODE

    context.user_data['setup_code'] = setup_code

    await update.message.reply_text(
        f"Code: {setup_code}\n\n"
        f"Enter setup name (e.g., Fair Value Zone 1):"
    )

    return SETUP_NAME


async def ask_setup_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for setup description"""
    setup_name = update.message.text.strip()

    if len(setup_name) < 3:
        await update.message.reply_text(
            "❌ Setup name too short.\n\n"
            "Try again:"
        )
        return SETUP_NAME

    context.user_data['setup_name'] = setup_name

    await update.message.reply_text(
        f"Name: {setup_name}\n\n"
        f"Enter description (optional, or type 'skip'):"
    )

    return SETUP_DESCRIPTION


async def save_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the setup to database"""
    from database.db_manager import DatabaseManager

    description = update.message.text.strip()

    if description.lower() == 'skip':
        description = None

    # Get user
    telegram_id = update.effective_user.id
    db = DatabaseManager()
    db.connect()

    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("❌ Please use /start first")
        db.close()
        return ConversationHandler.END

    # Check if setup code already exists
    setups = db.get_user_setups(user['id'], active_only=False)
    existing_codes = [s['setup_code'] for s in setups]

    if context.user_data['setup_code'] in existing_codes:
        await update.message.reply_text(
            f"❌ Setup code '{context.user_data['setup_code']}' already exists!\n\n"
            f"Choose a different code."
        )
        db.close()
        return ConversationHandler.END

    # Create setup
    try:
        db.create_setup(
            user_id=user['id'],
            setup_code=context.user_data['setup_code'],
            setup_name=context.user_data['setup_name'],
            description=description
        )

        await update.message.reply_text(
            f"✅ Setup created!\n\n"
            f"Code: {context.user_data['setup_code']}\n"
            f"Name: {context.user_data['setup_name']}\n"
            f"Description: {description or 'None'}\n\n"
            f"Use /setups to see all your setups."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error creating setup: {e}")
    finally:
        db.close()

    return ConversationHandler.END


async def cancel_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel /addsetup"""
    await update.message.reply_text("❌ Setup creation cancelled")
    return ConversationHandler.END


def get_addsetup_handler():
    """Get the /addsetup conversation handler"""
    return ConversationHandler(
        entry_points=[CommandHandler("addsetup", addsetup_start)],
        states={
            SETUP_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_setup_name)],
            SETUP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_setup_description)],
            SETUP_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_setup)]
        },
        fallbacks=[CommandHandler("cancel", cancel_setup)],
        per_message=False  # Track per user+chat, not per message
    )


# ==================== EDIT SETUP ====================

async def editsetup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start /editsetup conversation"""
    from database.db_manager import DatabaseManager

    telegram_id = update.effective_user.id
    db = DatabaseManager()
    db.connect()

    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("❌ Please use /start first")
        db.close()
        return ConversationHandler.END

    setups = db.get_user_setups(user['id'])
    db.close()

    if not setups:
        await update.message.reply_text(
            "No setups to edit. Use /addsetup to create one."
        )
        return ConversationHandler.END

    # Create setup selection keyboard
    keyboard = []
    for setup in setups:
        keyboard.append([InlineKeyboardButton(
            f"{setup['setup_code']} - {setup['setup_name']}",
            callback_data=f"edit_{setup['setup_code']}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Select setup to edit:",
        reply_markup=reply_markup
    )

    return EDIT_SELECT


async def edit_select_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Select which field to edit"""
    query = update.callback_query
    await query.answer()

    setup_code = query.data.replace("edit_", "")
    context.user_data['edit_setup_code'] = setup_code

    keyboard = [
        [InlineKeyboardButton("📝 Edit Name", callback_data="field_name")],
        [InlineKeyboardButton("📄 Edit Description", callback_data="field_description")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Editing setup: {setup_code}\n\n"
        f"What do you want to edit?",
        reply_markup=reply_markup
    )

    return EDIT_FIELD


async def edit_ask_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for new value"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Edit cancelled")
        return ConversationHandler.END

    field = query.data.replace("field_", "")
    context.user_data['edit_field'] = field

    if field == "name":
        await query.edit_message_text("Enter new setup name:")
    elif field == "description":
        await query.edit_message_text("Enter new description (or 'skip' to clear):")

    return EDIT_VALUE


async def edit_save_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save edited value"""
    from database.db_manager import DatabaseManager

    new_value = update.message.text.strip()

    if new_value.lower() == 'skip':
        new_value = None

    telegram_id = update.effective_user.id
    db = DatabaseManager()
    db.connect()

    user = db.get_user_by_telegram_id(telegram_id)
    setup_code = context.user_data['edit_setup_code']
    field = context.user_data['edit_field']

    # Update setup
    cursor = db.conn.cursor()

    if field == "name":
        cursor.execute(
            "UPDATE setups SET setup_name = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND setup_code = ?",
            (new_value, user['id'], setup_code)
        )
    elif field == "description":
        cursor.execute(
            "UPDATE setups SET description = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND setup_code = ?",
            (new_value, user['id'], setup_code)
        )

    db.conn.commit()
    db.close()

    await update.message.reply_text(
        f"✅ Setup updated!\n\n"
        f"Code: {setup_code}\n"
        f"Updated {field}: {new_value or 'None'}"
    )

    return ConversationHandler.END


def get_editsetup_handler():
    """Get the /editsetup conversation handler"""
    return ConversationHandler(
        entry_points=[CommandHandler("editsetup", editsetup_start)],
        states={
            EDIT_SELECT: [CallbackQueryHandler(edit_select_field)],
            EDIT_FIELD: [CallbackQueryHandler(edit_ask_value)],
            EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_save_value)]
        },
        fallbacks=[CommandHandler("cancel", cancel_setup)],
        per_message=False  # Track per user+chat, not per message
    )


# ==================== DELETE SETUP ====================

async def deletesetup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start /deletesetup conversation"""
    from database.db_manager import DatabaseManager

    telegram_id = update.effective_user.id
    db = DatabaseManager()
    db.connect()

    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("❌ Please use /start first")
        db.close()
        return ConversationHandler.END

    setups = db.get_user_setups(user['id'])
    db.close()

    if not setups:
        await update.message.reply_text(
            "No setups to delete. Use /addsetup to create one."
        )
        return ConversationHandler.END

    # Create setup selection keyboard
    keyboard = []
    for setup in setups:
        keyboard.append([InlineKeyboardButton(
            f"🗑️ {setup['setup_code']} - {setup['setup_name']}",
            callback_data=f"delete_{setup['setup_code']}"
        )])

    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "⚠️ Select setup to DELETE:",
        reply_markup=reply_markup
    )

    return DELETE_SELECT


async def delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm deletion"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Deletion cancelled")
        return ConversationHandler.END

    setup_code = query.data.replace("delete_", "")
    context.user_data['delete_setup_code'] = setup_code

    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, Delete", callback_data="confirm_delete"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"⚠️ Are you sure you want to delete setup '{setup_code}'?\n\n"
        f"This action cannot be undone!",
        reply_markup=reply_markup
    )

    return DELETE_CONFIRM


async def delete_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute deletion"""
    from database.db_manager import DatabaseManager

    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Deletion cancelled")
        return ConversationHandler.END

    telegram_id = update.effective_user.id
    db = DatabaseManager()
    db.connect()

    user = db.get_user_by_telegram_id(telegram_id)
    setup_code = context.user_data['delete_setup_code']

    # Delete setup (soft delete by setting is_active = 0)
    cursor = db.conn.cursor()
    cursor.execute(
        "UPDATE setups SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND setup_code = ?",
        (user['id'], setup_code)
    )
    db.conn.commit()
    db.close()

    await query.edit_message_text(
        f"✅ Setup '{setup_code}' deleted successfully!"
    )

    return ConversationHandler.END


def get_deletesetup_handler():
    """Get the /deletesetup conversation handler"""
    return ConversationHandler(
        entry_points=[CommandHandler("deletesetup", deletesetup_start)],
        states={
            DELETE_SELECT: [CallbackQueryHandler(delete_confirm)],
            DELETE_CONFIRM: [CallbackQueryHandler(delete_execute)]
        },
        fallbacks=[CommandHandler("cancel", cancel_setup)],
        per_message=False  # Track per user+chat, not per message
    )
