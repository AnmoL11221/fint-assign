from app.schemas.transaction import ColumnMapping
from app.services.parsing.column_inference import (
    infer_columns_from_data,
    infer_columns_from_header,
    merge_column_mappings,
)


def test_infer_columns_from_header():
    header = ["Date", "Narration", "Withdrawal", "Deposit", "Balance"]
    mapping = infer_columns_from_header(header)
    assert mapping.date == 0
    assert mapping.description == 1
    assert mapping.debit == 2
    assert mapping.credit == 3
    assert mapping.balance == 4


def test_infer_columns_from_data():
    rows = [
        ["01/04/2024", "Payment to vendor", "100.00", "", "900.00"],
        ["02/04/2024", "Refund", "", "50.00", "950.00"],
    ]
    mapping = infer_columns_from_data(rows)
    assert mapping.date == 0
    assert mapping.description == 1
    assert mapping.balance == 4


def test_merge_column_mappings_prefers_header():
    header = ColumnMapping(date=0, description=1, debit=2, credit=3, balance=4)
    data = ColumnMapping(date=1, description=0)
    merged = merge_column_mappings(header, data)
    assert merged.date == 0
    assert merged.description == 1
