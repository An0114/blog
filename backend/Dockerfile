# 多阶段构建：builder 安装依赖 → runtime 精简运行（无构建缓存、镜像小）
FROM python:3.14-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
COPY backend/requirements.txt .
RUN python -m pip install --prefix=/install -r requirements.txt

# ---- 运行阶段 ----
FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 非 root 运行（AGENTS.md 安全红线）；预建 uploads 目录并 chown，
# 保证 named volume 挂载时继承属主、容器内可写（上传媒体/站点图标）。
RUN groupadd -r appuser \
    && useradd -r -g appuser appuser \
    && mkdir -p /app/uploads \
    && chown -R appuser:appuser /app

COPY --from=builder /install /usr/local
COPY backend/app /app/app

USER appuser

EXPOSE 8000

# 健康检查：/health 需返回 200（slim 无 curl，用标准库 urllib）
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
