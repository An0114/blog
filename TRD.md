# TRD：个人博客网站

> 文档状态：v1.2（2026-10 补录二期已实现设计；新增三期：收藏 / 草稿箱 / 上传进度；UI 主题与导航权限）｜ 上游输入：PRD.md ｜ 技术栈决策人：博主（你）

## 1. 技术栈选型与理由

| 层 | 选型 | 理由（结合你的背景） |
|----|------|---------------------|
| 后端框架 | Python FastAPI + Uvicorn | 你有 Python 基础；生态成熟、面试常考；自带 OpenAPI 文档方便调试 |
| ORM | SQLAlchemy | 参数化查询天然防 SQL 注入，符合本项目安全红线 |
| 数据库 | PostgreSQL | 生产标准、功能强；备考面试加分；本地开发用 Docker 起实例 |
| 认证 | JWT（python-jose）+ bcrypt（passlib） | 无状态会话、主流方案；bcrypt 抗彩虹表 |
| 文件上传 | python-multipart + 本地存储 uploads/ | 个人站点量级足够；后续可换对象存储（OSS/S3） |
| 前端 | React + Vite + TypeScript | 主流、简历加分；组件化利于页面复用 |
| 部署 | Gunicorn/Uvicorn + Nginx 反向代理 | 你家 Linux 服务器可承载，正好练运维与 Nginx |
| 配置 | .env（python-dotenv） | 密钥/路径全部走环境变量，禁止硬编码 |

**否决项**：暂不上微服务、消息队列、Redis 缓存——MVP 用最简单能跑通的技术栈（遵循主文档 5.3 原则），需要时再升级并更新本 TRD。

## 2. 系统 / 分层架构

```
浏览器（React SPA）
   │  HTTPS
   ▼
Nginx ──▶ 静态资源（frontend/dist）  反向代理 /api → 后端
   │
   ▼
FastAPI（app/）
   ├─ routers/     接口路由层（auth/posts/media/comments/admin）
   ├─ services/    业务逻辑层
   ├─ models/      数据模型（SQLAlchemy）
   └─ core/        配置、安全工具、数据库、依赖注入
   │
   └─ PostgreSQL 数据库（Docker 本地实例）
   └─ 本地文件存储（uploads/）
```

## 3. 模块划分

| 模块 | 职责 |
|------|------|
| auth | 注册、登录、JWT 签发与校验、当前用户依赖 |
| posts | 动态 CRUD、分类筛选、分页 |
| media | 上传、类型/大小校验、UUID 重命名、文件删除 |
| comments | 评论列表、新增、删除（作者本人） |
| admin | 用户管理：列表、禁用/启用、软删除（仅博主） |
| common | 数据库会话、配置、统一响应、异常处理 |

## 4. API 接口设计

| 路径 | 方法 | 参数 | 返回 | 鉴权 |
|------|------|------|------|------|
| /api/auth/register | POST | username, email, password | 用户信息 | 无 |
| /api/auth/login | POST | email, password | {token, user} | 无 |
| /api/auth/me | GET | - | 当前用户（含 email_verified） | 需登录 |
| /api/auth/verify-email/request | POST | - | {message, expires_minutes} | 需登录 |
| /api/auth/verify-email/confirm | POST | token | 用户信息 | 无 |
| /api/auth/forgot-password | POST | email | {message}（防枚举） | 无 |
| /api/auth/reset-password | POST | token, new_password | {message} | 无 |
| /api/posts | GET | category?, page, size | 动态列表（含首图/封面/点赞数） | 无 |
| /api/posts/{id} | GET | - | 动态详情 + 媒体 + 评论 + 点赞/收藏状态 | 无（可选登录） |
| /api/posts | POST | title, content, category, media_ids? | 动态详情 | 博主 |
| /api/posts/{id} | DELETE | - | 204（级联删除媒体与评论） | 博主 |
| /api/posts/{id}/like | POST | - | {liked, like_count} | 需登录 |
| /api/posts/{id}/favorite | POST | - | {favorited, favorite_count} | 需登录 |
| /api/me/favorites | GET | page, size | 我的收藏列表（含收藏时间） | 需登录 |
| /api/drafts | POST | title, content, category, media_ids? | 草稿 | 博主 |
| /api/drafts | GET | page, size | 草稿列表 | 博主 |
| /api/drafts/{id} | GET | - | 草稿详情 | 博主 |
| /api/drafts/{id} | PUT | title, content, category, media_ids? | 草稿 | 博主 |
| /api/drafts/{id} | DELETE | - | 204 | 博主 |
| /api/drafts/{id}/publish | POST | - | 动态详情 | 博主 |
| /api/upload | POST | file, type(image/video) | {media_id, url} | 博主 |
| /api/posts/{id}/comments | GET | - | 评论列表 | 无 |
| /api/posts/{id}/comments | POST | content | 评论对象 | 需登录 |
| /api/comments/{id} | DELETE | - | 204 | 评论作者或博主 |
| /api/admin/users | GET | page, size | 用户列表 | 博主 |
| /api/admin/users/{id} | PATCH | status(active/disabled) | 用户 | 博主 |
| /api/admin/users/{id} | DELETE | - | 204（软删除 status=deleted，评论保留） | 博主 |
| /api/admin/comments | GET | page, size | 全站评论列表（含动态标题） | 博主 |
| /api/admin/comments/{id} | DELETE | - | 204 | 博主 |

