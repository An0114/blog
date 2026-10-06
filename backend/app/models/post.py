"""Post 模型（posts 表），字段与 TRD 第 5 节一致。

- author_id 引用 users.id（ON DELETE CASCADE）：动态随用户删除级联清理
- category: project / daily / diary
- 复合索引 (category, created_at DESC)：支撑分类筛选 + 时间倒序（TRD 第 5 节）
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.media import Media


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (Index("ix_posts_category_created_at", "category", text("created_at DESC")),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    media: Mapped[list[Media]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
        passive_deletes=True,  # 物理删除交由数据库外键级联（PRD A6）
    )

    def __repr__(self) -> str:
        return f"<Post id={self.id} title={self.title!r} category={self.category}>"
