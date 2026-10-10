"""Alembic env.py — 从 Pydantic Settings 读取真实 DB URL。"""

from __future__ import annotations

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

import app.models  # noqa: F401 — 注册元数据
from alembic import context
from app.core.config import settings
from app.db.base import Base

config = context.config

# 用运行时的 DATABASE_URL 替换 ini 里的占位
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # 手写迁移项目的 autogenerate 噪声抑制：
            # - 辅助索引 / FULLTEXT 索引只在 DDL 里、不在 SA metadata 里
            # - 类型对比已对得上（TIMESTAMP(fsp=6) 无差异），不需要 compare_type=False
            compare_index=False,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
