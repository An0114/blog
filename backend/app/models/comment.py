"""Comment 模型（comments 表），字段与 TRD 第 5 节一致。

- 用户删除采用软删除（status=deleted），历史评论保留并展示为"用户已注销"（PRD A8），
  因此正常流程不会触发 comments.user_id 的物理级联。
- 索引 (post_id, created_at DESC)：支撑按动态取评论并按时间倒序。
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = (
        # (post_id, created_at DESC, id DESC)：按动态取评论倒序，含 id 尾键避免补排序
        Index("ix_comments_post_created", "post_id", text("created_at DESC"), text("id DESC")),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[User] = relationship()

    def __repr__(self) -> str:
        return f"<Comment id={self.id} post_id={self.post_id} user_id={self.user_id}>"
