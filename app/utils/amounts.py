import re
from decimal import Decimal, InvalidOperation

_AMOUNT_CLEAN_RE = re.compile(r"[^\d.\-+,]")


def parse_amount(value: str | None) -> Decimal | None:
    if value is None:
        return None
    text = value.strip()
    if not text or text in {"-", "--", "—"}:
        return None

    # HDFC/Indian statements sometimes encode debit/credit as "Dr"/"Cr"
    # suffix/prefix on a single amount column (e.g. "500.00 Dr").
    sign = Decimal("1")
    m_suffix = re.search(r"(?:dr|cr)\.?\s*$", text, flags=re.IGNORECASE)
    if m_suffix:
        token = m_suffix.group(0).strip().lower().replace(".", "")
        sign = Decimal("-1") if token == "dr" else Decimal("1")
        text = re.sub(r"\s*(?:dr|cr)\.?\s*$", "", text, flags=re.IGNORECASE)
    else:
        m_prefix = re.search(r"^\s*(?:dr|cr)\.?\s*", text, flags=re.IGNORECASE)
        if m_prefix:
            token = m_prefix.group(0).strip().lower().replace(".", "")
            # token could still include whitespace; normalize
            token = token.split()[0] if token else token
            sign = Decimal("-1") if token == "dr" else Decimal("1")
            text = re.sub(r"^\s*(?:dr|cr)\.?\s*", "", text, flags=re.IGNORECASE)

    text = _AMOUNT_CLEAN_RE.sub("", text)
    if not text or text in {".", "-", "+"}:
        return None
    # Indian numbering: 1,23,456.78
    text = text.replace(",", "")
    try:
        amount = Decimal(text)
        # Normalize sign: if Dr/Cr token exists, force absolute value with sign.
        return sign * abs(amount)
    except InvalidOperation:
        return None


def is_amount_like(value: str) -> bool:
    return parse_amount(value) is not None
