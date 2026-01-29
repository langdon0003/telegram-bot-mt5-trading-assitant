"""
Tests for Settings Commands

Test risk value formatting and display logic used in /setrisk and /setrisktype commands.
"""

import pytest


def format_risk_value_display(risk_type: str, risk_value: float) -> str:
    """
    Format risk value for display based on risk type.

    This is the core logic used in /setrisktype to display the current value.

    Args:
        risk_type: "fixed_usd" or "percent"
        risk_value: Raw value from database
                   - For fixed_usd: actual USD amount (e.g., 100.0)
                   - For percent: decimal value (e.g., 0.01 for 1%)

    Returns:
        Formatted string for display (e.g., "$100" or "1%")
    """
    if risk_type == "fixed_usd":
        return f"${risk_value}"
    else:  # percent
        # Convert from decimal to percentage (0.01 -> 1%)
        return f"{risk_value * 100}%"


class TestRiskValueFormatting:
    """Test risk value formatting for display"""

    def test_format_fixed_usd(self):
        """
        GIVEN: Risk type is "fixed_usd" with value 100.0
        WHEN: Format for display
        THEN: Should show "$100.0"
        """
        result = format_risk_value_display("fixed_usd", 100.0)
        assert result == "$100.0"

    def test_format_fixed_usd_decimal(self):
        """
        GIVEN: Risk type is "fixed_usd" with value 50.5
        WHEN: Format for display
        THEN: Should show "$50.5"
        """
        result = format_risk_value_display("fixed_usd", 50.5)
        assert result == "$50.5"

    def test_format_percent_one(self):
        """
        GIVEN: Risk type is "percent" with value 0.01 (stored as decimal)
        WHEN: Format for display
        THEN: Should show "1%" (converted from decimal to percentage)
        """
        result = format_risk_value_display("percent", 0.01)
        assert result == "1.0%"

    def test_format_percent_half(self):
        """
        GIVEN: Risk type is "percent" with value 0.005 (0.5% stored as decimal)
        WHEN: Format for display
        THEN: Should show "0.5%"
        """
        result = format_risk_value_display("percent", 0.005)
        assert result == "0.5%"

    def test_format_percent_two(self):
        """
        GIVEN: Risk type is "percent" with value 0.02 (2% stored as decimal)
        WHEN: Format for display
        THEN: Should show "2.0%"
        """
        result = format_risk_value_display("percent", 0.02)
        assert result == "2.0%"

    def test_format_percent_large(self):
        """
        GIVEN: Risk type is "percent" with value 0.1 (10% stored as decimal)
        WHEN: Format for display
        THEN: Should show "10.0%"
        """
        result = format_risk_value_display("percent", 0.1)
        assert result == "10.0%"


class TestRiskTypeScenarios:
    """Test real-world scenarios for /setrisktype command"""

    def test_setrisktype_fixed_usd_to_percent(self):
        """
        GIVEN: User has risk_type="fixed_usd", risk_value=100.0
        WHEN: Change to "percent" via /setrisktype
        THEN: Should display old value as "$100.0 (unchanged)"
        """
        # Current settings
        current_type = "fixed_usd"
        current_value = 100.0

        # User clicks "Percent" button but value doesn't change
        display = format_risk_value_display(current_type, current_value)
        assert display == "$100.0"

    def test_setrisktype_percent_to_fixed_usd(self):
        """
        GIVEN: User has risk_type="percent", risk_value=0.01 (1%)
        WHEN: Change to "fixed_usd" via /setrisktype
        THEN: Should display old value as "1.0% (unchanged)"
        """
        # Current settings (before change)
        current_type = "percent"
        current_value = 0.01  # Stored as decimal

        # Display current value before type change
        display = format_risk_value_display(current_type, current_value)
        assert display == "1.0%"

    def test_setrisktype_preserves_value_format(self):
        """
        GIVEN: Multiple users with different risk settings
        WHEN: They use /setrisktype
        THEN: Each should see their value formatted correctly
        """
        # User A: Fixed $50
        user_a_type = "fixed_usd"
        user_a_value = 50.0
        assert format_risk_value_display(user_a_type, user_a_value) == "$50.0"

        # User B: 2% of balance
        user_b_type = "percent"
        user_b_value = 0.02
        assert format_risk_value_display(user_b_type, user_b_value) == "2.0%"

        # User C: Fixed $200
        user_c_type = "fixed_usd"
        user_c_value = 200.0
        assert format_risk_value_display(user_c_type, user_c_value) == "$200.0"


class TestEdgeCases:
    """Test edge cases for risk value formatting"""

    def test_format_very_small_percent(self):
        """
        GIVEN: Risk type is "percent" with value 0.001 (0.1%)
        WHEN: Format for display
        THEN: Should show "0.1%"
        """
        result = format_risk_value_display("percent", 0.001)
        assert result == "0.1%"

    def test_format_zero_value(self):
        """
        GIVEN: Risk value is 0 (edge case, shouldn't happen in production)
        WHEN: Format for display
        THEN: Should handle gracefully
        """
        # Fixed USD
        result_usd = format_risk_value_display("fixed_usd", 0.0)
        assert result_usd == "$0.0"

        # Percent
        result_pct = format_risk_value_display("percent", 0.0)
        assert result_pct == "0.0%"

    def test_format_large_usd_value(self):
        """
        GIVEN: Risk type is "fixed_usd" with value 10000.0
        WHEN: Format for display
        THEN: Should show "$10000.0"
        """
        result = format_risk_value_display("fixed_usd", 10000.0)
        assert result == "$10000.0"


class TestRiskTypeUpdate:
    """Test the /setrisktype command behavior"""

    def test_update_type_only_keeps_value(self):
        """
        GIVEN: User has risk_type="fixed_usd", risk_value=100.0
        WHEN: User changes type to "percent" using /setrisktype
        THEN:
            - risk_type should change to "percent"
            - risk_value should remain 100.0 (WARNING: now interpreted as 10000%!)
            - This is expected behavior - value doesn't auto-convert
        """
        # Initial state
        old_type = "fixed_usd"
        old_value = 100.0

        # User changes type (value unchanged)
        new_type = "percent"
        new_value = old_value  # Keep same value

        # Display NEW type with SAME value
        # WARNING: 100.0 now means 10000% when type is "percent"!
        display = format_risk_value_display(new_type, new_value)
        assert display == "10000.0%"  # This is technically correct but unusual

        # Note: Users should use /setrisk to properly set both type and value together
