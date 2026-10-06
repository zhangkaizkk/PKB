# PKB PROJECT

本文件是 README 的详细补充，用于阶段间交接。

## 阶段一交付清单 ✅

- [x] 根目录 `docker-compose.yml`、`.env.example`、`.env`、`.gitignore`
- [x] `deploy/mysql/my.cnf`（utf8mb4 + ngram_token_size=2）
- [x] `scripts/backup.sh`、`scripts/restore.sh`
- [x] 后端 `pyproject.toml` + `Dockerfile`
- [x] `backend/app/core/`：`config.py` `session.py` `security.py` `deps.py`
- [x] `backend/app/db/`：`base.py` `session.py` `init_db.py`
- [x] `backend/app/models/`：`user.py` `document.py` `tag.py` `setting.py`
- [x] `backend/alembic.ini` + `alembic/env.py` + 手写 `versions/0001_init.py`（含 `WITH PARSER ngram` 的 FULLTEXT 索引）
- [x] `backend/app/main.py` 入口 + CORS + `/api/health`
- [x] 所有包 `__init__.py` 存在，import 链无断点

## 阶段一验证项（待 Docker 就绪后执行）

```bash
cd backend
pip install -e ".[dev]"
alembic upgrade head        # 应在 MySQL 中建出 6 张表
python -c "from app.db.base import Base; from app import models; print(list(Base.metadata.tables.keys()))"
```

## 阶段一关键设计决策

1. **Alembic 手写迁移** — 自动生成无法识别 MySQL ngram 语法，故 `0001_init.py` 全文手写 DDL。
2. **pymysql 而非 aiomysql** — 文档明确用同步 SQLAlchemy + PyMySQL。
3. **SQLAlchemy 2.0 `Mapped` 注解风格** — 与 Python 3.11 配合最佳。
4. **`DocumentText` 使用 `LongText`** — SQLAlchemy `Text` 在 MySQL 上默认仅 MEDIUMTEXT，需要显式 LongText。

## 阶段二待办

- [ ] `backend/app/core/deps.py` 补 `get_current_user`（骨架已有，需联调）
- [ ] `backend/app/schemas/` 填充 auth/file/tag/common
- [ ] `backend/app/services/` 填充 storage/extractor/file_service/search_service
- [ ] `backend/app/api/` 填充 auth/files/tags/router
- [ ] 文本抽取：pypdf / python-docx / openpyxl / python-pptx
- [ ] SHA-256 去重、安全文件名 sanitize
