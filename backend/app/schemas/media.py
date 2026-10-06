"""媒体（上传）相关的 Pydantic 响应模型。"""

from pydantic import BaseModel, ConfigDict, computed_field


class MediaOut(BaseModel):
    """媒体响应：ID、类型、大小与可访问 URL（由 file_path 计算得出）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    file_path: str
    file_size: int

    @computed_field  # type: ignore[prop-decorator]
    @property
    def url(self) -> str:
        return f"/uploads/{self.file_path}"
