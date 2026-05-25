from datetime import date

import pytest

from app.utils.dates import format_date_iso, is_date_like, parse_date


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("01/04/2024", date(2024, 4, 1)),
        ("15-03-24", date(2024, 3, 15)),
        ("2024-04-01", date(2024, 4, 1)),
        ("01 Apr 2024", date(2024, 4, 1)),
        ("not-a-date", None),
    ],
)
def test_parse_date(raw, expected):
    assert parse_date(raw) == expected


def test_format_date_iso():
    assert format_date_iso(date(2024, 4, 1)) == "2024-04-01"
    assert format_date_iso(None) == ""


def test_is_date_like():
    assert is_date_like("01/04/2024")
    assert not is_date_like("hello")
