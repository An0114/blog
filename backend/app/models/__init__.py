"""models：SQLAlchemy ORM 数据模型。"""

from app.models import (  # noqa: F401  确保建表时已注册全部模型
    comment,
    email_token,
    like,
    media,
    post,
    user,
)
