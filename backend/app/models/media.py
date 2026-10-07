"""Media 模型（media 表）。

与 TRD 第 5 节的一个刻意偏离：post_id 允许 NULL——
TRD 的 /api/upload 独立于发布（先上传、后绑定到动态），上传时动态尚不存在，
因此 post_id 在绑定前为空；发布时由 services/posts 回填。
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.post import Post


class Media(Base):
    __tablename__ = "media"
    # post_id 索引：列表页 selectinload 按 post_id IN 批量取媒体（无索引会全表扫）
    __table_args__ = (Index("ix_media_post_id", "post_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), nullable=True
    )
    type: Mapped[str] = mapped_column(Text, nullable=False)  # image / video
    file_path: Mapped[str] = mapped_column(Text, nullable=False)  # uploads/ 内相对路径
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    post: Mapped[Post | None] = relationship(back_populates="media")

    def __repr__(self) -> str:
        return f"<Media id={self.id} type={self.type} path={self.file_path!r}>"
