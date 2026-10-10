# PKB PROJECT（v0.0.10）

> 个人知识库后端/前端项目的技术说明与设计文档。本文档反映当前真实代码状态，
> 以 Git tag `v0.0.10` 为准。阶段一~四的原始交付清单见 Git 改版记录。

## 1. 项目定位

PKB（Personal Knowledge Base）是一个**本地优先、单机部署**的个人知识库：
- 用户上传 md / txt / pdf / Word / Excel / PPT / 图片，后端抽取文本、可选 OCR、分块、嵌入，存入 ChromaDB。
- 前端提供**文件管理**（上传/下载/预览/重命名/标签/回收站）、**关键词 + ngram 全文搜索**、**RAG 问答**（引用卡片）、**问答历史**。
- **单用户为主**，但 tags、去重、向量分块的 metadata 已按 `owner_id` 隔离，为多用户场景预留。
- 运行方式：`docker compose up -d`（MySQL 8 + FastAPI + Vue3 + Nginx 三容器）。

## 2. 分层结构与关键文件职责

```
backend/app/
├── api/           # FastAPI 路由层 —— 只做参数校验 + 调 service + 返回 schema
│   ├── auth.py        POST /api/auth/login
│   ├── files.py       文件上传/列表/下载/预览/重命名/软删除/回收站/恢复/标签绑定
│   ├── tags.py        标签 CRUD + 按 owner 过滤
│   ├── rag.py         RAG 问答、历史、重建索引（后台化）、索引列表、孤儿 chunk 清理
│   └── router.py      汇总所有 router 到 app.main
├── services/      # 业务逻辑层 —— 可被 api 和后台任务共用
│   ├── rag_service.py         answer_question / index_document —— 问答主流水线
│   ├── vector_store.py        ChromaDB 封装 —— upsert / query / count / purge_orphan
│   ├── reranker_service.py   RERANK_MODE=none|llm 两种重排实现
│   ├── embedding_service.py  文本分块批量嵌入（semaphore 限并发）
│   ├── llm_client.py          Chat API 客户端（api_retry 包 httpx）
│   ├── api_retry.py          httpx AsyncClient 单例 + 指数退避重试（429/5xx/Timeout）
│   ├── chunker.py            分块 + overlap
│   ├── extractor.py          pypdf / python-docx / openpyxl / python-pptx 文本抽取
│   ├── ocr_service.py        PaddleOCR 图片/扫描 PDF 文字识别
│   ├── file_service.py       上传安全校验 + SHA-256 去重 + 标签同步
│   └── storage.py            本地磁盘读写
├── models/        # SQLAlchemy 2.0 Mapped 模型（全库 TIMESTAMP(6) UTC）
│   ├── user.py         users（username/password_hash/created_at）
│   ├── document.py     documents + document_texts + document_tags
│   ├── qa_history.py   问答历史（question/answer/citations/llm 统计）
│   ├── tag.py          tags（owner_id + name UniqueConstraint）
│   └── setting.py      settings（JSON 键值表）
├── db/            # 数据库基础设施
│   ├── base.py         Base + Base.metadata（Alembic env.py 读取）
│   ├── session.py      get_db / SessionLocal（mysql+pymysql）
│   └── init_db.py      启动时检查 5 张核心表是否存在，缺表则 fail-fast 提示 alembic upgrade head
├── core/          # 配置与安全
│   ├── config.py       pydantic Settings，从 .env 读，启动时 _check_fail_fast 校验 SECRET_KEY/ADMIN_PASSWORD/API Key
│   ├── security.py     bcrypt 密码哈希 + python-jose JWT（HS256，Access Token 1 天）
│   ├── deps.py         get_current_user（HTTP Bearer → DB 查 User）
│   └── session.py      （空文件，遗留占位）
├── schemas/       # Pydantic v2 响应/请求 schema
│   ├── auth.py / file.py / tag.py / rag.py / common.py
└── utils/         # 工具函数
    ├── files.py        sanitize_filename / make_title_from_filename（pytest 纯函数单测）
    └── hashing.py      SHA-256
backend/alembic/
└── versions/             0001_init / 0002_ocr_rag / 0003_owner_scope（全手写 DDL）
frontend/src/
├── api/             axios 封装 + 各模块 TS 接口定义
│   └── rag.ts           RagReindexTask / RagReindexStatus + reindexAll / reindexStatus
├── stores/          Pinia setup store（reactive 对象）
│   └── files.ts          files/filter/upload/delete/reindex 等状态机
├── views/           Vue 页面组件
│   ├── HomeView.vue      文件列表 + 上传 + 标签筛选
│   ├── TrashView.vue     回收站（软删除）
│   └── ChatView.vue      RAG 问答 + 重建索引 + 进度轮询
├── components/      Naive UI 组件封装
│   ├── FilePreview.vue   图片/PDF 预览
│   └── PreviewDrawer.vue TXT/MD 预览（异步加载内容）
└── App.vue / main.ts
```

## 3. 数据与索引流水线

