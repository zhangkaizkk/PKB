"""统一 router — 聚合 auth / files / tags / rag。"""

from __future__ import annotations

from fastapi import APIRouter

from app.api import auth, files, rag, tags

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(tags.router)
api_router.include_router(files.router)
api_router.include_router(rag.router)

__all__ = ["api_router"]
