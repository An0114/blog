"""管理端业务逻辑：用户列表、禁用/启用、软删除（仅博主，PRD A8）。"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.errors import ServiceError


class UserNotFoundError(ServiceError):
    """用户不存在或已软删除。"""

    status_code = 404
    detail = "用户不存在"


class SelfOperationError(ServiceError):
    """不能对博主自身执行禁用/删除等管理操作（避免锁死管理员账号）。"""

    status_code = 400
    detail = "不能对博主自身执行此操作"


def list_users(db: Session, page: int, size: int) -> tuple[list[User], int]:
    """用户列表（含全部状态），按注册时间倒序。"""
    total = db.scalar(select(func.count()).select_from(User)) or 0
    items = list(
        db.scalars(
            select(User).order_by(User.created_at.desc(), User.id.desc()).offset((page - 1) * size).limit(size)
        )
    )
    return items, total


def _get_operable_user(db: Session, user_id: int) -> User:
    """取可被管理的用户；已软删除视为不存在。"""
    user = db.get(User, user_id)
    if user is None or user.status == "deleted":
        raise UserNotFoundError()
    return user


def update_user_status(db: Session, operator: User, user_id: int, status: str) -> User:
    """启用 / 禁用用户；禁用后该用户无法登录（PRD A8）。"""
    if user_id == operator.id:
        raise SelfOperationError()
    user = _get_operable_user(db, user_id)
    user.status = status
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, operator: User, user_id: int) -> None:
    """软删除用户：记录保留、禁止登录、历史评论保留（PRD A8 定稿）。"""
    if user_id == operator.id:
        raise SelfOperationError()
    user = _get_operable_user(db, user_id)
    user.status = "deleted"
    db.commit()
