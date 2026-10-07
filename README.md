# 个人博客「未完成的页」

FastAPI + React 的个人博客基础项目：博主发布"项目 / 日常 / 日记"动态（支持图片、视频），用户注册登录后可评论、点赞、收藏。**本项目定位为可二次开发的基础模板**——想拥有自己的个人博客，克隆后在 AboutPage 常量、站点配置处做微量修改即可产出专属站点并部署。

技术栈：Python 3.14 + FastAPI + SQLAlchemy + PostgreSQL（后端）；React 19 + Vite + TypeScript 严格模式（前端）；Docker Compose 一键部署。需求与验收见 `PRD.md`，技术设计见 `TRD.md`。

---

## 功能简介

| 模块 | 已实现能力 |
|---|---|
| 认证 | 注册 / 登录（JWT 7 天，bcrypt 存密码）；禁用 / 软删除用户；忘记密码 / 邮箱验证（可选开关） |
| 内容 | 发布"项目/日常/日记"动态（文字 + 图片 ≤10MB / 视频 ≤100MB，白名单校验 + UUID 存储）；列表分类筛选 + 分页；删除动态（媒体级联下线） |
| 互动 | 评论（登录用户，作者本人或博主可删除）；点赞 / 收藏（toggle + 计数） |
| 博主管理 | 用户管理（禁用/启用/软删除）、评论管理（全站列表/删除） |
| 创作辅助 | 草稿箱（保存/编辑/一键发布，媒体先传后绑）、上传进度条 |
| 站点初始化 | 首次部署浏览器 `/admin/init` 创建博主账户（可传站点图标、开关邮箱验证与 SMTP） |
| UI | 深色文艺主题「未完成的页」：着陆页 + 滚动过渡、复古圆形徽章 Logo、关于我页（联系方式自填）、导航按角色显隐 |
| 部署 | Docker Compose 三服务（db/backend/frontend-nginx）一条命令启动；数据卷持久化 |

### 项目现状（2026-10，重要）

> 标注说明：`✅` = 已完成；`·` = 当前状态/边界（可用但未深化，属预期，可按需扩展；未用 ❌ 因为并非缺陷）。

- `·` **首页不显示评论**——评论只出现在详情页（`/posts/:id`）。
- `·` **评论区仅支持"发表评论"**——无回复楼、无评论点赞等互动，可按需扩展（表结构 `comments` 加 `parent_id` 即可支持楼中楼）。
- `·` **只允许博主一人发布内容**——注册用户只能评论/点赞/收藏；多作者发布未开放。
- `·` **邮箱验证需要个人 SMTP 配置**——`/admin/init` 或 `.env` 配置后开启；**未配置 SMTP 时验证/重置链接输出到后端日志**（`docker compose logs backend` 查看）。
- `·` **标签墙尚未实现**——首页侧栏的"标签墙"是静态占位文案（`frontend/src/pages/HomePage.tsx` 的 `SIDE` 常量），无数据模型支撑，可按需实现。
- ✅ **项目已 Docker 容器化**（见下方启动）；镜像已发布到 Docker Hub 与 GHCR（见"方式 B"）。
- `·` **关于我页的联系方式为空模板**——在 `frontend/src/pages/AboutPage.tsx` 的 `SITE` / `CONTACTS` 常量中自行填写平台名、账号、链接。

## 截图

实拍截图见 `docs/screenshots/`（容器部署后同源渲染）：

| 文件 | 内容 |
|---|---|
| `docs/screenshots/landing.png` | 着陆页：圆形徽章 Logo + 品牌 + 标语 + 定位四项 + 滚动进入提示 |
| `docs/screenshots/home.png` | 动态首页：侧栏导航（普通用户仅 动态/收藏/关于我）+ 分类筛选 + 动态卡片（封面/点赞/收藏）+ 分页 |
| `docs/screenshots/detail.png` | 详情页：正文 + 媒体 + 点赞/收藏 + 阅读时长 |

## 启动

> 三种方式任选。**方式 A 当前可用**；方式 B 需镜像发布后；方式 C 为无 Docker 的本地开发。

### 方式 A：克隆仓库 + Docker 构建（推荐）

```bash
git clone https://github.com/An0114/-.git blog
cd blog

# 1. 准备环境变量（JWT 密钥必须自生成）
cp .env.example .env
#   Windows: copy .env.example .env
#   生成密钥：openssl rand -hex 32（或 python -c "import secrets; print(secrets.token_hex(32))"）
#   填入 .env 的 JWT_SECRET_KEY；按需改 POSTGRES_PASSWORD / CORS_ORIGINS / SMTP_* / HTTP_PORT

# 2. 一条命令启动全栈
docker compose up -d --build

# 3. 浏览器打开站点（默认 http://localhost[:HTTP_PORT]/），首次进入 /admin/init 初始化
#    初始化：创建博主账户（可选上传站点图标、开关邮箱验证/SMTP）→ 登录 → 发布第一条动态
```

验证：`curl http://localhost/health` 返回 `{"status":"ok","database":"ok"}`。

### 方式 B：直接拉取 Docker 镜像（镜像发布后）

镜像发布到 Docker Hub 后（发布命令示例：`docker tag blog-backend <你的账号>/blog-backend:latest && docker push ...`，frontend 同理），可免构建直接启动：

```bash
# 准备好 .env 后：
docker compose up -d            # 自动拉取 compose 中指定的镜像
# 或显式拉取：
# docker pull <你的账号>/blog-backend:latest
# docker pull <你的账号>/blog-frontend:latest
```

> ⚠️ 当前 compose 默认 `build` 本地构建；发布镜像后把 `docker-compose.yml` 中 `backend/frontend` 的 `build` 段替换为 `image: <你的账号>/blog-backend:latest` 即可切换为纯拉取模式。

