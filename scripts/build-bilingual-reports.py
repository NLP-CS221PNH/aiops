"""Build two blank-result DOCX reports from the shared contract and markdown."""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

_IMPL = Path(__file__).resolve().parents[1]
if str(_IMPL) not in sys.path:
    sys.path.insert(0, str(_IMPL))

from src.data.common import IMPL, sha256, write_json

NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
RESULT_IDS = {"T1", "T2", "T3", "T4", "T5"}
FORBIDDEN = {"0", "-", "100%", "NOT_RUN"}


def _p(text: str, style: str = "Normal", size: int = 22, bold: bool = False, center: bool = False) -> str:
    align = "<w:jc w:val=\"center\"/>" if center else ""
    weight = "<w:b/>" if bold else ""
    return (
        f"<w:p><w:pPr><w:pStyle w:val=\"{style}\"/>{align}</w:pPr>"
        f"<w:r><w:rPr>{weight}<w:sz w:val=\"{size}\"/><w:rFonts w:ascii=\"Calibri\" w:hAnsi=\"Calibri\" w:eastAsia=\"Calibri\"/></w:rPr>"
        f"<w:t xml:space=\"preserve\">{escape(text)}</w:t></w:r></w:p>"
    )


def _page_break() -> str:
    return "<w:p><w:r><w:br w:type=\"page\"/></w:r></w:p>"


def _cell(text: str, result_cell: bool) -> str:
    if result_cell:
        text = ""
    return f"<w:tc><w:tcPr><w:tcW w:w=\"2000\" w:type=\"dxa\"/></w:tcPr><w:p><w:r><w:t xml:space=\"preserve\">{escape(text)}</w:t></w:r></w:p></w:tc>"


def _table(headers: list[str], rows: list[list[str]], result: bool) -> str:
    body = ["<w:tbl><w:tblPr><w:tblW w:w=\"5000\" w:type=\"pct\"/><w:tblBorders>",
            "<w:top w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"000000\"/>",
            "<w:left w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"000000\"/>",
            "<w:bottom w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"000000\"/>",
            "<w:right w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"000000\"/>",
            "<w:insideH w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"000000\"/>",
            "<w:insideV w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"000000\"/>",
            "</w:tblBorders></w:tblPr>"]
    body.append("<w:tr>" + "".join(_cell(h, False) for h in headers) + "</w:tr>")
    for row in rows:
        cells = []
        for index, value in enumerate(row):
            metric = result and index > 0
            if metric and value.strip() in FORBIDDEN:
                raise SystemExit(f"forbidden_result_placeholder:{value}")
            cells.append(_cell(value if not metric else "", True if metric else False))
        body.append("<w:tr>" + "".join(cells) + "</w:tr>")
    body.append("</w:tbl>")
    return "".join(body)


def parse_markdown(text: str) -> list[tuple[str, object]]:
    blocks: list[tuple[str, object]] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("|") and index + 1 < len(lines) and re.match(r"^\|[\s:\-|]+\|$", lines[index + 1] or ""):
            rows = []
            while index < len(lines) and lines[index].startswith("|"):
                rows.append([cell.strip() for cell in lines[index].strip().strip("|").split("|")])
                index += 1
            headers = rows[0]
            body = rows[2:]
            blocks.append(("table", (headers, body)))
            continue
        if line.startswith("# "):
            blocks.append(("h1", line[2:].strip()))
        elif line.startswith("## "):
            blocks.append(("h2", line[3:].strip()))
        elif line.startswith("### "):
            blocks.append(("h3", line[4:].strip()))
        elif line.startswith("```"):
            fence = []
            index += 1
            while index < len(lines) and not lines[index].startswith("```"):
                fence.append(lines[index])
                index += 1
            blocks.append(("pre", "\n".join(fence)))
        elif line.strip().startswith("- "):
            blocks.append(("li", line.strip()[2:]))
        elif line.strip():
            blocks.append(("p", line.strip()))
        index += 1
    return blocks


