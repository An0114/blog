# 阶段一：构建前端产物（node:22-alpine，满足 vite 8 的 Node >=20.19/22.12 要求）
FROM node:22-alpine AS builder

WORKDIR /app

# 先只拷依赖清单，利用层缓存（package-lock.json 不变则 npm ci 不重跑）
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ---- 阶段二：Nginx 静态托管 + 反代 /api、/uploads 到后端 ----
FROM nginx:1.27-alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

# 健康检查：首页需返回 200（busybox wget）
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]
