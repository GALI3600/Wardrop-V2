from enum import Enum
from datetime import datetime, timedelta


class Timeframe(str, Enum):
    DAY = "dia"
    WEEK = "semana"
    MONTH = "mes"
    ALL = "sempre"


def get_cutoff_date(timeframe: Timeframe) -> datetime | None:
    """Returns the cutoff date for filtering. None = no limit (ALL)."""
    if timeframe == Timeframe.ALL:
        return None

    now = datetime.utcnow()
    if timeframe == Timeframe.DAY:
        return now - timedelta(days=1)
    elif timeframe == Timeframe.WEEK:
        return now - timedelta(weeks=1)
    elif timeframe == Timeframe.MONTH:
        return now - timedelta(days=30)

    return None
