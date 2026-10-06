"""认证相关的 Pydantic 请求 / 响应模型。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# 用户名：3-30 位，允许中文、字母、数字、下划线、连字符
_USERNAME_PATTERN = r"^[\w\u4e00-\u9fff-]+$"


class RegisterRequest(BaseModel):
    """POST /api/auth/register 请求体。"""

    username: str = Field(min_length=3, max_length=30, pattern=_USERNAME_PATTERN)
    email: EmailStr
    password: str = Field(min_length=6, max_length=64)  # 64 字符上限，给 bcrypt 72 字节留余量


class LoginRequest(BaseModel):
    """POST /api/auth/login 请求体。"""

    email: EmailStr
    password: str


class UserOut(BaseModel):
    """用户响应体：绝不包含 password_hash。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: str
    status: str
    email_verified: bool = False
    created_at: datetime


class TokenResponse(BaseModel):
    """登录成功响应：JWT + 用户信息。"""

    token: str
    user: UserOut


class ConfirmTokenRequest(BaseModel):
    """POST /api/auth/verify-email/confirm 请求体。"""

    token: str


class ForgotPasswordRequest(BaseModel):
    """POST /api/auth/forgot-password 请求体。"""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """POST /api/auth/reset-password 请求体。"""

    token: str
    new_password: str = Field(min_length=6, max_length=64)


class MessageResponse(BaseModel):
    """通用消息响应。"""

    message: str


class VerifyEmailRequestOut(MessageResponse):
    """发送验证邮件响应：提示 + 有效期。"""

    expires_minutes: int
