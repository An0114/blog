"""动态（Post）相关的 Pydantic 请求 / 响应模型。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.comment import CommentOut
from app.schemas.media import MediaOut

# 动态分类（TRD 第 5 节）：project / daily / diary
PostCategory = Literal["project", "daily", "diary"]


class PostCreate(BaseModel):
    """POST /api/posts 请求体。"""

    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    category: PostCategory
    media_ids: list[int] = Field(default_factory=list, max_length=20)  # 已上传媒体的 ID


class PostOut(BaseModel):
    """动态详情响应体：正文 + 媒体列表 + 评论列表（TRD 第 4 节）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    author_id: int
    title: str
    content: str
    category: str
    created_at: datetime
    updated_at: datetime
    media: list[MediaOut] = Field(default_factory=list)
    comments: list[CommentOut] = Field(default_factory=list)


class PostListItem(PostOut):
    """动态列表条目：在详情基础上附加封面图 URL（取第一条图片媒体）。"""

    cover_url: str | None = None


class PostListResponse(BaseModel):
    """动态列表响应：分页元数据 + 条目。"""

    items: list[PostListItem]
    total: int
    page: int
    size: int
