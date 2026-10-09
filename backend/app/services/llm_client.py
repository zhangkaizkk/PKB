"""LLM 客户端 — 调 /v1/chat/completions。"""

from __future__ import annotations

import logging

from app.core.config import settings
from app.services.api_retry import post_openai_compat

logger = logging.getLogger(__name__)


class OpenAiCompatChatClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int = 120,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.3,
    ) -> dict:
        """调用 Chat Completions。"""
        data = await post_openai_compat(
            base_url=self.base_url,
            path="/chat/completions",
            api_key=self.api_key,
            payload={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "stream": False,
            },
            timeout=self.timeout,
            max_retries=settings.llm_max_retries,
        )

        return {
            "content": data["choices"][0]["message"]["content"],
            "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
            "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
            "model": data.get("model", self.model),
        }


def get_chat_client() -> OpenAiCompatChatClient:
    """从 settings 创建 Chat 客户端。"""
    return OpenAiCompatChatClient(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_chat_model,
        timeout=settings.llm_timeout_seconds,
    )
