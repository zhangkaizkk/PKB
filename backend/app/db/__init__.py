"""延迟 re-export — 避免模块加载时就初始化 SQLAlchemy 引擎。"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.db.session import SessionLocal, engine, get_db


def __getattr__(name: str):
    """按需加载，Alembic env.py 只需 import Base/models 时不会触发 engine 初始化。"""
    if name in {"SessionLocal", "engine", "get_db"}:
        from app.db.session import SessionLocal, engine, get_db
        return {"SessionLocal": SessionLocal, "engine": engine, "get_db": get_db}[name]
    raise AttributeError(name)


__all__ = ["SessionLocal", "engine", "get_db"]
