import re

from app.schemas.transaction import RawTransactionRow
from app.services.pdf_extraction import ExtractedTable
from app.services.parsing.column_inference import infer_columns_from_header
from app.utils.amounts import is_amount_like
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

_DISALLOWED_AMOUNT_HEADER = re.compile(
    r"\bchq|cheque|ref\.?\s*no|reference|value\s*dt\b",
    re.I,
)

_DATE_SUBSTRING_RE = re.compile(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}")


def _row_header_score(cells: list[str]) -> int:
    joined = " ".join(c.lower() for c in cells)
    return sum(1 for kw in _HEADER_KEYWORDS if kw in joined)


def _is_transaction_data_row(cells: list[str]) -> bool:
    if len(cells) < 2:
        return False
    if any(p.search(cells[0] or "") for p in _SKIP_ROW_PATTERNS):
        return False
    # Be stricter: a transaction data row should include either:
    # - a date-like cell, or
    # - enough numeric content to strongly indicate an amount-bearing row.
    has_date = any(is_date_like(c) for c in cells[:3])
    amount_count = sum(1 for c in cells if is_amount_like(c))
    return has_date or amount_count >= 2


def detect_transaction_tables(tables: list[ExtractedTable]) -> list[tuple[ExtractedTable, int]]:
    """Return tables with detected header row index, scored by likelihood."""
    candidates: list[tuple[ExtractedTable, int, int]] = []

    for table in tables:
        if len(table.rows) < 2:
            continue
        best_header_idx: int | None = None
        best_score = 0
        for idx, row in enumerate(table.rows[:10]):
            score = _row_header_score(row)
            if score > best_score:
                best_score = score
                best_header_idx = idx

        if best_header_idx is None or best_score < 2:
            continue

        header_cells = table.rows[best_header_idx]
        mapping = infer_columns_from_header(header_cells)

        # Hard constraints: must have date + description and balance, plus at least one amount column.
        if (
            mapping.date is None
            or mapping.description is None
            or mapping.balance is None
            or (mapping.debit is None and mapping.credit is None)
        ):
            continue

        # Reject candidates where mapped amount columns look like non-amount noise.
        for field in ("debit", "credit"):
            idx = getattr(mapping, field)
            if idx is None:
                continue
            if idx >= len(header_cells):
                continue
            header_cell = header_cells[idx]
            if _DISALLOWED_AMOUNT_HEADER.search(header_cell):
                # Example: "Chq./Ref.No." mapped as debit
                mapping = None  # type: ignore[assignment]
                break
            # If the header itself contains date-ish content, it's likely a column merge artifact.
            if "value dt" in header_cell.lower() or "posting date" in header_cell.lower():
                mapping = None  # type: ignore[assignment]
                break
        if mapping is None:  # type: ignore[truthy-bool]
            continue

        # Require at least one transaction-like row that matches the mapped date column.
        data_rows = 0
        sample = table.rows[best_header_idx + 1 : best_header_idx + 8]
        for row in sample:
            if not _is_transaction_data_row(row):
                continue
            # If a mapped amount cell contains a date substring, it's likely a merged text column.
            # Use a per-row flag so one bad row doesn't wipe out all previously counted valid rows.
            row_ok = True
            for field in ("debit", "credit", "balance"):
                idx = getattr(mapping, field)
                if idx is None or idx >= len(row):
                    continue
                cell = row[idx] or ""
                if _DATE_SUBSTRING_RE.search(cell):
                    row_ok = False
                    break
            if row_ok:
                data_rows += 1

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
