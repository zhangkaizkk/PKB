"""启动时初始化：建表 + 插入默认 admin。"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.user import User


def init_db() -> None:
    """仅开发期使用 — Alembic 已接管建表，这里负责"默认管理员"。"""
    Base.metadata.create_all(bind=engine)  # Alembic 存在时通常跳过，安全兜底
    _ensure_admin()


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
