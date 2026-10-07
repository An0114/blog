"""站点初始化业务（services 层，PRD A16 / TRD Task 16）。

口径（TRD 第 5 节）：is_initialized 的权威来源是 user 表是否存在 role=admin 记录；
site_configs 单行表仅作缓存，status 接口动态推导并同步。
"""

import base64
import binascii
import os
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User
from app.schemas.init import InitRequest
from app.services.errors import (
    AlreadyInitializedError,
    ConfigError,
    DuplicateError,
)
from app.services.site_config import get_site_config

# 网站图标白名单：mime → 扩展名（PRD A16 / TRD 错误约定）
_MIME_EXT = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
    "image/x-icon": "ico",
}

# 魔数签名 → 扩展名（mime 与内容不一致时兜底识别/拒绝）
_MAGIC_EXT = {
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpg",
    b"RIFF": "webp",  # 需再校验尾部 "WEBP"
    b"\x00\x00\x01\x00": "ico",
}

ICON_MAX_BYTES = 1024 * 1024  # 1MB

_ICON_DIR = "site_icon"  # uploads/site_icon/ 子目录，与媒体上传隔离


@dataclass
class InitStatus:
    """初始化状态快照。"""

    initialized: bool
    email_verify_enabled: bool
    has_site_icon: bool


def _admin_exists(db: Session) -> bool:
    """是否存在 role=admin 的博主账户（初始化判定的唯一权威来源）。"""
    return db.scalar(select(User.id).where(User.role == "admin").limit(1)) is not None


def get_init_status(db: Session) -> InitStatus:
    """读取初始化状态：由 user 表推导 initialized，并同步 site_configs 缓存。"""
    config = get_site_config(db)
    initialized = _admin_exists(db)
    if config.is_initialized != initialized:
        config.is_initialized = initialized
        db.commit()
    return InitStatus(
        initialized=initialized,
        email_verify_enabled=config.email_verify_enabled,
        has_site_icon=bool(config.site_icon_url),
    )


def _parse_site_icon(site_icon_base64: str) -> bytes:
    """解析网站图标 base64（data URL 或裸 base64）→ 原始字节。"""
    if site_icon_base64.startswith("data:"):
        header, _, b64 = site_icon_base64.partition(",")
        mime = header[5:header.find(";")] if ";" in header else header[5:]
        if mime not in _MIME_EXT:
            raise ConfigError("网站图标仅支持 png/jpg/webp/ico 格式")
    else:
        b64 = site_icon_base64
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        raise ConfigError("网站图标 base64 无效") from None
    if len(raw) > ICON_MAX_BYTES:
        raise ConfigError("网站图标不超过 1MB")
    return raw


def _icon_extension(raw: bytes) -> str:
    """按魔数识别扩展名；无法识别 → 400。"""
    for magic, ext in _MAGIC_EXT.items():
        if raw.startswith(magic):
            if ext == "webp" and raw[8:12] != b"WEBP":
                continue
            return ext
    raise ConfigError("网站图标格式无法识别，仅支持 png/jpg/webp/ico")


def _store_site_icon(raw: bytes, upload_dir: str) -> str:
    """图标落盘（UUID 重命名，禁原始文件名，AGENTS.md 红线 3）→ 返回可访问的相对路径。"""
    ext = _icon_extension(raw)
    filename = f"{uuid.uuid4().hex}.{ext}"
    target_dir = Path(upload_dir) / _ICON_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / filename).write_bytes(raw)
    return f"/uploads/{_ICON_DIR}/{filename}"


def _require_smtp(payload: InitRequest) -> None:
    """开启邮箱验证必须提供完整 SMTP 配置（TRD 错误约定）。"""
    if payload.email_verify_enabled and not (
        payload.smtp_host and payload.smtp_port and payload.smtp_user and payload.smtp_password
    ):
        raise ConfigError("开启邮箱验证必须填写 SMTP 配置（host/port/user/password）")


def initialize(db: Session, payload: InitRequest) -> User:
    """执行初始化：创建博主账户 + 写入站点配置，仅允许未初始化时调用。

    - 已初始化 → 409；用户名/邮箱重复 → 409；
    - 开启邮箱验证但 SMTP 缺失 → 400；网站图标非法 → 400；
    - 博主账户 email_verified=True（站长免邮箱验证，PRD A16）。
    """
    if _admin_exists(db):
        raise AlreadyInitializedError()
    if db.scalar(select(User.id).where(User.username == payload.username)) is not None:
        raise DuplicateError("用户名已存在")
    email = payload.email.strip().lower()
    if db.scalar(select(User.id).where(User.email == email)) is not None:
        raise DuplicateError("邮箱已存在")

    _require_smtp(payload)

    icon_url: str | None = None
    if payload.site_icon_base64:
        icon_url = _store_site_icon(_parse_site_icon(payload.site_icon_base64), settings.upload_dir)

    config = get_site_config(db)
    admin = User(
        username=payload.username,
        email=email,
        password_hash=hash_password(payload.password),
        role="admin",
        status="active",
        email_verified=True,
    )
    db.add(admin)
    config.is_initialized = True
    config.site_icon_url = icon_url
    config.email_verify_enabled = payload.email_verify_enabled
    config.smtp_host = payload.smtp_host or None
    config.smtp_port = payload.smtp_port
    config.smtp_user = payload.smtp_user or None
    config.smtp_password = payload.smtp_password or None
    try:
        db.commit()
    except IntegrityError:
        # 并发初始化的兜底：唯一约束兜住预检查的竞态窗口
        db.rollback()
        raise AlreadyInitializedError() from None
    db.refresh(admin)
    return admin


def _cleanup_orphan_icon(upload_dir: str, url: str) -> None:
    """删除初始化失败时可能已落盘的图标文件（幂等，文件不存在不报错）。"""
    if not url:
        return
    relative = url.removeprefix("/uploads/")
    target = Path(upload_dir) / relative
    if target.exists():
        os.remove(target)
