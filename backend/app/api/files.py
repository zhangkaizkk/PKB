"""文件 API — 文档 5.2 节完整实现 + OCR + RAG 后台任务。"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import UTC, datetime
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse as StarletteFileResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.common import Paginated
from app.schemas.file import (
    FileResponse,
    FileUpdateRequest,
    TagUpdateRequest,
    UploadItem,
    UploadResponse,
)
from app.services.extractor import extract_text_from_stored
from app.services.file_service import FileService
from app.services.ocr_service import needs_ocr, ocr_file
from app.services.rag_service import index_document
from app.services.storage import get_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])

# 文本预览支持的 MIME
_PREVIEW_TEXT_EXTS = {".txt", ".md", ".markdown"}
_PREVIEW_IMAGE_PREFIX = "image/"
_PREVIEW_PDF_MIME = "application/pdf"


def _enrich(doc: Document) -> FileResponse:
    """给 FileResponse 附加 preview_url / download_url。"""
    base = FileResponse.model_validate(doc)
    base.preview_url = f"/api/files/{doc.public_id}/preview"
    base.download_url = f"/api/files/{doc.public_id}/download"
    return base


def _bg_extract(doc_id: int) -> None:
    """后台文本抽取（同步函数，FastAPI BackgroundTasks 兼容）。"""
    from app.db.session import SessionLocal
    from app.services.file_service import FileService

    db = SessionLocal()
    try:
        svc = FileService(db)
        doc = db.get(Document, doc_id)
        if not doc:
            return
        content, error = extract_text_from_stored(doc.stored_path)
        if content is not None:
            svc.save_extraction_result(doc_id, content, None)
        elif error is not None:
            svc.save_extraction_result(doc_id, None, error)
        else:
            svc.save_extraction_result(doc_id, None, None)  # skipped
    finally:
        db.close()


def _bg_ocr_and_index(doc_id: int) -> None:
    """OCR + RAG 索引后台任务（同步包装 async）。"""
    from app.db.session import SessionLocal
    from app.models.document import DocumentText

    db = SessionLocal()
    try:
        doc = db.get(Document, doc_id)
        if not doc:
            return

        # ======= 阶段 1: OCR =======
        if needs_ocr(doc.mime_type or "", doc.original_name or doc.title):
            doc.ocr_status = "processing"
            db.commit()

            ocr_content, ocr_error = ocr_file(doc.stored_path)

            if ocr_error:
                doc.ocr_status = "failed"
                doc.ocr_error = ocr_error
                logger.warning("文档 %s OCR 失败: %s", doc.public_id, ocr_error)
            elif ocr_content is not None:
                doc.ocr_status = "done"

                # 合并 OCR 内容到 document_texts
                existing = db.get(DocumentText, doc_id)
                if existing:
                    # 已有抽取文本 → 在后面追加 OCR 内容
                    if ocr_content and ocr_content not in existing.content:
                        existing.content = existing.content + "\n\n[OCR 识别内容]\n" + ocr_content
                else:
                    # 没有抽取文本 → 直接用 OCR 内容
                    if ocr_content:
                        db.add(DocumentText(document_id=doc_id, content=ocr_content))

                # 如果之前 extract_status 是 skipped 或空，现在标记为 done
                if doc.extract_status in ("skipped", "pending"):
                    doc.extract_status = "done"
            else:
                doc.ocr_status = "skipped"
        else:
            doc.ocr_status = "skipped"

        db.commit()

        # ======= 阶段 2: RAG 索引 =======
        doc = db.get(Document, doc_id)  # 刷新
        if doc and doc.text_content and doc.text_content.content.strip():
            try:
                # asyncio.run() 每次在线程池线程里新建临时事件循环，安全且无跨 loop 冲突
                asyncio.run(_do_index(doc))
                doc.indexed_at = datetime.now(UTC).replace(tzinfo=None)
                db.commit()
            except Exception as exc:  # noqa: BLE001
                logger.error("文档 %s RAG 索引失败: %s", doc.public_id, exc)

    except Exception as exc:  # noqa: BLE001
        logger.exception("后台 OCR/索引任务异常: %s", exc)
    finally:
        db.close()


async def _do_index(doc: Document) -> None:
    """异步索引包装。"""
    if doc.text_content:
        await index_document(
            document_id=doc.id,
            public_id=doc.public_id,
            title=doc.title,
            text_content=doc.text_content.content,
            owner_id=doc.owner_id,
        )


# ============ 上传 ============


@router.post("/upload", response_model=UploadResponse)
async def upload_files(
    background_tasks: BackgroundTasks,
    files: Annotated[list[UploadFile], File()],
    tag_names: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> UploadResponse:
    tag_list = [t.strip() for t in tag_names.split(",") if t.strip()] if tag_names else []
    svc = FileService(db)
    results: list[UploadItem] = []

    for f in files:
        try:
            res = svc.upload(f, current.id, tag_list or None)
        except HTTPException as exc:
            results.append(UploadItem(status="failed", error=exc.detail))
            # 必须 reset，否则后续上传文件指针异常
            await f.close()
            continue

        if isinstance(res, dict) and res.get("duplicate"):
            doc = res["document"]
            results.append(UploadItem(status="duplicate", file=_enrich(doc)))
        else:
            doc: Document = res
            results.append(UploadItem(status="created", file=_enrich(doc)))
            # 文本抽取
            background_tasks.add_task(_bg_extract, doc.id)
            # OCR + RAG 索引（抽取完成后执行）
            background_tasks.add_task(_bg_ocr_and_index, doc.id)

        await f.close()

    return UploadResponse(items=results)


# ============ OCR 状态查询 ============


@router.get("/{public_id}/ocr-status", response_model=dict)
def get_ocr_status(
    public_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    svc = FileService(db)
    doc = svc.get_by_public_id(public_id, current.id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "文件不存在")

    return {
        "public_id": doc.public_id,
        "ocr_status": doc.ocr_status,
        "ocr_error": doc.ocr_error,
        "indexed_at": doc.indexed_at.isoformat() if doc.indexed_at else None,
    }


# ============ 列表 ============


@router.get("", response_model=Paginated[FileResponse])
def list_files(
    q: str | None = None,
    tag_id: int | None = None,
    status: str = Query("active", pattern="^(active|trashed)$"),
    page: int = 1,
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> Paginated[FileResponse]:
    svc = FileService(db)
    items, total = svc.list_documents(
        current.id, q=q, tag_id=tag_id, status=status, page=page, page_size=page_size
    )
    return Paginated(
        items=[_enrich(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


# ============ 详情 ============


@router.get("/{public_id}", response_model=FileResponse)
def get_file(
    public_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> FileResponse:
    svc = FileService(db)
    doc = svc.get_by_public_id(public_id, current.id, include_trashed=True)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "文件不存在")
    return _enrich(doc)


# ============ 预览 ============


@router.get("/{public_id}/preview")
def preview_file(
    public_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    svc = FileService(db)
    doc = svc.get_by_public_id(public_id, current.id, include_trashed=True)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "文件不存在")

    ext = os.path.splitext(doc.original_name or doc.title)[1].lower()
    mime = (doc.mime_type or "").lower()

    # 图片 / PDF → 直接返回文件流（前端 iframe 展示）
    if mime.startswith(_PREVIEW_IMAGE_PREFIX) or mime == _PREVIEW_PDF_MIME:
        abs_path = get_storage().finalize_path(doc.stored_path)
        if not abs_path.exists():
            raise HTTPException(status.HTTP_404_NOT_FOUND, "文件不在磁盘")
        return StarletteFileResponse(
            path=str(abs_path),
            media_type=mime,
            headers={"X-Content-Type-Options": "nosniff"},
        )

    # TXT / MD → 返回 JSON content
    if ext in _PREVIEW_TEXT_EXTS:
        abs_path = get_storage().finalize_path(doc.stored_path)
        try:
            content = abs_path.read_text(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            content = ""
        return {"content": content}

    # 其他 → 415
    raise HTTPException(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "该格式暂不支持在线预览，请下载查看"
    )


# ============ 下载 ============


@router.get("/{public_id}/download")
def download_file(
    public_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    svc = FileService(db)
    doc = svc.get_by_public_id(public_id, current.id, include_trashed=True)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "文件不存在")

    abs_path = get_storage().finalize_path(doc.stored_path)
    if not abs_path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "文件不在磁盘")

    safe = doc.original_name or doc.title or "file"
    return StarletteFileResponse(
        path=str(abs_path),
        filename=safe,
        media_type=doc.mime_type or "application/octet-stream",
    )


# ============ 更新 ============


@router.patch("/{public_id}", response_model=FileResponse)
def update_file(
    public_id: str,
    payload: FileUpdateRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> FileResponse:
    svc = FileService(db)
    doc = svc.get_by_public_id(public_id, current.id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "文件不存在")

    # 如果只给了 original_name 没给 title，自动从文件名派生 title（去掉扩展名）
    title = payload.title
    if title is None and payload.original_name is not None:
        from app.utils.files import make_title_from_filename

        title = make_title_from_filename(payload.original_name)

    doc = svc.update(doc, title=title, original_name=payload.original_name)
    return _enrich(doc)


# ============ 标签更新 ============


@router.put("/{public_id}/tags", response_model=FileResponse)
def update_tags(
    public_id: str,
    payload: TagUpdateRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> FileResponse:
    svc = FileService(db)
    doc = svc.get_by_public_id(public_id, current.id, include_trashed=True)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "文件不存在")
    svc.sync_tags(doc, payload.tag_ids)
    db.commit()
    db.refresh(doc)
    return _enrich(doc)


# ============ 批量清空回收站（必须放在 /{public_id} 之前，避免被路径参数吞掉） ============


@router.delete("/purge-all", status_code=200)
def purge_all(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    from app.models.document import Document
    from app.services.rag_service import unindex_document

    # 先收集所有待删的 doc_id，批量清向量
    doc_ids = [
        row[0]
        for row in db.query(Document.id)
        .where(Document.owner_id == current.id, Document.deleted_at.is_not(None))
        .all()
    ]
    for doc_id in doc_ids:
        try:
            unindex_document(doc_id)
        except Exception:  # noqa: BLE001
            pass

    svc = FileService(db)
    count = svc.purge_all_trashed(current.id)
    return {"purged_count": count}


# ============ 软删除 ============


@router.delete("/{public_id}", response_model=FileResponse)
def soft_delete(
    public_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> FileResponse:
    svc = FileService(db)
    doc = svc.get_by_public_id(public_id, current.id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "文件不存在")
    doc = svc.soft_delete(doc)
    return _enrich(doc)


# ============ 恢复 ============


@router.post("/{public_id}/restore", response_model=FileResponse)
def restore(
    public_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> FileResponse:
    svc = FileService(db)
    doc = svc.get_by_public_id(public_id, current.id, include_trashed=True)
    if not doc or not doc.deleted_at:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "回收站中未找到该文件")
    doc = svc.restore(doc)
    return _enrich(doc)


# ============ 彻底删除 ============


@router.delete("/{public_id}/purge", status_code=204)
def purge(
    public_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> None:
    from app.services.rag_service import unindex_document

    svc = FileService(db)
    doc = svc.get_by_public_id(public_id, current.id, include_trashed=True)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "文件不存在")
    # 先从向量库移除
    try:
        unindex_document(doc.id)
    except Exception:  # noqa: BLE001
        pass
    svc.purge(doc)
