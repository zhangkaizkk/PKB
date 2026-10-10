# Git 改版记录

> 每次 Git 提交的原因与结果。格式：`hash | 类型 | 原因 | 状态`

---

## v0.0.1

| Hash | 类型 | 原因 | 状态 |
|---|---|---|---|
| `4dd22b5` | feat | 阶段一至四全部完成，保存首个完整快照 | ✅ |
| `a30391b` | fix | tsconfig 报 baseUrl 已弃用，paths 需加 `./` 前缀适配 TS 6.0 | ✅ |
| `c590943` | fix | 点下载报 401 未提供 token，`window.open` 丢失 Authorization header | ✅ |
| `43813f4` | fix | 重命名后前端显示旧名称，后端 title 字段没跟着 original_name 更新 | ✅ |
| `9bf33f8` | style | 重命名弹 dialog.warning 黄色感叹号图标语义错误（不是警告），改为单 prompt | ✅ |
| `62c153d` | refactor | 点回收站侧边栏消失，平级路由切换时 HomeView 整体卸载，改为嵌套路由共用 Layout | ✅ |

## v0.0.2

| Hash | 类型 | 原因 | 状态 |
|---|---|---|---|
| `834a310` | docs | 新增 Git改版记录.md | ✅ |
| `6f54783` | style | 侧边栏动态标签（e2e-test 等）多余，只留「全部」按钮 | ✅ |
| `43f29e6` | docs | 补充之前漏的两条记录 | ✅ |
| `4e5a983` | docs | 精简改版记录格式，只留 hash/类型/原因/状态四列 | ✅ |

## v0.0.3

| Hash | 类型 | 原因 | 状态 |
|---|---|---|---|
| `9945787` | fix | 上传成功后文件列表不刷新，upload store 与 files store 无联动，加 400ms debounce 触发 list | ✅ |
| `c4302b8` | fix | 上传进度条不动，axios `onUploadProgress` 要求 `e.total` 存在才触发，快传场景下 total 常为 undefined | ✅ |
| `ea50bce` | fix | 上传成功进度条卡在 5%，status 与 progress 同 tick 变更时 NProgress 只捕获一个字段，组件层从 status 派生 percentage + store 用 Object.assign 批量更新 | ✅ |
| `1397881` | fix | 进度条/状态持续不更新（终极修复）— ref<[]> push 的 plain object 属性变更不触发 Pinia computed，改为 reactive<[]> + 直接修改属性 | ✅ |
| `7d7f510` | fix | 搜索栏消失，Layout.vue 的 NInput 漏从 naive-ui import | ✅ |
| `4ef43bc` | feat | 搜索栏后加搜索按钮 | ✅ |
| `940c9d9` | fix | 搜索按钮被挤到搜索栏下，.top-left 固定 width:420px 太窄，改 flex 自适应 | ✅ |

## v0.0.4

| Hash | 类型 | 原因 | 状态 |
|---|---|---|---|
| — | feat | **OCR + RAG 扩展**：PaddleOCR 本地抽取图片/扫描 PDF 文本，OpenAI 兼容 Embedding API 向量化，ChromaDB 持久化，`text-embedding-v3` 批量上限修正为 10（原 16 触发 400 零向量占位） | ✅ |
| — | feat | **知识库问答页**：新增 ChatView（侧边栏入口）、ChatWindow、ChatMessage、CitationCard 组件，支持模型信息、引用卡片、可折叠已索引文档列表 | ✅ |
| — | feat | **相似度阈值过滤**：无意义查询最小 similarity ≈ 47.7%，加 `MIN_SIMILARITY = 0.5` 阈值过滤 ChromaDB 噪声分块，解决"实习经历"混入课程报告的问题 | ✅ |
| — | fix | **零向量占位导致全库相似度 0%**：API Key 未配置时 Embedding 401 → 零向量占位 → 全局 distance=1.0；清空 ChromaDB 重新索引后修复 | ✅ |
| — | feat | **回收站「全部删除」按钮**：后端 `DELETE /api/files/purge-all` 路由 + `FileService.purge_all_trashed`，前端 TrashView 红色 ghost 按钮 + Naive UI dialog.warning 二次确认 | ✅ |
| — | fix | **分页翻页点击无反应**：FileList emit `pageChange` 但 HomeView/TrashView 都没监听 `@page-change` | ✅ |
| — | fix | **每页条数下拉点击无反应**：`@update:page-size` 丢弃 NPagination 传出的新值，store.pageSize 永远不更新 → 受控组件重渲染时强制覆盖回 20；新增 `pageSizeChange` emit + store.list 接受 size 参数 | ✅ |

