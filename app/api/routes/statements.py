from fastapi import APIRouter, Depends, File, UploadFile

from app.core.config import settings
from app.core.exceptions import ValidationError

from app.api.deps import get_statement_service
from app.schemas.parse import ParseResult
from app.schemas.statement import UploadResponse
from app.services.statement_service import StatementService

router = APIRouter()

async def _read_upload_limited(file: UploadFile, max_bytes: int) -> bytes:
    """
    Read an UploadFile into memory with a strict upper bound.

    This prevents loading arbitrarily large uploads into RAM before validation.
    """
    chunk_size = 1024 * 1024  # 1 MiB
    buf = bytearray()
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        buf.extend(chunk)
        if len(buf) > max_bytes:
            raise ValidationError(f"File exceeds maximum size of {max_bytes} bytes")
    return bytes(buf)


@router.post("/upload", response_model=UploadResponse)
async def upload_statement(
    file: UploadFile = File(...),
    service: StatementService = Depends(get_statement_service),
) -> UploadResponse:
    data = await _read_upload_limited(file, settings.max_upload_bytes)
    return service.upload(file.filename, file.content_type, data)


@router.post("/{statement_id}/parse", response_model=ParseResult)
def parse_statement(
    statement_id: str,
    service: StatementService = Depends(get_statement_service),
) -> ParseResult:
    return service.parse(statement_id)
