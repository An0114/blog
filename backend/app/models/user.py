"""User 模型（users 表），字段与 TRD 第 5 节一致 + 二期新增 email_verified。

- role:   admin / user（博主为 admin，注册用户默认 user）
- status: active / disabled / deleted（删除采用软删除，PRD A8）
- email_verified: 邮箱是否已验证（二期：可选验证，不阻断登录）
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False, default="user", server_default=text("'user'"))
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="active", server_default=text("'active'")
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:  # 便于调试，不返回敏感字段
        return f"<User id={self.id} username={self.username!r} role={self.role} status={self.status}>"