## v0.0.5

| Hash | 类型 | 原因 | 状态 |
|---|---|---|---|
| — | feat | **桌面快捷方式一键启动**：新增 `scripts/start-pkb.ps1`（PowerShell 主脚本）+ `start-pkb.bat`（极简 wrapper），自动检测 Docker → npm host build → docker compose → 健康检查 → 开浏览器；支持 `rebuild` 参数强制重建 | ✅ |
| — | fix | **bat 编码导致中文命令被 GBK 拆碎**：Windows cmd 默认 GBK，UTF-8 bat 中文字符被拆成无效命令；改用 PowerShell 主脚本 + bat wrapper 两层架构解决 | ✅ |
| — | fix | **npm 退出码被管道吞掉**：`npm run build *>&1 \| ForEach-Object` 管道的退出码是管道整体的而非 npm 的，导致编译成功却误判失败；改为直接调用 npm 不经过管道 | ✅ |
| — | feat | **启动脚本智能跳过 Docker build**：检测镜像是否存在 + 比较 `frontend/src` vs `frontend/dist` 时间戳，日常启动 `docker compose up -d`（秒启动），仅首次或源码变更时才 `--build` | ✅ |

## v0.0.6

| Hash | 类型 | 原因 | 状态 |
|---|---|---|---|
| — | fix | **[P0-1] 删除文件向量未清理（静默 await 漏用）**：`unindex_document` 是 `async def` 但 `purge` / `purge_all` 两个同步路由里直接调用没 `await`，Python 创建的协程对象永远不会执行 → ChromaDB 孤儿向量堆积且仍被检索到；改为同步函数 | ✅ |
| — | fix | **[P0-2] Embedding 失败静默降级零向量**：任何异常（401/限流/格式错误）都塞零向量继续，界面显示"已索引"实际 similarity=0 被阈值过滤；改为失败直接 `raise`，让文档保持 failed 状态 | ✅ |
| — | fix | **[P0-3] 每次问答新建 DB engine 不 dispose**：`get_indexed_documents_summary()` 里 `create_engine(os.environ["DATABASE_URL"])` 绕过 SessionLocal，连接靠 GC 回收，高并发顶到 max_connections；改为复用 `SessionLocal` | ✅ |
| — | fix | **[P0-4] datetime.utcnow() 弃用 + 时区混用**：3 处 `utcnow()`（files.py/rag.py）→ `datetime.now(timezone.utc).replace(tzinfo=None)`；`deleted_at` 已是正确写法 | ✅ |
| — | fix | **[P0-5] 前端 Dockerfile 干净 clone 必然失败**：原 Dockerfile 直接 `COPY dist`，但 .gitignore 排除 dist/；改为多阶段构建 `node:20-alpine → nginx:alpine`，`npm ci` + `npm run build` 全在镜像内完成 | ✅ |
| — | fix | **[P1-6] 默认凭据 fail-fast**：`SECRET_KEY` 仍为 `"change-me-to-a-long-random-string"` 时启动直接 `sys.exit(1)`；`ADMIN_PASSWORD` 默认值给 WARN | ✅ |
| — | fix | **[P1-7] /rag/stats + /rag/config 漏鉴权**：两个接口无 `Depends(get_current_user)`，任何人能读模型名/base_url/索引规模；补鉴权后无 token → 401 | ✅ |
| — | fix | **[P1-8] 预览接口补 nosniff**：`FileResponse` 加 `headers={"X-Content-Type-Options": "nosniff"}`，防止 MIME sniffing 同源脚本注入 | ✅ |
| — | feat | **[P1-9] ChromaDB owner 维度隔离**：`index_document` 新增 `owner_id` 参数写入 metadata；检索不带 where 过滤（ChromaDB 不支持 $exists），取回后在 Python 里按 `meta.get("owner_id")` 过滤（兼容旧分块 owner_id=None） | ✅ |
| — | fix | **.env.example 移除真实 API Key**：LLM_API_KEY / EMBEDDING_API_KEY 从真实值改成 `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` 占位符；base_url 从 maas.qianwenaiapi.com 改回官方 dashscope.aliyuncs.com | ✅ |

## v0.0.6 — 修复补遗（审计后）

