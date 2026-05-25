import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.schemas.statement import StatementRecord


class StatementStore:
    """File-based DAL for uploaded statement metadata and PDF paths."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self._base_dir = base_dir or settings.upload_dir
        self._meta_dir = self._base_dir / "meta"
        self._files_dir = self._base_dir / "files"
        self._meta_dir.mkdir(parents=True, exist_ok=True)
        self._files_dir.mkdir(parents=True, exist_ok=True)

    def save_upload(self, filename: str, content: bytes) -> StatementRecord:
        statement_id = str(uuid.uuid4())
        stored_name = f"{statement_id}.pdf"
        stored_path = self._files_dir / stored_name
        stored_path.write_bytes(content)

        record = StatementRecord(
            id=statement_id,
            original_filename=filename,
            stored_path=str(stored_path),
            size_bytes=len(content),
            uploaded_at=datetime.now(timezone.utc),
        )
        meta_path = self._meta_dir / f"{statement_id}.json"
        meta_path.write_text(record.model_dump_json(), encoding="utf-8")
        return record

    def get(self, statement_id: str) -> StatementRecord:
        meta_path = self._meta_dir / f"{statement_id}.json"
        if not meta_path.exists():
            raise NotFoundError(f"Statement {statement_id} not found")
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        return StatementRecord.model_validate(data)

    def get_pdf_path(self, statement_id: str) -> Path:
        record = self.get(statement_id)
        path = Path(record.stored_path)
        if not path.exists():
            raise NotFoundError(f"PDF file for statement {statement_id} not found")
        return path
