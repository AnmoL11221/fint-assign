from datetime import datetime

from pydantic import BaseModel, Field


class StatementRecord(BaseModel):
    id: str
    original_filename: str
    stored_path: str
    size_bytes: int
    uploaded_at: datetime


class UploadResponse(BaseModel):
    statement_id: str
    filename: str
    size_bytes: int
    message: str = "Upload successful"
