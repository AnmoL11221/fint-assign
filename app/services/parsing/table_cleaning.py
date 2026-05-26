import re

from app.services.pdf_extraction import ExtractedTable
from app.utils.dates import is_date_like
from app.utils.text import cell_text, normalize_whitespace

_HEADER_HINTS = re.compile(
    r"date|narration|particulars|withdrawal|deposit|balance|debit|credit|chq|ref",
    re.I,
)

_SKIP_ROW_PATTERNS = [
    re.compile(r"^opening\s*balance", re.I),
    re.compile(r"^closing\s*balance\s*$", re.I),
    re.compile(r"^total\b", re.I),
    re.compile(r"^brought\s*forward", re.I),
    re.compile(r"^carried\s*forward", re.I),
    re.compile(r"^statement\s*summary", re.I),
]


def _is_empty_row(cells: list[str]) -> bool:
    return not any(c.strip() for c in cells)


def _header_score(cells: list[str]) -> int:
    joined = " ".join(cells).lower()
    return len(_HEADER_HINTS.findall(joined))


def normalize_header_cell(cell: str) -> str:
    text = normalize_whitespace(cell)
    text = text.replace("\n", " ")
    # HDFC headers: "Withdrawal Amt." -> consistent token form
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_row_cells(cells: list[str]) -> list[str]:
    return [cell_text(c) for c in cells]


def remove_empty_rows(rows: list[list[str]]) -> list[list[str]]:
    return [row for row in rows if not _is_empty_row(row)]


def pad_rows_to_width(rows: list[list[str]], width: int) -> list[list[str]]:
    padded: list[list[str]] = []
    for row in rows:
        cells = list(row)
        if len(cells) < width:
            cells.extend([""] * (width - len(cells)))
        elif len(cells) > width:
            # Keep overflow in last column (common for split narration)
            head = cells[: width - 1]
            tail = " ".join(c for c in cells[width - 1 :] if c)
            cells = head + [tail]
        padded.append(cells)
    return padded


def merge_multiline_header_rows(rows: list[list[str]]) -> tuple[list[str], list[list[str]]]:
    """Merge consecutive header-like rows into a single header."""
    if not rows:
        return [], []

    working = [normalize_row_cells(r) for r in rows]
    if len(working) == 1:
        return [normalize_header_cell(c) for c in working[0]], []

    first_score = _header_score(working[0])
    second_score = _header_score(working[1]) if len(working) > 1 else 0

    if first_score >= 2 and second_score >= 1 and not any(is_date_like(c) for c in working[1]):
        width = max(len(working[0]), len(working[1]))
        working = pad_rows_to_width(working, width)
        merged: list[str] = []
        for col in range(width):
            parts = [working[0][col], working[1][col]]
            merged.append(normalize_header_cell(" ".join(p for p in parts if p)))
        return merged, working[2:]

    return [normalize_header_cell(c) for c in working[0]], working[1:]


def is_malformed_data_row(cells: list[str]) -> bool:
    if len(cells) < 2:
        return True
    joined = " ".join(cells).strip()
    if not joined:
        return True
    if any(p.search(cells[0] or "") for p in _SKIP_ROW_PATTERNS):
        return True
    return False


def clean_malformed_rows(rows: list[list[str]]) -> list[list[str]]:
    return [row for row in rows if not is_malformed_data_row(row)]


def clean_table(table: ExtractedTable) -> ExtractedTable:
    """
    Normalize a raw extracted table:
    - drop empty rows
    - normalize whitespace
    - merge multi-row headers
    - pad columns consistently
    - remove summary/skip rows from body
    """
    rows = remove_empty_rows([normalize_row_cells(r) for r in table.rows])
    if not rows:
        return ExtractedTable(page_index=table.page_index, rows=[])

    def _find_header_start(rows_: list[list[str]]) -> int | None:
        # HDFC statements often include a title row (e.g. "Account Statement")
        # before the actual column header. Choose the best header-like row
        # within the first N rows.
        best_idx: int | None = None
        best_score = 0
        for idx, row in enumerate(rows_[:12]):
            score = _header_score(row)
            if score > best_score:
                best_score = score
                best_idx = idx
        # Require a reasonably header-like row.
        return best_idx if best_score >= 2 else None

    header_start = _find_header_start(rows)
    if header_start is None:
        return ExtractedTable(page_index=table.page_index, rows=[])

    # Slice from the detected header start; any title/metadata rows before
    # this are not part of the transaction table structure.
    rows_from_header = rows[header_start:]

    header, body = merge_multiline_header_rows(rows_from_header)
    if not header:
        return ExtractedTable(page_index=table.page_index, rows=[])

    width = len(header)
    body = clean_malformed_rows(body)
    body = pad_rows_to_width(body, width)

    return ExtractedTable(page_index=table.page_index, rows=[header, *body])
