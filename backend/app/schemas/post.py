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
    """动态详情响应体：正文 + 媒体列表 + 评论列表 + 点赞/收藏信息（二期/三期）。"""

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
    like_count: int = 0
    liked: bool = False  # 当前登录用户是否已点赞；未登录恒为 False
    favorite_count: int = 0
    favorited: bool = False  # 当前登录用户是否已收藏；未登录恒为 False


class LikeResponse(BaseModel):
    """点赞 toggle 响应。"""

    liked: bool
    like_count: int


class FavoriteResponse(BaseModel):
    """收藏 toggle 响应。"""

    favorited: bool
    favorite_count: int


class PostListItem(PostOut):
    """动态列表条目：在详情基础上附加封面图 URL（取第一条图片媒体）。"""

    cover_url: str | None = None


class PostListResponse(BaseModel):
    """动态列表响应：分页元数据 + 条目。"""

    items: list[PostListItem]
    total: int
    page: int
    size: int


class FavoriteItemOut(PostListItem):
    """我的收藏列表条目：动态列表条目 + 收藏时间（三期）。

    favorited_at 允许 None 仅为适配 from-attributes 构造，路由层总会填充真实值。
    """

    favorited_at: datetime | None = None


class FavoriteListResponse(BaseModel):
    """我的收藏列表响应：分页元数据 + 条目。"""

    items: list[FavoriteItemOut]
    total: int
    page: int
    size: int
