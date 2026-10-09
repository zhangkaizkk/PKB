"""Pydantic Settings — 从环境变量读取配置。"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Database ---
    database_url: str = "mysql+pymysql://pkb:pkbpass@localhost:3306/pkb?charset=utf8mb4"

    # --- Security ---
    secret_key: str = "change-me-to-a-long-random-string"
    access_token_expire_minutes: int = 1440  # 1 天（单用户本地应用，如需更长自行调大）

    # --- Default admin ---
    admin_username: str = "admin"
    admin_password: str = "admin123"

    # --- Storage ---
    data_dir: str = "data/files"
    max_upload_size: int = 2 * 1024 * 1024 * 1024  # 2 GiB
    max_extract_size_mb: int = 50   # 文本抽取上限（MB），超过跳过

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
    rag_min_similarity: float = 0.35
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
    # ==== FATAL: SECRET_KEY ====
    default_secret = "change-me-to-a-long-random-string"
    sk = settings.secret_key.strip()
    if not sk or len(sk) < 16 or sk == default_secret:
        print(
            "[FATAL] SECRET_KEY 无效（空值 / 过短 / 默认占位符）\n"
            "  修复: 在 .env 里设置 >= 32 字符的随机串\n"
            "  Linux/Mac: openssl rand -hex 32\n"
            "  Windows:   -join ((48..57)+(65..90)+(97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})",
            file=sys.stderr,
        )
        fatal = True

    if fatal:
        sys.exit(1)

    # ==== WARN: ADMIN_PASSWORD 默认 ====
    default_admin = "admin123"
    if settings.admin_password.strip() == default_admin:
        print(
            "[WARN] ADMIN_PASSWORD 仍是默认值 '%s'，请尽快在 .env 中修改。" % default_admin,
            file=sys.stderr,
        )

    # ==== WARN: RAG API Key 缺失（分开报，知道哪个没配）====
    if not settings.llm_api_key.strip():
        print(
            "[WARN] LLM_API_KEY 为空，问答功能不可用（不能回答问题）。",
            file=sys.stderr,
        )
    if not settings.embedding_api_key.strip():
        print(
            "[WARN] EMBEDDING_API_KEY 为空，RAG 索引/检索不可用（不能上传+搜索文档）。",
            file=sys.stderr,
        )


_check_fail_fast()
