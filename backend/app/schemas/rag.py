"""RAG 相关 Schemas。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Citation(BaseModel):
    public_id: str | None = None
    title: str | None = None
    chunk_index: int | None = None
    snippet: str | None = None
    score: float | None = None


class RagAskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    top_k_retrieve: int | None = Field(default=None, ge=1, le=50)
    top_k_rerank: int | None = Field(default=None, ge=1, le=10)
    local_only: bool | None = None


class RagAskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    chat_model: str | None = None
    embed_model: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0


class RagHistoryItem(BaseModel):
    id: int
    question: str
    answer: str
    citations: list[Citation] | None = None
    chat_model: str | None = None
    embed_model: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_ms: int | None = None
    created_at: datetime


class RagStatsResponse(BaseModel):
    total_chunks: int
    unique_documents: int
    collection: str


class RagConfigResponse(BaseModel):
    chat_model: str
    chat_base_url: str
    embed_model: str
    embed_base_url: str
    embed_dim: int
    rerank_mode: str
    local_only: bool


class RagReindexResponse(BaseModel):
    message: str
    task_id: str | None = None  # 后台任务模式：POST /reindex 返回，GET /reindex/status 查进度


class RagIndexedDocument(BaseModel):
    public_id: str
    title: str
    original_name: str
    chunk_count: int
    indexed_at: datetime | None = None


class RagIndexedListResponse(BaseModel):
    documents: list[RagIndexedDocument]
