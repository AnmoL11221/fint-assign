from decimal import Decimal

from app.schemas.transaction import ColumnMapping, NormalizedTransaction, RawTransactionRow
from app.utils.amounts import parse_amount
from app.utils.dates import format_date_iso, parse_date
from app.utils.text import cell_text


def _safe_cell(cells: list[str], index: int | None) -> str:
    if index is None or index < 0 or index >= len(cells):
        return ""
    return cell_text(cells[index])


def parse_transaction_row(row: RawTransactionRow, mapping: ColumnMapping) -> NormalizedTransaction:
    cells = row.cells
    date_str = _safe_cell(cells, mapping.date)
    parsed_date = parse_date(date_str)
    description = _safe_cell(cells, mapping.description)

    debit = parse_amount(_safe_cell(cells, mapping.debit))
    credit = parse_amount(_safe_cell(cells, mapping.credit))
    balance = parse_amount(_safe_cell(cells, mapping.balance))

    # Only use a single-amount fallback when the statement does NOT have
    # separate debit/credit columns (otherwise we risk confusing balance as amount).
    if (
        mapping.amount is not None
        and mapping.debit is None
        and mapping.credit is None
        and debit is None
        and credit is None
    ):
        amount = parse_amount(_safe_cell(cells, mapping.amount))
        if amount is not None:
            if amount < 0:
                debit = abs(amount)
            else:
                credit = amount

    # If description empty, concatenate non-key cells
    if not description:
        used = {mapping.date, mapping.debit, mapping.credit, mapping.balance, mapping.amount}
        parts = [c for i, c in enumerate(cells) if i not in used and c]
        description = " ".join(parts)

    return NormalizedTransaction(
        date=format_date_iso(parsed_date) if parsed_date else date_str,
        description=description,
        debit=debit,
        credit=credit,
        balance=balance,
    )


def parse_transactions(
    rows: list[RawTransactionRow],
    mapping: ColumnMapping,
) -> list[NormalizedTransaction]:
    return [parse_transaction_row(row, mapping) for row in rows]
