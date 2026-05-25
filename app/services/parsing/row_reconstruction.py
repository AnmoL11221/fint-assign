from app.schemas.transaction import ColumnMapping, RawTransactionRow
from app.utils.dates import is_date_like
from app.utils.amounts import is_amount_like


def _row_has_amount(cells: list[str], mapping: ColumnMapping) -> bool:
    indices = {mapping.debit, mapping.credit, mapping.balance, mapping.amount}
    for idx in indices:
        if idx is None or idx >= len(cells):
            continue
        if is_amount_like(cells[idx]):
            return True
    return False


def _is_continuation_row(cells: list[str], mapping: ColumnMapping) -> bool:
    """Continuation rows lack a date but carry narration overflow."""
    if not cells:
        return False

    date_cell = ""
    if mapping.date is not None and mapping.date < len(cells):
        date_cell = cells[mapping.date].strip()

    if date_cell and is_date_like(date_cell):
        return False

    if _row_has_amount(cells, mapping):
        return False

    desc_idx = mapping.description
    if desc_idx is not None and desc_idx < len(cells) and cells[desc_idx].strip():
        return True

    # Narration may spill into column 0 when date column is empty
    if mapping.date != 0 and cells[0].strip() and not is_date_like(cells[0]):
        return True

    return False


def merge_multiline_narration_rows(
    rows: list[RawTransactionRow],
    mapping: ColumnMapping,
) -> list[RawTransactionRow]:
    if not rows:
        return []

    merged: list[RawTransactionRow] = []
    for row in rows:
        if merged and _is_continuation_row(row.cells, mapping):
            prev = merged[-1]
            desc_idx = mapping.description
            continuation = ""
            if desc_idx is not None and desc_idx < len(row.cells):
                continuation = row.cells[desc_idx].strip()
            if not continuation and row.cells:
                continuation = row.cells[0].strip()

            if continuation:
                prev_cells = list(prev.cells)
                if desc_idx is not None:
                    if desc_idx >= len(prev_cells):
                        prev_cells.extend([""] * (desc_idx - len(prev_cells) + 1))
                    prev_cells[desc_idx] = f"{prev_cells[desc_idx]} {continuation}".strip()
                else:
                    prev_cells[0] = f"{prev_cells[0]} {continuation}".strip()
                merged[-1] = prev.model_copy(update={"cells": prev_cells})
            continue

        merged.append(row)

    return merged


def reconstruct_transaction_rows(
    table_rows: list[list[str]],
    header_row_index: int,
    mapping: ColumnMapping,
    page_index: int = 0,
) -> list[RawTransactionRow]:
    from app.services.parsing.table_detection import _is_transaction_data_row
    from app.utils.text import cell_text

    raw: list[RawTransactionRow] = []
    for row_index, cells in enumerate(table_rows[header_row_index + 1 :], start=0):
        cleaned = [cell_text(c) for c in cells]
        if not _is_transaction_data_row(cleaned):
            continue
        raw.append(
            RawTransactionRow(
                cells=cleaned,
                page_index=page_index,
                row_index=row_index,
            )
        )

    return merge_multiline_narration_rows(raw, mapping)
