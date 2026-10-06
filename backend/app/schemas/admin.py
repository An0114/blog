"""管理端相关的 Pydantic 请求 / 响应模型。"""

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
