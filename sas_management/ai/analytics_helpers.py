"""
SAS AI Analytics Helpers - Shared utilities for data validation and forecasting.
"""


def require_min_records(count: int, min_required: int = 5) -> tuple:
    """
    Validate that sufficient historical data exists for analysis.
    
    Args:
        count: Number of records available
        min_required: Minimum records required (default: 5)
    
    Returns:
        tuple: (is_valid, error_message)
        - is_valid: True if count >= min_required, False otherwise
        - error_message: None if valid, error message string if invalid
    """
    if count < min_required:
        return False, (
            f"⚠️ Not enough historical data to perform analysis.\n\n"
            f"Required: {min_required}, Available: {count}.\n\n"
            f"Please ensure you have sufficient data before requesting forecasts."
        )
    return True, None


def format_forecast_disclaimer() -> str:
    """
    Return standard disclaimer for all forecasts.
    
    Returns:
        Disclaimer text explaining forecast limitations
    """
    return (
        "\n\n**Note:** This is an estimate based on historical data. "
        "Actual results may vary based on market conditions, seasonal factors, "
        "and other variables not captured in the analysis."
    )

