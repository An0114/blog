"""管理端接口：用户列表、禁用/启用、软删除（仅博主，TRD 第 4 节）。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.user import User
from app.schemas.admin import UserListResponse, UserStatusUpdate
from app.schemas.auth import UserOut
from app.services import admin as admin_service

router = APIRouter(prefix="/api/admin", tags=["admin"])

PageParam = Annotated[int, Query(ge=1)]
SizeParam = Annotated[int, Query(ge=1, le=100)]


@router.get("/users", response_model=UserListResponse)
def list_users(
    page: PageParam = 1,
    size: SizeParam = 10,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> UserListResponse:
    """用户列表（PRD A8：博主可查看用户列表）。"""
    items, total = admin_service.list_users(db, page, size)
    return UserListResponse(items=items, total=total, page=page, size=size)


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> User:
    """启用 / 禁用用户（PRD A8：禁用后无法登录）。"""
    return admin_service.update_user_status(db, admin, user_id, payload.status)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> None:
    """软删除用户（status=deleted，记录保留、禁止登录、评论保留，PRD A8）。"""
    admin_service.delete_user(db, admin, user_id)
