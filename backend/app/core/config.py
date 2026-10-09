"""Pydantic Settings — 从环境变量读取配置。"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Database ---
    database_url: str = "mysql+pymysql://pkb:pkbpass@localhost:3306/pkb?charset=utf8mb4"

    # --- Security ---
    secret_key: str = "change-me-to-a-long-random-string"
    access_token_expire_minutes: int = 10080  # 7 days

    # --- Default admin ---
    admin_username: str = "admin"
    admin_password: str = "admin123"

    # --- Storage ---
    data_dir: str = "data/files"
    max_upload_size: int = 2 * 1024 * 1024 * 1024  # 2 GiB

    # --- CORS ---
    allowed_origins: str = "http://localhost:8080"

    # --- OCR ---
    ocr_enabled: bool = True
    ocr_lang: str = "ch"
    ocr_use_gpu: bool = False

    # --- RAG ---
    chroma_persist_dir: str = "/app/data/chroma"
    chroma_collection_name: str = "pkb_documents"
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 50
    rag_top_k_retrieve: int = 20
    rag_top_k_rerank: int = 5
    rag_local_only: bool = False

    # --- Chat API（OpenAI 兼容，必填）---
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_chat_model: str = ""
    llm_timeout_seconds: int = 120
    llm_max_retries: int = 3

    # --- Embedding API（OpenAI 兼容，必填）---
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = ""
    embedding_dim: int = 1024
    embedding_batch_size: int = 16
    embedding_timeout_seconds: int = 60
    embedding_max_retries: int = 3

    # --- 重排模式：none | llm | cloud_api ---
    rerank_mode: str = "none"
    rerank_cloud_base_url: str = ""
    rerank_cloud_api_key: str = ""
    rerank_cloud_model: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()


def _check_fail_fast() -> None:
    """启动时校验关键配置，避免用默认值直接上线。"""
    import sys

    fatal = False
    warn = False

    # SECRET_KEY: 空 / 过短 / 等于默认占位值都拒绝启动
    default_secret = "change-me-to-a-long-random-string"
    sk = settings.secret_key.strip()
    if not sk or len(sk) < 16 or sk == default_secret:
        print(
            "[FATAL] 安全风险: SECRET_KEY 无效（空值 / 过短 / 默认占位符）\n"
            "  修复方式: 在 .env 里设置一个 >= 32 字符的随机串\n"
            "  Windows: [System.Guid]::NewGuid().ToString() + [System.Guid]::NewGuid().ToString()\n"
            "  Linux/Mac: openssl rand -hex 32",
            file=sys.stderr,
        )
        fatal = True

    # API Key: Chat 和 Embedding 至少一个不能为空（否则问答功能不可用）
    if not settings.llm_api_key and not settings.embedding_api_key:
        print(
            "[WARN] Chat 和 Embedding API Key 均为空，RAG 问答功能将不可用。\n"
            "  请在 .env 中配置 LLM_API_KEY 和 EMBEDDING_API_KEY。",
            file=sys.stderr,
        )
        warn = True

    if fatal:
        sys.exit(1)


_check_fail_fast()
