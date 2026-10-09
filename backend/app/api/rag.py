"""RAG API — 问答、历史、重建索引、配置查询。"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.document import Document
from app.models.qa_history import QaHistory
from app.models.user import User
from app.schemas.rag import (
    RagAskRequest,
    RagAskResponse,
    RagConfigResponse,
    RagHistoryItem,
    RagIndexedDocument,
    RagIndexedListResponse,
    RagReindexResponse,
    RagStatsResponse,
)
from app.services.rag_service import answer_question, index_document
from app.services.vector_store import count_collected, get_chunk_counts

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])


# ============ 问答 ============

@router.post("/ask", response_model=RagAskResponse)
async def ask(
    payload: RagAskRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> RagAskResponse:
    result = await answer_question(
        query=payload.question,
        top_k_retrieve=payload.top_k_retrieve,
        top_k_rerank=payload.top_k_rerank,
        local_only=payload.local_only,
        owner_id=current.id,
    )

    # 写入问答历史
    history = QaHistory(
        owner_id=current.id,
        question=payload.question,
        answer=result["answer"],
        citations=result.get("citations"),
        chat_model=result.get("chat_model"),
        embed_model=result.get("embed_model"),
        prompt_tokens=result.get("prompt_tokens"),
        completion_tokens=result.get("completion_tokens"),
        latency_ms=result.get("latency_ms"),
    )
    db.add(history)
    db.commit()

    return RagAskResponse(**result)


# ============ 问答历史 ============

@router.get("/history", response_model=list[RagHistoryItem])
def get_history(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> list[RagHistoryItem]:
    stmt = (
        select(QaHistory)
        .where(QaHistory.owner_id == current.id)
        .order_by(desc(QaHistory.created_at))
        .limit(limit)
    )
    items = db.scalars(stmt).all()

    results = []
    for item in items:
        citations = item.citations if item.citations else None
        results.append(RagHistoryItem(
            id=item.id,
            question=item.question,
            answer=item.answer,
            citations=citations,
            chat_model=item.chat_model,
            embed_model=item.embed_model,
            prompt_tokens=item.prompt_tokens,
            completion_tokens=item.completion_tokens,
            latency_ms=item.latency_ms,
            created_at=item.created_at,
        ))
    return results


# ============ 重建索引 ============

@router.post("/reindex", response_model=RagReindexResponse)
async def reindex_all(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> RagReindexResponse:
    """重建当前用户所有文档的 RAG 索引（逐篇容错，一篇失败不影响整批）。"""
    stmt = select(Document).where(
        Document.owner_id == current.id,
        Document.extract_status == "done",
        Document.deleted_at.is_(None),
    )
    docs = db.scalars(stmt).all()

    total_chunks = 0
    indexed_count = 0
    failed_count = 0
    errors: list[str] = []

    for doc in docs:
        if not doc.text_content:
            continue
        try:
            chunk_count = await index_document(
                document_id=doc.id,
                public_id=doc.public_id,
                title=doc.title,
                text_content=doc.text_content.content,
                owner_id=current.id,
            )
        except Exception as exc:  # noqa: BLE001
            failed_count += 1
            errors.append(f"{doc.title}: {exc}")
            logger.error("文档 %s 索引失败: %s", doc.public_id, exc)
            continue

        if chunk_count > 0:
            doc.indexed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            total_chunks += chunk_count
            indexed_count += 1

    db.commit()

    msg = f"重建完成，{indexed_count} 个文档，{total_chunks} 个分块已索引"
    if failed_count:
        msg += f"；{failed_count} 个失败（API Key 不可用或网络问题）"
    return RagReindexResponse(message=msg)


@router.post("/reindex/{public_id}", response_model=RagReindexResponse)
async def reindex_one(
    public_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> RagReindexResponse:
    """重建单个文档的索引。"""
    doc = db.scalar(
        select(Document).where(Document.public_id == public_id, Document.owner_id == current.id)
    )
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "文件不存在")

    if not doc.text_content:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "文档尚无文本内容，请先等待抽取完成")

    chunk_count = await index_document(
        document_id=doc.id,
        public_id=doc.public_id,
        title=doc.title,
        text_content=doc.text_content.content,
        owner_id=current.id,
    )
    doc.indexed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()

    return RagReindexResponse(
        message=f"索引完成，{chunk_count} 个分块"
    )


# ============ 索引统计 ============

@router.get("/stats", response_model=RagStatsResponse)
def get_stats(
    current: User = Depends(get_current_user),
) -> RagStatsResponse:
    stats = count_collected()
    return RagStatsResponse(**stats)


@router.get("/indexed-documents", response_model=RagIndexedListResponse)
def get_indexed_documents(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> RagIndexedListResponse:
    """返回当前用户已建立索引的文档列表（含分块数）。"""
    from app.services.vector_store import purge_orphan_chunks

    stmt = (
        select(Document)
        .where(
            Document.owner_id == current.id,
            Document.indexed_at.isnot(None),
            Document.deleted_at.is_(None),
        )
        .order_by(desc(Document.indexed_at))
    )
    docs = db.scalars(stmt).all()

    # 自动清理孤儿 chunk（历史残留的已删除文档向量）
    valid_ids = {doc.id for doc in docs}
    purge_orphan_chunks(valid_ids)

    # 只统计活跃文档的分块数
    chunk_counts = get_chunk_counts(valid_document_ids=valid_ids)

    result = []
    for doc in docs:
        result.append(RagIndexedDocument(
            public_id=doc.public_id,
            title=doc.title,
            original_name=doc.original_name,
            chunk_count=chunk_counts.get(doc.id, 0),
            indexed_at=doc.indexed_at,
        ))

    return RagIndexedListResponse(documents=result)


# ============ 配置（脱敏）============

@router.get("/config", response_model=RagConfigResponse)
def get_config(
    current: User = Depends(get_current_user),
) -> RagConfigResponse:
    return RagConfigResponse(
        chat_model=settings.llm_chat_model,
        chat_base_url=settings.llm_base_url,
        embed_model=settings.embedding_model,
        embed_base_url=settings.embedding_base_url,
        embed_dim=settings.embedding_dim,
        rerank_mode=settings.rerank_mode,
        local_only=settings.rag_local_only,
    )
