"""Compile markdown report and presentation slides into professional PDFs using ReportLab.
Full UTF-8 / Vietnamese Unicode support using system Arial fonts.
"""
import os
import re
from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Unicode TrueType Fonts from Windows Fonts
FONTS_DIR = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
pdfmetrics.registerFont(TTFont("Arial", str(FONTS_DIR / "arial.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Bold", str(FONTS_DIR / "arialbd.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Italic", str(FONTS_DIR / "ariali.ttf")))
pdfmetrics.registerFont(TTFont("Arial-BoldItalic", str(FONTS_DIR / "arialbi.ttf")))


def clean_markdown_inline(text: str) -> str:
    """Convert common markdown inline syntax to ReportLab XML tags."""
    # Escape XML entities first (except already formatted tags)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Bold **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Italic *text*
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    # Code `code`
    text = re.sub(r"`(.+?)`", r'<font face="Courier" color="#b91c1c"><b>\1</b></font>', text)
    # Math inline $...$
    text = re.sub(r"\$(.+?)\$", r"<i>\1</i>", text)
    # Re-enable allowed tags
    text = text.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
    text = text.replace("&lt;i&gt;", "<i>").replace("&lt;/i&gt;", "</i>")
    text = text.replace('&lt;font face="Courier" color="#b91c1c"&gt;', '<font face="Courier" color="#b91c1c">')
    text = text.replace("&lt;/font&gt;", "</font>")
    return text.strip()


def parse_markdown_table(lines: list[str]) -> list[list[str]]:
    """Parse markdown table lines into 2D text matrix."""
    table_data = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        # Skip separator line |-|-|
        if re.match(r"^\|(\s*:?-+:?\s*\|)+$", line):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        table_data.append(cells)
    return table_data


def build_report_pdf(md_path: Path, pdf_path: Path):
    """Compile final-report.md into A4 portrait academic PDF."""
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        fontName="Arial-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        alignment=1, # Center
        spaceAfter=12,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        fontName="Arial",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=16,
    )
    h1_style = ParagraphStyle(
        "ReportH1",
        fontName="Arial-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        "ReportH2",
        fontName="Arial-Bold",
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True,
    )
    h3_style = ParagraphStyle(
        "ReportH3",
        fontName="Arial-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        fontName="Arial",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6,
    )
    bullet_style = ParagraphStyle(
        "ReportBullet",
        fontName="Arial",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
        leftIndent=14,
        spaceAfter=3,
    )
    table_cell_style = ParagraphStyle(
        "ReportTableCell",
        fontName="Arial",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
    )
    table_header_style = ParagraphStyle(
        "ReportTableHeader",
        fontName="Arial-Bold",
        fontSize=7.5,
        leading=10,
        textColor=colors.white,
    )
    callout_style = ParagraphStyle(
        "ReportCallout",
        fontName="Arial-Italic",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1e3a8a"),
    )

    story = []
    i = 0
    in_code_block = False
    code_lines = []

    while i < len(lines):
        line = lines[i]

        # Handle code blocks
        if line.strip().startswith("```"):
            if in_code_block:
                in_code_block = False
                code_text = "<br/>".join([clean_markdown_inline(cl) for cl in code_lines])
                p_code = Paragraph(f'<font face="Courier" size="7.5">{code_text}</font>', body_style)
                code_table = Table([[p_code]], colWidths=[doc.width])
                code_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]))
                story.append(code_table)
                story.append(Spacer(1, 6))
                code_lines = []
            else:
                in_code_block = True
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Handle tables
        if line.strip().startswith("|") and line.strip().endswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i])
                i += 1
            raw_table = parse_markdown_table(table_lines)
            if raw_table and len(raw_table) > 1:
                col_count = len(raw_table[0])
                col_width = doc.width / col_count
                flowable_data = []
                for row_idx, row in enumerate(raw_table):
                    row_cells = []
                    for cell in row:
                        cell_style = table_header_style if row_idx == 0 else table_cell_style
                        row_cells.append(Paragraph(clean_markdown_inline(cell), cell_style))
                    flowable_data.append(row_cells)
                t = Table(flowable_data, colWidths=[col_width] * col_count)
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ]))
                story.append(Spacer(1, 4))
                story.append(t)
                story.append(Spacer(1, 6))
            continue

        stripped = line.strip()

        # Handle headings
        if stripped.startswith("# "):
            story.append(Paragraph(clean_markdown_inline(stripped[2:]), title_style))
            story.append(Spacer(1, 4))
        elif stripped.startswith("## "):
            story.append(Spacer(1, 6))
            story.append(Paragraph(clean_markdown_inline(stripped[3:]), h1_style))
            story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#e2e8f0"), spaceAfter=6))
        elif stripped.startswith("### "):
            story.append(Paragraph(clean_markdown_inline(stripped[4:]), h2_style))
        elif stripped.startswith("#### "):
            story.append(Paragraph(clean_markdown_inline(stripped[5:]), h3_style))
        elif stripped.startswith("> [!"):
            # Alert header
            alert_lines = [stripped]
            i += 1
            while i < len(lines) and lines[i].strip().startswith(">"):
                alert_lines.append(lines[i].strip()[1:].strip())
                i += 1
            alert_text = "<br/>".join([clean_markdown_inline(al) for al in alert_lines])
            callout_p = Paragraph(alert_text, callout_style)
            c_table = Table([[callout_p]], colWidths=[doc.width])
            c_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#3b82f6")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(c_table)
            story.append(Spacer(1, 6))
            continue
        elif stripped.startswith("- ") or stripped.startswith("* "):
            story.append(Paragraph(f"• {clean_markdown_inline(stripped[2:])}", bullet_style))
        elif re.match(r"^\d+\.\s+", stripped):
            num_match = re.match(r"^(\d+\.\s+)(.+)$", stripped)
            story.append(Paragraph(f"<b>{num_match.group(1)}</b>{clean_markdown_inline(num_match.group(2))}", bullet_style))
        elif stripped.startswith("---"):
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6))
        elif stripped:
            if "**Tên đề tài tiếng Anh:**" in stripped or "**Nhóm thực hiện:**" in stripped or "**Mã đề án:**" in stripped:
                story.append(Paragraph(clean_markdown_inline(stripped), subtitle_style))
            else:
                story.append(Paragraph(clean_markdown_inline(stripped), body_style))

        i += 1

    doc.build(story)
    print(f"Successfully generated report PDF: {pdf_path}")


