#!/usr/bin/env python3
"""Gera um arquivo .xlsx mínimo (OOXML) a partir de um JSON {headers, rows}.

Sem dependências externas (usa apenas zipfile/xml da stdlib) para não exigir
openpyxl ou qualquer pacote adicional instalado no ambiente do usuário.
"""
import json
import sys
import zipfile
from xml.sax.saxutils import escape


def column_letter(index: int) -> str:
    letters = ""
    index += 1
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def cell_xml(col: int, row: int, value: str, style: int) -> str:
    ref = f"{column_letter(col)}{row}"
    text = escape("" if value is None else str(value))
    style_attr = f' s="{style}"' if style else ""
    return f'<c r="{ref}" t="inlineStr"{style_attr}><is><t xml:space="preserve">{text}</t></is></c>'


def build_sheet_xml(headers, rows) -> str:
    row_xmls = []
    header_cells = "".join(cell_xml(i, 1, h, style=1) for i, h in enumerate(headers))
    row_xmls.append(f'<row r="1">{header_cells}</row>')
    for r_idx, row in enumerate(rows, start=2):
        cells = "".join(cell_xml(i, r_idx, v, style=0) for i, v in enumerate(row))
        row_xmls.append(f'<row r="{r_idx}">{cells}</row>')
    dim_last_col = column_letter(max(len(headers), 1) - 1)
    dim_last_row = max(len(rows) + 1, 1)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="A1:{dim_last_col}{dim_last_row}"/>'
        "<sheetData>" + "".join(row_xmls) + "</sheetData>"
        "</worksheet>"
    )


CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
    '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
    '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
    "</Types>"
)

ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
    "</Relationships>"
)

WORKBOOK_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    "</Relationships>"
)

STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    '<fonts count="2">'
    "<font><sz val=\"11\"/><name val=\"Calibri\"/></font>"
    "<font><b/><sz val=\"11\"/><name val=\"Calibri\"/></font>"
    "</fonts>"
    '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
    '<borders count="1"><border/></borders>'
    '<cellStyleXfs count="1"><xf/></cellStyleXfs>'
    '<cellXfs count="2"><xf fontId="0"/><xf fontId="1"/></cellXfs>'
    "</styleSheet>"
)


def build_workbook_xml(sheet_name: str) -> str:
    safe_name = escape(sheet_name)[:31] or "Sheet1"
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets><sheet name="{safe_name}" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )


def main() -> int:
    if len(sys.argv) != 3:
        print("Uso: generate_xlsx.py <input.json> <output.xlsx>", file=sys.stderr)
        return 1

    input_path, output_path = sys.argv[1], sys.argv[2]
    with open(input_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    headers = payload.get("headers", [])
    rows = payload.get("rows", [])
    sheet_name = payload.get("sheet_name", "Sheet1")

    if not headers:
        print("input.json precisa definir ao menos 'headers'", file=sys.stderr)
        return 1

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES)
        zf.writestr("_rels/.rels", ROOT_RELS)
        zf.writestr("xl/workbook.xml", build_workbook_xml(sheet_name))
        zf.writestr("xl/_rels/workbook.xml.rels", WORKBOOK_RELS)
        zf.writestr("xl/styles.xml", STYLES)
        zf.writestr("xl/worksheets/sheet1.xml", build_sheet_xml(headers, rows))

    print(f"OK: {output_path} ({len(rows)} linhas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
