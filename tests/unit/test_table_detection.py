from app.services.pdf_extraction import ExtractedTable
from app.services.parsing.table_detection import detect_transaction_tables, table_to_raw_rows


def test_detect_transaction_tables():
    table = ExtractedTable(
        page_index=0,
        rows=[
            ["Date", "Description", "Debit", "Credit", "Balance"],
            ["01/04/2024", "Test txn", "10.00", "", "90.00"],
        ],
    )
    detected = detect_transaction_tables([table])
    assert len(detected) == 1
    assert detected[0][1] == 0


def test_table_to_raw_rows_skips_non_data():
    table = ExtractedTable(
        page_index=0,
        rows=[
            ["Date", "Description", "Debit", "Credit", "Balance"],
            ["Opening Balance", "", "", "", "100.00"],
            ["01/04/2024", "Purchase", "10.00", "", "90.00"],
        ],
    )
    rows = table_to_raw_rows(table, header_row_index=0)
    assert len(rows) == 1
    assert rows[0].cells[1] == "Purchase"
