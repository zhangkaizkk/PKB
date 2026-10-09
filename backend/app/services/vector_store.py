"""向量存储 — ChromaDB 持久化。"""
from __future__ import annotations

import logging
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: chromadb.ClientAPI | None = None


def get_chroma_client() -> chromadb.ClientAPI:
    """获取全局 ChromaDB 客户端（单例）。"""
    global _client
    if _client is None:
        persist_dir = Path(settings.chroma_persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)

        _client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_collection() -> chromadb.Collection:
    """获取（或创建）文档集合。"""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=settings.chroma_collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def upsert_chunks(
    chunks: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
    ids: list[str],
) -> None:
    """批量写入（或更新）分块向量。"""
    collection = get_collection()
    collection.upsert(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )


def delete_document_chunks(document_id: int) -> None:
    """删除某个文档的所有分块。"""
    collection = get_collection()
    collection.delete(where={"document_id": document_id})


def query_similar(
    query_embedding: list[float],
    top_k: int = 20,
    where_filter: dict | None = None,
) -> dict:
    """相似度检索。"""
    collection = get_collection()
    kwargs: dict = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if where_filter:
        kwargs["where"] = where_filter

    return collection.query(**kwargs)


def count_collected() -> dict:
    """获取集合统计。"""
    client = get_chroma_client()
    try:
        collection = client.get_collection(settings.chroma_collection_name)
    except Exception:  # noqa: BLE001 — 集合不存在
        return {
            "total_chunks": 0,
            "unique_documents": 0,
            "collection": settings.chroma_collection_name,
        }

    total = collection.count()

    # 按 document_id 统计唯一文档数
    if total > 0:
        peek = collection.peek(limit=min(total, 10000))
        metadatas = peek.get("metadatas") or []
        doc_ids = set()
        for m in metadatas:
            if m and "document_id" in m:
                doc_ids.add(m["document_id"])
        unique_docs = len(doc_ids)
    else:
        unique_docs = 0

    return {
        "total_chunks": total,
        "unique_documents": unique_docs,
        "collection": settings.chroma_collection_name,
    }


def get_chunk_counts(valid_document_ids: set[int] | None = None) -> dict[int, int]:
    """返回每个文档在 ChromaDB 中的分块数量 {document_id: chunk_count}。

    若传入 valid_document_ids，则只统计这些文档（过滤掉孤儿 chunk）。
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(settings.chroma_collection_name)
    except Exception:  # noqa: BLE001 — 集合不存在
        return {}

    result = collection.get(include=["metadatas"])
    metadatas = result.get("metadatas") or []

    counts: dict[int, int] = {}
    for m in metadatas:
        if m and "document_id" in m:
            did = m["document_id"]
            if valid_document_ids is not None and did not in valid_document_ids:
                continue
            counts[did] = counts.get(did, 0) + 1

    return counts


def purge_orphan_chunks(valid_document_ids: set[int]) -> int:
    """删除 ChromaDB 中不属于任何活跃文档的孤儿分块，返回删除数量。"""
    client = get_chroma_client()
    try:
        collection = client.get_collection(settings.chroma_collection_name)
    except Exception:  # noqa: BLE001 — 集合不存在
        return 0

    result = collection.get(include=["metadatas"])
    ids = result.get("ids") or []
    metadatas = result.get("metadatas") or []

    orphan_ids: list[str] = []
    for chunk_id, m in zip(ids, metadatas):
        if m and "document_id" in m:
            if m["document_id"] not in valid_document_ids:
                orphan_ids.append(chunk_id)
        else:
            # 没有 metadata 的 chunk 也是孤儿
            orphan_ids.append(chunk_id)

    if orphan_ids:
        collection.delete(ids=orphan_ids)
        logger.info("清理 ChromaDB 孤儿分块 %d 条", len(orphan_ids))

    return len(orphan_ids)


def get_indexed_documents_summary() -> str:
    """
    返回当前活跃的已索引文档列表（纯文本，注入 LLM prompt）。
    格式: "1. 个人简历 (3 chunks, 索引于 2026/10/08 08:49)"
    复用 SessionLocal，不新建 engine。
    """
    from datetime import datetime, timezone

    from app.db.session import SessionLocal
    from app.models.document import Document

    db = SessionLocal()
    try:
        docs = (
            db.query(Document.id, Document.title, Document.original_name, Document.indexed_at)
            .filter(Document.deleted_at.is_(None), Document.indexed_at.isnot(None))
            .order_by(Document.indexed_at.desc())
            .limit(20)
            .all()
        )
    except Exception:  # noqa: BLE001
        return ""
    finally:
        db.close()

    if not docs:
        return ""

    # 查每个文档的 chunk_count（从 ChromaDB）
    try:
        counts = get_chunk_counts()
    except Exception:  # noqa: BLE001
        counts = {}

    lines = []
    for i, row in enumerate(docs, 1):
        did, title, original_name, indexed_at = row
        display_title = title or original_name or "未命名"
        chunk_count = counts.get(did, 0)
        if indexed_at is not None:
            # 数据库返回的是 naive UTC（或 MySQL 的 +08:00 时间），直接 strftime
            time_str = indexed_at.strftime("%Y/%m/%d %H:%M")
        else:
            time_str = "-"
        lines.append(f"{i}. {display_title} ({chunk_count} 个分块, 索引于 {time_str})")

    return "\n".join(lines)
