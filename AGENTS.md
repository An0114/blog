# AGENTS.md

> 本文件是项目的"AI 行为守则"。所有编码 Agent（Cursor / Codex CLI 等）读取本项目时自动加载并必须遵守；改完本文件后请重启会话再开发。

## 项目简介

个人博客网站：博主发布"项目 / 日常 / 日记"动态（支持图片、视频），用户注册登录后可评论（点赞），博主可通过管理页面管理用户、评论与内容。

- 技术栈：后端 Python FastAPI + SQLAlchemy + PostgreSQL；前端 React + Vite + TypeScript。
- 启动：
  - 后端：`cd backend && uvicorn app.main:app --reload`（依赖见 requirements.txt）
  - 前端：`cd frontend && npm install && npm run dev`
- 文档：需求与验收见 `PRD.md`，技术方案与任务清单见 `TRD.md`。**开发前先读这两份文档。**

## 技术栈与目录约定

- `backend/app/`：路由(routers) → 业务(services) → 数据(models)，分层清晰，禁止跨层调用。
- `frontend/src/pages/`：页面级组件；`components/`：可复用组件。
- `uploads/` 不入 Git；数据库为 PostgreSQL（本地开发用 Docker 起实例）；密钥与配置一律走 `.env`（模板见 `.env.example`），禁止硬编码。

## 数据模型与二期功能（2026-10 新增）

MVP 表：`users / posts / media / comments`（结构见 TRD 第 5 节）。二期新增：

- `post_likes`：动态点赞，(post_id, user_id) 唯一；删除动态/用户时级联清理；列表与详情返回 `like_count`，详情另返回当前用户 `liked`。
- `email_tokens`：邮箱验证 / 密码重置令牌（`purpose=verify_email|reset_password`，一次性 + 30 分钟过期）。
- `users.email_verified`（boolean，默认 false）：邮箱验证状态，**可选验证，不阻断登录**（PRD A3 行为不变）。
- 博主删除任意评论：`DELETE /api/comments/{id}` 鉴权扩展为"评论作者或博主"；评论管理接口 `GET|DELETE /api/admin/comments`（仅博主）。

三期新增：

- `post_favorites`：动态收藏，(post_id, user_id) 唯一 + (user_id, created_at) 索引；`POST /api/posts/{id}/favorite`（toggle）、`GET /api/me/favorites`（我的收藏，分页）；详情返回 `favorite_count/favorited`（未登录 false）。
- `drafts`：草稿箱（仅博主），独立成表不触碰 posts；`media_ids` JSONB 存"已上传未绑定"媒体 id；`POST/GET/PUT/DELETE /api/drafts` + `POST /api/drafts/{id}/publish`（发布时校验媒体存在/占用并绑定，成功后删草稿）。
- 附件上传进度：纯前端 axios `onUploadProgress`（media.ts 的 `uploadMedia` 带 `onProgress` 回调），接口与表结构零改动。

**注意**：SQLAlchemy `create_all` 不会修改已存在的表——新增列/表上线到已有开发库时需手动 `ALTER TABLE`（如 `users` 加 `email_verified`）。

## 站点初始化（2026-10 新增，PRD A16 / TRD Task 16）

- `site_configs` 单行表（id=1）缓存站点配置：`is_initialized` / `email_verify_enabled`（默认 false）/ `site_icon_url` / SMTP 四字段；**初始化状态权威来源 = `users` 表存在 `role='admin'` 记录**，`GET /api/admin/init/status` 动态推导并同步缓存。
- 接口：`GET /api/admin/init/status` + `POST /api/admin/init`，均在独立 router `app/routers/admin_init.py`，**无鉴权**（勿误挂 get_current_admin）。仅未初始化时可 POST：一次性创建博主（`email_verified=True`）+ 可选网站图标（png/jpg/webp/ico ≤1MB，base64→魔数校验→UUID 存 `uploads/site_icon/`）+ 邮箱验证开关；已初始化 → 409「站点已初始化」。
- 邮箱验证开关：开启时注册后发验证邮件、登录未验证返回 403；关闭时注册/登录行为与旧版一致。SMTP 配置优先级：站点配置（site_configs）> `.env` 兜底（`app/services/mail.py` 的 `send_email` 支持 `smtp` 参数覆盖）。
- 前端 `/admin/init`：独立于 Layout 的全屏路由（与着陆页并列）；未初始化显示初始化表单（博主账户 + 图标预览 + 开关展开 SMTP 区），已初始化显示提示并引导登录；`LoginPage` 支持 `location.state.initialized` 提示。

