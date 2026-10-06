"""草稿箱业务逻辑：创建/列表/详情/更新/删除/发布（三期功能，仅博主）。

草稿独立于动态存储：不进入动态流；发布时经 posts 服务创建 Post 并绑定媒体。
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.draft import Draft
from app.models.post import Post
from app.models.user import User
from app.schemas.draft import DraftCreate, DraftUpdate
from app.schemas.post import PostCreate
from app.services import posts as posts_service
from app.services.errors import ServiceError


class DraftNotFoundError(ServiceError):
    """草稿不存在（详情/更新/删除/发布 404）。"""

    status_code = 404
    detail = "草稿不存在"


def _get_owned_draft(db: Session, draft_id: int, author_id: int) -> Draft:
    """取属于该作者的草稿，不存在抛 404（路由已保证 author 为博主）。"""
    draft = db.scalar(
        select(Draft).where(Draft.id == draft_id, Draft.author_id == author_id)
    )
    if draft is None:
        raise DraftNotFoundError()
    return draft


def create_draft(db: Session, author: User, payload: DraftCreate) -> Draft:
    """保存草稿（仅记录 media_ids，不校验媒体占用——发布时才校验）。"""
    draft = Draft(
        author_id=author.id,
        title=payload.title,
        content=payload.content,
        category=payload.category,
        media_ids=list(payload.media_ids),
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


def list_drafts(
    db: Session, author_id: int, page: int, size: int
) -> tuple[list[Draft], int]:
    """草稿列表：按创建时间倒序分页（PRD A11）。"""
    stmt = (
        select(Draft)
        .where(Draft.author_id == author_id)
        .order_by(Draft.created_at.desc(), Draft.id.desc())
    )
    total = (
        db.scalar(
            select(func.count()).select_from(Draft).where(Draft.author_id == author_id)
        )
        or 0
    )
    items = list(db.scalars(stmt.offset((page - 1) * size).limit(size)))
    return items, total


def get_draft(db: Session, draft_id: int, author_id: int) -> Draft:
    """草稿详情。"""
    return _get_owned_draft(db, draft_id, author_id)


def update_draft(
    db: Session, draft_id: int, author_id: int, payload: DraftUpdate
) -> Draft:
    """全量更新草稿（PUT 语义：前端回传完整内容）。"""
    draft = _get_owned_draft(db, draft_id, author_id)
    draft.title = payload.title
    draft.content = payload.content
    draft.category = payload.category
    draft.media_ids = list(payload.media_ids)
    db.commit()
    db.refresh(draft)
    return draft


def delete_draft(db: Session, draft_id: int, author_id: int) -> None:
    """删除草稿（仅删除记录，媒体文件不受影响）。"""
    draft = _get_owned_draft(db, draft_id, author_id)
    db.delete(draft)
    db.commit()


def publish_draft(db: Session, author: User, draft_id: int) -> Post:
    """发布草稿：创建动态 + 绑定媒体（校验存在与占用），成功后删除草稿。"""
    draft = _get_owned_draft(db, draft_id, author.id)
    payload = PostCreate(
        title=draft.title,
        content=draft.content,
        category=draft.category,
        media_ids=list(draft.media_ids or []),
    )
    post = posts_service.create_post(db, author, payload)  # 内部完成媒体校验与提交
    db.delete(draft)
    db.commit()
    return post
