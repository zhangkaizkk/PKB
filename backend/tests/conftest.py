"""pytest 配置 + 公共 fixtures。

pytest 从 backend 根目录运行（python -m pytest）。
pyproject.toml 的 [tool.pytest.ini_options] 限定 testpaths = ["tests/unit"]，
因此 pytest 只会收集 tests/unit/ 下的 test_*.py。

纯函数单测放 tests/unit/ —— 这些测试只 import app.utils.files 和 app.services.reranker_service，
依赖链路仅涉及标准库 + FastAPI 类型定义，不需要安装项目依赖、不需要 DB、不需要运行后端服务。
若后续新增 import 重型依赖（ChromaDB / httpx / paddleocr / SQLAlchemy engine 等），
请同时调整 CI 的 pip install 步骤，或用 pytest.importorskip 包裹。
"""

from __future__ import annotations

import sys
from pathlib import Path

# 让 tests/unit/ 下的文件能 import app.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
