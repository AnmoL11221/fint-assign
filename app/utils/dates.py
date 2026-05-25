import re
from datetime import date, datetime

_DATE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^(\d{2})[/-](\d{2})[/-](\d{4})$"), "dmy"),
    (re.compile(r"^(\d{2})[/-](\d{2})[/-](\d{2})$"), "dmy_short"),
    (re.compile(r"^(\d{4})[/-](\d{2})[/-](\d{2})$"), "ymd"),
    (re.compile(r"^(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})$"), "d_mon_y"),
    (re.compile(r"^(\d{1,2})-([A-Za-z]{3})-(\d{2,4})$"), "d_mon_y_dash"),
]

_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None

    for pattern, fmt in _DATE_PATTERNS:
        match = pattern.match(text)
        if not match:
            continue
        groups = match.groups()
        try:
            if fmt == "dmy":
                d, m, y = int(groups[0]), int(groups[1]), int(groups[2])
                return date(y, m, d)
            if fmt == "dmy_short":
                d, m, y = int(groups[0]), int(groups[1]), int(groups[2])
                y += 2000 if y < 100 else 0
                return date(y, m, d)
            if fmt == "ymd":
                y, m, d = int(groups[0]), int(groups[1]), int(groups[2])
                return date(y, m, d)
            if fmt in {"d_mon_y", "d_mon_y_dash"}:
                d = int(groups[0])
                mon = _MONTHS.get(groups[1].lower()[:3])
                y = int(groups[2])
                if y < 100:
                    y += 2000
                if mon:
                    return date(y, mon, d)
        except (ValueError, TypeError):
            continue
    return None


def format_date_iso(d: date | None) -> str:
    return d.isoformat() if d else ""


def is_date_like(value: str) -> bool:
    return parse_date(value) is not None
