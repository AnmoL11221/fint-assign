from app.services.pdf_extraction import ExtractedTable
from app.services.parsing.table_cleaning import clean_table


def test_clean_table_merges_split_header():
    table = ExtractedTable(
        page_index=0,
        rows=[
            ["Date", "Narration", "", "", "Withdrawal Amt.", "Deposit Amt.", "Closing Balance"],
            ["", "", "Chq./Ref.No.", "Value Dt", "", "", ""],
            ["01/04/2024", "UPI-ABC", "REF123", "01/04/2024", "", "1,000.00", "11,000.00"],
        ],
    )
    cleaned = clean_table(table)
    assert len(cleaned.rows) >= 2
    header = cleaned.rows[0]
    assert "Narration" in header[1]
    assert any("Withdrawal" in c for c in header)


def test_clean_table_removes_empty_rows():
    table = ExtractedTable(
        page_index=0,
        rows=[
            ["Date", "Narration", "Withdrawal Amt.", "Deposit Amt.", "Closing Balance"],
            ["", "", "", "", ""],
            ["01/04/2024", "Payment", "100.00", "", "900.00"],
        ],
    )
    cleaned = clean_table(table)
    assert len(cleaned.rows) == 2
