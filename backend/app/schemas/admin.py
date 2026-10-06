"""管理端相关的 Pydantic 请求 / 响应模型。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.auth import UserOut

# 管理端可设置的用户状态（软删除走 DELETE，不在此列）
UserStatus = Literal["active", "disabled"]


class UserStatusUpdate(BaseModel):
    """PATCH /api/admin/users/{id} 请求体。"""

    status: UserStatus


class UserListResponse(BaseModel):
    """用户列表响应：分页元数据 + 条目。"""

    items: list[UserOut]
    total: int
    page: int
    size: int


class AdminCommentOut(BaseModel):
    """管理端评论条目：内容 + 作者 + 所属动态标题（二期：评论管理）。"""

    id: int
    post_id: int
    post_title: str
    user_id: int
    username: str
    content: str
    created_at: datetime


class AdminCommentListResponse(BaseModel):
    """评论管理列表响应。"""

    items: list[AdminCommentOut]
    total: int
    page: int
    size: int
