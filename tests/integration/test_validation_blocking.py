from unittest.mock import MagicMock

from app.schemas.metadata import StatementMetadata
from app.services.parsing.engine import ParsingEngine
from app.services.pdf_extraction import PdfExtractionEngine, PdfExtractionResult
from app.services.statement_service import StatementService
from app.services.dal.statement_store import StatementStore
from app.services.pdf_extraction import ExtractedTable


def test_parse_empty_transactions_is_invalid(temp_upload_dir, minimal_pdf_bytes):
    store = StatementStore(base_dir=temp_upload_dir)
    record = store.save_upload("empty.pdf", minimal_pdf_bytes)

    extraction = PdfExtractionResult(full_text="HDFC Bank", tables=[], page_count=1)
    mock_extractor = MagicMock(spec=PdfExtractionEngine)
    mock_extractor.extract.return_value = extraction

    service = StatementService(store=store, parsing_engine=ParsingEngine(pdf_extractor=mock_extractor))
    result = service.parse(record.id)

    assert result.transaction_count == 0
    assert result.is_valid is False
    assert any(i.code == "no_transactions" for i in result.validation_issues)


def test_missing_amount_is_blocking(temp_upload_dir, minimal_pdf_bytes):
    store = StatementStore(base_dir=temp_upload_dir)
    record = store.save_upload("missing_amount.pdf", minimal_pdf_bytes)

    # Table with headers, but row has neither debit nor credit
    table = ExtractedTable(
        page_index=0,
        rows=[
            ["Date", "Narration", "Withdrawal Amt.", "Deposit Amt.", "Closing Balance"],
            ["01/04/2024", "Test row", "", "", "100.00"],
        ],
    )
    extraction = PdfExtractionResult(full_text="HDFC Bank", tables=[table], page_count=1)
    mock_extractor = MagicMock(spec=PdfExtractionEngine)
    mock_extractor.extract.return_value = extraction

    service = StatementService(store=store, parsing_engine=ParsingEngine(pdf_extractor=mock_extractor))
    result = service.parse(record.id)

    assert result.transaction_count == 1
    assert result.is_valid is False
    assert any(i.code == "missing_amount" for i in result.validation_issues)


def test_summary_table_not_parsed_as_transactions(temp_upload_dir, minimal_pdf_bytes):
    store = StatementStore(base_dir=temp_upload_dir)
    record = store.save_upload("summary.pdf", minimal_pdf_bytes)

    # Header keywords exist, but the body row doesn't have a date and only
    # contains a single amount-like value (so it should not be treated as a
    # transaction row).
    table = ExtractedTable(
        page_index=0,
        rows=[
            ["Date", "Narration", "Closing Balance"],
            ["", "Account Details", "1,000.00"],
        ],
    )
    extraction = PdfExtractionResult(full_text="HDFC Bank Account Statement", tables=[table], page_count=1)
    mock_extractor = MagicMock(spec=PdfExtractionEngine)
    mock_extractor.extract.return_value = extraction

    service = StatementService(store=store, parsing_engine=ParsingEngine(pdf_extractor=mock_extractor))
    result = service.parse(record.id)

    assert result.transaction_count == 0
    assert result.is_valid is False
    assert any(i.code == "no_transactions" for i in result.validation_issues)

