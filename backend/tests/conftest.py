"""pytest 配置 + 公共 fixtures。

pytest 从 backend 根目录运行（python -m pytest），自动发现 tests/ 下的 test_*.py。
不需要 DB / 网络的纯函数单测直接放 tests/unit/。
"""
from __future__ import annotations

import sys
from pathlib import Path

# 让 tests/unit/ 下的文件能 import app.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
