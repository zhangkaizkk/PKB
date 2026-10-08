"""Embedding 服务 — 调 /v1/embeddings。"""
from __future__ import annotations

import asyncio
import logging

from app.core.config import settings
from app.services.api_retry import OpenAiCompatError, post_openai_compat

logger = logging.getLogger(__name__)

# 并发信号量 — 避免触发服务商限流
_embed_semaphore = asyncio.Semaphore(3)


class OpenAiCompatEmbeddingService:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        dim: int = 1024,
        batch_size: int = 16,
        timeout: int = 60,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.dim = dim
        self.batch_size = batch_size
        self.timeout = timeout

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量嵌入文本列表。"""
        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            payload = {
                "model": self.model,
                "input": batch,
            }
            # 部分服务商支持 dimensions 参数
            if self.dim:
                payload["dimensions"] = self.dim

            try:
                async with _embed_semaphore:
                    data = await post_openai_compat(
                        base_url=self.base_url,
                        path="/embeddings",
                        api_key=self.api_key,
                        payload=payload,
                        timeout=self.timeout,
                    )
                batch_emb = [item["embedding"] for item in data["data"]]
                all_embeddings.extend(batch_emb)
            except OpenAiCompatError as exc:
                logger.error("Embedding API 调用失败: %s", exc)
                # 返回零向量占位（维度正确），让索引不中断
                zero_vector = [0.0] * self.dim
                all_embeddings.extend([zero_vector] * len(batch))
            except Exception as exc:  # noqa: BLE001
                logger.exception("Embedding 未知错误: %s", exc)
                zero_vector = [0.0] * self.dim
                all_embeddings.extend([zero_vector] * len(batch))

        return all_embeddings

    async def embed_query(self, query: str) -> list[float]:
        """嵌入单个查询。"""
        result = await self.embed_texts([query])
        return result[0]


def get_embedding_service() -> OpenAiCompatEmbeddingService:
    """从 settings 创建 Embedding 服务实例。"""
    return OpenAiCompatEmbeddingService(
        base_url=settings.embedding_base_url,
        api_key=settings.embedding_api_key,
        model=settings.embedding_model,
        dim=settings.embedding_dim,
        batch_size=settings.embedding_batch_size,
        timeout=settings.embedding_timeout_seconds,
    )
