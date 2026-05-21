"""Utility functions for the Wardrop backend."""

from datetime import datetime, timezone, timedelta

# Brasília timezone (UTC-3)
BRT = timezone(timedelta(hours=-3))


def now_brasilia() -> datetime:
    """Return current datetime in Brasília timezone (naive, without tzinfo).

    Returns a naive datetime so PostgreSQL stores it as-is without conversion.
    """
    return datetime.now(BRT).replace(tzinfo=None)
