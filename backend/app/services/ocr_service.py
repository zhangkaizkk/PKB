"""OCR 服务 — 基于 PaddleOCR（本地传统 CV 模型，非大模型）。

支持：
- 图片文件（jpg/png/bmp/tiff/webp/gif）
- 扫描 PDF 逐页 OCR
- 原生 PDF 直接抽取（不走 OCR）

不支持：docx/xlsx/pptx 等（由 extractor.py 处理）
"""
from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path

import fitz  # PyMuPDF — 模块级导入，避免作用域问题

from app.core.config import settings
from app.services.storage import get_storage

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".gif"}
SCAN_PDF_MIN_TEXT_DENSITY = 20  # 字符数阈值：低于此值视为扫描 PDF

_ocr_instance = None


def _get_ocr():
    """懒加载 PaddleOCR 实例（全局复用，避免每次加载模型）。"""
    global _ocr_instance
    if _ocr_instance is None:
        from paddleocr import PaddleOCR
        _ocr_instance = PaddleOCR(
            use_angle_cls=True,
            lang=settings.ocr_lang,
            use_gpu=settings.ocr_use_gpu,
            show_log=False,
        )
    return _ocr_instance


def ocr_file(relative_path: str) -> tuple[str | None, str | None]:
    """对已存储的文件执行 OCR。

    返回 (content, error)：
    - content 非 None：OCR 成功
    - error 非 None：OCR 失败
    - 两者均 None：该文件类型不需要 OCR
    """
    ext = os.path.splitext(relative_path)[1].lower()
    abs_path = get_storage().finalize_path(relative_path)

    if ext in IMAGE_EXTS:
        return _ocr_image(abs_path)

    if ext == ".pdf":
        return _ocr_pdf(abs_path)

    # 其他类型不需要 OCR
    return None, None


def _ocr_image(abs_path: Path) -> tuple[str | None, str | None]:
    """单张图片 OCR。"""
    try:
        ocr = _get_ocr()
        result = ocr.ocr(str(abs_path), cls=True)

        # PaddleOCR 返回 [[[box, (text, conf)], ...]] 格式
        parts: list[str] = []
        if result and result[0]:
            for line in result[0]:
                if line and len(line) >= 2:
                    text = line[1][0] if isinstance(line[1], (list, tuple)) else str(line[1])
                    parts.append(text)

        content = "\n".join(parts).strip()
        return (content, None) if content else ("", None)

    except Exception as exc:  # noqa: BLE001
        return None, f"OCR 图片失败: {type(exc).__name__}: {exc}"


def _ocr_pdf(abs_path: Path) -> tuple[str | None, str | None]:
    """PDF OCR — 先检测是否为原生 PDF，扫描页才走 OCR。"""
    try:
        doc = fitz.open(str(abs_path))
        all_parts: list[str] = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            # 先尝试直接抽取文本
            native_text = page.get_text().strip()

            # 文本密度检测：低于阈值视为扫描页
            if len(native_text) < SCAN_PDF_MIN_TEXT_DENSITY:
                # 扫描页 → OCR
                page_text = _ocr_pdf_page(page)
                if page_text:
                    all_parts.append(page_text)
            else:
                # 原生 PDF → 直接用抽取的文本
                all_parts.append(native_text)

        doc.close()

        content = "\n\n".join(all_parts).strip()
        return (content, None) if content else ("", None)

    except Exception as exc:  # noqa: BLE001
        return None, f"OCR PDF 失败: {type(exc).__name__}: {exc}"


def _ocr_pdf_page(page) -> str:
    """将 PDF 页面渲染成图片后 OCR。"""
    try:
        # 渲染页面为图片（2x 分辨率以提升 OCR 精度）
        mat = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)

        # 保存为临时 PNG
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
            mat.save(tmp_path)

        try:
            ocr = _get_ocr()
            result = ocr.ocr(tmp_path, cls=True)

            parts: list[str] = []
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2:
                        text = line[1][0] if isinstance(line[1], (list, tuple)) else str(line[1])
                        parts.append(text)

            return "\n".join(parts).strip()

        finally:
            os.unlink(tmp_path)

    except Exception:  # noqa: BLE001
        return ""


def needs_ocr(mime_type: str, filename: str) -> bool:
    """判断文件是否需要 OCR。"""
    if not settings.ocr_enabled:
        return False

    ext = os.path.splitext(filename)[1].lower()
    if ext in IMAGE_EXTS:
        return True
    if ext == ".pdf":
        return True  # PDF 可能有扫描页
    return False
