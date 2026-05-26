from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber
from pypdf import PdfReader

from app.utils.text import cell_text, normalize_whitespace
from app.utils.amounts import is_amount_like
from app.utils.dates import is_date_like

_TABLE_SETTINGS: list[dict | None] = [
    None,
    {"vertical_strategy": "lines", "horizontal_strategy": "lines"},
    {"vertical_strategy": "text", "horizontal_strategy": "text"},
    {
        "vertical_strategy": "lines_strict",
        "horizontal_strategy": "lines_strict",
    },
]


@dataclass
class ExtractedTable:
    page_index: int
    rows: list[list[str]]


@dataclass
class PdfExtractionResult:
    full_text: str = ""
    page_texts: list[str] = field(default_factory=list)
    tables: list[ExtractedTable] = field(default_factory=list)
    page_count: int = 0


def _rows_from_table_matrix(table: list[list]) -> list[list[str]]:
    cleaned_rows: list[list[str]] = []
    for row in table:
        if row is None:
            continue
        cells = [cell_text(c) for c in row]
        if any(cells):
            cleaned_rows.append(cells)
    return cleaned_rows


def _cell_sig(s: str | None) -> str:
    if not s:
        return ""
    return normalize_whitespace(str(s))[:25]


def _row_fingerprint(cells: list[str]) -> tuple:
    # Use both structural info and content hints so we don't over-dedupe.
    date_count = sum(1 for c in cells[:3] if is_date_like(c))
    amount_count = sum(1 for c in cells if is_amount_like(c))
    first = _cell_sig(cells[0]) if cells else ""
    last = _cell_sig(cells[-1]) if cells else ""
    return (len(cells), date_count, amount_count, first, last)


def _table_signature(rows: list[list[str]]) -> tuple:
    if not rows:
        return tuple()
    max_width = max(len(r) for r in rows)
    first_row = rows[0]
    second_row = rows[1] if len(rows) > 1 else []
    mid_row = rows[len(rows) // 2] if rows else []
    last_row = rows[-1]
    return (
        len(rows),
        max_width,
        _row_fingerprint(first_row),
        _row_fingerprint(second_row),
        _row_fingerprint(mid_row),
        _row_fingerprint(last_row),
    )


def _extract_tables_from_words(page) -> list[list[list[str]]]:
    """Build table rows from word positions when line-based extraction fails."""
    words = page.extract_words(x_tolerance=3, y_tolerance=3, keep_blank_chars=False) or []
    if len(words) < 10:
        return []

    lines: dict[float, list[dict]] = {}
    for word in words:
        key = round(word["top"], 1)
        lines.setdefault(key, []).append(word)

    sorted_lines = sorted(lines.items(), key=lambda item: item[0])
    rows: list[list[str]] = []
    for _, line_words in sorted_lines:
        line_words.sort(key=lambda w: w["x0"])
        cells: list[str] = []
        current = ""
        prev_x1: float | None = None
        gap_threshold = 18

        for word in line_words:
            text = word["text"]
            if prev_x1 is not None and (word["x0"] - prev_x1) > gap_threshold:
                if current.strip():
                    cells.append(normalize_whitespace(current))
                current = text
            else:
                current = f"{current} {text}".strip()
            prev_x1 = word["x1"]

        if current.strip():
            cells.append(normalize_whitespace(current))
        if cells:
            rows.append(cells)

    if len(rows) < 2:
        return []
    return [rows]


class PdfExtractionEngine:
    """Extracts text and tables using pdfplumber with pypdf for page count validation."""

    def extract(self, pdf_path: Path) -> PdfExtractionResult:
        page_texts: list[str] = []
        tables: list[ExtractedTable] = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_index, page in enumerate(pdf.pages):
                # Deduplicate only within a page. The same transaction table
                # can legitimately appear on later pages with similar shape.
                seen_signatures: set[tuple] = set()

                text = page.extract_text() or ""
                if not text.strip():
                    text = page.extract_text(layout=True) or ""
                page_texts.append(normalize_whitespace(text))

                page_tables: list[list[list[str]]] = []
                for table_settings in _TABLE_SETTINGS:
                    kwargs = {"table_settings": table_settings} if table_settings else {}
                    for table in page.extract_tables(**kwargs) or []:
                        rows = _rows_from_table_matrix(table)
                        if rows:
                            page_tables.append(rows)

                if not page_tables:
                    page_tables = _extract_tables_from_words(page)

                for rows in page_tables:
                    sig = _table_signature(rows)
                    if sig in seen_signatures:
                        continue
                    seen_signatures.add(sig)
                    tables.append(ExtractedTable(page_index=page_index, rows=rows))

        reader = PdfReader(str(pdf_path))
        full_text = "\n".join(page_texts)

        return PdfExtractionResult(
            full_text=full_text,
            page_texts=page_texts,
            tables=tables,
            page_count=len(reader.pages),
        )
