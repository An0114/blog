"""评论相关的 Pydantic 请求 / 响应模型。"""

from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    """POST /api/posts/{id}/comments 请求体。"""

    content: str = Field(min_length=1, max_length=1000)


class CommentOut(BaseModel):
    """评论响应：含展示用户名（注销用户显示"用户已注销"，PRD A8）。"""

    id: int
    post_id: int
    user_id: int
    username: str
    content: str
    created_at: datetime
