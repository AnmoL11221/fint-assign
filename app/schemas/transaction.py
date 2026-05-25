from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class NormalizedTransaction(BaseModel):
    date: str = ""
    description: str = ""
    debit: Decimal | None = None
    credit: Decimal | None = None
    balance: Decimal | None = None


class RawTransactionRow(BaseModel):
    """Row extracted from a detected table before normalization."""

    cells: list[str] = Field(default_factory=list)
    page_index: int = 0
    row_index: int = 0


class ColumnMapping(BaseModel):
    date: int | None = None
    description: int | None = None
    debit: int | None = None
    credit: int | None = None
    balance: int | None = None
    amount: int | None = None  # single amount column when debit/credit split is absent
