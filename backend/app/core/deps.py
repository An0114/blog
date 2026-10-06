"""跨模块复用的 FastAPI 依赖注入（当前用户解析）。"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

_UNAUTHORIZED_DETAIL = "未登录或登录已过期"


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """从 Authorization: Bearer <token> 解析当前用户。

    - 无凭证 / token 无效或过期 / 用户已软删除：401
    - 用户被禁用：403（PRD A8：禁用后无法登录）
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_UNAUTHORIZED_DETAIL,
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_UNAUTHORIZED_DETAIL,
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        uid = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_UNAUTHORIZED_DETAIL,
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user = db.get(User, uid)
    if user is None or user.status == "deleted":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_UNAUTHORIZED_DETAIL,
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.status == "disabled":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )
    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """仅博主（role=admin）可用的依赖：发布/删除动态、用户管理等。"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅博主可执行此操作",
        )
    return current_user
