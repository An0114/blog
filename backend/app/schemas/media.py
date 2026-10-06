"""媒体（上传）相关的 Pydantic 响应模型。"""

from pydantic import BaseModel, ConfigDict


class MediaOut(BaseModel):
    """上传成功响应：媒体 ID 与可访问 URL。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    url: str
    file_size: int
