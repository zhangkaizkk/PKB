"""文件 API — 文档 5.2 节完整实现。"""
from __future__ import annotations

import asyncio
import os
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse as StarletteFileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
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
from app.services.storage import get_storage

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
    # 新建独立 Session（避免请求结束后原 session 关闭）
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
            background_tasks.add_task(_bg_extract, doc.id)

        await f.close()

    return UploadResponse(items=results)


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
    items, total = svc.list_documents(current.id, q=q, tag_id=tag_id, status=status, page=page, page_size=page_size)
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
        return StarletteFileResponse(path=str(abs_path), media_type=mime)

    # TXT / MD → 返回 JSON content
    if ext in _PREVIEW_TEXT_EXTS:
        abs_path = get_storage().finalize_path(doc.stored_path)
        try:
            content = abs_path.read_text(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            content = ""
        return {"content": content}

    # 其他 → 415
    raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "该格式暂不支持在线预览，请下载查看")


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
    doc = svc.update(doc, title=payload.title, original_name=payload.original_name)
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
    svc = FileService(db)
    doc = svc.get_by_public_id(public_id, current.id, include_trashed=True)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "文件不存在")
    svc.purge(doc)
