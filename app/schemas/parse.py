from pydantic import BaseModel, Field

from app.schemas.metadata import StatementMetadata
from app.schemas.transaction import NormalizedTransaction


class ValidationIssue(BaseModel):
    code: str
    message: str
    row_index: int | None = None
    field: str | None = None


class ParseResult(BaseModel):
    statement_id: str
    metadata: StatementMetadata
    transactions: list[NormalizedTransaction] = Field(default_factory=list)
    validation_issues: list[ValidationIssue] = Field(default_factory=list)
    transaction_count: int = 0
    is_valid: bool = True
