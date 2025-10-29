"""
Shared utility functions for data layer operations.
"""
import re


def sanitize_string(value: str) -> str:
    """
    Sanitize string input by stripping whitespace and normalizing spaces.
    Collapses multiple consecutive spaces into a single space.
    Returns normalized string.
    
    Examples:
        "  New York  " -> "New York"
        "New  York" -> "New York"
    """
    if not isinstance(value, str):
        return value
    # Strip leading/trailing whitespace and collapse multiple spaces to single space
    return re.sub(r'\s+', ' ', value.strip())


def sanitize_code(value: str) -> str:
    """
    Sanitize code input by stripping whitespace and converting to uppercase.
    Used for country_code, state_code, etc.
    
    Examples:
        " us " -> "US"
        "ny" -> "NY"
    """
    if not isinstance(value, str):
        return value
    return value.strip().upper()

