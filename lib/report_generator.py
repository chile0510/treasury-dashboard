"""
Report generator for Treasury Portfolio data.

Generates PDF summary reports and CSV exports for loans and investments
using financial data from lib.treasury_data.

Dependencies:
    - fpdf2 (PDF generation with UTF-8 support)
    - csv, io (stdlib ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â CSV generation)
"""

import csv
import io
from datetime import date
from typing import Any

from fpdf import FPDF

from lib.treasury_data import FINANCIAL_DATA


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_ty(value: float | int) -> str:
    """Format a raw VND amount as 'X.XXX tÃƒÂ¡Ã‚Â»Ã‚Â·' (billions).

    Examples:
        >>> _fmt_ty(1_204_420_673_710)
        '1.204 tÃƒÂ¡Ã‚Â»Ã‚Â·'
        >>> _fmt_ty(79_744_415_313)
        '79,7 tÃƒÂ¡Ã‚Â»Ã‚Â·'
    """
    ty = value / 1e9
    if ty >= 100:
        # Show as integer-like with dot-thousands: 1.204
        int_ty = round(ty)
        formatted = f"{int_ty:,}".replace(",", ".")
        return f"{formatted} tÃƒÂ¡Ã‚Â»Ã‚Â·"
    elif ty >= 10:
        return f"{ty:,.1f} tÃƒÂ¡Ã‚Â»Ã‚Â·".replace(",", ".")
    else:
        return f"{ty:,.2f} tÃƒÂ¡Ã‚Â»Ã‚Â·".replace(",", ".")


def _pct(value: float) -> str:
    """Format a percentage value with one decimal."""
    return f"{value:.1f}%"


def _rate(value: float) -> str:
    """Format an interest rate with one decimal and % suffix."""
    return f"{value:.1f}%"


# ---------------------------------------------------------------------------
# PDF Report
# ---------------------------------------------------------------------------

