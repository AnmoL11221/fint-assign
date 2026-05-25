import re

from app.adapters.generic import GenericAdapter
from app.schemas.metadata import StatementMetadata
from app.services.pdf_extraction import PdfExtractionResult


class SbiAdapter(GenericAdapter):
    bank_name = "State Bank of India"

    _HOLDER_RE = re.compile(r"name\s*:\s*([A-Za-z][A-Za-z\s.]{2,60})", re.I)
    _ACCOUNT_RE = re.compile(
        r"(?:account\s*number|a/c\s*no\.?)\s*:\s*([Xx*\d]{4,}[\dXx*]{4,})",
        re.I,
    )

    def extract_metadata(self, extraction: PdfExtractionResult) -> StatementMetadata:
        meta = super().extract_metadata(extraction)
        text = extraction.full_text
        meta.bank_name = self.bank_name
        meta.account_holder = self._find_first(text, self._HOLDER_RE) or meta.account_holder
        meta.masked_account_number = self._find_first(text, self._ACCOUNT_RE) or meta.masked_account_number
        return meta
