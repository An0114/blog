"""草稿箱接口：创建/列表/详情/更新/删除/发布（仅博主，三期功能，TRD 第 4 节）。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.post import Post
from app.models.user import User
from app.schemas.draft import (
    DraftCreate,
    DraftListItem,
    DraftListResponse,
    DraftOut,
    DraftUpdate,
)
from app.schemas.post import PostOut
from app.services import drafts as drafts_service

router = APIRouter(prefix="/api/drafts", tags=["drafts"])

PageParam = Annotated[int, Query(ge=1)]
SizeParam = Annotated[int, Query(ge=1, le=100)]


@router.post("", response_model=DraftOut, status_code=status.HTTP_201_CREATED)
def create_draft(
    payload: DraftCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> DraftOut:
    """保存草稿（仅博主；媒体仅记录 id，发布时才绑定）。"""
    return drafts_service.create_draft(db, admin, payload)


@router.get("", response_model=DraftListResponse)
def list_drafts(
    page: PageParam = 1,
    size: SizeParam = 10,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> DraftListResponse:
    """草稿列表：按创建时间倒序分页（PRD A11）。"""
    items, total = drafts_service.list_drafts(db, admin.id, page, size)
    return DraftListResponse(
        items=[DraftListItem.model_validate(item) for item in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{draft_id}", response_model=DraftOut)
def get_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> DraftOut:
    """草稿详情（仅博主）。"""
    return drafts_service.get_draft(db, draft_id, admin.id)


@router.put("/{draft_id}", response_model=DraftOut)
def update_draft(
    draft_id: int,
    payload: DraftUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> DraftOut:
    """全量更新草稿（仅博主）。"""
    return drafts_service.update_draft(db, draft_id, admin.id, payload)


@router.delete("/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> None:
    """删除草稿（仅博主）。"""
    drafts_service.delete_draft(db, draft_id, admin.id)


@router.post("/{draft_id}/publish", response_model=PostOut)
def publish_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> Post:
    """发布草稿：生成动态并绑定媒体，成功后删除草稿（PRD A11）。"""
    return drafts_service.publish_draft(db, admin, draft_id)
