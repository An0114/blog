"""站点初始化接口：GET /api/admin/init/status + POST /api/admin/init（PRD A16）。

与 admin.py 不同：这两个接口**无鉴权**（部署阶段尚无管理员），独立 router 避免误挂
get_current_admin 依赖；已初始化后 init 会返回 409（TRD 错误约定）。
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import UserOut
from app.schemas.init import InitRequest, InitResponse, InitStatusResponse
from app.services import init as init_service

router = APIRouter(prefix="/api/admin", tags=["admin-init"])


@router.get("/init/status", response_model=InitStatusResponse)
def init_status(db: Session = Depends(get_db)) -> InitStatusResponse:
    """初始化状态：initialized 以 user 表是否存在 admin 为准（无鉴权，供前端判断）。"""
    status_ = init_service.get_init_status(db)
    return InitStatusResponse(
        initialized=status_.initialized,
        email_verify_enabled=status_.email_verify_enabled,
        has_site_icon=status_.has_site_icon,
    )


@router.post("/init", response_model=InitResponse, status_code=status.HTTP_201_CREATED)
def init(payload: InitRequest, db: Session = Depends(get_db)) -> InitResponse:
    """初始化：创建博主账户 + 站点配置；已初始化返回 409。"""
    admin = init_service.initialize(db, payload)
    return InitResponse(
        message="站点初始化完成，请使用博主账户登录",
        admin=UserOut.model_validate(admin),
    )
