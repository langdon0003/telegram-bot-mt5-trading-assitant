"""
Database Manager

Handles SQLite database initialization and operations.
"""

import sqlite3
from pathlib import Path


class DatabaseManager:
    """Manages SQLite database connection and initialization"""

    def __init__(self, db_path: str = "trading_bot.db"):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access
        return self.conn

    def initialize_schema(self):
        """Create tables from schema.sql if they don't exist"""
        schema_path = Path(__file__).parent / "schema.sql"

        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        cursor = self.conn.cursor()
        cursor.executescript(schema_sql)
        self.conn.commit()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get_user_by_telegram_id(self, telegram_id: int):
        """Get user by Telegram ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        return cursor.fetchone()

    def create_user(self, telegram_id: int, username: str = None,
                    first_name: str = None, last_name: str = None):
        """Create new user"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO users (telegram_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
            (telegram_id, username, first_name, last_name)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_user_settings(self, user_id: int):
        """Get user settings"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
        return cursor.fetchone()

    def create_default_settings(self, user_id: int):
        """Create default settings for new user"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO user_settings (user_id) VALUES (?)",
            (user_id,)
        )
        self.conn.commit()

    def update_user_settings(self, user_id: int, **kwargs):
        """Update user settings"""
        valid_fields = [
            'default_symbol_base', 'symbol_prefix', 'symbol_suffix',
            'default_order_type', 'risk_type', 'risk_value', 'default_rr_ratio', 'default_account_id'
        ]

        updates = {k: v for k, v in kwargs.items() if k in valid_fields}

        if not updates:
            return

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values())
        values.append(user_id)

        cursor = self.conn.cursor()
        cursor.execute(
            f"UPDATE user_settings SET {set_clause} WHERE user_id = ?",
            values
        )
        self.conn.commit()

    def get_user_setups(self, user_id: int, active_only: bool = True):
        """Get user's trade setups"""
        cursor = self.conn.cursor()

        if active_only:
            cursor.execute(
                "SELECT * FROM setups WHERE user_id = ? AND is_active = 1",
                (user_id,)
            )
        else:
            cursor.execute("SELECT * FROM setups WHERE user_id = ?", (user_id,))

        return cursor.fetchall()

    def create_setup(self, user_id: int, setup_code: str,
                    setup_name: str, description: str = None):
        """Create new trade setup"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO setups (user_id, setup_code, setup_name, description) VALUES (?, ?, ?, ?)",
            (user_id, setup_code, setup_name, description)
        )
        self.conn.commit()
        return cursor.lastrowid

    def create_trade(self, **kwargs):
        """
        Create new trade record.

        Required kwargs:
        - user_id, account_id, symbol, order_type, entry, sl, tp,
          volume, risk_usd, emotion, setup_code
        """
        required_fields = [
            'user_id', 'account_id', 'symbol', 'order_type', 'entry',
            'sl', 'tp', 'volume', 'risk_usd', 'emotion', 'setup_code'
        ]

        for field in required_fields:
            if field not in kwargs:
                raise ValueError(f"Missing required field: {field}")

        fields = list(kwargs.keys())
        placeholders = ", ".join(["?" for _ in fields])
        field_names = ", ".join(fields)

        cursor = self.conn.cursor()
        cursor.execute(
            f"INSERT INTO trades ({field_names}) VALUES ({placeholders})",
            list(kwargs.values())
        )
        self.conn.commit()
        return cursor.lastrowid

    def update_trade(self, trade_id: int, **kwargs):
        """Update trade record"""
        if not kwargs:
            return

        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values())
        values.append(trade_id)

        cursor = self.conn.cursor()
        cursor.execute(
            f"UPDATE trades SET {set_clause} WHERE id = ?",
            values
        )
        self.conn.commit()

    def update_trade_status(
        self,
        trade_id: int,
        status: str,
        mt5_ticket: int = None,
        mt5_open_price: float = None,
        mt5_open_time: str = None,
        mt5_close_price: float = None,
        mt5_close_time: str = None,
        mt5_profit: float = None
    ):
        """
        Update trade execution status.

        Args:
            trade_id: Trade ID
            status: Trade status ('pending', 'filled', 'closed', 'cancelled', 'failed')
            mt5_ticket: MT5 order ticket number
            mt5_open_price: Actual MT5 open price
            mt5_open_time: MT5 open timestamp
            mt5_close_price: MT5 close price
            mt5_close_time: MT5 close timestamp
            mt5_profit: MT5 profit/loss
        """
        updates = {'status': status, 'updated_at': 'CURRENT_TIMESTAMP'}

        if mt5_ticket is not None:
            updates['mt5_ticket'] = mt5_ticket
        if mt5_open_price is not None:
            updates['mt5_open_price'] = mt5_open_price
        if mt5_open_time is not None:
            updates['mt5_open_time'] = mt5_open_time
        if mt5_close_price is not None:
            updates['mt5_close_price'] = mt5_close_price
        if mt5_close_time is not None:
            updates['mt5_close_time'] = mt5_close_time
        if mt5_profit is not None:
            updates['mt5_profit'] = mt5_profit

        self.update_trade(trade_id, **updates)
