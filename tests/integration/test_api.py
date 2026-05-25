from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_statement_service
from app.main import app
from app.services.dal.statement_store import StatementStore
from app.services.parsing.engine import ParsingEngine
from app.services.pdf_extraction import PdfExtractionEngine
from app.services.statement_service import StatementService


@pytest.fixture
def api_client(temp_upload_dir, sample_extraction):
    store = StatementStore(base_dir=temp_upload_dir)
    mock_extractor = MagicMock(spec=PdfExtractionEngine)
    mock_extractor.extract.return_value = sample_extraction
    service = StatementService(
        store=store,
        parsing_engine=ParsingEngine(pdf_extractor=mock_extractor),
    )

    get_statement_service.cache_clear()
    app.dependency_overrides[get_statement_service] = lambda: service
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    get_statement_service.cache_clear()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_invalid_file(client):
    response = client.post(
        "/statements/upload",
        files={"file": ("bad.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["error"] == "validation_error"


def test_upload_and_parse_flow(api_client, minimal_pdf_bytes):
    upload = api_client.post(
        "/statements/upload",
        files={"file": ("statement.pdf", minimal_pdf_bytes, "application/pdf")},
    )
    assert upload.status_code == 200
    statement_id = upload.json()["statement_id"]

    parse_resp = api_client.post(f"/statements/{statement_id}/parse")
    assert parse_resp.status_code == 200
    body = parse_resp.json()
    assert body["transaction_count"] == 3
    assert body["metadata"]["bank_name"] == "HDFC Bank"


def test_parse_not_found(client):
    response = client.post("/statements/nonexistent-id/parse")
    assert response.status_code == 404
