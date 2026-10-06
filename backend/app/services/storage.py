"""本地文件存储服务 — tmp 写入 + 正式目录移动 + 物理删除。"""
from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

from app.core.config import settings


class StorageService:
    """封装 DATA_DIR 的所有 IO 操作。"""

    def __init__(self, data_dir: str | None = None) -> None:
        base = data_dir or settings.data_dir
        # 解析为绝对路径（Docker 内是 /app/data/files，本地是相对路径）
        self.root = Path(base).resolve()
        self.tmp_dir = self.root / "tmp"
        self.files_dir = self.root / "files"
        self.root.mkdir(parents=True, exist_ok=True)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(parents=True, exist_ok=True)

    # ---------- tmp ----------

    def new_tmp_path(self, suffix: str = ".part") -> Path:
        return self.tmp_dir / f"{uuid.uuid4().hex}{suffix}"

    def write_tmp(self, data: bytes) -> Path:
        path = self.new_tmp_path()
        path.write_bytes(data)
        return path

    def remove_tmp(self, path: Path) -> None:
        if path.exists():
            path.unlink()

    # ---------- 正式 ----------

    def finalize_path(self, relative: str) -> Path:
        """根据文档表的 stored_path 解析为绝对路径。"""
        return self.root / relative

    def move_to_final(self, tmp: Path, relative_dest: str) -> Path:
        """移动 tmp 文件到正式位置（含目录创建）。"""
        dest = self.finalize_path(relative_dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        # 如果目标已存在（重复文件名但 SHA-256 不同的极端情况），加后缀
        if dest.exists():
            dest = dest.with_name(f"{dest.stem}_{uuid.uuid4().hex[:8]}{dest.suffix}")
        shutil.move(str(tmp), str(dest))
        return dest

    def physical_delete(self, relative_path: str) -> None:
        p = self.finalize_path(relative_path)
        if p.exists():
            p.unlink()

    def stream_iter(self, relative_path: str, chunk_size: int = 1 << 20):
        """逐块 yield 文件内容，用于下载/预览。"""
        p = self.finalize_path(relative_path)
        with p.open("rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def read_bytes(self, relative_path: str) -> bytes:
        return self.finalize_path(relative_path).read_bytes()


# 全局单例（lazy 初始化）
_storage: StorageService | None = None


def get_storage() -> StorageService:
    global _storage
    if _storage is None:
        _storage = StorageService()
    return _storage
