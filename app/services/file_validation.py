from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.config import settings
from app.core.exceptions import ValidationError


def validate_upload(filename: str | None, content_type: str | None, data: bytes) -> None:
    if not data:
        raise ValidationError("Uploaded file is empty")

    if len(data) > settings.max_upload_bytes:
        raise ValidationError(
            f"File exceeds maximum size of {settings.max_upload_bytes} bytes"
        )

    if not filename or not filename.lower().endswith(".pdf"):
        raise ValidationError("Only PDF files are supported")

    if content_type and content_type not in settings.allowed_content_types:
        raise ValidationError(f"Unsupported content type: {content_type}")

    _validate_pdf_structure(data)


def _validate_pdf_structure(data: bytes) -> None:
    if not data.startswith(b"%PDF"):
        raise ValidationError("File is not a valid PDF document")

    try:
        reader = PdfReader(BytesIO(data))
        if len(reader.pages) == 0:
            raise ValidationError("PDF has no pages")
        # Touch first page to ensure readability
        _ = reader.pages[0]
    except PdfReadError as exc:
        raise ValidationError(f"Invalid or corrupted PDF: {exc}") from exc
    except Exception as exc:
        raise ValidationError(f"Unable to read PDF: {exc}") from exc
