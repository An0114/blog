# 个人博客「未完成的页」

FastAPI + React 的个人博客：博主发布"项目 / 日常 / 日记"动态（支持图片、视频），用户注册登录后可评论、点赞、收藏；提供站点初始化、草稿箱、评论管理与邮箱验证。深色文艺主题，着陆页 + 滚动过渡，复古圆形徽章 Logo。

技术栈：Python 3.14 + FastAPI + SQLAlchemy + PostgreSQL（后端）；React 19 + Vite + TypeScript 严格模式（前端）；Docker Compose 一键部署。

---

## Docker 部署（推荐）

> 仅需 Docker 与 Docker Compose，无需安装任何本地依赖。需求与验收见 `PRD.md`，技术方案见 `TRD.md` 第 10 章。

### 快速开始（三步）

```bash
# 1. 准备环境变量（JWT 密钥必须自生成，禁止用模板默认值）
cp .env.example .env
#    生成密钥：openssl rand -hex 32   → 填入 .env 的 JWT_SECRET_KEY
#    按需修改：POSTGRES_PASSWORD / CORS_ORIGINS / SMTP_* / HTTP_PORT

# 2. 一条命令启动全栈（数据库 + 后端 + 前端 Nginx）
docker compose up -d --build

# 3. 浏览器打开站点，首次部署进入 /admin/init 初始化
#    http://<服务器IP或域名>[:HTTP_PORT]/
#    初始化页：创建博主账户（可选上传站点图标、配置邮箱验证开关与 SMTP）
#    完成后用博主账户登录 → 发布第一条动态
```

启动顺序由 compose 自动编排（后端等数据库就绪、前端等后端就绪）。验证：`curl http://localhost/health` 返回 `{"status":"ok","database":"ok"}`。

### 自定义配置

| 想改什么 | 改哪里 |
|---|---|
| 站点名 / 标语 / 关于我联系方式 | `frontend/src/pages/AboutPage.tsx` 等常量 + `index.html` title（改后 `docker compose up -d --build`） |
| 网站图标（浏览器标签页 Logo） | `/admin/init` 上传，或替换 `frontend/public/favicon.svg` |
| 邮箱验证开关与 SMTP | `/admin/init` 配置（site_configs 优先）；或 `.env` 的 `SMTP_*`（兜底）。SMTP 留空时验证/重置链接输出到后端日志（开发模式） |
| 对外端口 | `.env` 的 `HTTP_PORT`（默认 80） |
| 域名 / CORS | `.env` 的 `CORS_ORIGINS`（逗号分隔白名单）与 `FRONTEND_BASE_URL`；HTTPS 建议再套一层 Nginx/Caddy 或云负载均衡 |
| 数据库账号密码 | `.env` 的 `POSTGRES_USER/PASSWORD/DB`（首次启动前设置才生效） |

### 数据备份 / 恢复

```bash
# 备份数据库
docker compose exec db pg_dump -U blog blog > blog_backup.sql
# 恢复数据库
docker compose exec -T db psql -U blog blog < blog_backup.sql

# 备份上传媒体（图片/视频/站点图标）
docker run --rm -v blog_uploads:/data -v $(pwd):/backup alpine \
  tar czf /backup/uploads_backup.tar.gz -C /data .
```

### 升级步骤

```bash
git pull                     # 拉取新代码
docker compose up -d --build # 重建变更服务，数据卷不受影响
```

> ⚠️ **重要**：后端启动时用 `Base.metadata.create_all` 自动建表，它**只建新表、不会修改已存在的表**。后续版本新增列/表时，升级需手动执行 `ALTER TABLE`（历史案例：`users` 新增 `email_verified` 列）。具体语句以对应版本的 `TRD.md` 第 5 节为准。

### 开发模式（热重载）

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

后端挂载源码 `--reload` 热重载（8000 端口）、前端 `npm run dev`（5173，代理到容器内后端），数据库/上传数据与生产同卷。也可完全本地开发：见下方。

---

## 本地开发（不依赖 Docker 数据库时）

```bash
# 后端（需本地 PostgreSQL，配置见 backend/.env.example）
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows；Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 填写 DATABASE_URL
uvicorn app.main:app --reload                     # http://127.0.0.1:8000

# 前端
cd frontend
npm install
npm run dev                                       # http://127.0.0.1:5173（代理 /api、/uploads → 8000）
```

测试与构建：后端 `cd backend && pytest`；前端 `npm run lint && npm run build && npm run test`。

## 目录结构

```
backend/    FastAPI 应用（routers → services → models 分层）
frontend/   React + Vite（pages/ 页面、components/ 组件）
docker-compose.yml      生产部署（db + backend + frontend-nginx）
docker-compose.dev.yml  开发热重载（与生产共用数据卷）
```

安全约定：密码 bcrypt 哈希、SQL 全 ORM 参数化、上传白名单 + UUID 重命名、`.env` 与 `uploads/` 不入 Git（见 `AGENTS.md`）。
