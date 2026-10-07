"""站点初始化相关的 Pydantic 请求 / 响应模型（PRD A16 / TRD 第 4 节）。"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.auth import UserOut

# 与 auth 注册一致：用户名 3-30 位，允许中文、字母、数字、下划线、连字符
_USERNAME_PATTERN = r"^[\w\u4e00-\u9fff-]+$"


class InitStatusResponse(BaseModel):
    """GET /api/admin/init/status 响应：initialized 以 user 表是否存在 admin 为准。"""

    initialized: bool
    email_verify_enabled: bool = False
    has_site_icon: bool = False


class InitRequest(BaseModel):
    """POST /api/admin/init 请求体：创建博主账户 + 站点配置。"""

    username: str = Field(min_length=3, max_length=30, pattern=_USERNAME_PATTERN)
    email: EmailStr
    password: str = Field(min_length=6, max_length=64)
    # 网站图标：支持 data URL（data:image/png;base64,...）或裸 base64；仅 png/jpeg/webp/ico，≤1MB
    site_icon_base64: str | None = Field(default=None, max_length=2_000_000)
    email_verify_enabled: bool = False
    smtp_host: str | None = Field(default=None, max_length=255)
    smtp_port: int | None = Field(default=None, ge=1, le=65535)
    smtp_user: str | None = Field(default=None, max_length=255)
    smtp_password: str | None = Field(default=None, max_length=255)


class InitResponse(BaseModel):
    """初始化成功响应：提示 + 博主账户信息。"""

    message: str
    admin: UserOut


class SiteConfigOut(BaseModel):
    """站点配置响应（预留：管理端查看配置时使用；当前 init 流程返回 InitStatusResponse）。"""

    model_config = ConfigDict(from_attributes=True)

    is_initialized: bool
    site_icon_url: str | None
    email_verify_enabled: bool
