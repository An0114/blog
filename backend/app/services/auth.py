"""注册 / 登录业务逻辑（services 层：查重、哈希、写库、签发 token）。"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.services.errors import AccountDisabledError, DuplicateError, InvalidCredentialsError


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
