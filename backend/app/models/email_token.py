"""EmailToken 模型（email_tokens 表）：邮箱验证 / 密码重置令牌（二期功能）。

- purpose: verify_email / reset_password
- 一次性使用（used=True 后失效）；expires_at 过期失效
- 用户删除时令牌随外键级联清理
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EmailToken(Base):
    __tablename__ = "email_tokens"
    __table_args__ = (Index("ix_email_tokens_user_purpose", "user_id", "purpose"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)  # verify_email / reset_password
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<EmailToken user_id={self.user_id} purpose={self.purpose} used={self.used}>"
