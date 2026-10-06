"""评论接口：列表、新增（需登录）、删除（作者本人，TRD 第 4 节）。"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentOut
from app.services import comments as comments_service

router = APIRouter(prefix="/api", tags=["comments"])


@router.get("/posts/{post_id}/comments", response_model=list[CommentOut])
def list_comments(post_id: int, db: Session = Depends(get_db)) -> list[CommentOut]:
    """评论列表（按时间倒序，PRD A7）。"""
    return comments_service.list_comments(db, post_id)


@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(
    post_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommentOut:
    """发表评论（需登录；未登录 401，PRD A7）。"""
    return comments_service.create_comment(db, post_id, current_user, payload.content)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """删除自己的评论；他人评论返回 403（TRD 鉴权=评论作者）。"""
    comments_service.delete_comment(db, comment_id, current_user)