**约定**：分页统一 `page`（从 1 起）+ `size`（默认 10）；错误统一返回 `{detail: "原因"}`；JWT 放 `Authorization: Bearer <token>`。
**上传进度（三期）**：纯前端能力——axios `onUploadProgress` 计算实时百分比，接口无变化。
**UI 主题与导航权限（三期 UI，PRD A13）**：无新增表 / 字段、无新增 API；"关于我"为纯前端静态页；导航可见性与路由守卫均为前端约束（后端已有鉴权兜底）。

## 5. 数据库设计

数据库：**PostgreSQL**（2026-10-02 拍板，决策过程见 TRD--choosing.md 4.2）。

```
users
  id            BIGSERIAL PRIMARY KEY
  username      TEXT UNIQUE NOT NULL
  email         TEXT UNIQUE NOT NULL
  password_hash TEXT NOT NULL
  role          TEXT NOT NULL DEFAULT 'user'       -- admin / user
  status        TEXT NOT NULL DEFAULT 'active'     -- active / disabled / deleted
  email_verified BOOLEAN NOT NULL DEFAULT FALSE    -- 二期：邮箱验证（可选，不阻断登录）
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()

posts
  id         BIGSERIAL PRIMARY KEY
  author_id  BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE
  title      TEXT NOT NULL
  content    TEXT NOT NULL
  category   TEXT NOT NULL                        -- project / daily / diary
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()

media
  id         BIGSERIAL PRIMARY KEY
  post_id    BIGINT REFERENCES posts(id) ON DELETE CASCADE   -- 可为空：先上传后绑定（刻意偏离 MVP DDL）
  type       TEXT NOT NULL                        -- image / video
  file_path  TEXT NOT NULL                        -- uploads/ 相对路径
  file_size  INTEGER NOT NULL
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()

comments
  id         BIGSERIAL PRIMARY KEY
  post_id    BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE
  user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE
  content    TEXT NOT NULL
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()

post_likes                                          -- 二期：点赞
  id         BIGSERIAL PRIMARY KEY
  post_id    BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE
  user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
  UNIQUE (post_id, user_id)

email_tokens                                        -- 二期：邮件令牌
  id         BIGSERIAL PRIMARY KEY
  user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE
  token      TEXT UNIQUE NOT NULL
  purpose    TEXT NOT NULL                         -- verify_email / reset_password
  expires_at TIMESTAMPTZ NOT NULL
  used       BOOLEAN NOT NULL DEFAULT FALSE
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()

post_favorites                                      -- 三期：收藏
  id         BIGSERIAL PRIMARY KEY
  post_id    BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE
  user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
  UNIQUE (post_id, user_id)

drafts                                              -- 三期：草稿箱（仅博主）
  id         BIGSERIAL PRIMARY KEY
  author_id  BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE
  title      TEXT NOT NULL
  content    TEXT NOT NULL
  category   TEXT NOT NULL                        -- project / daily / diary
  media_ids  JSONB NOT NULL DEFAULT '[]'          -- 已上传待绑定的媒体 id 数组
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()

索引：
  posts(category, created_at DESC)
  comments(post_id, created_at)
  post_likes UNIQUE(post_id, user_id)
  email_tokens(user_id, purpose)（ix_email_tokens_user_purpose）；token UNIQUE
  post_favorites UNIQUE(post_id, user_id)；post_favorites(user_id, created_at DESC)（我的收藏按时间倒序）
  drafts(author_id, created_at DESC)
```

**Model 变更与建表语句（SQLAlchemy 对应）**：
- 新增模型：`PostLike`（models/like.py）、`EmailToken`（models/email_token.py）、`PostFavorite`（models/favorite.py）、`Draft`（models/draft.py），均在 `app/models/__init__.py` 导出并在 `main.py` 注册（`Base.metadata.create_all` 自动建新表）。
- `users` 新增列 `email_verified`（Boolean, nullable=False, server_default='false'）——**create_all 不改已有表**，开发库需手动 `ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE`。
- 收藏唯一约束：`UniqueConstraint('post_id','user_id', name='uq_post_favorites_post_user')` + 索引 `ix_post_favorites_user_created`。
- 草稿媒体：`media_ids` 用 `sqlalchemy.JSON`（PG 落为 JSONB），存"已上传未绑定"的 media id 数组；发布时经 posts 服务校验存在且未被占用后绑定到 Post 并删除草稿。

> 说明：删除用户采用**软删除**（users.status = 'deleted'）：记录保留、禁止登录；其历史评论保留展示并标注"用户已注销"，因此正常流程不会触发 comments.user_id 的物理级联删除（PRD A8 定稿）。

## 6. 项目目录结构

