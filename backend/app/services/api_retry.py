"""统一 API 重试模块 — 所有 OpenAI 兼容调用都走这里。"""
from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAiCompatError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


# ==================== 模块级 httpx.AsyncClient 单例 ====================
# 每次 post_openai_compat 之前 async with AsyncClient 会重建 TLS 握手；
# 单例 + lifespan shutdown 关闭 = 复用连接池，索引 10 个文档省几十次握手。
_client: httpx.AsyncClient | None = None


def _build_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(60.0, connect=10.0),
        limits=httpx.Limits(max_connections=50, max_keepalive_connections=10),
    )


def get_client() -> httpx.AsyncClient:
    """懒加载单例。"""
    global _client
    if _client is None:
        _client = _build_client()
    return _client


async def close_client() -> None:
    """lifespan shutdown 时调用，优雅关闭连接池。"""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


# ==================== 重试策略 ====================

# 需要重试的异常类型（网络层）
_RETRY_EXCEPTIONS = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.ReadError,
)

# 需要重试的 HTTP 状态码（临时可恢复的服务端问题 + 限流）
_RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

# 不需要重试的状态码（客户端错误，重试没用）
_NO_RETRY_STATUS_CODES = {400, 401, 403, 404}


async def post_openai_compat(
    base_url: str,
    path: str,
    api_key: str,
    payload: dict,
    timeout: int = 60,
    max_retries: int = 3,
) -> dict:
    """统一调用 OpenAI 兼容端点 — 自带重试（429/5xx/网络异常）。

    - 4xx 客户端错误（400/401/403/404）：立即抛 OpenAiCompatError，不重试
    - 429/5xx 服务端错误 + 网络异常：重试 max_retries 次（指数退避 + 读 Retry-After）
    """
    url = f"{base_url.rstrip('/')}{path}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            client = get_client()
            resp = await client.post(
                url,
                headers=headers,
                json=payload,
                timeout=timeout,
            )
        except _RETRY_EXCEPTIONS as exc:
            last_exc = exc
            if attempt < max_retries:
                wait = _exponential_backoff(attempt)
                logger.warning(
                    "API 网络异常 (attempt %d/%d): %s — 等待 %.1fs 重试",
                    attempt, max_retries, exc, wait,
                )
                await asyncio.sleep(wait)
                continue
            raise OpenAiCompatError(f"API 调用网络失败（{max_retries} 次重试）: {exc}") from exc

        # HTTP 状态码分支
        status = resp.status_code

        if status in _NO_RETRY_STATUS_CODES:
            # 客户端错误，重试没用，立即抛
            truncated = resp.text[:500]
            raise OpenAiCompatError(
                f"API 调用失败 {status}: {truncated}",
                status_code=status,
            )

        if status in _RETRY_STATUS_CODES and attempt < max_retries:
            # 可重试的服务端错误 — 先看 Retry-After 头
            retry_after = resp.headers.get("Retry-After")
            try:
                wait = float(retry_after) if retry_after else _exponential_backoff(attempt)
            except ValueError:
                wait = _exponential_backoff(attempt)
            logger.warning(
                "API 返回 %d (attempt %d/%d) — 等待 %.1fs 重试",
                status, attempt, max_retries, wait,
            )
            await asyncio.sleep(wait)
            continue

        if status >= 400:
            # 其他 4xx/5xx 已经到最后一次了
            truncated = resp.text[:500]
            raise OpenAiCompatError(
                f"API 调用失败 {status}（{max_retries} 次重试耗尽）: {truncated}",
                status_code=status,
            )

        return resp.json()

    # 理论不会走到这里（最后一次循环要么 return 要么 raise）
    assert last_exc is not None
    raise OpenAiCompatError(f"API 调用最终失败: {last_exc}") from last_exc


def _exponential_backoff(attempt: int, multiplier: float = 1.0, min_s: float = 1.0, max_s: float = 8.0) -> float:
    """指数退避：1s → 2s → 4s → 8s（封顶）。"""
    return min(max_s, max(min_s, multiplier * (2 ** (attempt - 1))))
