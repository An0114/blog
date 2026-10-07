"""性能压测数据灌入脚本：向指定数据库灌入 1000 条动态 + 5000 条评论 + 关联媒体/用户。

用法：
  DATABASE_URL=postgresql+psycopg://postgres:240352@127.0.0.1:5432/blog_perf python scripts/seed_perf.py

数据分布：
  - 1 个 admin（博主）+ 20 个普通用户
  - 1000 条动态（category 均匀分布），每篇 0~2 条图片媒体（共约 1000 条）
  - 5000 条评论（每篇 0~10 条随机，集中在部分热门动态上模拟热帖）
幂等：先 drop_all + create_all 再灌，可反复运行。
"""

import os
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# 必须在 import app.* 之前设置，engine 在模块导入时读取 DATABASE_URL
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = (
        "postgresql+psycopg://postgres:240352@127.0.0.1:5432/blog_perf"
    )

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import insert  # noqa: E402

from app.core.database import Base, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.comment import Comment  # noqa: E402
from app.models.media import Media  # noqa: E402
from app.models.post import Post  # noqa: E402
from app.models.user import User  # noqa: E402

POST_COUNT = 1000
COMMENT_COUNT = 5000
USER_COUNT = 21  # 1 admin + 20 user
MEDIA_PER_POST = (0, 2)  # 每篇媒体数区间

CATEGORIES = ["project", "daily", "diary"]


def _ts(seed: float) -> datetime:
    """按 seed 生成递减的带时区时间戳，模拟持续发布的动态（最新在前）。"""
    return datetime(2026, 10, 7, tzinfo=UTC) - timedelta(
        seconds=seed * 3600 + random.random() * 3600
    )


def seed() -> None:
    random.seed(20261007)  # 固定随机种子，保证可复现
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = engine.connect()

    # 用户
    users = [
        {
            "username": f"perf_user_{i}",
            "email": f"perf_user_{i}@example.com",
            "password_hash": hash_password("secret123"),
            "role": "admin" if i == 0 else "user",
            "status": "active",
            "email_verified": True,
        }
        for i in range(USER_COUNT)
    ]
    db.execute(insert(User), users)

    # 动态
    posts = []
    for i in range(POST_COUNT):
        posts.append(
            {
                "author_id": 1,
                "title": f"性能压测动态 #{i + 1}",
                "content": "这是一篇用于性能压测的正文。\n" + ("段落内容。" * random.randint(5, 40)),
                "category": random.choice(CATEGORIES),
                "created_at": _ts(i),
            }
        )
    db.execute(insert(Post), posts)

    # 媒体（部分动态绑定 1~2 条图片，模拟封面）
    medias = []
    for post_id in range(1, POST_COUNT + 1):
        for _ in range(random.randint(*MEDIA_PER_POST)):
            medias.append(
                {
                    "post_id": post_id,
                    "type": "image",
                    "file_path": f"perf/{post_id}_{len(medias)}.jpg",
                    "file_size": random.randint(50_000, 1_000_000),
                }
            )
    db.execute(insert(Media), medias)

    # 评论：先定每篇条数，凑满总数
    per_post = [0] * POST_COUNT
    remaining = COMMENT_COUNT
    while remaining > 0:
        idx = random.randrange(POST_COUNT)
        add = random.randint(1, 8)
        add = min(add, remaining)
        per_post[idx] += add
        remaining -= add
    comments = []
    for post_idx, count in enumerate(per_post, start=1):
        for _ in range(count):
            comments.append(
                {
                    "post_id": post_idx,
                    "user_id": random.randint(1, USER_COUNT),
                    "content": "性能压测评论。" + ("写得不错，支持一下！" * random.randint(1, 6)),
                    "created_at": _ts(post_idx + random.random()),
                }
            )
    db.execute(insert(Comment), comments)

    db.commit()
    db.close()
    print(
        f"seeded: users={USER_COUNT} posts={POST_COUNT} "
        f"medias={len(medias)} comments={len(comments)}"
    )


if __name__ == "__main__":
    seed()