| Hash | 类型 | 原因 | 状态 |
|---|---|---|---|
| — | fix | **[紧急1] .env.example 真实 API Key 再次泄露**：v0.0.6 提交时 LLM/Embedding Key 被写回真实签名字符串（`sk-ws-H.PEHRLRD...`），base_url 也改成了非官方 maas.qianwenaiapi.com；立刻换回占位符 + force push 重写历史 | ✅ 已 force push |
| — | fix | **[紧急2] $exists 非法 Chroma 算子导致问答全崩**：`answer_question` 构造 `{"$or": [{"owner_id": x}, {"owner_id": {"$exists": False}}]}`，ChromaDB 不支持 $exists → ValueError 被 except Exception 吞掉 → 每次问答返回"知识库检索失败"；改为 Python 层按 meta 过滤，不带 where 检索 | ✅ |
| — | feat | **[紧急2补充] embed_query try/except**：上一轮 Embedding 失败 `raise` 后，`answer_question` 里的 `embed_query` 没有 try/except，Embedding API 不可用时直接 500 抛栈；补上后返回"知识库服务暂时不可用" | ✅ |
| — | fix | **[紧急3] fail-fast 与 .env.example 自洽**：之前 `SECRET_KEY` 命中默认值直接 exit(1)，但 .env.example 写的正是默认值 → cp .env.example .env 立刻挂掉；改为空/过短/默认值都拒绝，并在错误信息里给出 Windows + Linux 的生成命令 | ✅ |
| — | feat | **[紧急3补充] start-pkb.ps1 首次自动生成 SECRET_KEY**：启动脚本加"初始化 .env"步骤 — 若 .env 不存在则从 .env.example 复制，然后检测 SECRET_KEY 是否有效（空/默认/过短），无效就用 64 位随机 alnum 替换 | ✅ |
| — | fix | **[二-4] 时区统一 UTC**：MySQL `default-time-zone` 从 +08:00 改 +00:00，compose `TZ: Asia/Shanghai` 改 `TZ: UTC`；Python 侧 `now(timezone.utc).replace(tzinfo=None)` 不变；全链路存储 UTC，展示层 strftime | ✅ 需重建 mysql_data |
| — | feat | **[二-5] get_indexed_documents_summary 补 owner 过滤**：新增 `owner_id` 参数，不带时全用户可见（管理场景）；answer_question 调用时传入当前用户 ID，避免跨用户文件清单泄露 | ✅ |
| — | feat | **[二-6] reindex_all 逐篇容错**：一篇失败不再整批 500，继续处理后续文档；返回消息里附带失败数量 | ✅ |

## v0.0.7

| Hash | 类型 | 原因 | 状态 |
|---|---|---|---|
| — | chore | **版本号从 0.0.6 → 0.0.7**：frontend package.json + backend pyproject.toml | ✅ |
| — | docs | **Git 改版记录 v0.0.6 区段补遗**：之前"P1-9 owner 隔离"声称用 `$or` + `$exists`，实际 ChromaDB 不支持 $exists；修正为"Python 层按 meta 过滤" | ✅ |
| — | docs | **Git 改版记录 v0.0.6 真实 Key 泄露修正**：两次提交（87c4002 / 33a48eb）中 .env.example 里真实 API Key 曾被带进来；最终换回占位符 `sk-xxxx...` 并指向官方 `dashscope.aliyuncs.com` | ✅ |

## v0.0.8

| Hash | 类型 | 原因 | 状态 |
|---|---|---|---|
| — | docs | **README 手动启动路径修复**：补 `openssl rand -hex 32` SECRET_KEY 生成命令、跨平台 PowerShell 命令、旧数据时区迁移 SQL（documents/qa_history/tags 三张表减 8h）；新增一键启动（Windows 推荐）vs 手动启动（Linux/macOS）两个区段 | ✅ |
| — | fix | **fail-fast 恢复 ADMIN_PASSWORD 默认值告警**：0.0.6 把它连同 `$default_admin` 校验一起删了，0.0.7 重写 `_check_fail_fast()` 时又漏加；现在默认 admin123 会触发 WARN | ✅ |
| — | fix | **API Key 分开报缺失**：之前 `not llm and not embedding` 两条件合并只报一次；改为各自独立判断，缺哪个报哪个（LLM 缺 → 问答不可用，Embedding 缺 → 索引/检索不可用） | ✅ |
| — | fix | **_check_fail_fast 清理死代码**：`warn = False` 赋值后从未使用 → 已删 | ✅ |
| — | feat | **reindex_all 错误列表不再浪费**：之前收集 `errors: list[str]` 只用来计 `failed_count`；现在前 3 条失败详情会拼进响应 message，超过 3 条附带计数提示 | ✅ |
| — | chore | **版本号 0.0.7 → 0.0.8**：frontend package.json + backend pyproject.toml | ✅ |

## v0.0.10（进行中 — P0 已完成）

