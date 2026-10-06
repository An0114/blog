"""注册 / 登录 / 邮箱验证 / 找回密码业务逻辑（services 层）。"""

import logging
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.email_token import EmailToken
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.services.errors import (
    AccountDisabledError,
    DuplicateError,
    InvalidCredentialsError,
    ServiceError,
)
from app.services.mail import send_email

logger = logging.getLogger(__name__)

# 邮件令牌用途
PURPOSE_VERIFY_EMAIL = "verify_email"
PURPOSE_RESET_PASSWORD = "reset_password"


class EmailTokenError(ServiceError):
    """验证/重置链接无效、已使用或过期。"""

    status_code = 400
    detail = "验证链接无效或已过期"


class EmailAlreadyVerifiedError(ServiceError):
    """邮箱已验证，无需重复发送。"""

    status_code = 400
    detail = "邮箱已验证，无需重复验证"


def _normalize_email(email: str) -> str:
    """邮箱统一转小写并去首尾空白，避免大小写导致重复账号。"""
    return email.strip().lower()


def _get_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def _get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def register(db: Session, payload: RegisterRequest) -> User:
    """创建新用户（role=user, status=active）。

    用户名 / 邮箱重复抛 DuplicateError(409)；密码只存 bcrypt 哈希。
    """
    email = _normalize_email(payload.email)

    if _get_by_username(db, payload.username) is not None:
        raise DuplicateError("用户名已存在")
    if _get_by_email(db, email) is not None:
        raise DuplicateError("邮箱已存在")

    user = User(
        username=payload.username,
        email=email,
        password_hash=hash_password(payload.password),
        role="user",
        status="active",
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # 并发注册的兜底：唯一约束兜住预检查的竞态窗口
        db.rollback()
        raise DuplicateError("用户名或邮箱已存在") from None
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> tuple[User, str]:
    """校验邮箱密码，成功返回 (user, token)。

    - 邮箱不存在或密码错误：401（统一提示，避免暴露账号是否存在）
    - 被禁用 / 已软删除：403（PRD A8）
    """
    user = _get_by_email(db, _normalize_email(email))
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("邮箱或密码错误")
    if user.status == "disabled":
        raise AccountDisabledError("账号已被禁用")
    if user.status == "deleted":
        raise AccountDisabledError("账号已注销，无法登录")
    return user, create_access_token(user.id)


def _create_email_token(db: Session, user_id: int, purpose: str) -> EmailToken:
    """生成一次性邮件令牌（默认 30 分钟有效，见 .env EMAIL_TOKEN_EXPIRE_MINUTES）。"""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.email_token_expire_minutes)
    email_token = EmailToken(
        user_id=user_id,
        token=token,
        purpose=purpose,
        expires_at=expires_at,
    )
    db.add(email_token)
    db.commit()
    db.refresh(email_token)
    return email_token


def _consume_email_token(db: Session, token: str, purpose: str) -> User:
    """校验并作废邮件令牌；无效/过期/已使用/用户已注销 → 400（不泄露细节）。"""
    email_token = db.scalar(
        select(EmailToken).where(EmailToken.token == token, EmailToken.purpose == purpose)
    )
    if email_token is None or email_token.used or email_token.expires_at < datetime.now(UTC):
        raise EmailTokenError()
    user = db.get(User, email_token.user_id)
    if user is None or user.status == "deleted":
        raise EmailTokenError()
    email_token.used = True
    db.commit()
    return user


def send_verify_email(db: Session, user: User) -> None:
    """发送邮箱验证链接（二期：可选验证，不阻断登录）。"""
    if user.email_verified:
        raise EmailAlreadyVerifiedError()
    email_token = _create_email_token(db, user.id, PURPOSE_VERIFY_EMAIL)
    link = f"{settings.frontend_base_url}/verify-email?token={email_token.token}"
    send_email(
        user.email,
        "【个人博客】验证邮箱",
        f"请点击以下链接完成邮箱验证（{settings.email_token_expire_minutes} 分钟内有效）：\n{link}",
    )


def confirm_email(db: Session, token: str) -> User:
    """凭令牌完成邮箱验证；令牌一次性使用。"""
    user = _consume_email_token(db, token, PURPOSE_VERIFY_EMAIL)
    user.email_verified = True
    db.commit()
    db.refresh(user)
    return user


def forgot_password(db: Session, email: str) -> None:
    """发送密码重置链接；邮箱不存在时也返回成功（防邮箱枚举）。"""
    user = _get_by_email(db, _normalize_email(email))
    if user is None or user.status == "deleted":
        logger.info("找回密码：邮箱 %s 不存在或已注销，不发送邮件", email)
        return
    email_token = _create_email_token(db, user.id, PURPOSE_RESET_PASSWORD)
    link = f"{settings.frontend_base_url}/reset-password?token={email_token.token}"
    send_email(
        user.email,
        "【个人博客】重置密码",
        f"请点击以下链接重置密码（{settings.email_token_expire_minutes} 分钟内有效）：\n{link}",
    )


def reset_password(db: Session, token: str, new_password: str) -> None:
    """凭令牌重置密码；令牌一次性使用，重置后旧密码立即失效。"""
    user = _consume_email_token(db, token, PURPOSE_RESET_PASSWORD)
    user.password_hash = hash_password(new_password)
    db.commit()
