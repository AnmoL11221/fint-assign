import re

from app.adapters.base import BankAdapter
from app.schemas.metadata import StatementMetadata
from app.services.pdf_extraction import PdfExtractionResult


class GenericAdapter(BankAdapter):
    bank_name = "Unknown"

    _ACCOUNT_RE = re.compile(
        # Masked account numbers like "XX1234" or "XXXX1234"
        r"(?:account\s*(?:no|number|#)?\.?\s*:?\s*)([Xx*\d]{4,})",
        re.I,
    )
    _HOLDER_RE = re.compile(
        # Capture person name without swallowing "Account No ..."
        r"(?:customer\s*name|account\s*holder)\s*:?\s*"
        r"([A-Za-z][A-Za-z\s.]{2,60}?)\s*"
        r"(?=account\s*no|a/c\s*no|account\b|$)",
        re.I,
    )
    _PERIOD_RE = re.compile(
        r"(?:statement\s*period|period)\s*:?\s*"
        r"(\d{1,2}[/-]\w+[/-]\d{2,4})\s*(?:to|-)\s*(\d{1,2}[/-]\w+[/-]\d{2,4})",
        re.I,
    )

    def extract_metadata(self, extraction: PdfExtractionResult) -> StatementMetadata:
        text = extraction.full_text
        account = self._find_first(text, self._ACCOUNT_RE)
        holder = self._find_first(text, self._HOLDER_RE)
        period_match = self._PERIOD_RE.search(text)
        start, end = None, None
        if period_match:
            start, end = period_match.group(1), period_match.group(2)

        return StatementMetadata(
            bank_name=None,
            account_holder=holder,
            masked_account_number=account,
            statement_period_start=start,
            statement_period_end=end,
        )
