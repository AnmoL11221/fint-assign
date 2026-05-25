from pydantic import BaseModel, Field


class StatementMetadata(BaseModel):
    bank_name: str | None = None
    account_holder: str | None = None
    masked_account_number: str | None = None
    statement_period_start: str | None = None
    statement_period_end: str | None = None
    raw_hints: dict[str, str] = Field(default_factory=dict)
