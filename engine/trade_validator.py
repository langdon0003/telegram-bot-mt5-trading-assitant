"""
Trade Validator - PHASE 4 Implementation

Validates trade parameters and calculates R:R ratio.
This implementation satisfies all test cases in test_trade_validator.py.

Critical Rules:
- LIMIT BUY: Stop Loss MUST be < Entry Price
- LIMIT SELL: Stop Loss MUST be > Entry Price
"""


class TradeValidator:
    """
    Validates trade setup and calculates risk:reward metrics.

    Enforces discipline by validating SL position relative to entry.
    """

    def validate_sl_position(
        self,
        order_type: str,
        entry_price: float,
        sl_price: float
    ) -> bool:
        """
        Validate stop loss position based on order type.

        Args:
            order_type: "LIMIT_BUY" or "LIMIT_SELL"
            entry_price: Entry price
            sl_price: Stop loss price

        Returns:
            True if SL position is valid, False otherwise

        Rules:
        - LIMIT_BUY: SL must be strictly < entry
        - LIMIT_SELL: SL must be strictly > entry
        - SL cannot equal entry (no risk management)
        """
        if order_type == "LIMIT_BUY":
            # For BUY: SL must be below entry
            return sl_price < entry_price

        elif order_type == "LIMIT_SELL":
            # For SELL: SL must be above entry
            return sl_price > entry_price

        else:
            return False

    def calculate_rr_ratio(
        self,
        order_type: str,
        entry_price: float,
        sl_price: float,
        tp_price: float
    ) -> float:
        """
        Calculate Risk:Reward ratio.

        Args:
            order_type: "LIMIT_BUY" or "LIMIT_SELL"
            entry_price: Entry price
            sl_price: Stop loss price
            tp_price: Take profit price

        Returns:
            R:R ratio (reward / risk)

        Formula:
        - Risk = |entry - sl|
        - Reward = |tp - entry|
        - R:R = Reward / Risk
        """
        risk = abs(entry_price - sl_price)
        reward = abs(tp_price - entry_price)

        if risk == 0:
            return 0.0

        # For BUY: if TP < entry, reward is negative
        # For SELL: if TP > entry, reward is negative
        if order_type == "LIMIT_BUY":
            if tp_price < entry_price:
                reward = -(entry_price - tp_price)
        elif order_type == "LIMIT_SELL":
            if tp_price > entry_price:
                reward = -(tp_price - entry_price)

        rr_ratio = reward / risk

        return round(rr_ratio, 2)

    def validate_trade(
        self,
        order_type: str,
        entry_price: float,
        sl_price: float,
        tp_price: float
    ) -> dict:
        """
        Perform full trade validation and return detailed results.

        Args:
            order_type: "LIMIT_BUY" or "LIMIT_SELL"
            entry_price: Entry price
            sl_price: Stop loss price
            tp_price: Take profit price

        Returns:
            Dictionary with validation results:
            {
                "is_valid": bool,
                "sl_valid": bool,
                "rr_ratio": float,
                "risk_pips": float,
                "reward_pips": float,
                "error": str (if invalid)
            }
        """
        result = {
            "is_valid": False,
            "sl_valid": False,
            "rr_ratio": 0.0,
            "risk_pips": 0.0,
            "reward_pips": 0.0
        }

        # Validate SL position
        sl_valid = self.validate_sl_position(order_type, entry_price, sl_price)
        result["sl_valid"] = sl_valid

        if not sl_valid:
            if order_type == "LIMIT_BUY":
                result["error"] = "For LIMIT BUY, stop loss must be below entry price"
            elif order_type == "LIMIT_SELL":
                result["error"] = "For LIMIT SELL, stop loss must be above entry price"
            else:
                result["error"] = "Invalid order type"
            return result

        # Calculate R:R ratio
        rr_ratio = self.calculate_rr_ratio(order_type, entry_price, sl_price, tp_price)
        result["rr_ratio"] = rr_ratio

        # Calculate risk and reward in pips/points
        result["risk_pips"] = abs(entry_price - sl_price)
        result["reward_pips"] = abs(tp_price - entry_price)

        # Mark as valid
        result["is_valid"] = True

        return result