def document_xml(contract: dict, markdown: str, lang: str) -> str:
    parts = [
        f"<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>",
        f"<w:document xmlns:w=\"{NS}\"><w:body>",
        _p(contract["title"][lang], "Title", 36, True, True),
    ]
    for member in contract["team"]:
        parts.append(_p(f"{member['name']} — {member['student_id']}", "Normal", 24, False, True))
    parts.append(_p(contract["blank_results_sentence"][lang], "Normal", 22, True, True))
    parts.append(_page_break())
    parts.append(_p("Mục lục / Contents", "Heading1", 28, True))
    parts.append("<w:p><w:r><w:fldChar w:fldCharType=\"begin\"/></w:r><w:r><w:instrText xml:space=\"preserve\"> TOC \\o \"1-3\" \\h \\z \\u </w:instrText></w:r><w:r><w:fldChar w:fldCharType=\"separate\"/></w:r><w:r><w:t>Update fields in Word to refresh TOC.</w:t></w:r><w:r><w:fldChar w:fldCharType=\"end\"/></w:r></w:p>")
    parts.append(_page_break())
    result_mode = False
    for kind, payload in parse_markdown(markdown):
        if kind == "h1":
            parts.append(_p(payload, "Heading1", 32, True))
        elif kind == "h2":
            result_mode = payload.startswith("8.") or payload.lower().startswith("table t") or "Kết quả" in payload or "Empirical" in payload or payload.startswith("Bảng T")
            parts.append(_p(payload, "Heading2", 26, True))
            if payload.startswith("8.") or "Kết quả thực nghiệm" in payload or payload.startswith("8. Empirical"):
                parts.append(_page_break())
        elif kind == "h3":
            result_mode = payload.startswith("Bảng T") or payload.startswith("Table T")
            parts.append(_p(payload, "Heading3", 24, True))
        elif kind == "table":
            headers, body = payload
            is_result = result_mode or headers[0] in {"method", "row", "metric"}
            parts.append(_table(headers, body, is_result))
        elif kind == "pre":
            parts.append(_p(payload, "Normal", 18))
        elif kind == "li":
            parts.append(_p("• " + payload, "Normal", 22))
        else:
            parts.append(_p(payload, "Normal", 22))
    footer_id = "<w:sectPr><w:pgSz w:w=\"11906\" w:h=\"16838\"/><w:pgMar w:top=\"1134\" w:right=\"1134\" w:bottom=\"1134\" w:left=\"1134\"/><w:footerReference w:type=\"default\" r:id=\"rId2\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\"/></w:sectPr>"
    parts.append(footer_id)
    parts.append("</w:body></w:document>")
    return "".join(parts)


def _content_types() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
</Types>
"""


def _rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
</Relationships>
"""


def _doc_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
</Relationships>
"""


def _styles() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<w:styles xmlns:w="{NS}">
  <w:style w:type="paragraph" w:styleId="Normal"><w:name w:val="Normal"/><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Calibri"/><w:sz w:val="22"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:pPr><w:outlineLvl w:val="0"/></w:pPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:pPr><w:outlineLvl w:val="1"/></w:pPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:pPr><w:outlineLvl w:val="2"/></w:pPr></w:style>
</w:styles>
"""


def _footer() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<w:ftr xmlns:w="{NS}">
  <w:p><w:pPr><w:jc w:val="center"/></w:pPr>
    <w:r><w:fldChar w:fldCharType="begin"/></w:r>
    <w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>
    <w:r><w:fldChar w:fldCharType="end"/></w:r>
  </w:p>
</w:ftr>
"""


def _core(title: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <dc:title>{escape(title)}</dc:title>
  <dc:creator>CS221 AIOps RAG</dc:creator>
</cp:coreProperties>
"""


def write_docx(path: Path, document: str, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _content_types())
        archive.writestr("_rels/.rels", _rels())
        archive.writestr("word/_rels/document.xml.rels", _doc_rels())
        archive.writestr("word/document.xml", document)
        archive.writestr("word/styles.xml", _styles())
        archive.writestr("word/footer1.xml", _footer())
        archive.writestr("docProps/core.xml", _core(title))


def inspect_docx(path: Path, contract: dict) -> dict:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
        footer = archive.read("word/footer1.xml").decode("utf-8")
    names = [member["name"] for member in contract["team"]]
    ids = [member["student_id"] for member in contract["team"]]
    missing = [item for item in names + ids if item not in xml]
    forbidden_hits = []
    for token in FORBIDDEN:
        if f"<w:t xml:space=\"preserve\">{token}</w:t>" in xml or f"<w:t>{token}</w:t>" in xml:
            forbidden_hits.append(token)
    pages = xml.count('w:type="page"') + 1
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "team_present": not missing,
        "missing_team": missing,
        "forbidden_result_tokens": forbidden_hits,
        "has_toc_field": "TOC" in xml,
        "has_page_field": "PAGE" in footer,
        "page_breaks": pages,
        "layout_tool": "xml-inspect",
        "docx_layout_verified": False,
        "layout_reason": "Word/visual renderer not attached; XML structure checked only",
    }


def build(contract_path: Path, output_dir: Path) -> dict:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    reports = IMPL / "docs"
    outputs = {}
    inspections = []
    for lang, name in (("vi", "aiops-report-vi.docx"), ("en", "aiops-report-en.docx")):
        markdown = (reports / f"report-{lang}.md").read_text(encoding="utf-8")
        xml = document_xml(contract, markdown, lang)
        dest = output_dir / name
        write_docx(dest, xml, contract["title"][lang])
        info = inspect_docx(dest, contract)
        outputs[lang] = info
        inspections.append(info)
    receipt = {
        "schema_version": "cs221-docx-receipt-v1",
        "blank_results": True,
        "results_intentionally_blank": True,
        "contract_sha256": sha256(contract_path),
        "reports": outputs,
        "docx_layout_verified": False,
        "n_docx": 2,
    }
    write_json(output_dir / "docx-layout-receipt.json", receipt)
    return receipt


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build bilingual blank-result Word reports")
    parser.add_argument("--contract", default=str(IMPL / "configs" / "report-contract.json"))
    parser.add_argument("--blank-results", action="store_true")
    parser.add_argument("--output", default=str(IMPL / "artifacts" / "kaggle-delivery" / "v1"))
    args = parser.parse_args(argv)
    receipt = build(Path(args.contract), Path(args.output))
    print(json.dumps({"n_docx": receipt["n_docx"], "output": args.output, "blank": receipt["blank_results"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
