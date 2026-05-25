from app.schemas.transaction import NormalizedTransaction
from app.utils.text import normalize_whitespace


def normalize_transactions(transactions: list[NormalizedTransaction]) -> list[NormalizedTransaction]:
    normalized: list[NormalizedTransaction] = []
    for txn in transactions:
        normalized.append(
            NormalizedTransaction(
                date=txn.date.strip(),
                description=normalize_whitespace(txn.description),
                debit=txn.debit,
                credit=txn.credit,
                balance=txn.balance,
            )
        )
    return normalized
