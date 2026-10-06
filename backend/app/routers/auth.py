"""认证接口：注册、登录、当前用户、邮箱验证、找回密码（TRD 第 4 节 + 二期）。"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.auth import (
    ConfirmTokenRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserOut,
    VerifyEmailRequestOut,
)
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


@router.post("/verify-email/request", response_model=VerifyEmailRequestOut)
def request_verify_email(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VerifyEmailRequestOut:
    """发送邮箱验证链接（需登录；二期：可选验证，不阻断登录）。"""
    auth_service.send_verify_email(db, current_user)
    return VerifyEmailRequestOut(
        message="验证邮件已发送（未配置 SMTP 时请在后端日志查看链接）",
        expires_minutes=settings.email_token_expire_minutes,
    )


@router.post("/verify-email/confirm", response_model=UserOut)
def confirm_verify_email(payload: ConfirmTokenRequest, db: Session = Depends(get_db)) -> User:
    """凭邮件链接中的 token 完成邮箱验证。"""
    return auth_service.confirm_email(db, payload.token)


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> MessageResponse:
    """找回密码：向邮箱发送重置链接；邮箱不存在也返回成功（防枚举）。"""
    auth_service.forgot_password(db, payload.email)
    return MessageResponse(message="如果该邮箱已注册，重置链接已发送")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> MessageResponse:
    """凭重置链接中的 token 设置新密码。"""
    auth_service.reset_password(db, payload.token, payload.new_password)
    return MessageResponse(message="密码已重置，请使用新密码登录")
