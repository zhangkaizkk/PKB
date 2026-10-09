"""流式 SHA-256 计算。"""

from __future__ import annotations

import hashlib
from typing import BinaryIO


def compute_sha256_stream(fileobj: BinaryIO, chunk_size: int = 1 << 20) -> str:
    """逐块读取文件并计算 SHA-256，返回 hex 字符串。"""
    h = hashlib.sha256()
    while True:
        chunk = fileobj.read(chunk_size)
        if not chunk:
            break
        h.update(chunk)
    return h.hexdigest()


def compute_sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
