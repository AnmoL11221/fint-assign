from decimal import Decimal

from app.schemas.transaction import ColumnMapping, RawTransactionRow
from app.services.parsing.transaction_parser import parse_transaction_row


def test_parse_transaction_row_debit():
    row = RawTransactionRow(
        cells=["01/04/2024", "ATM Withdrawal", "500.00", "", "4500.00"],
        page_index=0,
        row_index=0,
    )
    mapping = ColumnMapping(date=0, description=1, debit=2, credit=3, balance=4)
    txn = parse_transaction_row(row, mapping)
    assert txn.date == "2024-04-01"
    assert txn.description == "ATM Withdrawal"
    assert txn.debit == Decimal("500.00")
    assert txn.credit is None
    assert txn.balance == Decimal("4500.00")


def test_parse_transaction_row_dr_single_amount_is_debit():
    row = RawTransactionRow(
        cells=["01/04/2024", "ATM Withdrawal", "500.00 Dr", "4500.00"],
        page_index=0,
        row_index=0,
    )
    # Signed single-amount layout: mapping.amount only
    mapping = ColumnMapping(date=0, description=1, debit=None, credit=None, balance=3, amount=2)
    txn = parse_transaction_row(row, mapping)
    assert txn.debit == Decimal("500.00")
    assert txn.credit is None
    assert txn.balance == Decimal("4500.00")
