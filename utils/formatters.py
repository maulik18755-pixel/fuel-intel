"""Formatting helpers for Indian currency, numbers, and display."""


def format_inr_cr(value_cr: float) -> str:
    """Format a value in ₹ Crores."""
    if abs(value_cr) >= 1000:
        return f"₹{value_cr:,.0f} Cr"
    elif abs(value_cr) >= 1:
        return f"₹{value_cr:.1f} Cr"
    else:
        lakhs = value_cr * 100
        return f"₹{lakhs:.0f} L"


def format_indian_number(n: int) -> str:
    """Format large numbers with Indian abbreviations."""
    if n >= 10_000_000:
        return f"{n / 10_000_000:.1f} Cr"
    elif n >= 100_000:
        return f"{n / 100_000:.1f} L"
    elif n >= 1000:
        return f"{n / 1000:.1f}K"
    return str(n)


def score_color(score: int) -> str:
    if score >= 70:
        return "#059669"
    elif score >= 45:
        return "#D97706"
    return "#DC2626"


def score_bg(score: int) -> str:
    if score >= 70:
        return "#D1FAE5"
    elif score >= 45:
        return "#FEF3C7"
    return "#FEE2E2"


def score_tier_label(score: int) -> str:
    if score >= 70:
        return "High Potential"
    elif score >= 45:
        return "Moderate"
    return "Low Potential"
