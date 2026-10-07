"""收藏业务逻辑：收藏 toggle、收藏数查询、我的收藏列表（三期功能）。

与点赞（services/posts.py 内 toggle_like）对称，但收藏是"个人书签"语义：
详情/列表仅展示收藏数，个人收藏夹只返回本人收藏的动态。
"""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.favorite import PostFavorite
from app.models.post import Post
from app.services.errors import ServiceError


class PostNotFoundError(ServiceError):
    """动态不存在（收藏 toggle 404）。"""

    status_code = 404
    detail = "动态不存在"


def toggle_favorite(db: Session, post_id: int, user_id: int) -> tuple[bool, int]:
    """收藏/取消收藏（toggle）；动态不存在抛 404；返回 (是否已收藏, 收藏数)。"""
    post = db.get(Post, post_id)
    if post is None:
        raise PostNotFoundError()
    favorite = db.scalar(
        select(PostFavorite).where(
            PostFavorite.post_id == post_id, PostFavorite.user_id == user_id
        )
    )
    if favorite is None:
        db.add(PostFavorite(post_id=post_id, user_id=user_id))
        favorited = True
    else:
        db.delete(favorite)
        favorited = False
    db.commit()
    return favorited, get_favorite_count(db, post_id)


def favorite_counts(db: Session, post_ids: list[int]) -> dict[int, int]:
    """批量查询动态收藏数（列表页避免 N+1）。"""
    if not post_ids:
        return {}
    rows = db.execute(
        select(PostFavorite.post_id, func.count())
        .where(PostFavorite.post_id.in_(post_ids))
        .group_by(PostFavorite.post_id)
    ).all()
    return {post_id: count for post_id, count in rows}


def favorite_stats(db: Session, post_id: int, user_id: int | None) -> tuple[int, bool]:
    """详情页一次查询拿到收藏数 + 当前用户是否已收藏（替代两次单查）。"""
    rows = db.execute(
        select(PostFavorite.post_id, func.count(), func.bool_or(PostFavorite.user_id == user_id))
        .where(PostFavorite.post_id == post_id)
        .group_by(PostFavorite.post_id)
    ).all()
    if not rows:
        return 0, False
    _, count, favorited = rows[0]
    return int(count), bool(favorited)


def get_favorite_count(db: Session, post_id: int) -> int:
    """查询单条动态收藏数。"""
    return db.scalar(
        select(func.count()).select_from(PostFavorite).where(PostFavorite.post_id == post_id)
    ) or 0


def is_favorited(db: Session, post_id: int, user_id: int | None) -> bool:
    """当前用户是否已收藏（未登录恒为 False）。"""
    if user_id is None:
        return False
    return (
        db.scalar(
            select(PostFavorite.id)
            .where(PostFavorite.post_id == post_id, PostFavorite.user_id == user_id)
            .limit(1)
        )
        is not None
    )


def list_user_favorites(
    db: Session, user_id: int, page: int, size: int
) -> tuple[list[Post], dict[int, datetime], int]:
    """我的收藏列表：按收藏时间倒序分页；返回 (动态列表, 收藏时间映射, 总数)。"""
    stmt = (
        select(PostFavorite, Post)
        .join(Post, Post.id == PostFavorite.post_id)
        .options(selectinload(Post.media))
        .where(PostFavorite.user_id == user_id)
        .order_by(PostFavorite.created_at.desc(), PostFavorite.id.desc())
    )
    total = db.scalar(
        select(func.count())
        .select_from(PostFavorite)
        .where(PostFavorite.user_id == user_id)
    ) or 0
    rows = db.execute(stmt.offset((page - 1) * size).limit(size)).all()
    posts = [row.Post for row in rows]
    favorited_at = {row.Post.id: row.PostFavorite.created_at for row in rows}
    return posts, favorited_at, total
