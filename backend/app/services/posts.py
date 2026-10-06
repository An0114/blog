"""动态业务逻辑：发布（仅博主）、列表（分页/分类筛选）、详情、删除。"""

from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.media import Media
from app.models.post import Post
from app.models.user import User
from app.schemas.post import PostCreate
from app.services.errors import ServiceError


class PostNotFoundError(ServiceError):
    """动态不存在（详情 404 / 删除 404）。"""

    status_code = 404
    detail = "动态不存在"


class MediaNotFoundError(ServiceError):
    """发布时引用了不存在的媒体。"""

    status_code = 404
    detail = "部分媒体不存在"


class MediaAlreadyBoundError(ServiceError):
    """发布时引用了已被其他动态绑定的媒体。"""

    status_code = 409
    detail = "媒体已被其他动态使用"


def _get_post_with_media(db: Session, post_id: int) -> Post | None:
    """预加载媒体列表取动态，避免响应序列化时的懒加载问题。"""
    return db.scalar(
        select(Post).options(selectinload(Post.media)).where(Post.id == post_id)
    )


def _bind_media(db: Session, post: Post, media_ids: list[int]) -> None:
    """把已上传媒体绑定到动态；校验存在性与是否已被占用。"""
    if not media_ids:
        return
    unique_ids = list(dict.fromkeys(media_ids))
    medias = db.scalars(select(Media).where(Media.id.in_(unique_ids))).all()
    if len(medias) != len(unique_ids):
        raise MediaNotFoundError()
    if any(media.post_id is not None for media in medias):
        raise MediaAlreadyBoundError()
    for media in medias:
        media.post_id = post.id


def create_post(db: Session, author: User, payload: PostCreate) -> Post:
    """创建动态并绑定媒体（调用方需保证 author 为博主）。"""
    post = Post(
        author_id=author.id,
        title=payload.title,
        content=payload.content,
        category=payload.category,
    )
    db.add(post)
    db.flush()  # 先生成 post.id，供媒体绑定
    _bind_media(db, post, payload.media_ids)
    db.commit()
    created = _get_post_with_media(db, post.id)
    if created is None:  # pragma: no cover - 刚创建必然存在
        raise PostNotFoundError()
    return created


def list_posts(
    db: Session, category: str | None, page: int, size: int
) -> tuple[list[Post], int]:
    """动态列表：默认按发布时间倒序（PRD A5），支持分类筛选与分页。"""
    stmt = (
        select(Post)
        .options(selectinload(Post.media))
        .order_by(Post.created_at.desc(), Post.id.desc())
    )
    count_stmt = select(func.count()).select_from(Post)
    if category is not None:
        stmt = stmt.where(Post.category == category)
        count_stmt = count_stmt.where(Post.category == category)
    total = db.scalar(count_stmt) or 0
    items = list(db.scalars(stmt.offset((page - 1) * size).limit(size)))
    return items, total


def get_post(db: Session, post_id: int) -> Post:
    """按 ID 取动态（含媒体），不存在抛 404。"""
    post = _get_post_with_media(db, post_id)
    if post is None:
        raise PostNotFoundError()
    return post


def _remove_media_files(medias: list[Media]) -> None:
    """删除关联媒体在磁盘上的文件（PRD A6：媒体一并下线）。"""
    for media in medias:
        try:
            (Path(settings.upload_dir) / media.file_path).unlink(missing_ok=True)
        except OSError:
            # 文件已缺失或无权删除时不影响记录删除
            pass


def delete_post(db: Session, post_id: int) -> None:
    """删除动态：磁盘媒体文件移除，媒体/评论记录由外键级联清理（PRD A6）。"""
    post = _get_post_with_media(db, post_id)
    if post is None:
        raise PostNotFoundError()
    _remove_media_files(post.media)
    db.delete(post)
    db.commit()
