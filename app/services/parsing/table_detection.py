import re

from app.schemas.transaction import RawTransactionRow
from app.services.pdf_extraction import ExtractedTable
from app.utils.dates import is_date_like
from app.utils.text import cell_text

_HEADER_KEYWORDS = {
    "date",
    "txn date",
    "transaction date",
    "value date",
    "description",
    "narration",
    "particulars",
    "details",
    "debit",
    "withdrawal",
    "withdrawal amt",
    "credit",
    "deposit",
    "deposit amt",
    "balance",
    "closing balance",
    "amount",
}

_SKIP_ROW_PATTERNS = [
    re.compile(r"^opening balance", re.I),
    re.compile(r"^closing balance", re.I),
    re.compile(r"^total\b", re.I),
    re.compile(r"^brought forward", re.I),
    re.compile(r"^carried forward", re.I),
]


def _row_header_score(cells: list[str]) -> int:
    joined = " ".join(c.lower() for c in cells)
    return sum(1 for kw in _HEADER_KEYWORDS if kw in joined)


def _is_transaction_data_row(cells: list[str]) -> bool:
    if len(cells) < 2:
        return False
    if any(p.search(cells[0] or "") for p in _SKIP_ROW_PATTERNS):
        return False
    # At least one date-like cell or numeric amount in row
    has_date = any(is_date_like(c) for c in cells[:3])
    has_content = any(len(c) > 1 for c in cells[1:])
    return has_date or has_content


def detect_transaction_tables(tables: list[ExtractedTable]) -> list[tuple[ExtractedTable, int]]:
    """Return tables with detected header row index, scored by likelihood."""
    candidates: list[tuple[ExtractedTable, int, int]] = []

    for table in tables:
        if len(table.rows) < 2:
            continue
        best_header_idx = 0
        best_score = 0
        for idx, row in enumerate(table.rows[:5]):
            score = _row_header_score(row)
            if score > best_score:
                best_score = score
                best_header_idx = idx
        if best_score >= 2:
            data_rows = sum(
                1 for row in table.rows[best_header_idx + 1 :] if _is_transaction_data_row(row)
            )
            if data_rows >= 1:
                candidates.append((table, best_header_idx, best_score + data_rows))

    candidates.sort(key=lambda x: x[2], reverse=True)
    return [(t, h) for t, h, _ in candidates]


def table_to_raw_rows(table: ExtractedTable, header_row_index: int) -> list[RawTransactionRow]:
    rows: list[RawTransactionRow] = []
    for row_index, cells in enumerate(table.rows[header_row_index + 1 :], start=0):
        if not _is_transaction_data_row(cells):
            continue
        rows.append(
            RawTransactionRow(
                cells=[cell_text(c) for c in cells],
                page_index=table.page_index,
                row_index=row_index,
            )
        )
    return rows
