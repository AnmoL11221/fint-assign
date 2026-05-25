import re
from abc import ABC, abstractmethod

from app.schemas.metadata import StatementMetadata
from app.schemas.transaction import NormalizedTransaction
from app.services.pdf_extraction import PdfExtractionResult


class BankAdapter(ABC):
    bank_name: str

    @abstractmethod
    def extract_metadata(self, extraction: PdfExtractionResult) -> StatementMetadata:
        ...

    def fix_transactions(self, transactions: list[NormalizedTransaction]) -> list[NormalizedTransaction]:
        return transactions

    def _find_first(self, text: str, pattern: re.Pattern[str]) -> str | None:
        match = pattern.search(text)
        return match.group(1).strip() if match else None
