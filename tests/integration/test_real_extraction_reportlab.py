from decimal import Decimal
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, SimpleDocTemplate, Table, TableStyle
from reportlab.platypus.paragraph import Paragraph

from app.services.parsing.engine import ParsingEngine
from app.services.pdf_extraction import PdfExtractionEngine


def _make_hdfc_like_table_rows(
    title_row_first_cell: str,
    header_row: list[str],
    tx_rows: list[list[str]],
) -> list[list[str]]:
    # Table cleaners expect a "title row before real header" scenario in some PDFs.
    return [[title_row_first_cell, "", "", "", "", "", ""]] + [header_row] + tx_rows


def _build_pdf(pdf_path: Path) -> None:
    styles = getSampleStyleSheet()

    header = [
        "Date",
        "Narration",
        "Chq./Ref.No.",
        "Value Dt",
        "Withdrawal Amt.",
        "Deposit Amt.",
        "Closing Balance",
    ]

    page1_tx = [
        [
            "01/04/2024",
            "Test Debit 1",
            "REF1",
            "01/04/2024",
            "100.00",
            "",
            "900.00",
        ],
        [
            "02/04/2024",
            "Test Credit 1",
            "REF2",
            "02/04/2024",
            "",
            "200.00",
            "1100.00",
        ],
    ]
    page2_tx = [
        [
            "03/04/2024",
            "Test Debit 2",
            "REF3",
            "03/04/2024",
            "50.00",
            "",
            "1050.00",
        ],
        [
            "04/04/2024",
            "Test Credit 2",
            "REF4",
            "04/04/2024",
            "",
            "25.00",
            "1075.00",
        ],
    ]

    t1 = Table(
        _make_hdfc_like_table_rows(
            title_row_first_cell="Account Statement",
            header_row=header,
            tx_rows=page1_tx,
        ),
        colWidths=[70, 130, 90, 70, 90, 90, 100],
    )
    t1.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    t2 = Table(
        _make_hdfc_like_table_rows(
            title_row_first_cell="Account Statement",
            header_row=header,
            tx_rows=page2_tx,
        ),
        colWidths=[70, 130, 90, 70, 90, 90, 100],
    )
    t2.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
    story = [
        Paragraph(
            "HDFC Bank Account Statement Customer Name JOHN DOE Account No XX1234",
            styles["Normal"],
        ),
        t1,
        PageBreak(),
        t2,
    ]
    doc.build(story)


def test_real_pdf_extraction_multi_page(tmp_path: Path) -> None:
    pdf_path = tmp_path / "hdfc_multi_page.pdf"
    _build_pdf(pdf_path)

    engine = ParsingEngine(pdf_extractor=PdfExtractionEngine())
    metadata, transactions, extraction = engine.parse(pdf_path)

    assert metadata.bank_name == "HDFC Bank"
    assert len(extraction.tables) >= 2
    assert len(transactions) == 4

    assert transactions[0].date == "2024-04-01"
    assert transactions[0].description == "Test Debit 1"
    assert transactions[0].debit == Decimal("100.00")
    assert transactions[0].credit is None
    assert transactions[0].balance == Decimal("900.00")

    assert transactions[1].credit == Decimal("200.00")
    assert transactions[1].debit is None
    assert transactions[1].balance == Decimal("1100.00")

    assert transactions[2].debit == Decimal("50.00")
    assert transactions[2].balance == Decimal("1050.00")

    assert transactions[3].credit == Decimal("25.00")
    assert transactions[3].balance == Decimal("1075.00")