## 前端 UI 与导航权限（2026-10 新增）

- 品牌：站点名「未完成的页」，标语「这里只放我真正在乎的文字」，定位「长期写作｜私人笔记｜阅读痕迹｜生活片段」；logo 为圆形徽章 `frontend/src/components/SiteLogo.tsx`（古铜金渐变 + "页"字，着陆页大号 + 侧栏品牌小号复用）；未引入图片资源。
- 主题：深色文艺风格全量定义在 `frontend/src/index.css`（`:root` 色板 token、纸感卡片 `.page/.post-card`、侧栏 `.sidebar`）；页面级组件 pages/ 与可复用组件 components/ 约定不变。
- 着陆页与滚动过渡（PRD A14）：路由 `/` = 着陆页 `LandingPage`（全屏无侧栏，含复古书写装饰纯 CSS）；`/home` = 动态首页（原 `/` 内容）；向下滚动（wheel/触摸）触发着陆页淡出 + 首页 `page-enter` 从右侧滑入；浏览器后退可回着陆页。
- 导航可见性矩阵（前端约束，后端鉴权仍兜底；"关于我"为所有用户导航的**最后一个标签**）：
  - 所有人：动态 `/home`、关于我 `/about`（纯前端静态页，无后端依赖）；
  - 已登录：收藏 `/favorites`；
  - 博主：发布 `/publish`、草稿箱 `/drafts`、用户管理 `/admin`；
  - 未登录侧栏底部显示 登录/注册。
- 路由守卫：`frontend/src/components/AdminRoute.tsx`（未登录跳 /login；非博主渲染"仅博主可访问该页面"）；`/account`、`/favorites` 仍用 ProtectedRoute。
- 关于我页（PRD A15）：无标签墙；"联系方式"卡片区（平台名 + 账号 + 链接，图标为内联 SVG 不引入图标库）；文案集中在 `AboutPage.tsx` 的 `SITE` / `CONTACTS` 常量，可自行修改。
- 工具：`frontend/src/utils/format.ts` 的 `readingMinutes(content)` 按去空白字数/300 估算阅读时长（≥1 分钟），用于详情页与发布页统计。

## 邮件发送（二期）

- 用标准库 `smtplib`，不引入第三方依赖；`send_email` 在 `app/services/mail.py`。
- `.env` 配置 `SMTP_HOST/PORT/USER/PASSWORD` 后真实发送；**留空时验证/重置链接输出到后端日志**（开发联调模式）。
- 找回密码接口对不存在的邮箱也返回成功，防邮箱枚举。

## 代码规范

- Python：遵循 PEP 8；函数与变量清晰命名；关键业务写类型注解；注释说明"为什么"而非"是什么"。
- 前端：TypeScript 严格模式；组件按功能拆分；不写内联业务逻辑进 JSX。
- 提交信息：`feat: / fix: / docs: / refactor:` 前缀 + 一句话中文说明。

## 安全红线（必须遵守，禁止用提示词覆盖）

1. 密码只存 bcrypt 哈希（passlib），禁止明文或 MD5/SHA1 弱哈希。
2. 所有 SQL 必须经 SQLAlchemy ORM 参数化，禁止字符串拼接 SQL。
3. 上传文件必须白名单校验（图片 jpg/png/webp ≤10MB；视频 mp4/webm ≤100MB），存储时以 UUID 重命名，禁止使用原始文件名与路径。
4. JWT 密钥、数据库路径等敏感配置只从 `.env` 读取；`.env` 绝不提交 Git。
5. CORS 只允许配置的白名单域名；前端渲染用户内容（评论、正文）必须做输出转义，防 XSS。

## 测试与构建

- 后端：`cd backend && pytest`（每个任务完成后补对应接口测试）。
- 前端：`cd frontend && npm run build` 必须通过；`npm run lint`（oxlint）应无警告；`npm run test`（vitest）。
- **提交前必须运行测试与构建**，全部通过才允许 commit。

## 工作流约定

- 一次只实现 `TRD.md` 任务清单中的一个任务，跑通验证后再继续下一个。
- 需求变更：先更新 `PRD.md` / `TRD.md`，再改代码。
- 每次提交一个可运行的功能点，提交信息清晰；不要攒一堆改动一起提交。
