"""Document 模型 + 关联表（document_texts / document_tags）。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from sqlalchemy import CHAR, BigInteger, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

ExtractStatus = Literal["pending", "done", "failed", "skipped"]
OcrStatus = Literal["pending", "processing", "done", "failed", "skipped"]


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(CHAR(26), unique=True, nullable=False)
    owner_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    original_name: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)

    extract_status: Mapped[ExtractStatus] = mapped_column(
        Enum("pending", "done", "failed", "skipped", name="extract_status"),
        default="pending",
        nullable=False,
    )
    extract_error: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    ocr_status: Mapped[OcrStatus] = mapped_column(
        Enum("pending", "processing", "done", "failed", "skipped", name="ocr_status"),
        default="skipped",
        nullable=False,
    )
    ocr_error: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(6), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(6), server_default=func.now(6))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(6), server_default=func.now(6), onupdate=func.now(6)
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(6), nullable=True)

    # 关系
    owner: Mapped[User] = relationship(back_populates="documents")
    text_content: Mapped[DocumentText | None] = relationship(
        back_populates="document", uselist=False, cascade="all, delete-orphan"
    )
    tags: Mapped[list[Tag]] = relationship(
        secondary="document_tags", back_populates="documents", cascade="save-update, merge"
    )


class DocumentText(Base):
    __tablename__ = "document_texts"

    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )
    content: Mapped[str] = mapped_column(Text().with_variant(LONGTEXT, "mysql"), nullable=False)

    document: Mapped[Document] = relationship(back_populates="text_content")


class DocumentTag(Base):
    """文档—标签 关联表（非 class-mapped，仅让 SQLAlchemy 认识）。"""

    __tablename__ = "document_tags"

    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )
