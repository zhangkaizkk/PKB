# PKB — Personal Knowledge Base

个人使用的 Web 知识库：拖拽上传、本地保存、MySQL 元数据、搜索、标签、预览、下载、回收站、Docker Compose 部署。

## 快速开始

### 一键启动（Windows 推荐）

双击桌面 **🚀 启动 PKB**，或：

```powershell
scripts\start-pkb.bat   # 自动启动 Docker + 构建前端 + 开浏览器
```

### 手动启动（Linux / macOS / 有经验用户）

```bash
# 1. 准备环境变量
cp .env.example .env          # Windows: copy .env.example .env

# 2. 生成 SECRET_KEY（必填，否则容器启动失败）
#    Linux/Mac:
openssl rand -hex 32
#    Windows PowerShell:
#    -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})

# 3. 编辑 .env，替换 SECRET_KEY= 为上面生成的值
#    同时配置 LLM_API_KEY / EMBEDDING_API_KEY（通义千问 / DashScope）

# 4. 启动
docker compose up -d --build

# 5. 访问
#    前端 http://localhost:8080   (默认 admin / admin123)
#    后端 http://localhost:8000/docs
```

### 旧数据时区迁移（从 v0.0.6 升级）

MySQL 的时区从 `+08:00` 改为 `+00:00` 后，旧数据的显示口径会变化。**先确认列类型再执行**：

```sql
SHOW CREATE TABLE documents;
-- 看 created_at 是 TIMESTAMP 还是 DATETIME
```

**情况 A：`created_at` 是 `TIMESTAMP`（Alembic 建的，通常如此）**

`created_at` / `updated_at` 由 MySQL 自己生成，存的是正确的时间点，**不要修改**。
只有应用层写入的 `indexed_at` / `deleted_at` 会读早 8 小时：

```sql
UPDATE documents SET indexed_at = indexed_at + INTERVAL 8 HOUR WHERE indexed_at IS NOT NULL;
UPDATE documents SET deleted_at = deleted_at + INTERVAL 8 HOUR WHERE deleted_at IS NOT NULL;
```

**情况 B：`created_at` 是 `DATETIME`（只有被 `create_all` 建过表才可能）**

```sql
UPDATE documents SET created_at = created_at - INTERVAL 8 HOUR,
                     updated_at = updated_at - INTERVAL 8 HOUR;
UPDATE qa_history SET created_at = created_at - INTERVAL 8 HOUR;
UPDATE tags      SET created_at = created_at - INTERVAL 8 HOUR;
UPDATE users     SET created_at = created_at - INTERVAL 8 HOUR;
-- indexed_at / deleted_at 本来就是 UTC，不要动
```

执行前请先备份。可空列不需要 `WHERE`：`NULL ± INTERVAL` 结果仍是 `NULL`。

验证：取一条刚上传的文档，`created_at` 应约等于当前时间减 8 小时（UTC 口径），
并执行 `SELECT NOW(), UTC_TIMESTAMP();` 确认两者一致。

**更省心的替代方案（推荐，数据量小时首选）**：直接重建数据卷后重新上传、重建索引。

```bash
docker compose down
docker volume rm pkb_mysql_data
docker compose up -d --build
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
