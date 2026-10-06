"""上传业务逻辑：类型/大小白名单校验、文件头（magic bytes）识别、UUID 重命名落盘。

安全红线（AGENTS.md 3）：白名单校验 + UUID 重命名，禁止使用原始文件名与路径。
"""

import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.media import Media
from app.services.errors import ServiceError

# 每种媒体类型的允许扩展名、声明 MIME 与大小上限（PRD A4 / AGENTS.md）
_ALLOWED: dict[str, dict] = {
    "image": {
        "extensions": {".jpg", ".jpeg", ".png", ".webp"},
        "mimes": {"image/jpeg", "image/png", "image/webp"},
        "max_size": 10 * 1024 * 1024,  # 10MB
    },
    "video": {
        "extensions": {".mp4", ".webm"},
        "mimes": {"video/mp4", "video/webm"},
        "max_size": 100 * 1024 * 1024,  # 100MB
    },
}

# 文件头签名 → 实际格式（魔数识别，防伪造扩展名）
def _check_image_magic(header: bytes) -> bool:
    """JPEG(FFD8FF) / PNG(89504E47) / WEBP(RIFF....WEBP)。"""
    return (
        header.startswith(b"\xff\xd8\xff")
        or header.startswith(b"\x89PNG\r\n\x1a\n")
        or (header.startswith(b"RIFF") and header[8:12] == b"WEBP")
    )


def _check_video_magic(header: bytes) -> bool:
    """MP4(....ftyp) / WebM(EBML 1A45DFA3)。"""
    return header[4:8] == b"ftyp" or header.startswith(b"\x1a\x45\xdf\xa3")


def _detect_type_by_magic(header: bytes, expected: str) -> bool:
    """用文件头判断是否属于期望类型的白名单格式。"""
    if expected == "image":
        return _check_image_magic(header)
    return _check_video_magic(header)


class UnsupportedMediaTypeError(ServiceError):
    """文件格式不在白名单内。"""

    status_code = 415
    detail = "不支持的媒体类型"


class MediaTooLargeError(ServiceError):
    """文件大小超限。"""

    status_code = 413


def _detect_type_by_magic(header: bytes, expected: str) -> bool:
    """用文件头判断是否属于期望类型的白名单格式。"""
    if expected == "image":
        return _check_image_magic(header)
    return _check_video_magic(header)


def save_upload(db: Session, media_type: str, filename: str, content_type: str, data: bytes) -> Media:
    """校验并保存上传文件，返回 Media 记录。

    - media_type: image / video（由调用方传入）
    - filename: 客户端原始文件名（仅用于取扩展名，不用于存储）
    - content_type: 客户端声明的 MIME
    - data: 文件字节（调用方已按上限读取）
    """
    rules = _ALLOWED[media_type]
    ext = Path(filename).suffix.lower()
    if ext not in rules["extensions"] or content_type not in rules["mimes"]:
        raise UnsupportedMediaTypeError()
    if len(data) > rules["max_size"]:
        raise MediaTooLargeError(detail=f"{media_type}文件超过大小限制")
    # 魔数校验：拒绝伪造扩展名的文件
    if not _detect_type_by_magic(data[:16], media_type):
        raise UnsupportedMediaTypeError()

    storage_name = f"{uuid.uuid4().hex}{ext}"
    upload_root = Path(settings.upload_dir)
    upload_root.mkdir(parents=True, exist_ok=True)
    (upload_root / storage_name).write_bytes(data)

    media = Media(type=media_type, file_path=storage_name, file_size=len(data))
    db.add(media)
    db.commit()
    db.refresh(media)
    return media
