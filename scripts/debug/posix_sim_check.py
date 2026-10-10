"""在 Windows 上以 POSIX 语义运行 backend 单测，复现 CI(ubuntu-latest) 的行为。

原理：CI 与 Docker 上 os.path 就是 posixpath，因此把 os.path.basename / splitext
替换为 posixpath 的对应实现，即可忠实复现 Linux 的代码路径。
用法（仓库根目录）：python scripts/debug/posix_sim_check.py
"""
from __future__ import annotations

import os
import posixpath
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2] / "backend"

os.path.basename = posixpath.basename  # type: ignore[assignment]
os.path.splitext = posixpath.splitext  # type: ignore[assignment]

os.chdir(BACKEND)

import pytest  # noqa: E402

sys.exit(pytest.main(["tests/", "-q", "--no-header", "-p", "no:cacheprovider"]))
