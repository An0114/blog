"""草稿箱相关的 Pydantic 请求 / 响应模型（三期功能）。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.post import PostCategory


class DraftCreate(BaseModel):
    """POST /api/drafts 请求体（与发布动态同字段，但媒体仅记录 id 不绑定）。"""

    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    category: PostCategory
    media_ids: list[int] = Field(default_factory=list, max_length=20)


class DraftUpdate(DraftCreate):
    """PUT /api/drafts/{id} 请求体：全量替换（编辑草稿时前端回传完整内容）。"""


class DraftOut(BaseModel):
    """草稿详情响应体。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    category: str
    media_ids: list[int] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class DraftListItem(DraftOut):
    """草稿列表条目：与详情字段一致（无媒体 URL，媒体发布时绑定）。"""


class DraftListResponse(BaseModel):
    """草稿列表响应：分页元数据 + 条目。"""

    items: list[DraftListItem]
    total: int
    page: int
    size: int
