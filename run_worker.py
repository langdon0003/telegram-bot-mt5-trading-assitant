"""
Run Trade Engine Worker

This is the main entry point for running the MT5 trade engine worker.
Loads environment variables and starts monitoring the command queue.
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import worker
from engine.trade_engine_worker import TradeEngineWorker

if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded .env file")
    except ImportError:
        print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
        print("⚠️  Using environment variables from system")

    # Get configuration from environment
    QUEUE_DIR = os.getenv("QUEUE_DIR", "queue")
    DB_PATH = os.getenv("DATABASE_PATH", "trading_bot.db")
    POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "1.0"))

    # MT5 credentials (optional - can login manually in MT5)
    MT5_LOGIN = os.getenv("MT5_LOGIN")
    MT5_PASSWORD = os.getenv("MT5_PASSWORD")
    MT5_SERVER = os.getenv("MT5_SERVER")

    print("⚙️  Trade Engine Worker Configuration:")
    print(f"   Queue Directory: {QUEUE_DIR}")
    print(f"   Database: {DB_PATH}")
    print(f"   Poll Interval: {POLL_INTERVAL}s")

    if MT5_LOGIN:
        print(f"   MT5 Login: {MT5_LOGIN}")
        print(f"   MT5 Server: {MT5_SERVER}")
    else:
        print("   MT5: Will use existing login session")

    try:
        # Create worker
        worker = TradeEngineWorker(
            queue_dir=QUEUE_DIR,
            db_path=DB_PATH,
            poll_interval=POLL_INTERVAL
        )

        # Run worker
        worker.run()

    except KeyboardInterrupt:
        print("\n👋 Worker stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
