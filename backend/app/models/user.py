"""User 模型（users 表），字段与 TRD 第 5 节一致。

- role:   admin / user（博主为 admin，注册用户默认 user）
- status: active / disabled / deleted（删除采用软删除，PRD A8）
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Text, func, text
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:  # 便于调试，不返回敏感字段
        return f"<User id={self.id} username={self.username!r} role={self.role} status={self.status}>"
