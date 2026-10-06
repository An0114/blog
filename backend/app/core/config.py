"""应用配置：敏感值与可调参数统一从 .env 读取，禁止硬编码（AGENTS.md 红线 4）。"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """环境变量映射。database_url 与 jwt_secret_key 无默认值，缺少 .env 时启动即报错。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 数据库连接（PostgreSQL，本地 Docker）
    database_url: str

    # JWT 签名与有效期
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 7 * 24 * 60  # PRD A3：登录后 7 天免登录

    # CORS 白名单（逗号分隔，PRD A9：只允许配置的域名）
    cors_origins: str = "http://localhost:5173"

    # 上传文件存储目录（相对 backend 运行目录；不入 Git）
    upload_dir: str = "uploads"

    # 邮件服务（SMTP，二期：邮箱验证/找回密码）。smtp_host 留空时邮件内容输出到后端日志
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    mail_from: str = "blog@example.com"
    # 前端地址：用于拼验证邮箱/重置密码的链接
    frontend_base_url: str = "http://localhost:5173"
    # 邮件令牌有效期（分钟）
    email_token_expire_minutes: int = 30

    @property
    def cors_origin_list(self) -> list[str]:
        """把逗号分隔的 CORS 配置解析成列表。"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """模块级缓存单例，避免每次导入都重读 .env。"""
    return Settings()


settings = get_settings()
