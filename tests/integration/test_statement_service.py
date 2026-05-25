from unittest.mock import MagicMock

from app.services.dal.statement_store import StatementStore
from app.services.parsing.engine import ParsingEngine
from app.services.pdf_extraction import PdfExtractionEngine
from app.services.statement_service import StatementService


def test_full_parse_pipeline(
    temp_upload_dir, sample_extraction, minimal_pdf_bytes
):
    store = StatementStore(base_dir=temp_upload_dir)
    record = store.save_upload("hdfc.pdf", minimal_pdf_bytes)

    mock_extractor = MagicMock(spec=PdfExtractionEngine)
    mock_extractor.extract.return_value = sample_extraction

    service = StatementService(
        store=store,
        parsing_engine=ParsingEngine(pdf_extractor=mock_extractor),
    )
    result = service.parse(record.id)

    assert result.transaction_count == 3
    assert result.metadata.bank_name == "HDFC Bank"
    assert result.transactions[0].credit is not None
    assert any(i.code == "balance_mismatch" for i in result.validation_issues) is False
