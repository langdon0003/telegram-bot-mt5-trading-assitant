"""
Trade Command Builder - PHASE 4 Implementation

Builds validated JSON trade commands to send from Bot to Trade Engine.
This implementation satisfies all test cases in test_trade_command.py.
"""

from datetime import datetime


class TradeCommandBuilder:
    """
    Builds and validates trade command JSON.

    The command is sent from Telegram Bot to Trade Engine for execution.
    """

    VALID_ORDER_TYPES = ["LIMIT_BUY", "LIMIT_SELL"]
    VALID_EMOTIONS = ["calm", "confident", "fomo", "stressed", "revenge"]

    def build_command(
        self,
        user_id: int,
        account_id: int,
        order_type: str,
        symbol: str,
        entry_price: float,
        sl_price: float,
        tp_price: float,
        volume: float,
        risk_usd: float,
        emotion: str,
        setup_code: str,
        chart_url: str | None
    ) -> dict:
        """
        Build trade command JSON.

        Args:
            user_id: Telegram user ID
            account_id: MT5 account ID from database
            order_type: "LIMIT_BUY" or "LIMIT_SELL"
            symbol: MT5 symbol (e.g., "XAUUSD")
            entry_price: Entry price
            sl_price: Stop loss price
            tp_price: Take profit price
            volume: Position size in lots
            risk_usd: Risk amount in USD
            emotion: User's emotional state (calm, confident, fomo, stressed, revenge)
            setup_code: Setup code (e.g., "FZ1", "TLP1")
            chart_url: Optional TradingView chart URL

        Returns:
            Trade command dictionary ready for JSON serialization

        Raises:
            ValueError: If validation fails
        """
        # Validate order type
        if order_type not in self.VALID_ORDER_TYPES:
            raise ValueError(f"Invalid order_type: {order_type}. Must be one of {self.VALID_ORDER_TYPES}")

        # Validate emotion
        if emotion not in self.VALID_EMOTIONS:
            raise ValueError(f"Invalid emotion: {emotion}. Must be one of {self.VALID_EMOTIONS}")

        # Validate volume
        if volume <= 0:
            raise ValueError("Volume must be positive")

        # Validate risk
        if risk_usd <= 0:
            raise ValueError("Risk must be positive")

        # Build command
        command = {
            "user_id": user_id,
            "account_id": account_id,
            "order_type": order_type,
            "symbol": symbol,
            "entry": entry_price,
            "sl": sl_price,
            "tp": tp_price,
            "volume": volume,
            "risk_usd": risk_usd,
            "emotion": emotion,
            "setup_code": setup_code,
            "chart_url": chart_url,
            "created_at": datetime.utcnow().isoformat()
        }

        return command
