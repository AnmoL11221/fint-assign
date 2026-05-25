from decimal import Decimal

from app.schemas.transaction import NormalizedTransaction
from app.services.validation import StatementValidator


def test_missing_date_issue():
    validator = StatementValidator()
    txns = [NormalizedTransaction(date="", description="x", debit=Decimal("1"))]
    issues = validator.validate(txns)
    assert any(i.code == "missing_date" for i in issues)


def test_balance_mismatch_issue():
    validator = StatementValidator()
    txns = [
        NormalizedTransaction(
            date="2024-04-01",
            description="start",
            balance=Decimal("100"),
        ),
        NormalizedTransaction(
            date="2024-04-02",
            description="withdraw",
            debit=Decimal("10"),
            balance=Decimal("100"),  # should be 90
        ),
    ]
    issues = validator.validate(txns)
    assert any(i.code == "balance_mismatch" for i in issues)
