"""认证接口：注册、登录、当前用户（TRD 第 4 节）。"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.services import auth as auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    """注册：用户名/邮箱重复返回 409；密码入库为 bcrypt 哈希（PRD A2）。"""
    return auth_service.register(db, payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """登录：成功返回 {token, user}，token 有效期 7 天（PRD A3）。"""
    user, token = auth_service.authenticate(db, payload.email, payload.password)
    return TokenResponse(token=token, user=user)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> User:
    """当前登录用户信息（需 Authorization: Bearer <token>）。"""
    return current_user
