import logging
from typing import Any

from app.schemas.transaction import ColumnMapping, NormalizedTransaction, RawTransactionRow
from app.services.pdf_extraction import ExtractedTable

logger = logging.getLogger(__name__)


def log_extracted_tables(tables: list[ExtractedTable]) -> None:
    logger.debug("Extracted %d table(s) from PDF", len(tables))
    for idx, table in enumerate(tables):
        logger.debug(
            "Table %d (page %d): %d rows, preview=%s",
            idx,
            table.page_index,
            len(table.rows),
            table.rows[:3],
        )


def log_detected_header(header_cells: list[str], header_row_index: int, table_index: int) -> None:
    logger.debug(
        "Table %d header at row %d: %s",
        table_index,
        header_row_index,
        header_cells,
    )


def log_column_mapping(mapping: ColumnMapping, table_index: int) -> None:
    payload = mapping.model_dump()
    logger.info("Table %d inferred column mapping: %s", table_index, payload)
    logger.debug("Table %d column mapping detail: %s", table_index, payload)


def log_parsed_rows_before_normalization(
    rows: list[NormalizedTransaction],
    table_index: int,
) -> None:
    logger.debug(
        "Table %d parsed %d row(s) before normalization (first 5): %s",
        table_index,
        len(rows),
        [r.model_dump() for r in rows[:5]],
    )


def log_raw_rows(rows: list[RawTransactionRow], table_index: int) -> None:
    logger.debug(
        "Table %d raw rows after reconstruction (%d), preview=%s",
        table_index,
        len(rows),
        [r.cells for r in rows[:5]],
    )


def log_cleaned_table(table: ExtractedTable, table_index: int) -> None:
    logger.debug(
        "Table %d after cleaning: %d rows, header=%s",
        table_index,
        len(table.rows),
        table.rows[0] if table.rows else [],
    )
