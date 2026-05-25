import re
from decimal import Decimal, InvalidOperation

_AMOUNT_CLEAN_RE = re.compile(r"[^\d.\-+,]")


def parse_amount(value: str | None) -> Decimal | None:
    if value is None:
        return None
    text = value.strip()
    if not text or text in {"-", "--", "—"}:
        return None
    # HDFC / Indian statements sometimes suffix Dr/Cr
    text = re.sub(r"\s*(?:dr|cr)\.?\s*$", "", text, flags=re.IGNORECASE)
    text = _AMOUNT_CLEAN_RE.sub("", text)
    if not text or text in {".", "-", "+"}:
        return None
    # Indian numbering: 1,23,456.78
    text = text.replace(",", "")
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def is_amount_like(value: str) -> bool:
    return parse_amount(value) is not None
