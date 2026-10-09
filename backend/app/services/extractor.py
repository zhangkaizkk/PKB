"""文本抽取 — TXT/MD/PDF/DOCX/XLSX/PPTX。"""

from __future__ import annotations

import io
import os

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


def _extract_pdf_path(path: str) -> tuple[str | None, str | None]:
    """从文件路径直接读 PDF — 避免整文件进内存（pypdf 支持 path 参数）。"""
    from pypdf import PdfReader

    try:
        reader = PdfReader(path)
    except Exception as exc:  # noqa: BLE001
        return None, f"PDF 打开失败: {exc}"
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
    """从已存储文件抽取（内存阈值保护：> 50MB 直接跳过）。"""
    from app.core.config import settings

    abs_path = get_storage().finalize_path(relative_path)
    max_bytes = settings.max_extract_size_mb * 1024 * 1024

    try:
        size = abs_path.stat().st_size
        if size > max_bytes:
            return None, f"文件超过 {settings.max_extract_size_mb}MB 阈值，已跳过文本抽取"

        # PDF 从路径直接读（pypdf/fitz.open 都接受 path），避免整文件进内存
        lower = abs_path.name.lower()
        if lower.endswith(".pdf"):
            return _extract_pdf_path(str(abs_path))

        # Office / txt / md 读 bytes（通常不大，已被阈值保护）
        data = abs_path.read_bytes()
        return extract_text_from_bytes(abs_path.name, data)
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}"
