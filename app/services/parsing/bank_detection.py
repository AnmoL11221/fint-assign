import re
from enum import Enum

from app.services.pdf_extraction import PdfExtractionResult


class BankCode(str, Enum):
    HDFC = "hdfc"
    SBI = "sbi"
    ICICI = "icici"
    GENERIC = "generic"


_BANK_PATTERNS: list[tuple[BankCode, re.Pattern[str]]] = [
    (BankCode.HDFC, re.compile(r"\bHDFC\s*Bank\b", re.I)),
    (BankCode.SBI, re.compile(r"\bState\s*Bank\s*of\s*India\b|\bSBI\b", re.I)),
    (BankCode.ICICI, re.compile(r"\bICICI\s*Bank\b", re.I)),
]


def detect_bank(extraction: PdfExtractionResult) -> BankCode:
    text = extraction.full_text
    for code, pattern in _BANK_PATTERNS:
        if pattern.search(text):
            return code
    return BankCode.GENERIC
