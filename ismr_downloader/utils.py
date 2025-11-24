from datetime import datetime, timedelta
from typing import Iterator, Tuple


def daterange_chunks(
    start: datetime, end: datetime, max_days: int = 62
) -> Iterator[Tuple[datetime, datetime]]:
    """
    Yield chunks between start and end with at most `max_days` each.
    Always ensures non-overlapping ranges.
    """
    current = start
    while current < end:
        chunk_end = min(current + timedelta(days=max_days), end)
        yield current, chunk_end
        current = chunk_end + timedelta(days=1)


def normalize_datetime(dt_str: str, is_start: bool) -> datetime:
    """
    Normalizes user-provided date/time strings.

    Supported formats:
    - '2025-11-17'            → expands to full-day bounds (00:00:00 or 23:59:59)
    - '2025-11-17T05:30:00'   → uses the exact timestamp provided
    """
    try:
        dt = datetime.fromisoformat(dt_str)

        if "T" not in dt_str:
            if is_start:
                return dt.replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                return dt.replace(hour=23, minute=59, second=59, microsecond=0)
        return dt
    except ValueError:
        pass

    date = datetime.strptime(dt_str, "%Y-%m-%d")
    if is_start:
        return datetime.combine(date, datetime.min.time())
    else:
        return datetime.combine(date, datetime.max.time().replace(microsecond=0))
