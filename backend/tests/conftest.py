"""pytest 全局夹具。

约定：
- 测试使用独立数据库 blog_test（与开发库 blog 隔离，避免污染）。
- 每个用例开始前清空 users 表，保证用例互不影响。
- 依赖本机 Docker 的 PostgreSQL 实例（见 .env DATABASE_URL）。
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

TEST_DB_NAME = "blog_test"


def _test_database_url() -> str:
    """把 DATABASE_URL 的库名替换为 blog_test。"""
    base, _, db = settings.database_url.rpartition("/")
    if not db:
        raise RuntimeError(f"无法从 DATABASE_URL 解析库名: {settings.database_url}")
    return f"{base}/{TEST_DB_NAME}"


def _ensure_test_database() -> None:
    """若 blog_test 不存在则创建（库名是模块常量，非用户输入）。"""
    admin_engine = create_engine(settings.database_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DB_NAME}
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    admin_engine.dispose()


@pytest.fixture(scope="session")
def test_engine() -> Generator:
    """会话级测试引擎：建表于 blog_test，会话结束后删表。"""
    _ensure_test_database()
    engine = create_engine(_test_database_url())
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(test_engine) -> Generator[Session, None, None]:
    """独立会话，供用例直接查库断言（如校验密码哈希）。"""
    factory = sessionmaker(
        bind=test_engine, autocommit=False, autoflush=False, expire_on_commit=False
    )
    session = factory()
    yield session
    session.close()


@pytest.fixture(autouse=True)
def _clean_users(test_engine) -> None:
    """每个用例开始前清空 users 表，保证用例间相互独立。"""
    with test_engine.begin() as conn:
        conn.execute(text("DELETE FROM users"))


@pytest.fixture()
def client(test_engine) -> Generator[TestClient, None, None]:
    """TestClient：将 get_db 依赖替换为测试引擎会话。"""
    factory = sessionmaker(
        bind=test_engine, autocommit=False, autoflush=False, expire_on_commit=False
    )

    def override_get_db() -> Generator[Session, None, None]:
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
