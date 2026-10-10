"""重排服务 — 根据 RERANK_MODE 选择实现。"""

from __future__ import annotations

import logging
import re
from typing import Protocol

logger = logging.getLogger(__name__)


class Reranker(Protocol):
    """重排器协议。"""

    async def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int = 5,
    ) -> list[dict]: ...


# ==================== 模式 A：none（默认） ====================


class NoReranker:
    """不做重排，直接用相似度排序。

    ChromaDB cosine distance = 1 - cosine_similarity，范围 [0, 2]。
    直接用 similarity = 1 - distance 得到 [0, 1] 范围的相似度。
    """

    async def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        for c in candidates:
            dist = c.get("distance", 2.0)
            c["rerank_score"] = max(0.0, 1.0 - dist)
        sorted_candidates = sorted(candidates, key=lambda x: x.get("distance", 2.0))
        return sorted_candidates[:top_k]


# ==================== 模式 B：llm ====================


class LlmReranker:
    """用 Chat API 做重排。"""

    def __init__(self, chat_client):
        self.chat_client = chat_client

    async def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        numbered = "\n".join(f"[{i}] {c['content'][:300]}" for i, c in enumerate(candidates))
        prompt = f"""请根据用户问题，对以下文档片段按相关性从高到低排序。
只返回编号，用逗号分隔，最多返回 {top_k} 个，不要解释。

用户问题：{query}

文档片段：
{numbered}

排序结果（逗号分隔的编号）："""

        try:
            result = await self.chat_client.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            indices = self._parse_indices(result["content"], len(candidates), top_k)
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM 重排失败，降级为不重排: %s", exc)
            indices = list(range(min(top_k, len(candidates))))

        reranked = []
        for idx in indices:
            c = candidates[idx].copy()
            # 评分口径统一为向量相似度（1 - cosine distance），LLM 只负责排序
            dist = c.get("distance", 2.0)
            c["rerank_score"] = max(0.0, 1.0 - dist)
            reranked.append(c)
        return reranked

    @staticmethod
    def _parse_indices(text: str, total: int, top_k: int) -> list[int]:
        nums = re.findall(r"\d+", text)
        seen = set()
        result = []
        for n in nums:
            i = int(n)
            if 0 <= i < total and i not in seen:
                seen.add(i)
                result.append(i)
            if len(result) >= top_k:
                break
        # 解析失败时按原顺序兜底
        if not result:
            result = list(range(min(top_k, total)))
        return result


# ==================== 工厂 ====================


def get_reranker(rerank_mode: str, chat_client=None) -> Reranker:
    """根据配置创建重排器。"""
    if rerank_mode == "llm" and chat_client is not None:
        return LlmReranker(chat_client)
    return NoReranker()
