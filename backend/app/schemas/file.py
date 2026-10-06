"""文件 schema — 文档 5.2 节严格匹配。"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.tag import TagResponse

ExtractStatus = Literal["pending", "done", "failed", "skipped"]


class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: str
    original_name: str
    title: str
    mime_type: str
    size_bytes: int
    sha256: str
    extract_status: ExtractStatus
    extract_error: str | None = None
    tags: list[TagResponse] = []
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    # 附加字段（不来自 ORM）
    preview_url: str | None = None
    download_url: str | None = None


class UploadItem(BaseModel):
    """POST /api/files/upload 单个条目。"""
    status: Literal["created", "duplicate", "failed"]
    file: FileResponse | None = None
    error: str | None = None


class UploadResponse(BaseModel):
    items: list[UploadItem]


class FileUpdateRequest(BaseModel):
    title: str | None = None
    original_name: str | None = None


class TagUpdateRequest(BaseModel):
    tag_ids: list[int] = []
