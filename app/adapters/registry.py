from app.adapters.base import BankAdapter
from app.adapters.generic import GenericAdapter
from app.adapters.hdfc import HdfcAdapter
from app.adapters.icici import IciciAdapter
from app.adapters.sbi import SbiAdapter
from app.services.parsing.bank_detection import BankCode

_ADAPTERS: dict[BankCode, BankAdapter] = {
    BankCode.HDFC: HdfcAdapter(),
    BankCode.SBI: SbiAdapter(),
    BankCode.ICICI: IciciAdapter(),
    BankCode.GENERIC: GenericAdapter(),
}


def get_adapter(bank_code: BankCode) -> BankAdapter:
    return _ADAPTERS.get(bank_code, GenericAdapter())
