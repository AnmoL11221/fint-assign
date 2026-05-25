from pathlib import Path

from app.core.exceptions import ParseError
from app.schemas.parse import ParseResult
from app.schemas.statement import StatementRecord, UploadResponse
from app.services.dal.statement_store import StatementStore
from app.services.file_validation import validate_upload
from app.services.parsing.engine import ParsingEngine
from app.services.validation import StatementValidator


class StatementService:
    """Business logic orchestrating upload, parse, and validation."""

    def __init__(
        self,
        store: StatementStore | None = None,
        parsing_engine: ParsingEngine | None = None,
        validator: StatementValidator | None = None,
    ) -> None:
        self._store = store or StatementStore()
        self._parser = parsing_engine or ParsingEngine()
        self._validator = validator or StatementValidator()

    def upload(self, filename: str | None, content_type: str | None, data: bytes) -> UploadResponse:
        validate_upload(filename, content_type, data)
        record = self._store.save_upload(filename or "statement.pdf", data)
        return UploadResponse(
            statement_id=record.id,
            filename=record.original_filename,
            size_bytes=record.size_bytes,
        )

    def parse(self, statement_id: str) -> ParseResult:
        pdf_path = self._store.get_pdf_path(statement_id)
        try:
            metadata, transactions, _ = self._parser.parse(pdf_path)
        except Exception as exc:
            raise ParseError(f"Failed to parse statement: {exc}") from exc

        issues = self._validator.validate(transactions)
        blocking_codes = {"invalid_date", "malformed_row", "balance_mismatch"}

        return ParseResult(
            statement_id=statement_id,
            metadata=metadata,
            transactions=transactions,
            validation_issues=issues,
            transaction_count=len(transactions),
            is_valid=not any(i.code in blocking_codes for i in issues),
        )

    def get_record(self, statement_id: str) -> StatementRecord:
        return self._store.get(statement_id)
