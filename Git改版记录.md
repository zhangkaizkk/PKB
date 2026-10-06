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

---

**版本标签**：`v0.0.1` → `9bf33f8` · `v0.0.2` → `4e5a983` · `v0.0.3` → `d427529`
