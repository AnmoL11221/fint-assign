import tempfile
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.core.config import settings
from app.main import app
from app.services.dal.statement_store import StatementStore
from app.services.pdf_extraction import ExtractedTable, PdfExtractionResult
from app.services.statement_service import StatementService


@pytest.fixture
def temp_upload_dir(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        upload_dir = Path(tmp) / "uploads"
        monkeypatch.setattr(settings, "upload_dir", upload_dir)
        yield upload_dir


@pytest.fixture
def statement_store(temp_upload_dir):
    return StatementStore(base_dir=temp_upload_dir)


@pytest.fixture
def statement_service(statement_store):
    return StatementService(store=statement_store)


@pytest.fixture
def client(temp_upload_dir):
    from app.api.deps import get_statement_service

    get_statement_service.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
    get_statement_service.cache_clear()


@pytest.fixture
def minimal_pdf_bytes() -> bytes:
    buffer = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(buffer)
    return buffer.getvalue()


@pytest.fixture
def sample_extraction() -> PdfExtractionResult:
    table = ExtractedTable(
        page_index=0,
        rows=[
            [
                "Date",
                "Narration",
                "Chq./Ref.No.",
                "Value Dt",
                "Withdrawal Amt.",
                "Deposit Amt.",
                "Closing Balance",
            ],
            ["01/04/2024", "Salary Credit", "", "01/04/2024", "", "50,000.00", "50,000.00"],
            ["02/04/2024", "ATM Withdrawal", "", "02/04/2024", "5,000.00", "", "45,000.00"],
            ["03/04/2024", "UPI Payment", "", "03/04/2024", "1,200.50", "", "43,799.50"],
        ],
    )
    return PdfExtractionResult(
        full_text="HDFC Bank Account Statement Customer Name JOHN DOE Account No XX1234",
        page_texts=["HDFC Bank statement"],
        tables=[table],
        page_count=1,
    )
