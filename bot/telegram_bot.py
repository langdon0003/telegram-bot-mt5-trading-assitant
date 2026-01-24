"""
Telegram Bot - Conversation-based Trading Assistant

Handles user interaction, validates input, and sends trade commands to Trade Engine.
Uses python-telegram-bot ConversationHandler for state management.
"""

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

from bot.trade_command_builder import TradeCommandBuilder
from bot.setup_commands import (
    get_addsetup_handler,
    get_editsetup_handler,
    get_deletesetup_handler
)
from bot.settings_commands import (
    get_setsymbol_handler,
    get_setrisk_handler,
    get_setprefix_handler,
    get_setsuffix_handler,
    get_setrisktype_handler
)
from engine.symbol_resolver import SymbolResolver
from engine.trade_validator import TradeValidator
from engine.risk_calculator import RiskCalculator
from engine.mt5_adapter import MT5Adapter
from database.db_manager import DatabaseManager

# Conversation states
(
    SYMBOL,
    ENTRY,
    STOP_LOSS,
    TAKE_PROFIT,
    EMOTION,
    SETUP,
    CHART_URL,
    CONFIRM
) = range(8)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TradingBot:
    """Telegram bot for manual trading into MT5"""

    def __init__(self, token: str, db_path: str = "trading_bot.db"):
        """
        Initialize bot.

        Args:
            token: Telegram bot token
            db_path: Path to SQLite database
        """
        self.token = token
        self.db = DatabaseManager(db_path)
        self.db.connect()
        self.db.initialize_schema()

        self.symbol_resolver = SymbolResolver()
        self.trade_validator = TradeValidator()
        self.risk_calculator = RiskCalculator()
        self.mt5_adapter = MT5Adapter()

        # Connect to MT5 on initialization
        if not self.mt5_adapter.connect():
            logger.warning("MT5 connection failed on bot init. Will retry on trade execution.")

    def run(self):
        """Start the bot"""
        app = Application.builder().token(self.token).build()

        # Conversation handler for /limitbuy
        limitbuy_handler = ConversationHandler(
            entry_points=[CommandHandler("limitbuy", self.limitbuy_start)],
            states={
                SYMBOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ask_entry)],
                ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ask_stop_loss)],
                STOP_LOSS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ask_take_profit)],
                TAKE_PROFIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.show_preview)],
                EMOTION: [CallbackQueryHandler(self.ask_setup)],
                SETUP: [CallbackQueryHandler(self.ask_chart_url)],
                CHART_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ask_confirm)],
                CONFIRM: [CallbackQueryHandler(self.execute_trade)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )

        # Conversation handler for /limitsell
        limitsell_handler = ConversationHandler(
            entry_points=[CommandHandler("limitsell", self.limitsell_start)],
            states={
                SYMBOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ask_entry)],
                ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ask_stop_loss)],
                STOP_LOSS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ask_take_profit)],
                TAKE_PROFIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.show_preview)],
                EMOTION: [CallbackQueryHandler(self.ask_setup)],
                SETUP: [CallbackQueryHandler(self.ask_chart_url)],
                CHART_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ask_confirm)],
                CONFIRM: [CallbackQueryHandler(self.execute_trade)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )

        # Basic handlers
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("settings", self.settings))
        app.add_handler(CommandHandler("setups", self.manage_setups))
        app.add_handler(CommandHandler("queue", self.check_queue))
        app.add_handler(CommandHandler("clearqueue", self.clear_queue))

        # Setup management
        app.add_handler(get_addsetup_handler())
        app.add_handler(get_editsetup_handler())
        app.add_handler(get_deletesetup_handler())

        # Settings management
        app.add_handler(get_setsymbol_handler())
        app.add_handler(get_setrisk_handler())
        app.add_handler(get_setprefix_handler())
        app.add_handler(get_setsuffix_handler())
        app.add_handler(get_setrisktype_handler())

        # Trade handlers
        app.add_handler(limitbuy_handler)
        app.add_handler(limitsell_handler)

        logger.info("Bot started")
        app.run_polling()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        telegram_id = update.effective_user.id

        # Get or create user
        user = self.db.get_user_by_telegram_id(telegram_id)
        if not user:
            user_id = self.db.create_user(
                telegram_id=telegram_id,
                username=update.effective_user.username,
                first_name=update.effective_user.first_name,
                last_name=update.effective_user.last_name
            )
            self.db.create_default_settings(user_id)

        await update.message.reply_text(
            "Welcome to MT5 Trading Assistant!\n\n"
            "📈 Trading:\n"
            "/limitbuy - Place LIMIT BUY order\n"
            "/limitsell - Place LIMIT SELL order\n\n"
            "📝 Setup Management:\n"
            "/addsetup - Add new trade setup\n"
            "/editsetup - Edit existing setup\n"
            "/deletesetup - Delete a setup\n"
            "/setups - View all setups\n\n"
            "⚙️ Configuration:\n"
            "/setsymbol - Configure symbol settings\n"
            "/setprefix - Configure prefix only\n"
            "/setsuffix - Configure suffix only\n"
            "/setrisk - Configure risk settings\n"
            "/setrisktype - Configure risk type only\n"
            "/settings - View current settings\n\n"
            "🔧 MT5 Connection:\n"
            "/queue - Check MT5 connection status\n"
            "/clearqueue - Reconnect to MT5\n\n"
            "/cancel - Cancel current operation"
        )

    async def settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command"""
        telegram_id = update.effective_user.id
        user = self.db.get_user_by_telegram_id(telegram_id)

        if not user:
            await update.message.reply_text("Please use /start first")
            return

        settings = self.db.get_user_settings(user['id'])

        if settings:
            await update.message.reply_text(
                f"Your Settings:\n\n"
                f"Symbol Base: {settings['default_symbol_base']}\n"
                f"Symbol Prefix: {settings['symbol_prefix'] or 'None'}\n"
                f"Symbol Suffix: {settings['symbol_suffix'] or 'None'}\n"
                f"Risk Type: {settings['risk_type']}\n"
                f"Risk Value: {settings['risk_value']}\n\n"
                f"Use /setsymbol, /setrisk to change settings"
            )

    async def manage_setups(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setups command"""
        telegram_id = update.effective_user.id
        user = self.db.get_user_by_telegram_id(telegram_id)

        if not user:
            await update.message.reply_text("Please use /start first")
            return

        setups = self.db.get_user_setups(user['id'])

        if setups:
            setup_list = "\n".join([f"- {s['setup_code']}: {s['setup_name']}" for s in setups])
            await update.message.reply_text(f"Your Setups:\n\n{setup_list}")
        else:
            await update.message.reply_text("No setups configured. Use /addsetup to create one.")

    async def check_queue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /queue command - Check MT5 connection status"""
        telegram_id = update.effective_user.id
        user = self.db.get_user_by_telegram_id(telegram_id)

        if not user:
            await update.message.reply_text("Please use /start first")
            return

        # Check MT5 connection
        if self.mt5_adapter.connected:
            account_info = self.mt5_adapter.get_account_info()
            await update.message.reply_text(
                f"✅ MT5 Connected\n\n"
                f"Account: {account_info['login']}\n"
                f"Balance: ${account_info['balance']:.2f}\n"
                f"Equity: ${account_info['equity']:.2f}\n"
                f"Currency: {account_info['currency']}"
            )
        else:
            await update.message.reply_text(
                "❌ MT5 Not Connected\n\n"
                "Please ensure MetaTrader 5 is running and logged in,\n"
                "then restart the bot."
            )

    async def clear_queue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clearqueue command - Reconnect to MT5"""
        telegram_id = update.effective_user.id
        user = self.db.get_user_by_telegram_id(telegram_id)

        if not user:
            await update.message.reply_text("Please use /start first")
            return

        # Reconnect to MT5
        await update.message.reply_text("🔄 Reconnecting to MT5...")

        # Disconnect first
        if self.mt5_adapter.connected:
            self.mt5_adapter.disconnect()

        # Reconnect
        if self.mt5_adapter.connect():
            account_info = self.mt5_adapter.get_account_info()
            await update.message.reply_text(
                f"✅ MT5 Reconnected!\n\n"
                f"Account: {account_info['login']}\n"
                f"Balance: ${account_info['balance']:.2f}"
            )
        else:
            await update.message.reply_text(
                "❌ Failed to reconnect to MT5\n\n"
                "Please check:\n"
                "- MT5 is running\n"
                "- You are logged in\n"
                "- No firewall blocking"
            )
    # LIMIT BUY conversation flow
    async def limitbuy_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start LIMIT BUY conversation"""
        telegram_id = update.effective_user.id
        user = self.db.get_user_by_telegram_id(telegram_id)

        if not user:
            await update.message.reply_text("Please use /start first")
            return ConversationHandler.END

        settings = self.db.get_user_settings(user['id'])

        context.user_data['order_type'] = 'LIMIT_BUY'
        context.user_data['user_id'] = user['id']
        context.user_data['telegram_id'] = telegram_id

        await update.message.reply_text(
            f"LIMIT BUY Trade\n\n"
            f"Enter symbol base (default: {settings['default_symbol_base']}):"
        )

        return SYMBOL

    async def limitsell_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start LIMIT SELL conversation"""
        telegram_id = update.effective_user.id
        user = self.db.get_user_by_telegram_id(telegram_id)

        if not user:
            await update.message.reply_text("Please use /start first")
            return ConversationHandler.END

        settings = self.db.get_user_settings(user['id'])

        context.user_data['order_type'] = 'LIMIT_SELL'
        context.user_data['user_id'] = user['id']
        context.user_data['telegram_id'] = telegram_id

        await update.message.reply_text(
            f"LIMIT SELL Trade\n\n"
            f"Enter symbol base (default: {settings['default_symbol_base']}):"
        )

        return SYMBOL

    async def ask_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ask for entry price"""
        symbol_base = update.message.text.strip().upper() or "XAU"
        context.user_data['symbol_base'] = symbol_base

        # Resolve symbol
        user_id = context.user_data['user_id']
        settings = self.db.get_user_settings(user_id)

        symbol = self.symbol_resolver.resolve(
            base=symbol_base,
            prefix=settings['symbol_prefix'],
            suffix=settings['symbol_suffix']
        )

        context.user_data['symbol'] = symbol

        await update.message.reply_text(f"Symbol: {symbol}\n\nEnter entry price:")

        return ENTRY

    async def ask_stop_loss(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ask for stop loss"""
        try:
            entry = float(update.message.text)
            context.user_data['entry'] = entry

            order_type = context.user_data['order_type']

            if order_type == 'LIMIT_BUY':
                await update.message.reply_text(
                    f"Entry: {entry}\n\n"
                    f"Enter stop loss (must be < {entry}):"
                )
            else:
                await update.message.reply_text(
                    f"Entry: {entry}\n\n"
                    f"Enter stop loss (must be > {entry}):"
                )

            return STOP_LOSS

        except ValueError:
            await update.message.reply_text("Invalid price. Please enter a number:")
            return ENTRY

    async def ask_take_profit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ask for take profit"""
        try:
            sl = float(update.message.text)
            entry = context.user_data['entry']
            order_type = context.user_data['order_type']

            # Validate SL position
            is_valid = self.trade_validator.validate_sl_position(
                order_type=order_type,
                entry_price=entry,
                sl_price=sl
            )

            if not is_valid:
                if order_type == 'LIMIT_BUY':
                    await update.message.reply_text(
                        f"❌ Invalid! For BUY, SL must be < {entry}\n\n"
                        f"Enter stop loss again:"
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Invalid! For SELL, SL must be > {entry}\n\n"
                        f"Enter stop loss again:"
                    )
                return STOP_LOSS

            context.user_data['sl'] = sl

            await update.message.reply_text(f"Stop Loss: {sl}\n\nEnter take profit:")

            return TAKE_PROFIT

        except ValueError:
            await update.message.reply_text("Invalid price. Please enter a number:")
            return STOP_LOSS

    async def show_preview(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show trade preview and ask for emotion"""
        try:
            tp = float(update.message.text)
            context.user_data['tp'] = tp

            # Get trade details
            entry = context.user_data['entry']
            sl = context.user_data['sl']
            order_type = context.user_data['order_type']
            symbol = context.user_data['symbol']

            # Calculate R:R
            validation = self.trade_validator.validate_trade(
                order_type=order_type,
                entry_price=entry,
                sl_price=sl,
                tp_price=tp
            )

            # Calculate volume (mock pip value for now - will get from MT5)
            user_id = context.user_data['user_id']
            settings = self.db.get_user_settings(user_id)

            # Mock: assume $1 per lot per point for gold
            pip_value = 1.0
            risk_usd = settings['risk_value']

            volume = self.risk_calculator.calculate_volume(
                risk_usd=risk_usd,
                entry_price=entry,
                sl_price=sl,
                pip_value=pip_value,
                tick_size=0.01,
                volume_step=0.01
            )

            context.user_data['volume'] = volume
            context.user_data['risk_usd'] = risk_usd
            context.user_data['rr'] = validation['rr_ratio']

            # Create emotion keyboard
            keyboard = [
                [
                    InlineKeyboardButton("😌 Calm", callback_data="calm"),
                    InlineKeyboardButton("💪 Confident", callback_data="confident")
                ],
                [
                    InlineKeyboardButton("😰 FOMO", callback_data="fomo"),
                    InlineKeyboardButton("😤 Stressed", callback_data="stressed")
                ],
                [InlineKeyboardButton("😡 Revenge", callback_data="revenge")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"📊 Trade Preview\n\n"
                f"Symbol: {symbol}\n"
                f"Type: {order_type}\n"
                f"Entry: {entry}\n"
                f"SL: {sl}\n"
                f"TP: {tp}\n\n"
                f"💰 Risk: ${risk_usd}\n"
                f"📦 Volume: {volume} lots\n"
                f"📈 R:R: {validation['rr_ratio']}\n\n"
                f"How are you feeling?",
                reply_markup=reply_markup
            )

            return EMOTION

        except ValueError:
            await update.message.reply_text("Invalid price. Please enter a number:")
            return TAKE_PROFIT

    async def ask_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ask for setup selection"""
        query = update.callback_query
        await query.answer()

        emotion = query.data
        context.user_data['emotion'] = emotion

        # Get user setups
        user_id = context.user_data['user_id']
        setups = self.db.get_user_setups(user_id)

        if not setups:
            await query.edit_message_text(
                "No setups configured! Use /addsetup first.\n\n"
                "Using default setup: GENERIC"
            )
            context.user_data['setup_code'] = 'GENERIC'
            return CHART_URL

        # Create setup keyboard
        keyboard = []
        row = []
        for i, setup in enumerate(setups):
            row.append(InlineKeyboardButton(setup['setup_code'], callback_data=setup['setup_code']))
            if (i + 1) % 3 == 0:
                keyboard.append(row)
                row = []

        if row:
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"Emotion: {emotion}\n\nSelect your setup:",
            reply_markup=reply_markup
        )

        return SETUP

    async def ask_chart_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ask for TradingView chart URL"""
        query = update.callback_query
        await query.answer()

        setup_code = query.data
        context.user_data['setup_code'] = setup_code

        await query.edit_message_text(
            f"Setup: {setup_code}\n\n"
            f"Enter TradingView chart URL (or type 'skip'):"
        )

        return CHART_URL

    async def ask_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ask for final confirmation"""
        chart_url = update.message.text.strip()

        if chart_url.lower() == 'skip':
            chart_url = None

        context.user_data['chart_url'] = chart_url

        # Create confirmation keyboard
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data="confirm"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"📋 Final Confirmation\n\n"
            f"Symbol: {context.user_data['symbol']}\n"
            f"Type: {context.user_data['order_type']}\n"
            f"Entry: {context.user_data['entry']}\n"
            f"SL: {context.user_data['sl']}\n"
            f"TP: {context.user_data['tp']}\n"
            f"Volume: {context.user_data['volume']} lots\n"
            f"Risk: ${context.user_data['risk_usd']}\n"
            f"R:R: {context.user_data['rr']}\n"
            f"Emotion: {context.user_data['emotion']}\n"
            f"Setup: {context.user_data['setup_code']}\n"
            f"Chart: {chart_url or 'None'}\n\n"
            f"Execute this trade?",
            reply_markup=reply_markup
        )

        return CONFIRM

    async def execute_trade(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Execute trade or cancel"""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel":
            await query.edit_message_text("❌ Trade cancelled")
            return ConversationHandler.END

        # Get account_id from user settings
        user_id = context.user_data['user_id']
        telegram_id = context.user_data['telegram_id']
        settings = self.db.get_user_settings(user_id)
        account_id = settings['default_account_id'] or 1  # Fallback to 1 if not set

        # Show processing message
        await query.edit_message_text("⏳ Executing trade in MT5...")

        # Build trade command
        command = {
            "user_id": user_id,
            "account_id": account_id,
            "telegram_id": telegram_id,
            "order_type": context.user_data['order_type'],
            "symbol": context.user_data['symbol'],
            "entry": context.user_data['entry'],
            "sl": context.user_data['sl'],
            "tp": context.user_data['tp'],
            "volume": context.user_data['volume'],
            "risk_usd": context.user_data['risk_usd'],
            "emotion": context.user_data['emotion'],
            "setup_code": context.user_data['setup_code'],
            "chart_url": context.user_data['chart_url']
        }

        # Save to database first
        trade_id = self.db.create_trade(
            user_id=user_id,
            account_id=account_id,
            symbol=context.user_data['symbol'],
            order_type=context.user_data['order_type'],
            entry=context.user_data['entry'],
            sl=context.user_data['sl'],
            tp=context.user_data['tp'],
            volume=context.user_data['volume'],
            risk_usd=context.user_data['risk_usd'],
            rr=context.user_data['rr'],
            emotion=context.user_data['emotion'],
            setup_code=context.user_data['setup_code'],
            chart_url=context.user_data['chart_url']
        )

        # Execute trade in MT5 directly
        try:
            # Check MT5 connection
            if not self.mt5_adapter.connected:
                logger.warning("MT5 not connected, attempting to connect...")
                if not self.mt5_adapter.connect():
                    raise Exception("Failed to connect to MT5. Please ensure MT5 is running and logged in.")

            # Execute trade
            result = self.mt5_adapter.execute_trade_command(command)

            if result['success']:
                # Update database with success
                self.db.update_trade_status(
                    trade_id=trade_id,
                    status='filled',
                    mt5_ticket=result['ticket'],
                    mt5_open_price=result.get('execution_price'),
                    mt5_open_time=datetime.utcnow().isoformat()
                )

                # Send success message
                await query.edit_message_text(
                    f"✅ Trade #{trade_id} executed successfully!\n\n"
                    f"MT5 Ticket: {result['ticket']}\n"
                    f"Symbol: {context.user_data['symbol']}\n"
                    f"Type: {context.user_data['order_type']}\n"
                    f"Entry: {context.user_data['entry']}\n"
                    f"SL: {context.user_data['sl']}\n"
                    f"TP: {context.user_data['tp']}\n"
                    f"Volume: {result.get('volume', context.user_data['volume'])} lots\n"
                    f"Risk: ${context.user_data['risk_usd']}\n"
                    f"R:R: {context.user_data['rr']}"
                )

                logger.info(f"Trade #{trade_id} executed successfully - Ticket: {result['ticket']}")

            else:
                # Update database with failure
                self.db.update_trade_status(
                    trade_id=trade_id,
                    status='failed'
                )

                # Send failure message
                await query.edit_message_text(
                    f"❌ Trade #{trade_id} failed\n\n"
                    f"Error: {result['error']}\n\n"
                    f"Symbol: {context.user_data['symbol']}\n"
                    f"Type: {context.user_data['order_type']}\n"
                    f"Entry: {context.user_data['entry']}\n\n"
                    f"Please check:\n"
                    f"- Market is open\n"
                    f"- Symbol exists in MT5\n"
                    f"- Sufficient margin"
                )

                logger.error(f"Trade #{trade_id} failed - Error: {result['error']}")

        except Exception as e:
            # Update database with failure
            self.db.update_trade_status(
                trade_id=trade_id,
                status='failed'
            )

            # Send error message
            await query.edit_message_text(
                f"❌ Trade #{trade_id} execution error\n\n"
                f"Error: {str(e)}\n\n"
                f"Please ensure:\n"
                f"- MetaTrader 5 is running\n"
                f"- You are logged in\n"
                f"- Market is open\n\n"
                f"Use /queue to check MT5 connection"
            )

            logger.exception(f"Error executing trade #{trade_id}")

        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel conversation"""
        await update.message.reply_text("Operation cancelled")
        return ConversationHandler.END

    async def poll_notifications(self, context: ContextTypes.DEFAULT_TYPE):
        """Poll notification queue and send to users"""
        try:
            notifications = self.notification_queue.get_pending()

            for notif in notifications:
                telegram_id = notif['telegram_id']
                message = notif['message']
                notification_id = notif['notification_id']

                try:
                    # Send notification to user
                    await context.bot.send_message(
                        chat_id=telegram_id,
                        text=message
                    )

                    # Mark as sent
                    self.notification_queue.mark_sent(notification_id)
                    logger.info(f"Notification sent to {telegram_id}: Trade #{notif['trade_id']}")

                except Exception as e:
                    logger.error(f"Failed to send notification {notification_id}: {e}")
                    # Don't mark as sent, will retry next poll

        except Exception as e:
            logger.error(f"Error polling notifications: {e}")


if __name__ == "__main__":
    BOT_TOKEN = os.getenv("BOT_TOKEN")

    if not BOT_TOKEN:
        raise ValueError(
            "BOT_TOKEN environment variable is not set.\n"
            "Please set it using: export BOT_TOKEN='your_bot_token_here'"
        )

    bot = TradingBot(token=BOT_TOKEN)
    bot.run()
