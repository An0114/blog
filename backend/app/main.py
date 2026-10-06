"""FastAPI 应用入口。"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.models import media, post, user  # noqa: F401  注册全部表到 Base.metadata
from app.routers import auth, posts
from app.routers import media as media_router
from app.services.errors import ServiceError


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """启动时自动建表（MVP 未引入 Alembic；生产上线前应迁移到迁移工具）。"""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="个人博客 API", version="0.1.0", lifespan=lifespan)

# CORS 白名单（PRD A9：只允许配置的域名，见 .env CORS_ORIGINS）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(media_router.router)

# 上传文件静态访问（/uploads/<uuid>.<ext>）；目录不存在时先创建
os.makedirs(settings.upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.exception_handler(ServiceError)
async def service_error_handler(_: Request, exc: ServiceError) -> JSONResponse:
    """业务异常统一转成 {detail: "原因"}（TRD 第 4 节错误约定）。"""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """健康检查：返回 200 并验证数据库连通性（Task 1 验收点）。"""
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
