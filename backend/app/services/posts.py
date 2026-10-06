"""动态业务逻辑：发布（仅博主）、列表（分页/分类筛选）、详情、删除。"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.user import User
from app.schemas.post import PostCreate
from app.services.errors import ServiceError


class PostNotFoundError(ServiceError):
    """动态不存在（详情 404 / 删除 404）。"""

    status_code = 404
    detail = "动态不存在"


def create_post(db: Session, author: User, payload: PostCreate) -> Post:
    """创建动态（调用方需保证 author 为博主）。"""
    post = Post(
        author_id=author.id,
        title=payload.title,
        content=payload.content,
        category=payload.category,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def list_posts(
    db: Session, category: str | None, page: int, size: int
) -> tuple[list[Post], int]:
    """动态列表：默认按发布时间倒序（PRD A5），支持分类筛选与分页。"""
    stmt = select(Post).order_by(Post.created_at.desc(), Post.id.desc())
    count_stmt = select(func.count()).select_from(Post)
    if category is not None:
        stmt = stmt.where(Post.category == category)
        count_stmt = count_stmt.where(Post.category == category)
    total = db.scalar(count_stmt) or 0
    items = list(db.scalars(stmt.offset((page - 1) * size).limit(size)))
    return items, total


def get_post(db: Session, post_id: int) -> Post:
    """按 ID 取动态，不存在抛 404。"""
    post = db.get(Post, post_id)
    if post is None:
        raise PostNotFoundError()
    return post


def delete_post(db: Session, post_id: int) -> None:
    """删除动态；其媒体 / 评论由数据库外键级联清理（PRD A6）。"""
    post = get_post(db, post_id)
    db.delete(post)
    db.commit()
