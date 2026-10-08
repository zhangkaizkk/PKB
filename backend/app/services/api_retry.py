"""统一 API 重试模块 — 所有 OpenAI 兼容调用都走这里。"""
from __future__ import annotations

import logging

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger(__name__)


class OpenAiCompatError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    reraise=True,
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
async def post_openai_compat(
    base_url: str,
    path: str,
    api_key: str,
    payload: dict,
    timeout: int = 60,
) -> dict:
    """统一调用 OpenAI 兼容端点。"""
    url = f"{base_url.rstrip('/')}{path}"
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        if resp.status_code >= 400:
            # 不把完整响应体打到日志（可能含敏感信息）
            truncated = resp.text[:500]
            raise OpenAiCompatError(
                f"OpenAI 兼容 API 调用失败: {resp.status_code} {truncated}",
                status_code=resp.status_code,
            )
        return resp.json()
