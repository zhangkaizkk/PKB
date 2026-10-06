# PKB — Personal Knowledge Base

个人使用的 Web 知识库：拖拽上传、本地保存、MySQL 元数据、搜索、标签、预览、下载、回收站、Docker Compose 部署。

## 快速开始

```bash
# 1. 准备环境变量
cp .env.example .env    # Windows: copy .env.example .env

# 2. 一键启动（MySQL + Backend + Nginx/Frontend）
docker compose up -d --build

# 3. 访问
# 前端 http://localhost:8080   (默认 admin / admin123)
# 后端 http://localhost:8000/api/health
# MySQL localhost:3306
```

## 目录结构

```
pkb/
├── docker-compose.yml
├── .env.example / .env
├── deploy/mysql/my.cnf      # MySQL 配置（utf8mb4 + ngram）
├── scripts/                 # backup.sh / restore.sh
├── backend/                 # FastAPI + SQLAlchemy + Alembic
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini + alembic/versions/0001_init.py   # 手写 ngram 迁移
│   └── app/
│       ├── main.py          # 入口
│       ├── core/            # config / session / security / deps
│       ├── db/              # Base / session / init_db
│       ├── models/          # User / Document / Tag / Setting
│       ├── schemas/ api/ services/ utils/  (阶段二填充)
├── frontend/                # Vue 3 + Vite + Naive UI  (阶段三填充)
├── data/files/              # 实际文件存储位置
└── docs/PROJECT.md
```

## 备份与恢复

```bash
# 备份
bash scripts/backup.sh

# 恢复
bash scripts/restore.sh backups/pkb-YYYY-MM-DD.sql backups/pkb-files-YYYY-MM-DD.tar.gz
```

## 技术栈锁定

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + Vite + TypeScript + Pinia + Naive UI |
| 后端 | Python 3.11+ + FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic v2 |
| 数据库 | MySQL 8.0，utf8mb4，中文全文搜索 ngram |
| 部署 | Docker Compose：mysql + backend + nginx(frontend) |

详见 [docs/PROJECT.md](docs/PROJECT.md) 和开发文档（桌面 `# 个人知识库 PKB 开发文档（TraeCode 版）.md`）。
