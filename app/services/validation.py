from decimal import Decimal

from app.schemas.parse import ValidationIssue
from app.schemas.transaction import NormalizedTransaction
from app.utils.dates import parse_date


class StatementValidator:
    def validate(self, transactions: list[NormalizedTransaction]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        issues.extend(self._validate_rows(transactions))
        issues.extend(self._validate_balance_consistency(transactions))
        return issues

    def _validate_rows(self, transactions: list[NormalizedTransaction]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for idx, txn in enumerate(transactions):
            if not txn.date:
                issues.append(
                    ValidationIssue(
                        code="missing_date",
                        message="Transaction date is missing",
                        row_index=idx,
                        field="date",
                    )
                )
            elif parse_date(txn.date) is None:
                issues.append(
                    ValidationIssue(
                        code="invalid_date",
                        message=f"Invalid date format: {txn.date}",
                        row_index=idx,
                        field="date",
                    )
                )

            if not txn.description:
                issues.append(
                    ValidationIssue(
                        code="missing_description",
                        message="Transaction description is missing",
                        row_index=idx,
                        field="description",
                    )
                )

            if txn.debit is None and txn.credit is None:
                issues.append(
                    ValidationIssue(
                        code="missing_amount",
                        message="Neither debit nor credit amount is present",
                        row_index=idx,
                        field="debit/credit",
                    )
                )

            if txn.debit is not None and txn.credit is not None:
                if txn.debit > 0 and txn.credit > 0:
                    issues.append(
                        ValidationIssue(
                            code="malformed_row",
                            message="Both debit and credit have non-zero values",
                            row_index=idx,
                            field="debit/credit",
                        )
                    )
        return issues

    def _validate_balance_consistency(
        self, transactions: list[NormalizedTransaction]
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        prev_balance: Decimal | None = None

        for idx, txn in enumerate(transactions):
            if txn.balance is None:
                prev_balance = txn.balance
                continue

            if prev_balance is not None:
                expected = prev_balance
                if txn.credit is not None:
                    expected += txn.credit
                if txn.debit is not None:
                    expected -= txn.debit

                # Allow small rounding tolerance
                diff = abs(expected - txn.balance)
                if diff > Decimal("0.02"):
                    issues.append(
                        ValidationIssue(
                            code="balance_mismatch",
                            message=(
                                f"Balance inconsistency: expected {expected}, "
                                f"got {txn.balance}"
                            ),
                            row_index=idx,
                            field="balance",
                        )
                    )
            prev_balance = txn.balance

        return issues
