from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_statement_service
from app.schemas.parse import ParseResult
from app.schemas.statement import UploadResponse
from app.services.statement_service import StatementService

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_statement(
    file: UploadFile = File(...),
    service: StatementService = Depends(get_statement_service),
) -> UploadResponse:
    data = await file.read()
    return service.upload(file.filename, file.content_type, data)


@router.post("/{statement_id}/parse", response_model=ParseResult)
def parse_statement(
    statement_id: str,
    service: StatementService = Depends(get_statement_service),
) -> ParseResult:
    return service.parse(statement_id)
