"""
MT5 Adapter - Trade Engine

Receives trade commands from Bot and executes them in MetaTrader 5.
Handles symbol resolution, volume calculation, and order placement.

This is a SEPARATE process from the Telegram bot.
"""

import MetaTrader5 as mt5
import logging
import os

from datetime import datetime
from typing import Dict, Optional

from engine.symbol_resolver import SymbolResolver
from engine.risk_calculator import RiskCalculator
from engine.trade_validator import TradeValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MT5Adapter:
    """
    Trade Engine that executes trades in MetaTrader 5.

    Receives trade commands (JSON) from Telegram Bot.
    Resolves symbol, validates, calculates volume, and places order.
    """

    def __init__(self):
        self.symbol_resolver = SymbolResolver()
        self.risk_calculator = RiskCalculator()
        self.trade_validator = TradeValidator()
        self.connected = False

    def connect(self, login: int = None, password: str = None, server: str = None, force_reconnect: bool = False) -> bool:
        """
        Connect to MT5.

        Args:
            login: MT5 account number (optional, reads from env if not provided)
            password: MT5 password (optional, reads from env if not provided)
            server: MT5 server (optional, reads from env if not provided)
            force_reconnect: Force shutdown and reconnect even if already connected

        Returns:
            True if connected, False otherwise
        """
        # Read credentials from env if not provided
        if login is None:
            login = os.getenv("MT5_LOGIN")
        if password is None:
            password = os.getenv("MT5_PASSWORD")
        if server is None:
            server = os.getenv("MT5_SERVER")

        # Read MT5 terminal path from env
        mt5_terminal_path = os.getenv("MT5_TERMINAL_PATH")

        # Check if already connected to the same account
        if not force_reconnect:
            try:
                account_info = mt5.account_info()
                if account_info is not None:
                    # Already connected
                    if login is None or int(login) == account_info.login:
                        logger.info(f"✅ Already connected to MT5 account {account_info.login}")
                        self.connected = True
                        return True
                    else:
                        # Connected but to different account, need to switch
                        logger.info(f"Switching from account {account_info.login} to {login}")
                        force_reconnect = True
            except:
                # Not connected or error, proceed with connection
                pass

        # Shutdown if force_reconnect or connection check failed
        if force_reconnect:
            try:
                mt5.shutdown()
                logger.info("MT5 shutdown completed before reconnect")
                import time
                time.sleep(2)  # Wait 2 seconds after shutdown to avoid IPC timeout
            except Exception as e:
                logger.warning(f"Shutdown warning: {e}")

        # Initialize MT5 connection with retry logic
        import time
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(1, max_retries + 1):
            # Initialize with terminal path if provided
            if mt5_terminal_path:
                logger.info(f"Initializing MT5 with terminal path: {mt5_terminal_path}")
                init_result = mt5.initialize(path=mt5_terminal_path)
            else:
                init_result = mt5.initialize()

            if init_result:
                break
            else:
                error = mt5.last_error()
                logger.warning(f"MT5 initialize attempt {attempt}/{max_retries} failed: {error}")

                if attempt < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"MT5 initialize failed after {max_retries} attempts: {error}")
                    return False

        logger.info(f"Connecting to MT5 with Login: {login}, Server: {server}")

        if login and password and server:
            authorized = mt5.login(login=int(login), password=password, server=server)
            if not authorized:
                error_code, error_msg = mt5.last_error()
                logger.error(f"MT5 login failed: ({error_code}) {error_msg}")
                mt5.shutdown()
                return False
            logger.info(f"✅ MT5 logged in successfully with account {login}")
        else:
            logger.info("⚠️  No credentials provided, using existing MT5 session")

        self.connected = True
        logger.info("MT5 connected successfully")
        return True

    def disconnect(self):
        """Disconnect from MT5"""
        mt5.shutdown()
        self.connected = False
        logger.info("MT5 disconnected")

    def is_connected(self) -> bool:
        """
        Check if MT5 is connected and responding.

        Returns:
            True if connected and healthy, False otherwise
        """
        try:
            account_info = mt5.account_info()
            if account_info is None:
                logger.warning("MT5 connection lost - account_info is None")
                self.connected = False
                return False

            # Connection is healthy
            return True
        except Exception as e:
            logger.warning(f"MT5 connection check failed: {e}")
            self.connected = False
            return False

    def ensure_connected(self) -> bool:
        """
        Ensure MT5 is connected, reconnect if needed.

        Returns:
            True if connected (after reconnect if needed), False if failed
        """
        if self.is_connected():
            return True

        logger.warning("MT5 connection lost, attempting to reconnect...")
        return self.connect(force_reconnect=True)

    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """
        Get symbol information from MT5.

        Args:
            symbol: MT5 symbol (e.g., "XAUUSD")

        Returns:
            Dictionary with symbol info or None if not found
        """
        if not self.ensure_connected():
            logger.error("Not connected to MT5")
            return None

        symbol_info = mt5.symbol_info(symbol)

        if symbol_info is None:
            logger.error(f"Symbol {symbol} not found")
            return None

        if not symbol_info.visible:
            # Try to enable symbol in Market Watch
            if not mt5.symbol_select(symbol, True):
                logger.error(f"Failed to select symbol {symbol}")
                return None

        return {
            'name': symbol_info.name,
            'trade_contract_size': symbol_info.trade_contract_size,
            'trade_tick_value': symbol_info.trade_tick_value,
            'trade_tick_size': symbol_info.trade_tick_size,
            'volume_min': symbol_info.volume_min,
            'volume_max': symbol_info.volume_max,
            'volume_step': symbol_info.volume_step,
            'point': symbol_info.point,
            'digits': symbol_info.digits,
            'bid': symbol_info.bid,
            'ask': symbol_info.ask
        }

    def calculate_pip_value(self, symbol_info: Dict) -> float:
        """
        Calculate pip value per lot.

        Args:
            symbol_info: Symbol information from get_symbol_info()

        Returns:
            Pip value in account currency per lot
        """
        # For most symbols: pip_value = tick_value / tick_size
        tick_value = symbol_info['trade_tick_value']
        tick_size = symbol_info['trade_tick_size']

        pip_value = tick_value / tick_size

        return pip_value

    def place_limit_order(
        self,
        symbol: str,
        order_type: str,
        entry_price: float,
        sl_price: float,
        tp_price: float,
        volume: float,
        comment: str = ""
    ) -> Optional[Dict]:
        """
        Place LIMIT order in MT5.

        Args:
            symbol: MT5 symbol
            order_type: "LIMIT_BUY" or "LIMIT_SELL"
            entry_price: Entry price
            sl_price: Stop loss price
            tp_price: Take profit price
            volume: Volume in lots
            comment: Order comment

        Returns:
            Order result dictionary or None if failed
        """
        if not self.ensure_connected():
            logger.error("Not connected to MT5")
            return None

        # Map order type
        if order_type == "LIMIT_BUY":
            mt5_order_type = mt5.ORDER_TYPE_BUY_LIMIT
        elif order_type == "LIMIT_SELL":
            mt5_order_type = mt5.ORDER_TYPE_SELL_LIMIT
        else:
            logger.error(f"Invalid order type: {order_type}")
            return None

        # Build order request
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": volume,
            "type": mt5_order_type,
            "price": entry_price,
            "sl": sl_price,
            "tp": tp_price,
            "deviation": 0,
            "magic": 123456,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        print(f"Order Request: {request}")
        # Send order
        result = mt5.order_send(request)

        if result is None:
            logger.error(f"Order send failed: {mt5.last_error()}")
            return None

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Order failed: {result.retcode} - {result.comment}")
            return None

        logger.info(f"Order placed successfully: Ticket {result.order}")

        return {
            "ticket": result.order,
            "volume": result.volume,
            "price": result.price,
            "retcode": result.retcode,
            "comment": result.comment
        }

    def execute_trade_command(self, command: Dict) -> Dict:
        """
        Execute trade command received from Telegram Bot.

        Args:
            command: Trade command dictionary from TradeCommandBuilder

        Returns:
            Execution result dictionary
        """
        result = {
            "success": False,
            "error": None,
            "ticket": None,
            "execution_price": None
        }

        try:
            # Get symbol info
            symbol = command['symbol']
            symbol_info = self.get_symbol_info(symbol)

            if not symbol_info:
                result["error"] = f"Symbol {symbol} not found in MT5"
                return result

            # Validate trade
            validation = self.trade_validator.validate_trade(
                order_type=command['order_type'],
                entry_price=command['entry'],
                sl_price=command['sl'],
                tp_price=command['tp']
            )

            if not validation['is_valid']:
                result["error"] = validation.get('error', 'Invalid trade parameters')
                return result

            # Recalculate volume with actual MT5 pip value
            pip_value = self.calculate_pip_value(symbol_info)

            volume = self.risk_calculator.calculate_volume(
                risk_usd=command['risk_usd'],
                entry_price=command['entry'],
                sl_price=command['sl'],
                pip_value=pip_value,
                tick_size=symbol_info['trade_tick_size'],
                volume_step=symbol_info['volume_step'],
                min_volume=symbol_info['volume_min'],
                max_volume=symbol_info['volume_max']
            )

            if volume is None:
                result["error"] = "Failed to calculate volume"
                return result

            # Place order
            order_comment = f"{command['emotion']}|{command['setup_code']}"

            order_result = self.place_limit_order(
                symbol=symbol,
                order_type=command['order_type'],
                entry_price=command['entry'],
                sl_price=command['sl'],
                tp_price=command['tp'],
                volume=volume,
                comment=order_comment
            )

            if order_result:
                result["success"] = True
                result["ticket"] = order_result['ticket']
                result["execution_price"] = order_result['price']
                result["volume"] = order_result['volume']
            else:
                result["error"] = "Order placement failed"

        except Exception as e:
            logger.exception("Trade execution error")
            result["error"] = str(e)

        return result

    def get_account_info(self) -> Optional[Dict]:
        """
        Get MT5 account information.

        Returns:
            Account info dictionary
        """
        if not self.ensure_connected():
            return None

        account_info = mt5.account_info()

        if account_info is None:
            return None

        return {
            'login': account_info.login,
            'balance': account_info.balance,
            'equity': account_info.equity,
            'margin': account_info.margin,
            'margin_free': account_info.margin_free,
            'margin_level': account_info.margin_level,
            'profit': account_info.profit,
            'currency': account_info.currency
        }

    def get_pending_orders(self) -> list:
        """
        Get all pending orders (LIMIT BUY/SELL).

        Returns:
            List of pending order dictionaries
        """
        if not self.ensure_connected():
            logger.error("Not connected to MT5")
            return []

        orders = mt5.orders_get()

        if orders is None:
            logger.warning("No pending orders or error fetching orders")
            return []

        pending_orders = []
        for order in orders:
            # Only include LIMIT orders (not STOP orders)
            if order.type in (mt5.ORDER_TYPE_BUY_LIMIT, mt5.ORDER_TYPE_SELL_LIMIT):
                pending_orders.append({
                    'ticket': order.ticket,
                    'symbol': order.symbol,
                    'type': 'BUY LIMIT' if order.type == mt5.ORDER_TYPE_BUY_LIMIT else 'SELL LIMIT',
                    'type_raw': order.type,
                    'volume': order.volume_current,
                    'price_open': order.price_open,
                    'sl': order.sl,
                    'tp': order.tp,
                    'price_current': order.price_current,
                    'time_setup': order.time_setup,
                    'comment': order.comment,
                    'magic': order.magic
                })

        return pending_orders

    def get_order_detail(self, ticket: int) -> Optional[Dict]:
        """
        Get detailed information about a specific order.

        Args:
            ticket: Order ticket number

        Returns:
            Order detail dictionary or None if not found
        """
        if not self.ensure_connected():
            logger.error("Not connected to MT5")
            return None

        orders = mt5.orders_get(ticket=ticket)

        if orders is None or len(orders) == 0:
            logger.warning(f"Order {ticket} not found")
            return None

        order = orders[0]

        # Get symbol info for additional details
        symbol_info = self.get_symbol_info(order.symbol)

        return {
            'ticket': order.ticket,
            'symbol': order.symbol,
            'type': 'BUY LIMIT' if order.type == mt5.ORDER_TYPE_BUY_LIMIT else 'SELL LIMIT',
            'type_raw': order.type,
            'volume': order.volume_current,
            'price_open': order.price_open,
            'sl': order.sl,
            'tp': order.tp,
            'price_current': order.price_current,
            'time_setup': order.time_setup,
            'time_setup_msc': order.time_setup_msc,
            'comment': order.comment,
            'magic': order.magic,
            'state': order.state,
            'symbol_info': symbol_info
        }

    def close_pending_order(self, ticket: int) -> Dict:
        """
        Close (delete) a pending order.

        Args:
            ticket: Order ticket number

        Returns:
            Result dictionary with success status and message
        """
        result = {
            "success": False,
            "error": None,
            "ticket": ticket
        }

        if not self.ensure_connected():
            result["error"] = "Not connected to MT5"
            return result

        # Get order details first
        order_detail = self.get_order_detail(ticket)

        if not order_detail:
            result["error"] = f"Order {ticket} not found"
            return result

        # Build close request
        request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": ticket,
            "comment": "Closed via Telegram Bot"
        }

        # Send close request
        close_result = mt5.order_send(request)

        if close_result is None:
            error = mt5.last_error()
            result["error"] = f"Close failed: {error}"
            logger.error(f"Failed to close order {ticket}: {error}")
            return result

        if close_result.retcode != mt5.TRADE_RETCODE_DONE:
            result["error"] = f"Close failed: {close_result.retcode} - {close_result.comment}"
            logger.error(f"Order {ticket} close failed: {close_result.retcode}")
            return result

        result["success"] = True
        result["message"] = f"Order {ticket} closed successfully"
        logger.info(f"Order {ticket} closed successfully")

        return result


# Example usage
if __name__ == "__main__":
    # Initialize adapter
    adapter = MT5Adapter()

    # Connect to MT5
    connected = adapter.connect()

    if connected:
        # Get account info
        account = adapter.get_account_info()
        print(f"Account: {account}")

        # Example trade command (from Telegram Bot)
        trade_command = {
            "user_id": 12345,
            "account_id": 1,
            "order_type": "LIMIT_BUY",
            "symbol": "XAUUSD",
            "entry": 2000.00,
            "sl": 1995.00,
            "tp": 2015.00,
            "volume": 0.10,
            "risk_usd": 50.00,
            "emotion": "calm",
            "setup_code": "FZ1",
            "chart_url": None,
            "created_at": datetime.utcnow().isoformat()
        }

        # Execute trade
        result = adapter.execute_trade_command(trade_command)
        print(f"Trade result: {result}")

        # Disconnect
        adapter.disconnect()