### 方式 C：本地开发（无 Docker）

```bash
# 后端（需本地 PostgreSQL；配置见 backend/.env.example → 复制为 backend/.env）
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload                        # http://127.0.0.1:8000

# 前端（另开终端）
cd frontend
npm install
npm run dev                                          # http://127.0.0.1:5173（代理 /api、/uploads → 8000）
```

**开发模式（容器内热重载，数据与生产同卷）**：

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### 数据备份 / 恢复 / 升级

```bash
# 备份数据库
docker compose exec db pg_dump -U blog blog > blog_backup.sql
# 恢复数据库
docker compose exec -T db psql -U blog blog < blog_backup.sql
# 备份上传媒体（图片/视频/站点图标）
docker run --rm -v blog_uploads:/data -v $(pwd):/backup alpine tar czf /backup/uploads_backup.tar.gz -C /data .
# 升级（拉新代码后重建，数据卷不受影响）
git pull && docker compose up -d --build
```

> ⚠️ 后端 `create_all` 只建新表、**不会修改已存在的表**。升级到含新列/新表的版本时，需手动执行 `ALTER TABLE`（历史案例：`users` 新增 `email_verified`；语句见对应版本 `TRD.md` 第 5 节）。

## 环境变量

### 根目录 `.env`（容器化部署，模板 `.env.example`）

| 变量 | 必填 | 说明 | 默认 |
|---|---|---|---|
| `JWT_SECRET_KEY` | ✅ | 签名密钥，**必须自生成**（`openssl rand -hex 32`）；缺失时 compose 直接报错 | - |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | ✅ 密码必填 | 数据库账号/密码/库名（密码避免 `@ : / #` 等 URL 特殊字符） | blog / - / blog |
| `CORS_ORIGINS` | 否 | 逗号分隔的前端域名白名单（改域名后必须同步） | `http://localhost` |
| `HTTP_PORT` | 否 | 对外暴露端口 | 80 |
| `FRONTEND_BASE_URL` | 否 | 拼验证/重置邮件链接的前端地址 | `http://localhost` |
| `SMTP_HOST/PORT/USER/PASSWORD/MAIL_FROM` | 否 | 邮件服务；**留空时验证/重置链接输出到后端日志** | 空 |
| `EMAIL_TOKEN_EXPIRE_MINUTES` | 否 | 邮件令牌有效期 | 30 |
| `JWT_EXPIRE_MINUTES` | 否 | JWT 有效期 | 10080（7 天） |
| `PIP_INDEX_URL` | 否 | 构建时 PyPI 源（国内部署建议 `https://pypi.tuna.tsinghua.edu.cn/simple` 加速） | 官方源 |

### `backend/.env`（本地开发，模板 `backend/.env.example`）

`DATABASE_URL`（如 `postgresql+psycopg://postgres:密码@127.0.0.1:5432/blog`）、`JWT_SECRET_KEY`、`CORS_ORIGINS`、SMTP 五字段、`FRONTEND_BASE_URL`、`EMAIL_TOKEN_EXPIRE_MINUTES`。**两个 `.env` 各自独立**，容器部署只读根目录那个。

## 常见问题

**Q1：Windows Docker 拉取基础镜像很慢 / 报 gRPC 错误？**
镜像走 Docker Hub，网络受限时配置镜像加速；compose 多服务并发构建偶发 `failed to dial gRPC` 会话错误，改为逐个构建即可：`docker compose build backend` → `docker compose build frontend` → `docker compose up -d`。后端依赖安装慢时在 `.env` 设 `PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple`。

**Q2：上传视频报 413？**
Nginx 默认请求体 1MB，本项目已配 `client_max_body_size 100m`。若自己改大后端白名单（`services/media.py`），记得同步改 `frontend/nginx.conf`。

**Q3：注册后收不到验证邮件 / 忘记密码没反应？**
SMTP 未配置时链接打印在后端日志：`docker compose logs backend | grep -i link`（本地开发看运行 uvicorn 的终端）。配置真实 SMTP（QQ 邮箱等）后重启：`docker compose up -d --build`。

**Q4：改了域名/端口后页面打不开或接口报 CORS？**
同步改 `.env` 的 `CORS_ORIGINS`（逗号分隔）与 `HTTP_PORT` / `FRONTEND_BASE_URL`，然后 `docker compose up -d`。前端是 SPA，直接刷新 `/login` 等路径返回 404 时检查 nginx `try_files`（已默认配置）。

**Q5：`docker compose up -d` 后博客是空的？**
首次部署需浏览器访问 `/admin/init` 创建博主账户（无 admin 时初始化页才开放；已完成初始化后该页关闭并引导登录）。

**Q6：想改站点名 / 标语 / 关于我联系方式？**
站点文案集中在 `frontend/src/pages/AboutPage.tsx`（`SITE` / `CONTACTS` 常量）与 `frontend/index.html`（title）；浏览器标签图标改 `frontend/public/favicon.svg`。改完 `docker compose up -d --build`。

**Q7：`.env` 会被提交进 Git 吗？**
不会。`.gitignore` 已忽略 `.env`（任意层级），仓库内只有 `.env.example` 模板；`.dockerignore` 同时保证镜像内不含 `.env`。**不要把真实 `.env` 发给别人或传上公开仓库**。

**Q8：三个月后我自己忘了怎么跑？**
读本 README 的"方式 A"三步即可；数据备份/升级命令在本节上方；数据库结构变更先看 `TRD.md` 第 5 节再手动 ALTER。

---

## Star 历史

![Star History](https://api.star-history.com/svg?repos=An0114/-&type=Date)

> 仓库公开后此图自动生效；未公开时显示空数据，属正常。
