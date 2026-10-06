"""上传接口：POST /api/upload（仅博主），返回 {media_id, url}（TRD 第 4 节）。"""

from typing import Literal

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.user import User
from app.schemas.media import MediaOut
from app.services import media as media_service

router = APIRouter(prefix="/api", tags=["media"])


@router.post("/upload", response_model=MediaOut, status_code=status.HTTP_201_CREATED)
async def upload(
    file: UploadFile = File(...),
    type: Literal["image", "video"] = Form(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> MediaOut:
    """上传图片/视频：白名单校验 + 大小限制 + UUID 重命名（PRD A4）。

    图片 jpg/png/webp ≤10MB；视频 mp4/webm ≤100MB。
    """
    data = await file.read()
    media = media_service.save_upload(
        db,
        media_type=type,
        filename=file.filename or "",
        content_type=file.content_type or "",
        data=data,
    )
    return MediaOut.model_validate(media)
