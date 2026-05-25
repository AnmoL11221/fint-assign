from app.services.parsing.column_inference import infer_columns_from_header


def test_hdfc_standard_header_mapping():
    header = [
        "Date",
        "Narration",
        "Chq./Ref.No.",
        "Value Dt",
        "Withdrawal Amt.",
        "Deposit Amt.",
        "Closing Balance",
    ]
    mapping = infer_columns_from_header(header)
    assert mapping.date == 0
    assert mapping.description == 1
    assert mapping.debit == 4
    assert mapping.credit == 5
    assert mapping.balance == 6
