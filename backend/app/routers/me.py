"""当前登录用户相关接口：我的收藏列表（三期功能，TRD 第 4 节）。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.post import Post
from app.models.user import User
from app.schemas.post import FavoriteItemOut, FavoriteListResponse
from app.services import favorites as favorites_service

router = APIRouter(prefix="/api/me", tags=["me"])

PageParam = Annotated[int, Query(ge=1)]
SizeParam = Annotated[int, Query(ge=1, le=100)]


def _cover_url(post: Post) -> str | None:
    """列表封面：取第一条图片媒体。"""
    for media in post.media:
        if media.type == "image":
            return f"/uploads/{media.file_path}"
    return None


def _to_favorite_item(post: Post, favorited_at) -> FavoriteItemOut:
    item = FavoriteItemOut.model_validate(post)
    item.cover_url = _cover_url(post)
    item.favorited_at = favorited_at
    return item


@router.get("/favorites", response_model=FavoriteListResponse)
def list_my_favorites(
    page: PageParam = 1,
    size: SizeParam = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FavoriteListResponse:
    """我的收藏：按收藏时间倒序分页（PRD A10，仅本人可见）。"""
    posts, favorited_at, total = favorites_service.list_user_favorites(
        db, current_user.id, page, size
    )
    return FavoriteListResponse(
        items=[_to_favorite_item(post, favorited_at[post.id]) for post in posts],
        total=total,
        page=page,
        size=size,
    )
