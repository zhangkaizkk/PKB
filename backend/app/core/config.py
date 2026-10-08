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
