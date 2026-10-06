"""安全文件名处理 — 文档 6.4 节规则。"""
from __future__ import annotations

import os
import re

# Windows 禁止 + 额外安全字符
_ILLEGAL_CHARS = re.compile(r'[\\/:*?"<>|]')
_MAX_LEN = 200
_FALLBACK = "untitled"


def sanitize_filename(raw: str) -> str:
    """安全化文件名：

    1. 只取 basename，去掉路径
    2. 替换非法字符为 _
    3. 禁止 '..'
    4. 限长 200
    5. 空文件名使用 'untitled'
    """
    # 1. 只保留 basename（兼容路径分隔符）
    name = os.path.basename(raw.replace("\\", "/").replace("/", "\\"))

    # 2. 替换非法字符
    name = _ILLEGAL_CHARS.sub("_", name)

    # 3. 禁止 ..
    name = name.replace("..", "_")

    # 4. 限长
    if len(name) > _MAX_LEN:
        # 保留扩展名
        stem, ext = os.path.splitext(name)
        stem = stem[: _MAX_LEN - len(ext)]
        name = stem + ext

    # 5. 空名兜底
    if not name or not name.strip():
        name = _FALLBACK

    return name


def make_storage_path(sha256_prefix: str, safe_name: str, year: int, month: int) -> str:
    """相对 DATA_DIR 的存储路径。"""
    return f"files/{year:04d}/{month:02d}/{sha256_prefix}_{safe_name}"


def make_title_from_filename(filename: str) -> str:
    """从文件名生成默认 title（去掉扩展名）。"""
    base = os.path.splitext(os.path.basename(filename))[0]
    return base or _FALLBACK