| Hash | 类型 | 原因 | 状态 |
|---|---|---|---|
| `323b47d` | fix | **P0-1 CI pytest 必然失败**：`backend/tests/test_e2e.py` 顶层 `import httpx` + 模块级 httpx.get()，文件名匹配 `test_*.py` 被 pytest 收集 → CI 报 ModuleNotFoundError；调试脚本 `test_e2e.py` / `quick_download.py` 移至 `scripts/debug/`，pyproject.toml 加 `[tool.pytest.ini_options] testpaths=["tests/unit"] asyncio_mode="strict"`，conftest.py 补依赖边界注释 | ✅ 验证：ruff + pytest 19/19 全过 |
| `f34857a` | fix | **P0-2 Docker 下两个新配置完全失效**：`MAX_EXTRACT_SIZE_MB` / `RAG_MIN_SIMILARITY` 加进了 config.py 但 docker-compose.yml 未转发到容器；同时 compose 和 .env.example 还残留已从 config.py 移除的 `RERANK_CLOUD_*` 三行死变量。compose 补两行、删三行；.env.example 补 `RAG_MIN_SIMILARITY=0.35`、删三行、改注释为 `none|llm` | ✅ 验证：`docker compose config` 输出两变量可见、cloud_api 完全消失 |
| `9d1e341` | fix | **P0-3 purge_orphan_chunks 跨用户误删向量**：`get_indexed_documents()` 调用 `purge_orphan_chunks(valid_ids)` 时 valid_ids 只包含当前用户的已索引文档 ID，导致**用户 A 打开问答页就把用户 B 的 ChromaDB 分块全部删掉**。修法：purge 从 GET 接口移出，改在 `_reindex_bg` 后台任务完成后统一执行一次，且 alive_ids = **全库** `Document.deleted_at.is_(None)` 的 ID 集合 | ✅ 验证：ruff + pytest 通过，多用户打开 GET 不再互相影响 |

## v0.0.9（已完成 — 阶段一→二→三→四）