```
上传（POST /api/files/upload）
 │  安全校验：扩展名白名单 13 种 → mimetypes.guess_type → application/octet-stream
 │  边写边校验大小：超 MAX_UPLOAD_SIZE 立即中断，413 消息带 GiB 值
 │  sha256 计算 → 与 owner_id+sha256 去重（唯一约束）
 │  后台 Asyncio.to_thread 不卡事件循环
 ↓
文本抽取（extract_status → done/failed/skipped）
 │  pypdf / python-docx / openpyxl / python-pptx 按扩展名选择
 │  PDF 直接从路径读 → 50MB 内存阈值（config.max_extract_size_mb）
 ↓
OCR（ocr_status，默认 skipped）
 │  PaddleOCR 3.x：图片 + 扫描 PDF
 │  后台子进程，不阻塞 API
 ↓
文本分块（RAG_CHUNK_SIZE=500 / RAG_CHUNK_OVERLAP=50）
 │  chunker.py 按字符切割
 ↓
嵌入（Embedding API OpenAI 兼容）
 │  批量 BATCH_SIZE=10，asyncio.to_thread 包 httpx 调用
 │  单例 AsyncClient + Retry（429/5xx/Timeout + 指数退避 + Retry-After）
 ↓
ChromaDB upsert（metadata 含 document_id / owner_id）
 ↓
查询（POST /api/rag/ask）
 │  ChromaDB cosine distance 过滤 owner_id + deleted_at=None
 │  rerank_mode=none: 按相似度排序；llm: Chat API 重排顺序
 │  rag_min_similarity=0.35 阈值过滤（rerank_score = max(0, 1 - distance)）
 ↓
LLM 回答（Chat API OpenAI 兼容）+ 引用卡片（top_k_retrieve=20 → top_k_rerank=5）
```

## 4. 关键设计决策

| 决策 | 原因 | 落点 |
|------|------|------|
| **Alembic 手写迁移** | MySQL FULLTEXT 索引的 `WITH PARSER ngram` 自动生成无法识别 | `alembic/versions/0001_init.py` 全文手写 DDL |
| **全库时间统一 TIMESTAMP(6) UTC** | MySQL `default-time-zone='+00:00'`，模型与迁移对齐 | 所有 `DateTime(6)` → `TIMESTAMP(fsp=6)`，避免 autogenerate 噪声 |
| **删除 create_all** | 改用 `init_db.py` 启动时检查 5 张核心表，缺表 fail-fast 提示 `alembic upgrade head` | 防止生产环境跳过 Alembic 直接建表 |
| **重排模式 none\|llm** | 移除 cloud_api（未实现）；llm 只负责排序，评分口径统一为向量相似度 `1 - distance` | 两种模式的阈值过滤语义一致 |
| **reindex 后台化** | POST /rag/reindex 返回 202 + task_id，BackgroundTasks 执行 | 避免大文档集同步阻塞 HTTP |
| **孤儿 chunk 清理** | purge_orphan_chunks 从 GET 移出，改在 _reindex_bg 完成后统一执行一次；alive_ids = 全库口径 | 防止"打开问答页就删掉别的用户向量"的跨用户破坏 |
| **asyncio.to_thread** | rag_service.py 内 ChromaDB 查询 + 同步 DB 调用全部包一层 | 避免阻塞 FastAPI 事件循环 |
| **httpx Retry + to_thread** | api_retry.py 单例 AsyncClient + 重试覆盖 429/5xx/Timeout | LLM/Embedding API 的 max_retries 配置真正生效 |
| **失败限流** | auth.py 登录 15 分钟窗口 5 次 429；登录成功清零 | 模块级 `dict + threading.Lock + deque` |

## 5. 运维

| 操作 | 命令 |
|------|------|
| 一键启动 | `docker compose up -d` |
| 后端重建 | `docker compose up -d --build backend` |
| 数据库迁移 | `docker compose exec backend alembic upgrade head` |
| 日志 | `docker compose logs -f backend` |
| 健康检查 | `curl http://localhost:8000/api/health` |
| 时区迁移 | 见 README 「旧数据时区迁移」（TIMESTAMP vs DATETIME 分情况处理） |
| 备份 | `scripts/backup.sh` / `scripts/restore.sh` |
| 日志级别 | `.env` 加 `LOG_LEVEL=DEBUG/INFO/WARNING`，由 `logging.basicConfig` 驱动 |

## 6. 测试与 CI

- 后端 pytest：`backend/tests/unit/test_pure.py`（19 项纯函数单测，无需 DB/网络）
- ruff lint：`ruff check app/`（select E/F/I/UP/B，ignore B008/B905/F821）
- ruff format：`ruff format app/ tests/`
- `.github/workflows/ci.yml` 目前跑 backend 一个 job（ruff + pytest）
- 手工调试脚本在 `scripts/debug/`，不参与 pytest 收集

## 7. 技术栈

- **后端**：FastAPI + SQLAlchemy 2.0 + Alembic + PyMySQL + ChromaDB + Pydantic v2 + python-jose + bcrypt + PaddleOCR/PaddlePaddle + httpx
- **前端**：Vue3 + Vite + TypeScript + Pinia（setup） + Naive UI + axios
- **基础设施**：MySQL 8（utf8mb4 + ngram_token_size=2 + default-time-zone +00:00） + Docker Compose 三容器 + Nginx
- **CI**：GitHub Actions（ruff + pytest，后续增加 frontend lint/build + docker build）
