"""
Run Telegram Trading Bot

This is the main entry point for running the bot.
Loads environment variables and starts the bot.
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import bot
from bot.telegram_bot import TradingBot

if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded .env file")
    except ImportError:
        print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
        print("⚠️  Using environment variables from system")

    # Get bot token from environment
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        print("❌ ERROR: TELEGRAM_BOT_TOKEN not set in .env file!")
        print("Please edit .env file and add your bot token from @BotFather")
        sys.exit(1)

    # Get database path
    DB_PATH = os.getenv("DATABASE_PATH", "trading_bot.db")

    print(f"🤖 Starting Telegram Trading Bot...")
    print(f"📊 Database: {DB_PATH}")

    try:
        # Create and run bot
        bot = TradingBot(token=BOT_TOKEN, db_path=DB_PATH)
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
