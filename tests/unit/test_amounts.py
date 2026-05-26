from decimal import Decimal

import pytest

from app.utils.amounts import parse_amount


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("1,234.56", Decimal("1234.56")),
        ("50,000.00", Decimal("50000.00")),
        ("500.00 Dr", Decimal("-500.00")),
        ("500 Cr", Decimal("500")),
        ("200.50 cr", Decimal("200.50")),
        ("200 dr", Decimal("-200")),
        ("", None),
        ("-", None),
        ("abc", None),
    ],
)
def test_parse_amount(raw, expected):
    assert parse_amount(raw) == expected
