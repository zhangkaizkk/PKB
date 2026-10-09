"""文件业务服务 — 上传、去重、列表、搜索、CRUD、标签绑定。"""
from __future__ import annotations

import datetime as dt
import mimetypes
import uuid
from typing import Iterable

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql import text
from ulid import ULID

from app.services.storage import get_storage
from app.utils.files import make_storage_path, make_title_from_filename, sanitize_filename
from app.utils.hashing import compute_sha256_stream

from ..core.config import settings
from ..models.document import Document, DocumentTag, DocumentText, ExtractStatus
from ..models.tag import Tag

# 扩展名 → MIME 白名单（不依赖 python-magic，避免 Dockerfile 加系统依赖）
_MIME_WHITELIST: dict[str, str] = {
    ".pdf":  "application/pdf",
    ".txt":  "text/plain",
    ".md":   "text/markdown",
    ".markdown": "text/markdown",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif":  "image/gif",
    ".webp": "image/webp",
    ".svg":  "image/svg+xml",
}


def _detect_mime(filename: str | None) -> str:
    """服务端判定 MIME：扩展名白名单优先，其次 mimetypes.guess_type，最后 octet-stream。
    不信任客户端上传时带的 content_type。"""
    if not filename:
        return "application/octet-stream"
    safe = sanitize_filename(filename)
    lower = safe.lower()
    # 白名单
    for ext, mime in _MIME_WHITELIST.items():
        if lower.endswith(ext):
            return mime
    # 标准库兜底
    guessed, _ = mimetypes.guess_type(safe)
    if guessed:
        return guessed
    return "application/octet-stream"


