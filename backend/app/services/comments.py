"""评论业务逻辑：列表（倒序）、新增（需登录）、删除（作者本人或博主）、管理端全站列表。"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas.admin import AdminCommentOut
from app.schemas.comment import CommentOut
from app.services.errors import PermissionDeniedError, ServiceError
from app.services.posts import get_post

DELETED_USER_DISPLAY = "用户已注销"  # PRD A8：软删除用户的评论展示名


class CommentNotFoundError(ServiceError):
    """评论不存在。"""

    status_code = 404
    detail = "评论不存在"


def _to_out(comment: Comment, user: User) -> CommentOut:
    """组装评论响应；注销用户的展示名为固定文案。"""
    username = DELETED_USER_DISPLAY if user.status == "deleted" else user.username
    return CommentOut(
        id=comment.id,
        post_id=comment.post_id,
        user_id=comment.user_id,
        username=username,
        content=comment.content,
        created_at=comment.created_at,
    )


def list_comments(db: Session, post_id: int) -> list[CommentOut]:
    """按动态取评论，时间倒序（PRD A7）；动态不存在抛 404。"""
    get_post(db, post_id)  # 动态不存在时先 404
    rows = db.execute(
        select(Comment, User)
        .join(User, Comment.user_id == User.id)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.desc(), Comment.id.desc())
    ).all()
    return [_to_out(comment, user) for comment, user in rows]


def create_comment(db: Session, post_id: int, user: User, content: str) -> CommentOut:
    """在动态下发表评论（调用方需保证已登录）。"""
    get_post(db, post_id)  # 动态不存在时先 404
    comment = Comment(post_id=post_id, user_id=user.id, content=content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return _to_out(comment, user)


def delete_comment(db: Session, comment_id: int, operator: User) -> None:
    """删除评论：评论作者本人，或博主删除任意评论（二期：博主删除评论）。"""
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise CommentNotFoundError()
    if comment.user_id != operator.id and operator.role != "admin":
        raise PermissionDeniedError("只能删除自己的评论")
    db.delete(comment)
    db.commit()


def list_all_comments(db: Session, page: int, size: int) -> tuple[list[AdminCommentOut], int]:
    """管理端全站评论列表（分页，时间倒序；二期：评论管理）。"""
    total = db.scalar(select(func.count()).select_from(Comment)) or 0
    rows = db.execute(
        select(Comment, User, Post.title)
        .join(User, Comment.user_id == User.id)
        .join(Post, Comment.post_id == Post.id)
        .order_by(Comment.created_at.desc(), Comment.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    items = [
        AdminCommentOut(
            id=comment.id,
            post_id=comment.post_id,
            post_title=post_title,
            user_id=comment.user_id,
            username=DELETED_USER_DISPLAY if user.status == "deleted" else user.username,
            content=comment.content,
            created_at=comment.created_at,
        )
        for comment, user, post_title in rows
    ]
    return items, total
