import pytest

from app.core.exceptions import ValidationError
from app.services.file_validation import validate_upload


def test_rejects_empty_file():
    with pytest.raises(ValidationError, match="empty"):
        validate_upload("stmt.pdf", "application/pdf", b"")


def test_rejects_non_pdf_extension():
    with pytest.raises(ValidationError, match="PDF"):
        validate_upload("stmt.txt", "text/plain", b"hello")


def test_rejects_invalid_pdf_magic():
    with pytest.raises(ValidationError, match="valid PDF"):
        validate_upload("stmt.pdf", "application/pdf", b"not a pdf")


def test_accepts_minimal_pdf(minimal_pdf_bytes):
    validate_upload("stmt.pdf", "application/pdf", minimal_pdf_bytes)
