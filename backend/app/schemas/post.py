"""动态（Post）相关的 Pydantic 请求 / 响应模型。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# 动态分类（TRD 第 5 节）：project / daily / diary
PostCategory = Literal["project", "daily", "diary"]


class PostCreate(BaseModel):
    """POST /api/posts 请求体。"""

    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    category: PostCategory


class PostOut(BaseModel):
    """动态响应体。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    author_id: int
    title: str
    content: str
    category: str
    created_at: datetime
    updated_at: datetime


class PostListResponse(BaseModel):
    """动态列表响应：分页元数据 + 条目。"""

    items: list[PostOut]
    total: int
    page: int
    size: int
