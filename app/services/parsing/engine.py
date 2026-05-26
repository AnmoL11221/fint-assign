import logging

from app.adapters.registry import get_adapter
from app.schemas.metadata import StatementMetadata
from app.schemas.transaction import NormalizedTransaction
from app.utils.amounts import is_amount_like
from app.utils.dates import is_date_like
from app.services.pdf_extraction import PdfExtractionEngine, PdfExtractionResult
from app.services.parsing.bank_detection import detect_bank
from app.services.parsing.column_inference import (
    format_column_mapping,
    infer_columns_from_data,
    infer_columns_from_header,
    merge_column_mappings,
)
from app.services.parsing.normalization import normalize_transactions
from app.services.parsing.parse_logging import (
    log_cleaned_table,
    log_column_mapping,
    log_detected_header,
    log_extracted_tables,
    log_parsed_rows_before_normalization,
    log_raw_rows,
)
from app.services.parsing.row_reconstruction import reconstruct_transaction_rows
from app.services.parsing.table_cleaning import clean_table
from app.services.parsing.table_detection import detect_transaction_tables
from app.services.parsing.transaction_parser import parse_transactions

logger = logging.getLogger(__name__)


class ParsingEngine:
    def __init__(
        self,
        pdf_extractor: PdfExtractionEngine | None = None,
    ) -> None:
        self._pdf_extractor = pdf_extractor or PdfExtractionEngine()

    def parse(self, pdf_path) -> tuple[StatementMetadata, list[NormalizedTransaction], PdfExtractionResult]:
        extraction = self._pdf_extractor.extract(pdf_path)
        log_extracted_tables(extraction.tables)

        bank_code = detect_bank(extraction)
        adapter = get_adapter(bank_code)
        metadata = adapter.extract_metadata(extraction)

        transactions: list[NormalizedTransaction] = []
        cleaned_tables = [clean_table(t) for t in extraction.tables]
        cleaned_tables = [t for t in cleaned_tables if t.rows]

        detected = detect_transaction_tables(cleaned_tables)
        if not detected and cleaned_tables:
            # Tight fallback: only accept tables whose header maps to a plausible
            # transaction schema and that actually contain transaction-like rows.
            tightened: list[tuple] = []

            for t in cleaned_tables:
                if len(t.rows) < 2:
                    continue
                header_cells = t.rows[0]
                mapping = infer_columns_from_header(header_cells)

                if mapping.date is None or mapping.description is None:
                    continue
                if mapping.balance is None and mapping.debit is None and mapping.credit is None:
                    continue

                # Check for at least one likely transaction-like row under the
                # current mapping (prefer date-like in the mapped date column).
                has_txn_row = False
                for row in t.rows[1 : 10]:
                    date_ok = (
                        mapping.date is not None
                        and mapping.date < len(row)
                        and is_date_like(row[mapping.date])
                    )
                    amount_count = sum(1 for c in row if is_amount_like(c))
                    if date_ok or amount_count >= 2:
                        has_txn_row = True
                        break

                if has_txn_row:
                    tightened.append((t, 0))

            detected = tightened

        for table_index, (table, header_idx) in enumerate(detected):
            log_cleaned_table(table, table_index)
            header_cells = table.rows[header_idx]
            log_detected_header(header_cells, header_idx, table_index)

            header_mapping = infer_columns_from_header(header_cells)
            data_rows = table.rows[header_idx + 1 :]
            data_mapping = infer_columns_from_data(data_rows)
            mapping = merge_column_mappings(header_mapping, data_mapping)

            mapping_repr = format_column_mapping(mapping, header_cells)
            logger.info("Final inferred column mapping (table %d): %s", table_index, mapping_repr)
            log_column_mapping(mapping, table_index)

            raw_rows = reconstruct_transaction_rows(
                table.rows,
                header_idx,
                mapping,
                page_index=table.page_index,
            )
            log_raw_rows(raw_rows, table_index)

            parsed = parse_transactions(raw_rows, mapping)
            log_parsed_rows_before_normalization(parsed, table_index)
            transactions.extend(parsed)

        transactions = adapter.fix_transactions(transactions)
        transactions = normalize_transactions(transactions)

        logger.info(
            "Parse complete: %d transaction(s), bank=%s",
            len(transactions),
            metadata.bank_name,
        )
        return metadata, transactions, extraction