class FileService:
    """封装所有 Document + Tag 的 DB 操作 + Storage 操作。"""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.storage = get_storage()

    # ---------- 上传 ----------

    def upload(self, file: UploadFile, owner_id: int, tag_names: list[str] | None = None) -> Document | dict:
        """处理单个文件上传：tmp 写入 → SHA-256 去重 → 正式目录移动 → DB 插入。

        返回 Document 对象（新建）或 {"duplicate": True, "document": Document}（重复）。
        """
        # —— 1. tmp 写入 + SHA-256 流式计算 + 边写边校验大小 ——
        tmp_path = self.storage.new_tmp_path()
        sha_hash = ""
        size = 0
        truncated = False
        try:
            with tmp_path.open("wb") as out:
                h = __import__("hashlib").sha256()
                limit = settings.max_upload_size
                while True:
                    chunk = file.file.read(1 << 20)
                    if not chunk:
                        break
                    # 边写边校验 — 超限时立即中断，不占满磁盘
                    if size + len(chunk) > limit:
                        truncated = True
                        break
                    out.write(chunk)
                    h.update(chunk)
                    size += len(chunk)

            if truncated:
                self.storage.remove_tmp(tmp_path)
                raise HTTPException(
                    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    f"文件超过上传上限（{limit / 1024 / 1024 / 1024:.1f} GiB）",
                )
            sha_hash = h.hexdigest()
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            self.storage.remove_tmp(tmp_path)
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"文件读取失败: {exc}") from exc

        # —— 2. SHA-256 去重（按用户隔离：同用户重复传同文件才算重复）——
        dup = self._find_active_by_sha(sha_hash, owner_id)
        if dup:
            self.storage.remove_tmp(tmp_path)
            return {"duplicate": True, "document": dup}

        # —— 3. 安全文件名 + 存储路径 ——
        safe_name = sanitize_filename(file.filename or "untitled")
        now = dt.datetime.now()
        stored_path = make_storage_path(sha_hash[:8], safe_name, now.year, now.month)

        # —— 4. 移动到正式目录 ——
        self.storage.move_to_final(tmp_path, stored_path)

        # —— 5. 写 DB ——
        doc = Document(
            public_id=str(ULID()),
            owner_id=owner_id,
            original_name=file.filename or "untitled",
            title=make_title_from_filename(file.filename or "untitled"),
            stored_path=stored_path,
            mime_type=_detect_mime(file.filename),
            size_bytes=size,
            sha256=sha_hash,
            extract_status="pending",
        )
        self.db.add(doc)
        self.db.flush()  # 拿到 doc.id

        # 绑定 tags
        if tag_names:
            self._bind_tags(doc, tag_names)

        self.db.commit()
        self.db.refresh(doc)
        return doc

    # ---------- SHA-256 去重 ----------

    def _find_active_by_sha(self, sha: str, owner_id: int) -> Document | None:
        """按 sha256 + owner_id 查活跃文档（软删除的不算）。"""
        stmt = select(Document).where(
            Document.sha256 == sha,
            Document.owner_id == owner_id,
            Document.deleted_at.is_(None),
        )
        return self.db.execute(stmt).scalar_one_or_none()

    # ---------- 标签 ----------

    def _bind_tags(self, doc: Document, tag_names: Iterable[str]) -> None:
        for name in tag_names:
            name = name.strip()
            if not name:
                continue
            tag = self.db.query(Tag).filter(
                Tag.owner_id == doc.owner_id, Tag.name == name
            ).first()
            if not tag:
                tag = Tag(owner_id=doc.owner_id, name=name)
                self.db.add(tag)
                self.db.flush()
            doc.tags.append(tag)

    def sync_tags(self, doc: Document, tag_ids: list[int]) -> None:
        """完全覆盖文档的标签（只允许绑定本用户的标签）。"""
        doc.tags.clear()
        if not tag_ids:
            return
        tags = (
            self.db.query(Tag)
            .filter(Tag.id.in_(tag_ids), Tag.owner_id == doc.owner_id)
            .all()
        )
        for t in tags:
            doc.tags.append(t)

    # ---------- 列表 ----------

    def list_documents(
        self,
        owner_id: int,
        q: str | None = None,
        tag_id: int | None = None,
        status: str = "active",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Document], int]:
        page_size = max(1, min(100, page_size))
        page = max(1, page)

        stmt = select(Document).where(Document.owner_id == owner_id)

        # 软删除过滤
        if status == "trashed":
            stmt = stmt.where(Document.deleted_at.is_not(None))
        else:
            stmt = stmt.where(Document.deleted_at.is_(None))

        # 标签过滤
        if tag_id is not None:
            stmt = stmt.join(DocumentTag).where(DocumentTag.tag_id == tag_id)

        # 搜索 — FULLTEXT 优先，LIKE 兜底
        if q and q.strip():
            results = self._search_fulltext(owner_id, q.strip())
            if results:
                ids = [r[0] for r in results]
                stmt = stmt.where(Document.id.in_(ids))
            else:
                like = f"%{q.strip()}%"
                stmt = stmt.where(
                    or_(
                        Document.title.ilike(like),
                        Document.original_name.ilike(like),
                    )
                )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one() or 0

        stmt = stmt.order_by(Document.created_at.desc())
        stmt = stmt.options(selectinload(Document.tags))
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def _search_fulltext(self, owner_id: int, q: str) -> list[tuple[int]]:
        """原生 SQL 做 FULLTEXT 搜索（MySQL 8.0 ngram）。"""
        try:
            # 文档/标题 FULLTEXT
            r1 = self.db.execute(
                text("""
                    SELECT id FROM documents
                    WHERE owner_id = :owner
                      AND deleted_at IS NULL
                      AND MATCH(title, original_name) AGAINST(:q IN NATURAL LANGUAGE MODE)
                """),
                {"owner": owner_id, "q": q},
            ).all()

            # 文本 FULLTEXT（JOIN）
            r2 = self.db.execute(
                text("""
                    SELECT d.id FROM documents d
                    JOIN document_texts dt ON dt.document_id = d.id
                    WHERE d.owner_id = :owner
                      AND d.deleted_at IS NULL
                      AND MATCH(dt.content) AGAINST(:q IN NATURAL LANGUAGE MODE)
                """),
                {"owner": owner_id, "q": q},
            ).all()

            return list(set(r1 + r2))
        except Exception:  # noqa: BLE001 — FULLTEXT 失败就让 LIKE 兜底
            return []

    # ---------- 查询 ----------

    def get_by_public_id(self, public_id: str, owner_id: int | None = None, include_trashed: bool = False) -> Document | None:
        stmt = select(Document).where(Document.public_id == public_id)
        if owner_id is not None:
            stmt = stmt.where(Document.owner_id == owner_id)
        if not include_trashed:
            stmt = stmt.where(Document.deleted_at.is_(None))
        stmt = stmt.options(selectinload(Document.tags))
        return self.db.execute(stmt).scalar_one_or_none()

    # ---------- 更新 ----------

    def update(self, doc: Document, *, title: str | None = None, original_name: str | None = None) -> Document:
        if title is not None:
            doc.title = title
        if original_name is not None:
            doc.original_name = original_name
        self.db.commit()
        self.db.refresh(doc)
        return doc

    # ---------- 软删除 ----------

    def soft_delete(self, doc: Document) -> Document:
        doc.deleted_at = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def restore(self, doc: Document) -> Document:
        doc.deleted_at = None
        self.db.commit()
        self.db.refresh(doc)
        return doc

    # ---------- 彻底删除 ----------

    def purge(self, doc: Document) -> None:
        self.storage.physical_delete(doc.stored_path)
        self.db.delete(doc)
        self.db.commit()

    def purge_all_trashed(self, owner_id: int) -> int:
        """彻底删除当前用户所有回收站文件，返回删除数量。"""
        from app.models.document import Document

        trashed = (
            self.db.query(Document)
            .where(Document.owner_id == owner_id, Document.deleted_at.is_not(None))
            .all()
        )
        count = 0
        for doc in trashed:
            try:
                self.storage.physical_delete(doc.stored_path)
            except Exception:  # noqa: BLE001
                pass
            self.db.delete(doc)
            count += 1
        self.db.commit()
        return count

    # ---------- 文本抽取回调 ----------

    def save_extraction_result(self, doc_id: int, content: str | None, error: str | None) -> None:
        doc = self.db.get(Document, doc_id)
        if not doc:
            return
        if content is not None and content.strip():
            doc.extract_status = "done"
            existing = self.db.query(DocumentText).filter(DocumentText.document_id == doc_id).first()
            if existing:
                existing.content = content
            else:
                self.db.add(DocumentText(document_id=doc_id, content=content))
        elif content is not None:  # 空内容也算成功
            doc.extract_status = "done"
        elif error is not None:
            doc.extract_status = "failed"
            doc.extract_error = error
        else:  # 不支持格式
            doc.extract_status = "skipped"
        self.db.commit()
