from app.schemas.transaction import ColumnMapping, RawTransactionRow
from app.services.parsing.row_reconstruction import merge_multiline_narration_rows


def test_merge_multiline_narration():
    mapping = ColumnMapping(date=0, description=1, debit=2, credit=3, balance=4)
    rows = [
        RawTransactionRow(
            cells=["01/04/2024", "UPI/ABC STORE", "", "500.00", "10,500.00"],
            page_index=0,
            row_index=0,
        ),
        RawTransactionRow(
            cells=["", "MUMBAI INDIA", "", "", ""],
            page_index=0,
            row_index=1,
        ),
    ]
    merged = merge_multiline_narration_rows(rows, mapping)
    assert len(merged) == 1
    assert "MUMBAI" in merged[0].cells[1]
    assert "ABC STORE" in merged[0].cells[1]
