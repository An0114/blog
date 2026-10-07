"""SiteConfig 模型（site_configs 单行表）：部署初始化后的站点级配置（TRD 第 5 节 / PRD A16）。

- 单行设计：id 恒为 1（主键 + CHECK），避免多行漂移；
- is_initialized 由 user 表是否存在 admin 推导，此处仅作缓存（以 user 表为准）；
- SMTP 配置存于站点表，页面配置优先于 .env（.env 兜底）。
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SiteConfig(Base):
    __tablename__ = "site_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    is_initialized: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    site_icon_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email_verify_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    smtp_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    smtp_user: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<SiteConfig id={self.id} is_initialized={self.is_initialized} "
            f"email_verify_enabled={self.email_verify_enabled}>"
        )
