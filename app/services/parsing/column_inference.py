import logging
import re

from app.schemas.transaction import ColumnMapping
from app.utils.amounts import is_amount_like, parse_amount
from app.utils.dates import is_date_like

logger = logging.getLogger(__name__)

# Ordered rules: (field, pattern, priority). Higher priority wins per field.
_HEADER_RULES: list[tuple[str, re.Pattern[str], int]] = [
    ("date", re.compile(r"^(?:date|txn\.?\s*date|transaction\s*date)\b", re.I), 100),
    ("date", re.compile(r"\bvalue\s*(?:dt|date)\b", re.I), 40),
    ("date", re.compile(r"\bposting\s*date\b", re.I), 50),
    ("description", re.compile(r"\bnarration\b", re.I), 100),
    ("description", re.compile(r"\bparticulars?\b", re.I), 90),
    ("description", re.compile(r"\bdescription\b", re.I), 85),
    ("description", re.compile(r"\btransaction\s*details?\b", re.I), 80),
    ("description", re.compile(r"\bremarks?\b", re.I), 70),
    ("debit", re.compile(r"\bwithdrawal\s*(?:amt|amount)?\.?\b", re.I), 100),
    ("debit", re.compile(r"\bwithdrawal\b", re.I), 90),
    ("debit", re.compile(r"\bdebit\b", re.I), 85),
    ("debit", re.compile(r"\bdr\.?\b", re.I), 60),
    ("debit", re.compile(r"\bpaid\s*out\b", re.I), 50),
    ("credit", re.compile(r"\bdeposit\s*(?:amt|amount)?\.?\b", re.I), 100),
    ("credit", re.compile(r"\bdeposit\b", re.I), 90),
    ("credit", re.compile(r"\bcredit\b", re.I), 85),
    ("credit", re.compile(r"\bcr\.?\b", re.I), 60),
    ("credit", re.compile(r"\bpaid\s*in\b", re.I), 50),
    ("balance", re.compile(r"\bclosing\s*balance\b", re.I), 100),
    ("balance", re.compile(r"\brunning\s*balance\b", re.I), 90),
    ("balance", re.compile(r"\bbalance\b", re.I), 70),
    ("amount", re.compile(r"^amount$", re.I), 100),
    ("amount", re.compile(r"\btransaction\s*amount\b", re.I), 80),
]

# Columns that are not transaction amounts (avoid mapping Chq/Ref as debit)
_NON_AMOUNT_HEADERS = re.compile(r"\bchq|cheque|ref\.?\s*no|reference|value\s*dt\b", re.I)


def normalize_header_for_inference(header: str) -> str:
    text = header.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _score_header_cell(cell: str, field: str, pattern: re.Pattern[str], priority: int) -> int:
    text = normalize_header_for_inference(cell)
    if not text:
        return -1
    if field in {"debit", "credit", "balance", "amount"} and _NON_AMOUNT_HEADERS.search(text):
        return -1
    if pattern.search(text):
        return priority
    return -1


def infer_columns_from_header(header_cells: list[str]) -> ColumnMapping:
    normalized_headers = [normalize_header_for_inference(c) for c in header_cells]
    best: dict[str, tuple[int, int]] = {}  # field -> (index, score)

    for idx, cell in enumerate(header_cells):
        display = cell.strip() or f"col_{idx}"
        for field, pattern, priority in _HEADER_RULES:
            score = _score_header_cell(display, field, pattern, priority)
            if score < 0:
                continue
            current = best.get(field)
            if current is None or score > current[1]:
                best[field] = (idx, score)

    mapping = ColumnMapping(
        date=best.get("date", (None, 0))[0],
        description=best.get("description", (None, 0))[0],
        debit=best.get("debit", (None, 0))[0],
        credit=best.get("credit", (None, 0))[0],
        balance=best.get("balance", (None, 0))[0],
        amount=best.get("amount", (None, 0))[0],
    )

    logger.debug(
        "Header inference for %s -> %s",
        normalized_headers,
        mapping.model_dump(),
    )
    return mapping


