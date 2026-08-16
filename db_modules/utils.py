"""
Utility and helper functions module.
"""

from .connection import conn, cursor


def format_gold(amount):
    try:
        amount = float(amount)
    except Exception:
        amount = 0.0

    GOLD_ICON = "💰"
    GOLD_NAME = "золото"
    
    return f"{amount:.2f} {GOLD_ICON} {GOLD_NAME}"


def get_today_str():
    from datetime import date
    return date.today().isoformat()


def get_daily_today_str():
    from datetime import date
    return date.today().isoformat()
