# Bank Statement PDF Parser

MVP backend service that parses digital bank statement PDFs and returns structured metadata and transactions. Built with Python 3.12, FastAPI, pdfplumber, pypdf, and Pydantic.

## Architecture

- **`app/api`** — HTTP routes and dependency injection
- **`app/core`** — Configuration and application exceptions
- **`app/schemas`** — Pydantic request/response models
- **`app/services/dal`** — File storage data access layer
- **`app/services`** — Business logic (upload, parse orchestration, validation)
- **`app/services/parsing`** — Generic table detection, column inference, transaction parsing
- **`app/adapters`** — Lightweight bank-specific metadata and formatting (HDFC, SBI, ICICI, generic)
- **`app/utils`** — Date/amount/text helpers

Parsing is **bank-agnostic** by default. Adapters only enrich metadata and apply minor formatting fixes.

## Quick start

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/statements/upload` | Upload a PDF (`multipart/form-data`, field `file`) |
| POST | `/statements/{statement_id}/parse` | Parse a previously uploaded statement |

### Example

```bash
curl -F "file=@statement.pdf" http://127.0.0.1:8000/statements/upload
curl -X POST http://127.0.0.1:8000/statements/{statement_id}/parse
```

### Response shape (parse)

```json
{
  "statement_id": "...",
  "metadata": {
    "bank_name": "HDFC Bank",
    "account_holder": "JOHN DOE",
    "masked_account_number": "XX1234",
    "statement_period_start": "01/04/2024",
    "statement_period_end": "30/04/2024"
  },
  "transactions": [
    {
      "date": "2024-04-01",
      "description": "Salary Credit",
      "debit": null,
      "credit": "50000.00",
      "balance": "50000.00"
    }
  ],
  "validation_issues": [],
  "transaction_count": 1,
  "is_valid": true
}
```

## Configuration

Environment variables (prefix `PDF_PARSER_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `PDF_PARSER_UPLOAD_DIR` | `data/uploads` | Storage directory |
| `PDF_PARSER_MAX_UPLOAD_BYTES` | `10485760` | Max upload size (10 MB) |
| `PDF_PARSER_DEBUG` | `false` | Enable debug logging |
| `PDF_PARSER_PARSE_DEBUG_LOGGING` | `false` | Verbose parse pipeline logs |

When parse debug logging is on, the parser logs extracted tables, detected headers, inferred column mappings, raw reconstructed rows, and parsed transactions before normalization.

## HDFC statement notes

HDFC digital statements commonly use headers such as **Date**, **Narration**, **Withdrawal Amt.**, **Deposit Amt.**, and **Closing Balance**. The parser:

1. Cleans tables (empty rows, merged headers, padded columns)
2. Maps HDFC headers to debit/credit/balance/description via scored header rules
3. Merges multiline narration continuation rows into a single transaction

**Important:** PDFs that are scanned images or ReportLab renders with no text layer will not produce transactions. Use the official downloadable statement from HDFC netbanking (text-selectable PDF).

## Tests

```bash
pip install -r requirements.txt
pytest -v
```

## Design notes

- **Generic engine** detects transaction tables and infers date, description, debit, credit, and balance columns from headers and row patterns.
- **Validation** flags missing fields, invalid dates, malformed rows, and balance inconsistencies.
- **Extensibility** — add a new adapter and detection pattern without rewriting the core parser.
