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

---

**版本标签**：`v0.0.1` → `9bf33f8` · `v0.0.2` → `4e5a983` · `v0.0.3` → `d427529` · `v0.0.4` → `HEAD-1` · `v0.0.5` → `HEAD`
