"""文本抽取 — TXT/MD/PDF/DOCX/XLSX/PPTX。"""
from __future__ import annotations

import io
import os
from pathlib import Path

from app.services.storage import get_storage

SUPPORTED_EXTS = {".txt", ".md", ".markdown", ".pdf", ".docx", ".xlsx", ".pptx"}


def extract_text_from_bytes(filename: str, data: bytes) -> tuple[str | None, str | None]:
    """尝试从文件 bytes 抽取文本。

    返回 (content, error) —— 成功时 content 非 None，失败时 error 非 None，
    跳过（不支持格式）时返回 (None, None)。
    """
    ext = os.path.splitext(filename)[1].lower()

    try:
        if ext in (".txt", ".md", ".markdown"):
            return data.decode("utf-8", errors="replace"), None

        if ext == ".pdf":
            return _extract_pdf(data)

        if ext == ".docx":
            return _extract_docx(data)

        if ext == ".xlsx":
            return _extract_xlsx(data)

        if ext == ".pptx":
            return _extract_pptx(data)

    except Exception as exc:  # noqa: BLE001 — 任何抽取失败都写 extract_error
        return None, f"{type(exc).__name__}: {exc}"

    # 不支持的格式 → skipped
    return None, None


def _extract_pdf(data: bytes) -> tuple[str | None, str | None]:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        try:
            t = page.extract_text()
            if t:
                parts.append(t)
        except Exception:  # noqa: BLE001
            continue
    return ("\n".join(parts), None) if parts else ("", None)


def _extract_docx(data: bytes) -> tuple[str | None, str | None]:
    from docx import Document

    doc = Document(io.BytesIO(data))
    return ("\n".join(p.text for p in doc.paragraphs), None)


def _extract_xlsx(data: bytes) -> tuple[str | None, str | None]:
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(data), data_only=True, read_only=True)
    parts: list[str] = []
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            line = "\t".join(str(c) for c in row if c is not None)
            if line:
                parts.append(line)
    return ("\n".join(parts), None)


def _extract_pptx(data: bytes) -> tuple[str | None, str | None]:
    from pptx import Presentation

    prs = Presentation(io.BytesIO(data))
    parts: list[str] = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    text = para.text.strip()
                    if text:
                        parts.append(text)
            if shape.has_table:
                for row in shape.table.rows:
                    cells = [c.text.strip() for c in row.cells]
                    parts.append("\t".join(cells))
    return ("\n".join(parts), None)


def extract_text_from_stored(relative_path: str) -> tuple[str | None, str | None]:
    """从已存储文件抽取。"""
    abs_path = get_storage().finalize_path(relative_path)
    try:
        data = abs_path.read_bytes()
        return extract_text_from_bytes(abs_path.name, data)
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}"
