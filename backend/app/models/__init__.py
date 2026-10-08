"""models 包入口 — Alembic env.py 通过 `from app.models import *` 收集元数据。"""
from app.models import user, document, tag, setting, qa_history  # noqa: F401  — 注册元数据

__all__ = ["user", "document", "tag", "setting", "qa_history"]
