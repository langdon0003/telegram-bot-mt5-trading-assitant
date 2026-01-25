"""
Trade Engine Worker - MT5 Command Processor

Monitors the command queue and executes trade commands in MetaTrader 5.
This runs as a separate process from the Telegram Bot.

Usage:
    python engine/trade_engine_worker.py
"""

import os
import time
import signal
import logging
from datetime import datetime
from typing import Optional

from engine.command_queue import CommandQueue
from engine.mt5_adapter import MT5Adapter
from engine.notification_queue import NotificationQueue
from database.db_manager import DatabaseManager

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TradeEngineWorker:
    """
    Worker that processes trade commands from queue.

    Monitors the command queue directory and executes trades in MT5.
    Updates the database with execution results.
    """

    def __init__(
        self,
        queue_dir: str = "queue",
        db_path: str = "trading_bot.db",
        poll_interval: float = 1.0
    ):
        """
        Initialize trade engine worker.

        Args:
            queue_dir: Directory for command queue
            db_path: Path to SQLite database
            poll_interval: Seconds between queue polls
        """
        self.queue = CommandQueue(queue_dir=queue_dir)
        self.adapter = MT5Adapter()
        self.db = DatabaseManager(db_path)
        self.notification_queue = NotificationQueue()
        self.poll_interval = poll_interval
        self.running = False

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()

    def connect_mt5(
        self,
        login: Optional[int] = None,
        password: Optional[str] = None,
        server: Optional[str] = None
    ) -> bool:
        """
        Connect to MT5.

        Args:
            login: MT5 account number
            password: MT5 password
            server: MT5 server

        Returns:
            True if connected successfully
        """
        # Try to get credentials from environment if not provided
        if not login:
            login = os.getenv("MT5_LOGIN")
            if login:
                login = int(login)

        if not password:
            password = os.getenv("MT5_PASSWORD")

        if not server:
            server = os.getenv("MT5_SERVER")
        print(login, password, server)
        connected = self.adapter.connect(
            login=login,
            password=password,
            server=server
        )

        if connected:
            account_info = self.adapter.get_account_info()
            if account_info:
                logger.info(
                    f"Connected to MT5 - Account: {account_info['login']}, "
                    f"Balance: {account_info['balance']} {account_info['currency']}"
                )

        return connected

    def process_command(self, queue_id: str, queue_command: dict) -> bool:
        """
        Process a single trade command.

        Args:
            queue_id: Queue file ID
            queue_command: Queue command data

        Returns:
            True if processed successfully
        """
        command = queue_command.get('command', {})
        trade_id = command.get('trade_id')

        logger.info(
            f"Processing command {queue_id} - "
            f"Trade #{trade_id} - {command.get('order_type')} "
            f"{command.get('symbol')} @ {command.get('entry_price')}"
        )

        try:
            # Execute trade in MT5
            result = self.adapter.execute_trade_command(command)

            # Get telegram_id for notification
            telegram_id = command.get('telegram_id')

            # Update database
            if result['success']:
                logger.info(
                    f"✅ Trade #{trade_id} executed successfully - "
                    f"Ticket: {result['ticket']}"
                )

                # Update trade status in database
                if trade_id:
                    self.db.update_trade_status(
                        trade_id=trade_id,
                        status='filled',
                        mt5_ticket=result['ticket'],
                        mt5_open_price=result.get('execution_price'),
                        mt5_open_time=datetime.utcnow().isoformat()
                    )

                # Send success notification
                if telegram_id and trade_id:
                    self.notification_queue.enqueue(
                        telegram_id=telegram_id,
                        trade_id=trade_id,
                        success=True,
                        message=f"✅ Trade #{trade_id} executed successfully!\n\n"
                                f"MT5 Ticket: {result['ticket']}\n"
                                f"Symbol: {command.get('symbol')}\n"
                                f"Type: {command.get('order_type')}\n"
                                f"Entry: {command.get('entry_price')}\n"
                                f"Volume: {result.get('volume', command.get('volume'))} lots",
                        details={
                            'ticket': result['ticket'],
                            'execution_price': result.get('execution_price'),
                            'volume': result.get('volume')
                        }
                    )
            else:
                logger.error(
                    f"❌ Trade #{trade_id} failed - Error: {result['error']}"
                )

                # Update trade status as failed
                if trade_id:
                    self.db.update_trade_status(
                        trade_id=trade_id,
                        status='failed'
                    )

                # Send failure notification
                if telegram_id and trade_id:
                    self.notification_queue.enqueue(
                        telegram_id=telegram_id,
                        trade_id=trade_id,
                        success=False,
                        message=f"❌ Trade #{trade_id} failed\n\n"
                                f"Error: {result['error']}\n\n"
                                f"Symbol: {command.get('symbol')}\n"
                                f"Type: {command.get('order_type')}\n"
                                f"Entry: {command.get('entry_price')}",
                        details={
                            'error': result['error']
                        }
                    )

            return result['success']

        except Exception as e:
            logger.exception(f"Error processing command {queue_id}")

            # Mark trade as failed
            if trade_id:
                try:
                    self.db.update_trade_status(
                        trade_id=trade_id,
                        status='failed'
                    )
                except Exception as db_error:
                    logger.error(f"Failed to update database: {db_error}")

            return False

    def run(self):
        """
        Start the worker main loop.

        Continuously monitors queue and processes commands.
        """
        logger.info("=" * 60)
        logger.info("Trade Engine Worker Starting")
        logger.info("=" * 60)

        # Connect to database
        self.db.connect()
        logger.info("Database connected")

        # Connect to MT5
        if not self.connect_mt5():
            logger.error("Failed to connect to MT5. Exiting.")
            return

        self.running = True
        logger.info(f"Worker started - Polling interval: {self.poll_interval}s")
        logger.info(f"Monitoring queue: {self.queue.queue_dir.absolute()}")
        logger.info("Press Ctrl+C to stop")
        logger.info("-" * 60)

        processed_count = 0
        failed_count = 0

        try:
            while self.running:
                # Get pending commands
                pending_ids = self.queue.list_pending()

                if pending_ids:
                    logger.info(f"Found {len(pending_ids)} pending command(s)")

                    for queue_id in pending_ids:
                        if not self.running:
                            break

                        # Dequeue command
                        queue_command = self.queue.dequeue(queue_id)

                        if queue_command:
                            # Process command
                            success = self.process_command(queue_id, queue_command)

                            if success:
                                processed_count += 1
                            else:
                                failed_count += 1

                            logger.info(
                                f"Stats - Processed: {processed_count}, "
                                f"Failed: {failed_count}"
                            )

                # Wait before next poll
                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")

        finally:
            self.stop()

    def stop(self):
        """Stop the worker gracefully"""
        logger.info("Stopping worker...")
        self.running = False

        # Disconnect from MT5
        if self.adapter.connected:
            self.adapter.disconnect()

        # Close database
        if self.db.conn:
            self.db.close()

        logger.info("Worker stopped")
        logger.info("=" * 60)


def main():
    """Main entry point"""
    # Configuration from environment or defaults
    queue_dir = os.getenv("QUEUE_DIR", "queue")
    db_path = os.getenv("DB_PATH", "trading_bot.db")
    poll_interval = float(os.getenv("POLL_INTERVAL", "1.0"))

    # Create and run worker
    worker = TradeEngineWorker(
        queue_dir=queue_dir,
        db_path=db_path,
        poll_interval=poll_interval
    )

    worker.run()


if __name__ == "__main__":
    main()
