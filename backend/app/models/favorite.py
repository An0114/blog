"""PostFavorite 模型（post_favorites 表）：动态收藏（三期功能）。

- (post_id, user_id) 唯一：一个用户对一条动态只能收藏一次（toggle）
- 动态/用户删除时收藏记录随外键级联清理
- (user_id, created_at) 索引：支撑"我的收藏"按收藏时间倒序分页
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PostFavorite(Base):
    __tablename__ = "post_favorites"
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_post_favorites_post_user"),
        Index("ix_post_favorites_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<PostFavorite post_id={self.post_id} user_id={self.user_id}>"
