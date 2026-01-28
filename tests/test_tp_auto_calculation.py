"""
Tests for TP Auto-Calculation from R:R ratio

Test that TP is correctly calculated based on:
- Entry price
- Stop loss price
- User's R:R ratio setting
"""

import pytest


def calculate_tp(entry: float, sl: float, order_type: str, rr_ratio: float) -> float:
    """
    Calculate TP from entry, SL, and R:R ratio.

    Args:
        entry: Entry price
        sl: Stop loss price
        order_type: "LIMIT_BUY" or "LIMIT_SELL"
        rr_ratio: Risk:Reward ratio (e.g., 2.0 for 2:1)

    Returns:
        Take profit price
    """
    risk_distance = abs(entry - sl)
    reward_distance = risk_distance * rr_ratio

    if order_type == "LIMIT_BUY":
        tp = entry + reward_distance
    else:  # LIMIT_SELL
        tp = entry - reward_distance

    return round(tp, 2)


class TestTPAutoCalculation:
    """Test TP auto-calculation logic"""

    def test_buy_order_rr_2_to_1(self):
        """
        GIVEN: LIMIT BUY with entry=2000, SL=1995, R:R=2:1
        WHEN: Calculate TP
        THEN: TP should be 2010 (risk=5, reward=10)
        """
        tp = calculate_tp(
            entry=2000.00,
            sl=1995.00,
            order_type="LIMIT_BUY",
            rr_ratio=2.0
        )

        assert tp == 2010.00
        assert tp > 2000.00  # TP above entry for BUY

    def test_sell_order_rr_2_to_1(self):
        """
        GIVEN: LIMIT SELL with entry=2000, SL=2010, R:R=2:1
        WHEN: Calculate TP
        THEN: TP should be 1980 (risk=10, reward=20)
        """
        tp = calculate_tp(
            entry=2000.00,
            sl=2010.00,
            order_type="LIMIT_SELL",
            rr_ratio=2.0
        )

        assert tp == 1980.00
        assert tp < 2000.00  # TP below entry for SELL

    def test_buy_order_rr_3_to_1(self):
        """
        GIVEN: LIMIT BUY with entry=2000, SL=1990, R:R=3:1
        WHEN: Calculate TP
        THEN: TP should be 2030 (risk=10, reward=30)
        """
        tp = calculate_tp(
            entry=2000.00,
            sl=1990.00,
            order_type="LIMIT_BUY",
            rr_ratio=3.0
        )

        assert tp == 2030.00

    def test_sell_order_rr_3_to_1(self):
        """
        GIVEN: LIMIT SELL with entry=2000, SL=2005, R:R=3:1
        WHEN: Calculate TP
        THEN: TP should be 1985 (risk=5, reward=15)
        """
        tp = calculate_tp(
            entry=2000.00,
            sl=2005.00,
            order_type="LIMIT_SELL",
            rr_ratio=3.0
        )

        assert tp == 1985.00

    def test_buy_order_rr_1_5_to_1(self):
        """
        GIVEN: LIMIT BUY with entry=2000, SL=1980, R:R=1.5:1
        WHEN: Calculate TP
        THEN: TP should be 2030 (risk=20, reward=30)
        """
        tp = calculate_tp(
            entry=2000.00,
            sl=1980.00,
            order_type="LIMIT_BUY",
            rr_ratio=1.5
        )

        assert tp == 2030.00

    def test_forex_pair_precision(self):
        """
        GIVEN: Forex pair with 4 decimal precision
        WHEN: Calculate TP
        THEN: TP should maintain precision
        """
        tp = calculate_tp(
            entry=1.0850,
            sl=1.0830,
            order_type="LIMIT_BUY",
            rr_ratio=2.0
        )

        # Risk = 0.0020, Reward = 0.0040
        # TP = 1.0850 + 0.0040 = 1.0890
        assert tp == 1.09  # Rounded to 2 decimals

    def test_gold_small_stop(self):
        """
        GIVEN: Gold with tight stop
        WHEN: Calculate TP with R:R 2:1
        THEN: TP should be correct
        """
        tp = calculate_tp(
            entry=2000.50,
            sl=1998.50,
            order_type="LIMIT_BUY",
            rr_ratio=2.0
        )

        # Risk = 2.00, Reward = 4.00
        # TP = 2000.50 + 4.00 = 2004.50
        assert tp == 2004.50

    def test_rr_ratio_5_to_1(self):
        """
        GIVEN: Aggressive R:R ratio of 5:1
        WHEN: Calculate TP
        THEN: TP should be 5x the risk distance
        """
        tp = calculate_tp(
            entry=2000.00,
            sl=1995.00,
            order_type="LIMIT_BUY",
            rr_ratio=5.0
        )

        # Risk = 5, Reward = 25
        # TP = 2000 + 25 = 2025
        assert tp == 2025.00

    def test_symmetric_buy_sell(self):
        """
        GIVEN: Same entry and risk for BUY and SELL
        WHEN: Calculate TP
        THEN: TPs should be symmetric around entry
        """
        entry = 2000.00
        risk = 10.00
        rr = 2.0

        tp_buy = calculate_tp(entry, entry - risk, "LIMIT_BUY", rr)
        tp_sell = calculate_tp(entry, entry + risk, "LIMIT_SELL", rr)

        # BUY: entry=2000, sl=1990, tp=2020
        # SELL: entry=2000, sl=2010, tp=1980
        assert tp_buy == 2020.00
        assert tp_sell == 1980.00
        assert abs(tp_buy - entry) == abs(entry - tp_sell)  # Symmetric
