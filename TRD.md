# TRD：个人博客网站

> 文档状态：MVP 版 v1.0 ｜ 上游输入：PRD.md ｜ 技术栈决策人：博主（你）

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
| /api/auth/me | GET | - | 当前用户 | 需登录 |
| /api/posts | GET | category?, page, size | 动态列表（含首图/封面） | 无 |
| /api/posts/{id} | GET | - | 动态详情 + 媒体列表 + 评论 | 无 |
| /api/posts | POST | title, content, category, media_ids? | 动态详情 | 博主 |
| /api/posts/{id} | DELETE | - | 204（级联删除媒体与评论） | 博主 |
| /api/upload | POST | file, type(image/video) | {media_id, url} | 博主 |
| /api/posts/{id}/comments | GET | - | 评论列表 | 无 |
| /api/posts/{id}/comments | POST | content | 评论对象 | 需登录 |
| /api/comments/{id} | DELETE | - | 204 | 评论作者 |
| /api/admin/users | GET | page, size | 用户列表 | 博主 |
| /api/admin/users/{id} | PATCH | status(active/disabled) | 用户 | 博主 |
| /api/admin/users/{id} | DELETE | - | 204（软删除 status=deleted，评论保留） | 博主 |

**约定**：分页统一 `page`（从 1 起）+ `size`（默认 10）；错误统一返回 `{detail: "原因"}`；JWT 放 `Authorization: Bearer <token>`。

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
  post_id    BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE
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

索引：posts(category, created_at DESC)；comments(post_id, created_at)
```

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

## 8. 非功能性要求

- **性能**：列表接口本地 P95 < 300ms；图片懒加载；视频使用 HTML5 播放器。
- **安全**（对应 PRD A9）：bcrypt 存密码；JWT 密钥走 .env、7 天过期；上传白名单 + 大小限制 + UUID 重命名；全部 SQL 走 ORM 参数化；CORS 白名单（仅允许你的域名）；前端对评论/正文做输出转义防 XSS；.env 与 uploads/ 不入 Git。
- **部署**：Nginx 托管前端静态资源 + 反代 /api；HTTPS（Let's Encrypt，可选）；定期 pg_dump 备份数据库与 uploads/。
