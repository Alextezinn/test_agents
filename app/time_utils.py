"""Time helpers: ISO 8601 parsing, reservation duration."""
from datetime import datetime, timedelta

RESERVATION_DURATION_HOURS = 2


def parse_iso8601(value: str) -> datetime:
    """Parse an ISO 8601 string; the trailing 'Z' (UTC) is also accepted."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
