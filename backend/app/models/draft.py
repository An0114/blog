"""Draft 模型（drafts 表）：博主发布前保存的草稿（三期功能）。

- 独立成表，不动 posts：草稿不进入动态流，发布时才生成 Post
- media_ids 存"已上传未绑定"的媒体 id 数组（JSONB），发布时校验并绑定
- (author_id, created_at) 索引：支撑草稿箱按创建时间倒序分页
"""

from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Draft(Base):
    __tablename__ = "drafts"
    __table_args__ = (Index("ix_drafts_author_created", "author_id", "created_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    category: Mapped[str] = mapped_column(nullable=False)  # project / daily / diary
    media_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Draft id={self.id} title={self.title!r}>"
