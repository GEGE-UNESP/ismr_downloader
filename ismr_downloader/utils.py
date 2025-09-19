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