class _TreasuryPDF(FPDF):
    """Custom FPDF subclass with header/footer branding and Unicode support."""

    # Font family name used throughout the report
    _FONT = "Helvetica"  # default fallback

    def __init__(self) -> None:
        super().__init__(orientation="L", unit="mm", format="A4")
        # Try to register a Unicode font for Vietnamese support
        self._setup_unicode_font()
        self.add_page()
        self.set_auto_page_break(auto=True, margin=15)

    def _setup_unicode_font(self) -> None:
        """Find and register a Unicode TTF font that supports Vietnamese."""
        import os
        import glob

        font_candidates = []

        # Check common font directories
        font_dirs = []
        # Linux (Vercel runtime)
        for d in ["/usr/share/fonts", "/usr/local/share/fonts"]:
            if os.path.isdir(d):
                font_dirs.append(d)
        # Windows
        windir = os.environ.get("WINDIR", "C:\\Windows")
        win_fonts = os.path.join(windir, "Fonts")
        if os.path.isdir(win_fonts):
            font_dirs.append(win_fonts)

        # Preferred fonts (in order of preference)
        preferred = [
            ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans-Oblique.ttf"),
            ("arial.ttf", "arialbd.ttf", "ariali.ttf"),
            ("LiberationSans-Regular.ttf", "LiberationSans-Bold.ttf", "LiberationSans-Italic.ttf"),
            ("FreeSans.ttf", "FreeSansBold.ttf", "FreeSansOblique.ttf"),
        ]

        for regular, bold, italic in preferred:
            for fdir in font_dirs:
                reg_path = self._find_font(fdir, regular)
                bold_path = self._find_font(fdir, bold)
                italic_path = self._find_font(fdir, italic)
                if reg_path:
                    try:
                        self.add_font("UnicodeFont", "", reg_path, uni=True)
                        if bold_path:
                            self.add_font("UnicodeFont", "B", bold_path, uni=True)
                        else:
                            self.add_font("UnicodeFont", "B", reg_path, uni=True)
                        if italic_path:
                            self.add_font("UnicodeFont", "I", italic_path, uni=True)
                        else:
                            self.add_font("UnicodeFont", "I", reg_path, uni=True)
                        _TreasuryPDF._FONT = "UnicodeFont"
                        return
                    except Exception:
                        pass  # Try next font

    @staticmethod
    def _find_font(directory: str, filename: str) -> str | None:
        """Search for a font file recursively in a directory."""
        import os
        # Direct path
        direct = os.path.join(directory, filename)
        if os.path.isfile(direct):
            return direct
        # Recursive search
        for root, dirs, files in os.walk(directory):
            for f in files:
                if f.lower() == filename.lower():
                    return os.path.join(root, f)
        return None

    # -- branded header / footer ------------------------------------------

    def header(self) -> None:  # noqa: D401
        """Page header with report title."""
        self.set_font(self._FONT, "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "Treasury Portfolio Report", align="L")
        self.ln(8)

    def footer(self) -> None:  # noqa: D401
        """Page footer with page number."""
        self.set_y(-12)
        self.set_font(self._FONT, "I", 8)
        self.set_text_color(160, 160, 160)
        self.cell(0, 10, f"Trang {self.page_no()}/{{nb}}", align="C")

    # -- convenience helpers ----------------------------------------------

    def section_title(self, title: str) -> None:
        """Render a coloured section heading."""
        self.ln(4)
        self.set_font(self._FONT, "B", 12)
        self.set_text_color(0, 51, 102)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        # underline
        self.set_draw_color(0, 51, 102)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def _table_header(self, col_widths: list[float], headers: list[str]) -> None:
        """Render a table header row with a blue background."""
        self.set_font(self._FONT, "B", 9)
        self.set_fill_color(0, 51, 102)
        self.set_text_color(255, 255, 255)
        for w, h in zip(col_widths, headers):
            self.cell(w, 7, h, border=1, fill=True, align="C")
        self.ln()
        # Reset text colour for body rows
        self.set_text_color(0, 0, 0)

    def _table_row(
        self,
        col_widths: list[float],
        values: list[str],
        *,
        even: bool = False,
        aligns: list[str] | None = None,
    ) -> None:
        """Render one data row, optionally with zebra-striped background."""
        self.set_font(self._FONT, "", 9)
        if even:
            self.set_fill_color(230, 237, 247)
        else:
            self.set_fill_color(255, 255, 255)
        if aligns is None:
            aligns = ["L"] * len(values)
        for w, v, a in zip(col_widths, values, aligns):
            self.cell(w, 6, v, border=1, fill=True, align=a)
        self.ln()


def generate_summary_pdf() -> bytes:
    """Generate a full Treasury Portfolio PDF report.

    The report contains:
    * Summary KPIs (total loan, total invest, rates, spread, P&L)
    * Limit-control utilisation table
    * Outstanding loans table
    * Outstanding investments table
    * Duration-mismatch table

    Returns:
        Raw PDF bytes suitable for writing to a file or HTTP response.
    """
    data: dict[str, Any] = FINANCIAL_DATA
    summary = data["summary"]

    pdf = _TreasuryPDF()
    pdf.alias_nb_pages()

    # -- Title -------------------------------------------------------------
    pdf.set_font(pdf._FONT, "B", 18)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 12, "Treasury Portfolio Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(pdf._FONT, "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 7, f"NgÃƒÂ y bÃƒÂ¡o cÃƒÂ¡o: {date.today().strftime('%d/%m/%Y')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # -- Summary KPIs ------------------------------------------------------
    pdf.section_title("TÃ¡Â»â€¢ng quan danh mÃ¡Â»Â¥c")

    kpi_col = 45
    kpi_labels: list[tuple[str, str]] = [
        ("TÃ¡Â»â€¢ng DÃ†Â° nÃ¡Â»Â£", _fmt_ty(summary["totalLoan"])),
        ("TÃ¡Â»â€¢ng Ã„ÂÃ¡ÂºÂ§u tÃ†Â°", _fmt_ty(summary["totalInvest"])),
        ("LS Huy Ã„â€˜Ã¡Â»â„¢ng BQ", _rate(summary["fundingRate"])),
        ("LS Ã„ÂÃ¡ÂºÂ§u tÃ†Â° BQ", _rate(summary["investYield"])),
        ("Net Spread", _rate(summary["netSpread"])),
        ("LÃ¡Â»Â£i nhuÃ¡ÂºÂ­n rÃƒÂ²ng", _fmt_ty(summary["netPL"])),
    ]

    pdf.set_font(pdf._FONT, "", 10)
    x_start = pdf.l_margin
    items_per_row = 3
    for idx, (label, val) in enumerate(kpi_labels):
        col_idx = idx % items_per_row
        x = x_start + col_idx * (kpi_col * 2 + 10)
        pdf.set_x(x)
        pdf.set_font(pdf._FONT, "B", 10)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(kpi_col, 7, f"{label}:", align="L")
        pdf.set_font(pdf._FONT, "", 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(kpi_col, 7, val, align="L")
        if col_idx == items_per_row - 1:
            pdf.ln()
    pdf.ln(4)

    # -- Limit Controls ----------------------------------------------------
    pdf.section_title("HÃ¡ÂºÂ¡n mÃ¡Â»Â©c tÃƒÂ­n dÃ¡Â»Â¥ng")

    lc_widths = [35.0, 45.0, 45.0, 25.0, 45.0, 30.0]
    lc_headers = ["NgÃƒÂ¢n hÃƒÂ ng", "DÃ†Â° nÃ¡Â»Â£", "HÃ¡ÂºÂ¡n mÃ¡Â»Â©c", "Util%", "Room", "TrÃ¡ÂºÂ¡ng thÃƒÂ¡i"]
    pdf._table_header(lc_widths, lc_headers)

    for i, row in enumerate(data["limitControls"]):
        status_text = "CÃ¡ÂºÂ£nh bÃƒÂ¡o" if row["status"] == "danger" else "An toÃƒÂ n"
        pdf._table_row(
            lc_widths,
            [
                row["bank"],
                _fmt_ty(row["duNo"]),
                _fmt_ty(row["hanMuc"]),
                _pct(row["util"]),
                _fmt_ty(row["room"]) if row["room"] > 0 else "0",
                status_text,
            ],
            even=(i % 2 == 0),
            aligns=["L", "R", "R", "C", "R", "C"],
        )

    # -- Loans -------------------------------------------------------------
    pdf.section_title("Danh sÃƒÂ¡ch khoÃ¡ÂºÂ£n vay")

    loan_widths = [30.0, 45.0, 25.0, 35.0, 35.0]
    loan_headers = ["NgÃƒÂ¢n hÃƒÂ ng", "SÃ¡Â»â€˜ tiÃ¡Â»Ân", "LÃƒÂ£i suÃ¡ÂºÂ¥t", "NgÃƒÂ y bÃ¡ÂºÂ¯t Ã„â€˜Ã¡ÂºÂ§u", "NgÃƒÂ y Ã„â€˜ÃƒÂ¡o hÃ¡ÂºÂ¡n"]
    pdf._table_header(loan_widths, loan_headers)

    for i, row in enumerate(data["loans"]):
        pdf._table_row(
            loan_widths,
            [
                row["bank"],
                _fmt_ty(row["amount"]),
                _rate(row["rate"]),
                row["startDate"],
                row["endDate"],
            ],
            even=(i % 2 == 0),
            aligns=["L", "R", "C", "C", "C"],
        )

    # -- Investments -------------------------------------------------------
    pdf.section_title("Danh sÃƒÂ¡ch Ã„â€˜Ã¡ÂºÂ§u tÃ†Â°")

    inv_widths = [30.0, 45.0, 25.0, 20.0, 35.0, 35.0]
    inv_headers = ["TÃ¡Â»â€¢ chÃ¡Â»Â©c", "SÃ¡Â»â€˜ tiÃ¡Â»Ân", "LÃƒÂ£i suÃ¡ÂºÂ¥t", "LoÃ¡ÂºÂ¡i", "NgÃƒÂ y bÃ¡ÂºÂ¯t Ã„â€˜Ã¡ÂºÂ§u", "NgÃƒÂ y Ã„â€˜ÃƒÂ¡o hÃ¡ÂºÂ¡n"]
    pdf._table_header(inv_widths, inv_headers)

    for i, row in enumerate(data["investments"]):
        pdf._table_row(
            inv_widths,
            [
                row["bank"],
                _fmt_ty(row["amount"]),
                _rate(row["rate"]),
                row["type"],
                row["startDate"],
                row["endDate"],
            ],
            even=(i % 2 == 0),
            aligns=["L", "R", "C", "C", "C", "C"],
        )

    # -- Duration Mismatches -----------------------------------------------
    pdf.section_title("ChÃƒÂªnh lÃ¡Â»â€¡ch kÃ¡Â»Â³ hÃ¡ÂºÂ¡n")

    dm_widths = [30.0, 30.0, 35.0, 35.0, 25.0, 45.0, 45.0]
    dm_headers = [
        "Ã„ÂT - TÃ¡Â»â€¢ chÃ¡Â»Â©c",
        "Vay - NH",
        "Ã„ÂT Ã„â€˜ÃƒÂ¡o hÃ¡ÂºÂ¡n",
        "Vay Ã„â€˜ÃƒÂ¡o hÃ¡ÂºÂ¡n",
        "ChÃƒÂªnh (ngÃƒÂ y)",
        "Ã„ÂT - SÃ¡Â»â€˜ tiÃ¡Â»Ân",
        "Vay - SÃ¡Â»â€˜ tiÃ¡Â»Ân",
    ]
    pdf._table_header(dm_widths, dm_headers)

    for i, row in enumerate(data["durationMismatches"]):
        pdf._table_row(
            dm_widths,
            [
                row["investBank"],
                row["loanBank"],
                row["investEnd"],
                row["loanEnd"],
                str(row["daysDiff"]),
                _fmt_ty(row["investAmt"]),
                _fmt_ty(row["loanAmt"]),
            ],
            even=(i % 2 == 0),
            aligns=["L", "L", "C", "C", "C", "R", "R"],
        )

    # -- Output ------------------------------------------------------------
    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# CSV Exports
# ---------------------------------------------------------------------------

def generate_loans_csv() -> bytes:
    """Generate a CSV export of outstanding loans.

    Columns: Bank, Amount, Rate, Start Date, End Date, Status

    Returns:
        Raw CSV bytes (UTF-8 with BOM for Excel compatibility).
    """
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Bank", "Amount", "Rate", "Start Date", "End Date", "Status"])

    for row in FINANCIAL_DATA["loans"]:
        writer.writerow([
            row["bank"],
            row["amount"],
            f"{row['rate']:.1f}%",
            row["startDate"],
            row["endDate"],
            row["status"],
        ])

    # UTF-8 BOM so Excel auto-detects encoding
    csv_bytes = b"\xef\xbb\xbf" + buf.getvalue().encode("utf-8")
    return csv_bytes


def generate_investments_csv() -> bytes:
    """Generate a CSV export of outstanding investments.

    Columns: Bank, Amount, Rate, Type, Start Date, End Date, Status

    Returns:
        Raw CSV bytes (UTF-8 with BOM for Excel compatibility).
    """
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Bank", "Amount", "Rate", "Type", "Start Date", "End Date", "Status"])

    for row in FINANCIAL_DATA["investments"]:
        writer.writerow([
            row["bank"],
            row["amount"],
            f"{row['rate']:.1f}%",
            row["type"],
            row["startDate"],
            row["endDate"],
            row["status"],
        ])

    csv_bytes = b"\xef\xbb\xbf" + buf.getvalue().encode("utf-8")
    return csv_bytes
