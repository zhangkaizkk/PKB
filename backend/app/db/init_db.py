"""启动时初始化：查表存在性 + 插入默认 admin。"""
from __future__ import annotations

import sys

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal, engine
from app.models.user import User

# Alembic 迁移应已创建的核心表（缺任何一个都说明迁移没跑）
_REQUIRED_TABLES = ["users", "documents", "document_texts", "tags", "qa_history"]


def init_db() -> None:
    """启动时检查表是否存在；不存在则 fail-fast 提示跑 Alembic 迁移。"""
    _verify_tables()
    _ensure_admin()


def _verify_tables() -> None:
    """查 information_schema.tables，核心表缺失则 exit(1)。"""
    missing: list[str] = []
    with engine.connect() as conn:
        db_name = engine.url.database
        for tbl in _REQUIRED_TABLES:
            row = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = :db AND table_name = :tbl"
                ),
                {"db": db_name, "tbl": tbl},
            ).scalar()
            if row == 0:
                missing.append(tbl)
    if missing:
        print(
            f"[FATAL] 数据库缺少以下表: {', '.join(missing)}\n"
            "  请先运行 Alembic 迁移: cd backend && alembic upgrade head",
            file=sys.stderr,
        )
        sys.exit(1)


def _ensure_admin() -> None:
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == settings.admin_username).first()
        if existing:
            return
        admin = User(
            username=settings.admin_username,
            password_hash=hash_password(settings.admin_password),
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    finally:
        db.close()
