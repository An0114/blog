"""动态接口：列表（分页/分类筛选）、详情、发布与删除（仅博主，TRD 第 4 节）。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin, get_current_user, get_current_user_optional
from app.models.post import Post
from app.models.user import User
from app.schemas.post import (
    FavoriteResponse,
    LikeResponse,
    PostCategory,
    PostCreate,
    PostListItem,
    PostListResponse,
    PostOut,
)
from app.services import comments as comments_service
from app.services import favorites as favorites_service
from app.services import posts as posts_service

router = APIRouter(prefix="/api/posts", tags=["posts"])

PageParam = Annotated[int, Query(ge=1)]
SizeParam = Annotated[int, Query(ge=1, le=100)]


def _cover_url(post: Post) -> str | None:
    """列表封面：取第一条图片媒体。"""
    for media in post.media:
        if media.type == "image":
            return f"/uploads/{media.file_path}"
    return None


def _to_list_item(post: Post, like_count: int = 0, favorite_count: int = 0) -> PostListItem:
    item = PostListItem.model_validate(post)
    item.cover_url = _cover_url(post)
    item.like_count = like_count
    item.favorite_count = favorite_count
    return item


@router.get("", response_model=PostListResponse)
def list_posts(
    category: Annotated[PostCategory | None, Query()] = None,
    page: PageParam = 1,
    size: SizeParam = 10,
    db: Session = Depends(get_db),
) -> PostListResponse:
    """动态流：默认按发布时间倒序，支持按分类筛选（PRD A5）。"""
    items, total = posts_service.list_posts(db, category, page, size)
    post_ids = [post.id for post in items]
    like_counts = posts_service.like_counts(db, post_ids)
    favorite_counts = favorites_service.favorite_counts(db, post_ids)
    return PostListResponse(
        items=[
            _to_list_item(
                post,
                like_counts.get(post.id, 0),
                favorite_counts.get(post.id, 0),
            )
            for post in items
        ],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{post_id}", response_model=PostOut)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> PostOut:
    """动态详情：正文 + 媒体 + 评论 + 点赞/收藏状态（未登录也可看，PRD A1/A6）。"""
    post = posts_service.get_post(db, post_id)
    user_id = current_user.id if current_user else None
    detail = PostOut.model_validate(post)
    detail.comments = comments_service.list_comments(db, post_id)
    detail.like_count, detail.liked = posts_service.like_stats(db, post_id, user_id)
    detail.favorite_count, detail.favorited = favorites_service.favorite_stats(
        db, post_id, user_id
    )
    return detail


@router.post("/{post_id}/like", response_model=LikeResponse)
def toggle_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LikeResponse:
    """点赞 / 取消点赞（toggle，需登录；二期功能）。"""
    liked, like_count = posts_service.toggle_like(db, post_id, current_user.id)
    return LikeResponse(liked=liked, like_count=like_count)


@router.post("/{post_id}/favorite", response_model=FavoriteResponse)
def toggle_favorite(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FavoriteResponse:
    """收藏 / 取消收藏（toggle，需登录；三期功能）。"""
    favorited, favorite_count = favorites_service.toggle_favorite(
        db, post_id, current_user.id
    )
    return FavoriteResponse(favorited=favorited, favorite_count=favorite_count)


@router.post("", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: PostCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> Post:
    """发布动态（仅博主，PRD 角色模型）。"""
    return posts_service.create_post(db, admin, payload)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> None:
    """删除动态（仅博主）；媒体与评论由外键级联清理（PRD A6）。"""
    posts_service.delete_post(db, post_id)
