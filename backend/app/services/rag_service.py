"""RAG 服务 — 编排索引管道和问答流程。"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from app.core.config import settings
from app.services.chunker import chunk_text
from app.services.embedding_service import get_embedding_service
from app.services.llm_client import get_chat_client
from app.services.reranker_service import get_reranker
from app.services.vector_store import (
    delete_document_chunks,
    get_collection,
    upsert_chunks,
)

logger = logging.getLogger(__name__)


# ==================== 索引管道 ====================

async def index_document(
    document_id: int,
    public_id: str,
    title: str,
    text_content: str,
    owner_id: int | None = None,
) -> int:
    """将一个文档的文本内容分块、向量化、存入 ChromaDB。

    返回写入的分块数量。
    """
    if not text_content or not text_content.strip():
        return 0

    # 1. 分块
    chunks = chunk_text(
        text_content,
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
    )

    if not chunks:
        return 0

    # 2. 嵌入
    embed_svc = get_embedding_service()
    embeddings = await embed_svc.embed_texts(chunks)

    # 3. 构造元数据和 ID
    metadatas = []
    ids = []
    for i, chunk in enumerate(chunks):
        meta = {
            "document_id": document_id,
            "public_id": public_id,
            "title": title,
            "chunk_index": i,
        }
        if owner_id is not None:
            meta["owner_id"] = owner_id
        metadatas.append(meta)
        ids.append(f"doc_{document_id}_chunk_{i}")

    # 4. 写入 ChromaDB（先删旧的，避免重复）— Chroma 阻塞库，丢线程池
    try:
        await asyncio.to_thread(delete_document_chunks, document_id)
    except Exception:  # noqa: BLE001
        pass

    await asyncio.to_thread(
        upsert_chunks,
        chunks=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )

    logger.info("文档 %s（%s）索引完成，%d 个分块", public_id, title, len(chunks))
    return len(chunks)


def unindex_document(document_id: int) -> None:
    """从 ChromaDB 移除某个文档的所有分块（同步函数，供同步路由直接调用）。"""
    delete_document_chunks(document_id)


# ==================== 问答流程 ====================

async def answer_question(
    query: str,
    top_k_retrieve: int | None = None,
    top_k_rerank: int | None = None,
    local_only: bool | None = None,
    owner_id: int | None = None,
) -> dict:
    """完整 RAG 问答流程。"""
    import time

    from app.services.vector_store import query_similar

    start = time.time()

    top_k_retrieve = top_k_retrieve or settings.rag_top_k_retrieve
    top_k_rerank = top_k_rerank or settings.rag_top_k_rerank
    local_only = local_only if local_only is not None else settings.rag_local_only

    # 1. query 嵌入
    embed_svc = get_embedding_service()
    try:
        query_embedding = await embed_svc.embed_query(query)
    except Exception as exc:  # noqa: BLE001
        logger.error("Query 嵌入失败: %s", exc)
        return {
            "answer": "知识库服务暂时不可用，请稍后重试。",
            "citations": [],
            "chat_model": None,
            "embed_model": embed_svc.model,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "latency_ms": int((time.time() - start) * 1000),
        }

    # 2. 不带 where 检索（ChromaDB where 不支持 $exists 等高级算子）
    # ChromaDB 是同步阻塞库，在 async 路由里会卡住事件循环 — 用 to_thread 丢到线程池
    try:
        results = await asyncio.to_thread(
            query_similar,
            query_embedding=query_embedding,
            top_k=top_k_retrieve,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("向量检索失败: %s", exc)
        return {
            "answer": "知识库检索失败，请稍后重试。",
            "citations": [],
            "chat_model": None,
            "embed_model": embed_svc.model,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "latency_ms": int((time.time() - start) * 1000),
        }

    candidates = []
    docs = results.get("documents", [[]])[0] if results.get("documents") else []
    metas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
    dists = results.get("distances", [[]])[0] if results.get("distances") else []

    for doc, meta, dist in zip(docs, metas, dists):
        if not meta:
            continue
        # owner 隔离：如果分块有 owner_id，必须匹配当前用户（兼容旧分块 owner_id 为 None）
        if owner_id is not None:
            chunk_owner = meta.get("owner_id")
            if chunk_owner is not None and chunk_owner != owner_id:
                continue
        candidates.append({
            "content": doc,
            "document_id": meta.get("document_id"),
            "public_id": meta.get("public_id"),
            "title": meta.get("title"),
            "chunk_index": meta.get("chunk_index"),
            "distance": dist,
        })

    if not candidates:
        latency = int((time.time() - start) * 1000)
        return {
            "answer": "知识库中未找到相关内容。",
            "citations": [],
            "chat_model": None,
            "embed_model": embed_svc.model,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "latency_ms": latency,
        }

    # 3. 重排
    chat_client = None
    if settings.rerank_mode == "llm":
        try:
            chat_client = get_chat_client()
        except Exception:  # noqa: BLE001
            pass
    reranker = get_reranker(settings.rerank_mode, chat_client)
    candidates = await reranker.rerank(query, candidates, top_k=top_k_rerank)

    # 3.5 相似度阈值过滤 — 配置化（默认 0.35，让更多候选给 LLM 自己判断）
    min_similarity = settings.rag_min_similarity
    original_count = len(candidates)
    candidates = [
        c for c in candidates
        if c.get("rerank_score", 0) >= min_similarity
    ]
    if len(candidates) < original_count:
        logger.info(
            "相似度阈值过滤: %d → %d (阈值 %.2f)",
            original_count, len(candidates), min_similarity,
        )

    # 4. 引用组装
    citations = [
        {
            "public_id": c.get("public_id"),
            "title": c.get("title"),
            "chunk_index": c.get("chunk_index"),
            "snippet": c["content"][:200],
            "score": c.get("rerank_score", 0),
        }
        for c in candidates
    ]

    latency_before_llm = int((time.time() - start) * 1000)

    # 5. 本地模式：只返回检索片段
    if local_only:
        return {
            "answer": "（当前为本地检索模式，未调用大模型，以下为检索到的相关片段）",
            "citations": citations,
            "chat_model": None,
            "embed_model": embed_svc.model,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "latency_ms": latency_before_llm,
        }

    # 6. 拼接 Prompt

    # 6.1 注入用户的文件列表 metadata — 让 LLM 能答"我有哪些文件"、"最近的是什么"这类问题
    from app.services.vector_store import get_indexed_documents_summary
    # 同步 DB 查询 → 丢线程池避免卡事件循环
    docs_summary = await asyncio.to_thread(get_indexed_documents_summary, owner_id=owner_id)

    context_block = ""
    has_context = bool(candidates)
    if has_context:
        context_block = "\n\n【知识片段】\n" + "\n\n---\n\n".join(
            f"[来源: {c.get('title', '未知')}]\n{c['content']}" for c in candidates
        )

    docs_block = ""
    if docs_summary:
        docs_block = "\n\n【用户已上传的文件列表】\n" + docs_summary

    prompt = f"""你是用户的个人知识库助手。你可以：
1. 回答任何问题、和用户闲聊（不需要依赖知识库）
2. 当问题涉及用户文件时，使用下方的【文件列表】回答
3. 当知识片段与问题相关时，结合片段回答并标注来源

{docs_block}
{context_block}

用户问题：{query}

请用中文回答，自然亲切。"""

    # 7. 调用 Chat API
    try:
        chat_client = get_chat_client()
        llm_result = await chat_client.chat([
            {"role": "system", "content": "你是一个友好的 AI 助手，同时也是用户的个人知识库问答助手。"},
            {"role": "user", "content": prompt},
        ])

        latency = int((time.time() - start) * 1000)
        return {
            "answer": llm_result["content"],
            "citations": citations,
            "chat_model": llm_result["model"],
            "embed_model": embed_svc.model,
            "prompt_tokens": llm_result["prompt_tokens"],
            "completion_tokens": llm_result["completion_tokens"],
            "latency_ms": latency,
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("LLM 调用失败，降级返回检索片段: %s", exc)
        latency = int((time.time() - start) * 1000)
        return {
            "answer": "（大模型服务暂时不可用，以下为检索到的相关片段）",
            "citations": citations,
            "chat_model": None,
            "embed_model": embed_svc.model,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "latency_ms": latency,
        }
