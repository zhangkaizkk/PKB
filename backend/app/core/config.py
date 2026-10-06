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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