def build_slides_pdf(md_path: Path, pdf_path: Path):
    """Compile slides.md into A4 landscape presentation PDF."""
    text = md_path.read_text(encoding="utf-8")
    raw_slides = text.split("<!-- slide -->")

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=landscape(A4),
        leftMargin=35,
        rightMargin=35,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()
    slide_title_style = ParagraphStyle(
        "SlideTitle",
        fontName="Arial-Bold",
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=10,
    )
    slide_h3_style = ParagraphStyle(
        "SlideH3",
        fontName="Arial-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=6,
        spaceAfter=4,
    )
    slide_body_style = ParagraphStyle(
        "SlideBody",
        fontName="Arial",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=4,
    )
    slide_bullet_style = ParagraphStyle(
        "SlideBullet",
        fontName="Arial",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1e293b"),
        leftIndent=12,
        spaceAfter=3,
    )
    slide_table_cell = ParagraphStyle(
        "SlideTableCell",
        fontName="Arial",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#0f172a"),
    )
    slide_table_header = ParagraphStyle(
        "SlideTableHeader",
        fontName="Arial-Bold",
        fontSize=7,
        leading=9,
        textColor=colors.white,
    )

    story = []

    for s_idx, slide in enumerate(raw_slides):
        slide = slide.strip()
        if not slide:
            continue
        if s_idx > 0:
            story.append(PageBreak())

        lines = slide.splitlines()
        j = 0
        while j < len(lines):
            line = lines[j]
            stripped = line.strip()

            if stripped.startswith("|") and stripped.endswith("|"):
                t_lines = []
                while j < len(lines) and lines[j].strip().startswith("|") and lines[j].strip().endswith("|"):
                    t_lines.append(lines[j])
                    j += 1
                raw_t = parse_markdown_table(t_lines)
                if raw_t and len(raw_t) > 1:
                    c_cnt = len(raw_t[0])
                    c_w = doc.width / c_cnt
                    f_data = []
                    for r_idx, row in enumerate(raw_t):
                        r_cells = []
                        for c in row:
                            st = slide_table_header if r_idx == 0 else slide_table_cell
                            r_cells.append(Paragraph(clean_markdown_inline(c), st))
                        f_data.append(r_cells)
                    st_table = Table(f_data, colWidths=[c_w] * c_cnt)
                    st_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                        ("PADDING", (0, 0), (-1, -1), 3),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ]))
                    story.append(Spacer(1, 4))
                    story.append(st_table)
                    story.append(Spacer(1, 4))
                continue

            if stripped.startswith("# ") or stripped.startswith("## "):
                title_clean = stripped.lstrip("#").strip()
                story.append(Paragraph(clean_markdown_inline(title_clean), slide_title_style))
                story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#3b82f6"), spaceAfter=8))
            elif stripped.startswith("### "):
                story.append(Paragraph(clean_markdown_inline(stripped[4:]), slide_h3_style))
            elif stripped.startswith("- ") or stripped.startswith("* "):
                story.append(Paragraph(f"• {clean_markdown_inline(stripped[2:])}", slide_bullet_style))
            elif re.match(r"^\d+\.\s+", stripped):
                n_match = re.match(r"^(\d+\.\s+)(.+)$", stripped)
                story.append(Paragraph(f"<b>{n_match.group(1)}</b>{clean_markdown_inline(n_match.group(2))}", slide_bullet_style))
            elif stripped and not stripped.startswith("---"):
                story.append(Paragraph(clean_markdown_inline(stripped), slide_body_style))

            j += 1

    doc.build(story)
    print(f"Successfully generated slides PDF: {pdf_path}")


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    report_md = base_dir / "reports" / "final-report.md"
    report_pdf = base_dir / "reports" / "final-report.pdf"
    slides_md = base_dir / "reports" / "slides.md"
    slides_pdf = base_dir / "reports" / "slides.pdf"

    build_report_pdf(report_md, report_pdf)
    build_slides_pdf(slides_md, slides_pdf)
