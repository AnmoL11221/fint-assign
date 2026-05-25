from pathlib import Path
from unittest.mock import MagicMock

from app.services.parsing.engine import ParsingEngine
from app.services.pdf_extraction import PdfExtractionEngine


def test_parsing_engine_with_mocked_extraction(sample_extraction, tmp_path):
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 mock")

    mock_extractor = MagicMock(spec=PdfExtractionEngine)
    mock_extractor.extract.return_value = sample_extraction

    engine = ParsingEngine(pdf_extractor=mock_extractor)
    metadata, transactions, _ = engine.parse(pdf_path)

    assert metadata.bank_name == "HDFC Bank"
    assert len(transactions) == 3
    assert transactions[0].credit is not None
    assert transactions[1].debit is not None
