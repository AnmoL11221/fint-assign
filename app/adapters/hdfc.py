import re

from app.adapters.generic import GenericAdapter
from app.schemas.metadata import StatementMetadata
from app.schemas.transaction import NormalizedTransaction
from app.services.pdf_extraction import PdfExtractionResult
from app.utils.text import normalize_whitespace


class HdfcAdapter(GenericAdapter):
    bank_name = "HDFC Bank"

    _HOLDER_RE = re.compile(
        r"(?:customer\s*id|customer\s*name)\s*[:\s]+\s*"
        r"([A-Za-z][A-Za-z\s.]{2,60}?)\s*"
        r"(?=account\s*no|a/c\s*no|account\b|$)",
        re.I,
    )
    _ACCOUNT_RE = re.compile(
        # Masked account numbers like "XX1234" or "XXXX1234"
        r"(?:account\s*no|a/c\s*no)\s*[:\s]+([Xx*\d]{4,})",
        re.I,
    )

    def extract_metadata(self, extraction: PdfExtractionResult) -> StatementMetadata:
        meta = super().extract_metadata(extraction)
        text = extraction.full_text
        meta.bank_name = self.bank_name
        meta.account_holder = self._find_first(text, self._HOLDER_RE) or meta.account_holder
        meta.masked_account_number = self._find_first(text, self._ACCOUNT_RE) or meta.masked_account_number
        return meta

    def fix_transactions(self, transactions: list[NormalizedTransaction]) -> list[NormalizedTransaction]:
        fixed: list[NormalizedTransaction] = []
        for txn in transactions:
            desc = normalize_whitespace(txn.description)
            # HDFC statements sometimes prefix ref numbers
            desc = re.sub(r"^\d{12,}\s+", "", desc)
            fixed.append(txn.model_copy(update={"description": desc}))
        return fixed