def infer_columns_from_data(rows: list[list[str]], sample_size: int = 20) -> ColumnMapping:
    """Adaptive inference when headers are weak or missing."""
    if not rows:
        return ColumnMapping()

    col_count = max(len(r) for r in rows)
    date_scores = [0] * col_count
    amount_scores = [0] * col_count
    text_scores = [0] * col_count

    for row in rows[:sample_size]:
        for idx in range(min(len(row), col_count)):
            cell = row[idx]
            if is_date_like(cell):
                date_scores[idx] += 1
            elif is_amount_like(cell):
                amount_scores[idx] += 1
            elif len(cell) > 3:
                text_scores[idx] += 1

    mapping = ColumnMapping()
    if date_scores and max(date_scores) > 0:
        mapping.date = max(range(col_count), key=lambda i: date_scores[i])

    amount_cols = sorted(i for i in range(col_count) if amount_scores[i] > 0)

    if len(amount_cols) >= 3:
        # Initial assumption: [... debit, credit, balance] in left-to-right order.
        # This matches the majority of Indian bank statement layouts (HDFC, SBI, ICICI).
        balance_col = amount_cols[-1]
        debit_col   = amount_cols[-3]
        credit_col  = amount_cols[-2]

        # Validate assignment with a fill-count heuristic over the sample rows.
        # In a proper split layout: both debit and credit columns are sparse
        # (only one is populated per row), and balance is always filled.
        # If the assumed debit column is consistently MORE filled than the
        # assumed credit column, the two are likely swapped — swap them back.
        sample_rows = rows[:sample_size]

        def _fill_count(col: int) -> int:
            return sum(
                1 for r in sample_rows
                if col < len(r) and is_amount_like((r[col] or "").strip())
            )

        debit_fill   = _fill_count(debit_col)
        credit_fill  = _fill_count(credit_col)
        balance_fill = _fill_count(balance_col)

        # Sanity: balance should be the most-filled column of the three.
        # If it isn't, something is structurally wrong — log and proceed as-is.
        if balance_fill < max(debit_fill, credit_fill):
            logger.warning(
                "Balance column (col %d, fill=%d) is not the most filled "
                "amount column (debit col %d fill=%d, credit col %d fill=%d). "
                "Column assignment may be incorrect.",
                balance_col, balance_fill,
                debit_col, debit_fill,
                credit_col, credit_fill,
            )

        # Swap debit/credit if debit appears denser than credit.
        # In a correctly-labelled split layout, both should be roughly equal
        # in sparsity (each row populates only one). A 2× density difference
        # strongly suggests the labels are reversed.
        if debit_fill > 0 and credit_fill > 0 and debit_fill > 2 * credit_fill:
            logger.warning(
                "Swapping inferred debit (col %d, fill=%d) and credit (col %d, fill=%d) "
                "columns based on fill-count heuristic.",
                debit_col, debit_fill, credit_col, credit_fill,
            )
            debit_col, credit_col = credit_col, debit_col

        mapping.balance = balance_col
        mapping.debit   = debit_col
        mapping.credit  = credit_col

    elif len(amount_cols) == 2:
        other_col = amount_cols[0]
        balance_col = amount_cols[1]

        # Two-amount-column layouts are ambiguous:
        # - debit + balance (debit column empty on credit rows)
        # - amount (signed via Dr/Cr) + balance
        #
        # Heuristic:
        # - if signs vary (both positive and negative amounts appear), treat as
        #   single signed amount column.
        # - otherwise, if the column is consistently populated, treat as the
        #   single signed amount column.
        considered_rows = rows[:sample_size]
        total_with_col = 0
        filled_with_amount = 0
        neg_count = 0
        pos_count = 0

        for row in considered_rows:
            if other_col >= len(row):
                continue
            total_with_col += 1
            cell = (row[other_col] or "").strip()
            if not cell:
                continue
            if not is_amount_like(cell):
                continue
            filled_with_amount += 1
            parsed = parse_amount(cell)
            if parsed is None:
                continue
            if parsed < 0:
                neg_count += 1
            elif parsed > 0:
                pos_count += 1

        filled_ratio = (
            filled_with_amount / total_with_col if total_with_col > 0 else 0
        )

        if (neg_count > 0 and pos_count > 0) or filled_ratio >= 0.8:
            mapping.amount = other_col
        else:
            # Treat as debit-only column (credit is absent).
            mapping.debit = other_col

        mapping.balance = balance_col
    elif len(amount_cols) == 1:
        mapping.amount = amount_cols[0]

    if text_scores and max(text_scores) > 0:
        desc_idx = max(range(col_count), key=lambda i: text_scores[i])
        if desc_idx != mapping.date:
            mapping.description = desc_idx

    return mapping


def merge_column_mappings(header: ColumnMapping, data: ColumnMapping) -> ColumnMapping:
    return ColumnMapping(
        date=header.date if header.date is not None else data.date,
        description=header.description if header.description is not None else data.description,
        debit=header.debit if header.debit is not None else data.debit,
        credit=header.credit if header.credit is not None else data.credit,
        balance=header.balance if header.balance is not None else data.balance,
        amount=header.amount if header.amount is not None else data.amount,
    )


def format_column_mapping(mapping: ColumnMapping, header_cells: list[str]) -> str:
    """Human-readable mapping for logs."""
    parts: list[str] = []
    fields = {
        "date": mapping.date,
        "description": mapping.description,
        "debit": mapping.debit,
        "credit": mapping.credit,
        "balance": mapping.balance,
        "amount": mapping.amount,
    }
    for name, idx in fields.items():
        if idx is None:
            parts.append(f"{name}=None")
        else:
            label = header_cells[idx] if idx < len(header_cells) else f"col_{idx}"
            parts.append(f"{name}=[{idx}]'{label}'")
    return "{" + ", ".join(parts) + "}"
