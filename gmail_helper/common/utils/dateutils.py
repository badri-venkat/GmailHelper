from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


def to_utc_iso(dt) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def parse_rfc2822_to_iso(date_header: str) -> str:
    """
    Gmail 'Date' header is typically RFC2822. Convert to UTC ISO8601.
    Falls back to current UTC if parsing fails.
    """
    try:
        dt = parsedate_to_datetime(date_header)
        return to_utc_iso(dt)
    except Exception:
        return to_utc_iso(datetime.utcnow())