```
个人博客项目/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 入口
│   │   ├── core/              # config.py / security.py / database.py
│   │   ├── models/            # user.py / post.py / media.py / comment.py
│   │   ├── schemas/           # Pydantic 请求/响应模型
│   │   ├── services/          # 业务逻辑
│   │   └── routers/           # auth.py / posts.py / media.py / comments.py / admin.py
│   ├── tests/                 # pytest 测试
│   ├── requirements.txt
│   └── .env.example           # DATABASE_URL 指向 PostgreSQL
├── frontend/
│   ├── src/
│   │   ├── api/               # 接口封装
│   │   ├── pages/             # Home / PostDetail / Login / Register / Publish / Admin
│   │   ├── components/        # PostCard / CommentList / Uploader ...
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── uploads/                   # 上传文件（不入 Git）
├── AGENTS.md / CLAUDE.md      # AI 行为守则
├── PRD.md / TRD.md            # 本文档
└── README.md                  # 启动说明
```

## 7. 任务清单（按依赖排序，每项可独立验收）

| 任务 | 内容 | 验收 |
|------|------|------|
| Task 1 | 项目骨架：FastAPI + PostgreSQL（Docker 本地实例）+ .env + 目录结构 | 服务启动，健康检查返回 200，数据库连接成功 |
| Task 2 | User 模型 + 注册/登录 + JWT + bcrypt | 注册/登录接口按 PRD A2/A3 通过 |
| Task 3 | Post 模型 + 动态 CRUD + 分类/分页 | 动态流接口按 A5 通过 |
| Task 4 | 上传接口 + 白名单校验 + UUID 存储 | 图片/视频上传按 A4 通过 |
| Task 5 | Comment 模型 + 评论接口 | 评论按 A7 通过 |
| Task 6 | admin 用户管理接口 | 管理接口按 A8 通过 |
| Task 7 | 前端骨架 + 动态列表/详情页 | 页面可浏览（A1） |
| Task 8 | 前端注册/登录 + 发布页（含上传） | 完整走通发布流程（A2-A4） |
| Task 9 | 前端管理页面 | 用户管理可用（A8） |
| Task 10 | 测试补全 + Nginx 部署 + 备份方案 | 公网可访问，文档齐全 |
| Task 11 | 收藏：post_favorites 表 + 收藏 toggle + 我的收藏列表 + 详情收藏状态 + 前端收藏入口 | 按 PRD A10 通过 |
| Task 12 | 草稿箱：drafts 表 + 草稿 CRUD + 发布 + 前端草稿入口 | 按 PRD A11 通过 |
| Task 13 | 附件上传进度：前端 onUploadProgress 进度条 | 按 PRD A12 通过 |
| Task 14 | UI 主题与导航权限：深色文艺主题（品牌"未完成的页"）、侧边导航布局、普通用户仅见 动态/收藏/关于我、博主见全部、"关于我"页 | 按 PRD A13 通过 |

## 9. 前端 UI 与导航权限设计（2026-10，PRD A13）

**品牌与主题**：
- 站点标题 / logo：**未完成的页**（手写体风格）；标语「这里只放我真正在乎的文字」；定位「长期写作｜私人笔记｜阅读痕迹｜生活片段」。
- 主题：深色文艺质感——墨色/暖棕底色 + 纸感卡片（信纸、钢笔、便签装饰元素）、手写体点缀；按钮/标签/输入框沿用暖色系高亮。

**布局**：深色左侧导航栏（logo + 栏目）+ 中间内容区 + 可选右侧个人板块；登录页为深色背景 + 居中登录弹窗；发布页为编辑区 + 字数统计 + 预估阅读时长（纯前端计算：字数 = 正文长度，阅读时长 ≈ 字数 / 300 字每分钟）。

**导航可见性矩阵**（前端约束，路由层用守卫组件兜底）：

| 栏目 | 未登录 | 普通用户 | 博主 |
|------|--------|----------|------|
| 动态（首页） | ✓ | ✓ | ✓ |
| 收藏 | ✗ | ✓ | ✓ |
| 关于我 | ✓ | ✓ | ✓ |
| 发布 | ✗ | ✗ | ✓ |
| 草稿箱 | ✗ | ✗ | ✓ |
| 用户管理 | ✗ | ✗ | ✓ |

- 新增 `AdminRoute`（前端路由守卫：非博主渲染"仅博主可访问"提示）；`/admin`、`/drafts`、`/publish` 使用该守卫（后端 403 仍为最终兜底）。
- 登录入口（用户名 → 账户设置 / 退出）对已登录用户保留。

## 8. 非功能性要求

- **性能**：列表接口本地 P95 < 300ms；图片懒加载；视频使用 HTML5 播放器。
- **安全**（对应 PRD A9）：bcrypt 存密码；JWT 密钥走 .env、7 天过期；上传白名单 + 大小限制 + UUID 重命名；全部 SQL 走 ORM 参数化；CORS 白名单（仅允许你的域名）；前端对评论/正文做输出转义防 XSS；.env 与 uploads/ 不入 Git。
- **部署**：Nginx 托管前端静态资源 + 反代 /api；HTTPS（Let's Encrypt，可选）；定期 pg_dump 备份数据库与 uploads/。
