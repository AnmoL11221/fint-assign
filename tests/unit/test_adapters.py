from app.adapters.hdfc import HdfcAdapter
from app.adapters.registry import get_adapter
from app.services.parsing.bank_detection import BankCode
from app.services.pdf_extraction import PdfExtractionResult


def test_hdfc_metadata(sample_extraction):
    adapter = HdfcAdapter()
    meta = adapter.extract_metadata(sample_extraction)
    assert meta.bank_name == "HDFC Bank"
    assert meta.account_holder == "JOHN DOE"
    assert meta.masked_account_number == "XX1234"


def test_registry_returns_adapter():
    assert get_adapter(BankCode.HDFC).bank_name == "HDFC Bank"
    assert get_adapter(BankCode.GENERIC).bank_name == "Unknown"
