# Git 改版记录

> 记录 PKB 项目每次 Git 提交的原因、改动范围与验证结果。
> 格式：`hash | 类型 | 原因 | 改动 | 状态`

---

## v0.0.1 （初始快照 + 5 次修复）

### 4dd22b5 · feat: PKB v0.1.0 完整快照 - 阶段一至阶段四

| 项目 | 内容 |
|---|---|
| **原因** | 项目从零搭建完成，需保存首个可运行的完整快照 |
| **改动** | 新增 90 个文件（含 build_backend.log 已在 amend 中移除） |
| **范围** | `docker-compose.yml`、`backend/`（FastAPI 核心 + Alembic）、`frontend/`（Vue 3 + Naive UI）、`deploy/`、`scripts/` |
| **状态** | ✅ 成功 |
| **备注** | .gitignore 排除 `.env`、`backend/data/`、`node_modules`、`dist/`、`*.log`、`__pycache__/` |

---

### a30391b · fix(frontend): tsconfig.app.json 兼容 TS 6.0 - 移除 baseUrl + paths 加 ./ 前缀

| 项目 | 内容 |
|---|---|
| **原因** | VS Code 报 `ignoreDeprecations: "6.0"` 无效，vue-tsc 报 `baseUrl` 已弃用 |
| **改动** | 删 `baseUrl: "."`、删 `ignoreDeprecations: "6.0"`，paths 值从 `["src/*"]` 改为 `["./src/*"]` |
| **范围** | `frontend/tsconfig.app.json` |
| **状态** | ✅ 成功 — `npm run build` 452ms 零错误 |
| **教训** | TS 6.0 正式弃用 `baseUrl`，paths 自动相对 tsconfig.json 目录解析，但必须加 `./` 前缀 |

---

### c590943 · fix(下载): window.open 裸请求丢失 token → 改用 axios 带认证 + Blob + a[download]

| 项目 | 内容 |
|---|---|
| **原因** | 点下载按钮浏览器打开新页面显示 `{"detail": "未提供 token"}` —— `window.open` 绕过 axios 拦截器，没带 Authorization header，后端 401 |
| **改动** | `api/files.ts` 新增 `download(publicId, originalName)`：axios get blob → URL.createObjectURL → `<a download>` 触发保存；`FileCard.vue` 的 `onDownload` 从 `window.open(url)` 改为 `await filesApi.download(...)` |
| **范围** | `frontend/src/api/files.ts`、`frontend/src/components/FileCard.vue` |
| **状态** | ✅ 成功 — 后端日志 `GET .../download 200 OK`，浏览器弹出保存对话框 |
| **教训** | 所有需要认证的 API 调用必须走 axios 拦截器；裸浏览器导航（`window.open`、`<a href>` 跳转）不会带 Authorization header |

---

### 43813f4 · fix(重命名): 后端 PATCH original_name 时自动派生 title

| 项目 | 内容 |
|---|---|
| **原因** | 重命名成功后前端列表仍显示旧名称 —— 前端卡片显示 `item.title`，但只发 `{ original_name }`，后端 DB 里 `title` 是独立字段没跟着更新 |
| **改动** | 后端 `api/files.py` 的 `update_file` 增加：如果 `original_name` 有值但 `title` 为空，调用 `make_title_from_filename` 自动去掉扩展名派生 title |
| **范围** | `backend/app/api/files.py` |
| **状态** | ✅ 成功 — PATCH 前 `title="简历" original_name="简历.docx"`，PATCH 后 `title="测试重命名" original_name="测试重命名.docx"` |
| **教训** | 后端两个独立字段（`title` 展示 + `original_name` 完整名）必须在更新时保持数据一致；前端改什么字段就要考虑 DB 其他关联字段 |

---

### 9bf33f8 · style(重命名): 移除 dialog.warning 冗余弹窗 + 成功提示改文案