| Hash | 类型 | 原因 | 状态 |
|---|---|---|---|
| `9eab719` | feat | **[1.1] 登录失败限流**：auth.py 加模块级 `dict+threading.Lock+deque`，key=`username\|ip`，15 分钟窗口 5 次触发 429；登录成功清零；401 消息附带"还可尝试 N 次" | ✅ 验证：第 5 次开始 429 |
| `0ab5158` | fix | **[1.2] token 有效期 7d→1d**：config.py `access_token_expire_minutes` 10080→1440；.env.example 同步改 | ✅ |
| `0ab5158` | docs | **[1.5] .env.example SECRET_KEY 补注释**：上方加 `# 必须替换为随机串，生成方式见 README 快速开始` | ✅ |
| `215ebec` | fix | **[1.3] 端口绑定 127.0.0.1**：compose mysql 3306 + backend 8000 都从 `0.0.0.0` 改成 `127.0.0.1:port:port`；nginx 8080 仍对外（浏览器需要） | ✅ |
| `1fa87bd` | fix | **[1.4] 服务端扩展名白名单判 MIME**：不再信任 `UploadFile.content_type`，改用 `_detect_mime(filename)` — 白名单 13 种扩展名 → `mimetypes.guess_type` → `application/octet-stream`；零新依赖 | ✅ |
| `c3b0ad7` | perf | **[2.1] asyncio.to_thread 包阻塞调用**：rag_service.py 里 ChromaDB query_similar / upsert_chunks / 同步 DB 调用全部 `asyncio.to_thread(...)`，不卡事件循环 | ✅ |
| `9b5f8da` | perf | **[2.2+2.3] httpx 单例 + 重试 429/5xx**：api_retry.py 重写 — 模块级 `_client` 单例懒加载 + `get_client/close_client`；重试条件={Timeout/Connect/ReadError + 429/500/502/503/504}，4xx 立即抛；指数退避 + 读 Retry-After；llm/embedding max_retries 配置项真正生效 | ✅ |
| `5217062` | fix | **[2.4] 去 new_event_loop + 跨 loop 信号量**：embedding_service.py 删模块级 `asyncio.Semaphore(3)`；files.py `new_event_loop()/run_until_complete/close` → `asyncio.run()` | ✅ |
| `e0c4e63` | fix | **[2.5] 抽取内存阈值**：config.py 加 `max_extract_size_mb=50`；extractor.py 新 `_extract_pdf_path` 让 pypdf 直接读路径不整文件进内存 | ✅ |
| `05cf139` | perf | **[2.6] 边写边校验大小**：upload while 循环里加 `if size+len(chunk)>limit: truncated=True; break`，413 消息带 GiB 值；超限立即中断不占磁盘 | ✅ |
| `feac33c` | feat | **[2.7] reindex 后台化**：POST /rag/reindex 改 202+task_id，BackgroundTasks + `_reindex_tasks` dict + threading.Lock；新增 GET /rag/reindex/status 查进度（running/total/done/failed/progress） | ✅ |
| `985592d` | fix | **[3.1] Text with_variant→LONGTEXT**：document.py DocumentText.content + qa_history.py question/answer 从 `Text().with_variant(Text,"mysql")` 改 `Text().with_variant(LONGTEXT,"mysql")`，与 Alembic 迁移对齐 | ✅ |
| `83af7db` | fix | **[3.2] 删掉 create_all + 缺表 fail-fast**：init_db.py 删 `Base.metadata.create_all`，启动查 information_schema.tables 5 张核心表，缺任一 print+sys.exit(1) 提示跑 alembic upgrade head | ✅ |
| `fae6e07` | feat | **[3.3] tags 按用户隔离 + 去重 owner_id+sha256**：Tag 模型加 owner_id + UniqueConstraint(owner_id,name)；file_service `_find_active_by_sha`/`_bind_tags`/`sync_tags` 全部带 owner；tags.py API 全按 current_user 过滤；新增 Alembic 0003 迁移 | ✅ |
| `759c6ad` | config | **[3.4] MIN_SIMILARITY 配置化**：config.py 加 `rag_min_similarity: float = 0.35`；rag_service 硬编码 `MIN_SIMILARITY=0.35` 改读 settings.rag_min_similarity | ✅ |
| `b8dfd53` | refactor | **[3.5+3.6] lifespan + 日志配置**：`@app.on_event("startup")` → `@asynccontextmanager lifespan`；shutdown 时 `await close_client()` 关 httpx 连接池；main.py 加 `LOG_LEVEL` env 驱动的 logging.basicConfig | ✅ |
| `4898163` | refactor | **[3.7] 移除未实现 cloud_api 模式**：config.py 删 rerank_cloud_* 三项 + 注释从 `none\|llm\|cloud_api` 改 `none\|llm`；reranker_service 删 cloud_api 注释 | ✅ |
| `e7d7e54` | test | **[4.1] pytest 纯函数单测**：tests/conftest.py + tests/unit/test_pure.py（sanitize_filename/make_title/LlmReranker._parse_indices/NoReranker 共 19 项全过）；pyproject dev 依赖加 pytest-asyncio + ruff | ✅ |
| `4405cc5` | chore | **[4.2] ruff lint+format 全过**：pyproject.toml 加 [tool.ruff] select E/F/I/UP/B，ignore B008(Depends)/B905(zip strict)/F821(SA 前向引用)；ruff format 42 文件；lint+format 全绿 | ✅ |
| `80f8ca4` | ci | **[4.3] GitHub Actions CI**：.github/workflows/ci.yml — backend 跑 ruff check + format check + pytest 纯函数单测（无需重型依赖） | ✅ |
| `395e0ae` | chore | **[4.4+4.5] MIT LICENSE + 删脚手架残留**：新增根目录 LICENSE（MIT）；删 HelloWorld.vue / vue.svg / vite.svg / hero.png / frontend/README.md | ✅ |
| `1b1d812` | feat | **[4.6] PreviewDrawer TXT/MD 预览内容加载**：stores/files.ts 加 previewContent/Loading/Error，openPreview 异步调 preview API 存文本；PreviewDrawer.vue 渲染 loading+error+内容；前端 build 通过 | ✅ |
| `1b1d812` | chore | **[4.7] 版本号三处统一 0.0.9**：frontend package.json + backend pyproject.toml + main.py FastAPI version 全部改为 0.0.9（之前 main.py 硬编码 0.1.0 不一致） | ✅ |
| `1650dfe` | fix | **docker: 基础镜像 pin python:3.11-slim-bookworm**：原 python:3.11-slim 指向 Debian 13 trixie，阿里 apt 源未同步导致 404；pin 到 bookworm（Debian 12 stable）解决 | ✅ 镜像重建成功 |

---

**版本标签**：`v0.0.1` → `9bf33f8` · `v0.0.2` → `4e5a983` · `v0.0.3` → `d427529` · `v0.0.4` → `HEAD-10` · `v0.0.5` → `HEAD-9` · `v0.0.6` → `HEAD-8` · `v0.0.7` → `HEAD-7` · `v0.0.8` → `HEAD-6` · `v0.0.9` → `HEAD`（部署验证：容器三服务健康 + 健康检查 ok）