| 项目 | 内容 |
|---|---|
| **原因** | 原来重命名流程是**双弹窗**：先弹 Naive UI 的 `dialog.warning`（黄色感叹号图标，重命名不是警告！）→ 点保存 → 再弹 `window.prompt`。冗余且图标语义错误 |
| **改动** | 直接用 `window.prompt` 获取新名称；成功提示从 `"已重命名"` 改为 `"重命名成功"`（绿色勾）；清理无用的 `useDialog` import 和 `dialog` 变量 |
| **范围** | `frontend/src/components/FileCard.vue` |
| **状态** | ✅ 成功 — 单 prompt → 单绿色成功提示 |

---

### 62c153d · refactor(Layout): 侧边栏常驻 — 抽取共用 Layout.vue + 嵌套路由

| 项目 | 内容 |
|---|---|
| **原因** | 点"回收站"后侧边栏 + 顶部 Header 全部消失 —— 原来 `/` 和 `/trash` 是平级路由，HomeView 包含完整 Layout，TrashView 只有裸内容。路由切换时 HomeView 整个卸载 → Sider/Header 销毁 |
| **改动** | 新建 `Layout.vue` 包含完整 Sider + Header + `<router-view>` + PreviewDrawer；Router 改为嵌套结构（Layout 为父路由，HomeView/TrashView 作为子路由）；HomeView 从 120 行完整视图精简为纯 FileList 内容组件 |
| **范围** | 新增 `frontend/src/views/Layout.vue`；重写 `router/index.ts`、`HomeView.vue`、`TrashView.vue` |
| **状态** | ✅ 成功 — 浏览器验证：URL `/trash` + `hasTrashWrap: true` + `hasSider: true` 三指标全通过 |
| **教训** | 需要在多个页面间共享的布局元素（侧边栏、Header、全局抽屉）必须抽到共用 Layout，路由设为嵌套；平级路由会导致旧组件整体卸载 |

---

### 834a310 · docs: 新增 Git改版记录.md（6次提交 + 版本标签 + 通用教训）

| 项目 | 内容 |
|---|---|
| **原因** | 项目提交频繁（6 次修复/重构），每次改完容易忘记为什么改、怎么改的 |
| **改动** | 新建 `Git改版记录.md`，按时间倒序记录每次提交的原因、改动范围、验证结果与经验教训 |
| **范围** | 新增 `Git改版记录.md` |
| **状态** | ✅ 成功 |

---

### 6f54783 · style(侧边栏): 删除动态标签列表，只保留「全部」按钮

| 项目 | 内容 |
|---|---|
| **原因** | 侧边栏显示了数据库里存储的所有动态标签（e2e-test、work-notes、??? 等），用户觉得多余，只需要「全部」一个入口 |
| **改动** | 移除 `v-for="t in tags"` 动态标签行 + `<div class="tags-title">标签</div>` 标题，标签区只保留「全部」按钮 |
| **范围** | `frontend/src/views/Layout.vue`（-7 行） |
| **状态** | ✅ 成功 — `npm run build` 481ms 零错误，前端容器重建正常 |

---

## 版本标签

| 标签 | 指向 | 说明 |
|---|---|---|
| `v0.0.1` | 9bf33f8 | 完整快照 + 5 个热修，`git tag -a v0.0.1` 注解标签 |

---

## 通用教训（值得长期记住）

| # | 场景 | 问题 | 解决 |
|---|---|---|---|
| 1 | TS 6.0 升级 | `baseUrl` 弃用 | 删 baseUrl + paths 加 `./` 前缀 |
| 2 | Naive UI v-model | `visible` 只读 computed 无法写入 | 改可写 computed（带 setter） |
| 3 | API 认证 | `window.open`/`<a href>` 裸请求丢 token | 走 axios + 拦截器 + Blob + `a.download` |
| 4 | 路由布局 | 平级路由切换卸载 Layout | 共用 Layout 父路由 + 嵌套子路由 |
| 5 | DB 多字段同步 | 改 original_name 忘同步 title | 后端自动派生（单一信源） |
