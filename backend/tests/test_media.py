"""上传接口测试：覆盖 PRD A4（白名单/大小限制/UUID 存储）与权限。"""

import re
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.models.user import User

UPLOAD_URL = "/api/upload"

# 各类最小合法文件头（仅用于通过魔数识别）
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 64
WEBP_BYTES = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"\x00" * 64
MP4_BYTES = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 64
WEBM_BYTES = b"\x1a\x45\xdf\xa3" + b"\x00" * 64


@pytest.fixture()
def admin(db_session: Session) -> User:
    user = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("secret123"),
        role="admin",
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def normal_user(db_session: Session) -> User:
    user = User(
        username="reader",
        email="reader@example.com",
        password_hash=hash_password("secret123"),
        role="user",
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(autouse=True)
def _tmp_upload_dir(tmp_path, monkeypatch):
    """上传落盘重定向到临时目录，避免污染项目 uploads/。"""
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    return tmp_path


def _auth_headers(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def _upload(client, admin, content: bytes, filename: str, content_type: str, media_type: str):
    return client.post(
        UPLOAD_URL,
        data={"type": media_type},
        files={"file": (filename, content, content_type)},
        headers=_auth_headers(admin.id),
    )


class TestUpload:
    def test_upload_png_ok(self, client, admin, _tmp_upload_dir):
        resp = _upload(client, admin, PNG_BYTES, "photo.png", "image/png", "image")
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["type"] == "image"
        assert data["file_size"] == len(PNG_BYTES)
        assert re.fullmatch(r"/uploads/[0-9a-f]{32}\.png", data["url"])
        stored = Path(data["url"].removeprefix("/uploads/"))
        assert (Path(_tmp_upload_dir) / stored.name).exists()
        assert stored.name != "photo.png"  # 已用 UUID 重命名，非原始文件名

    def test_upload_webm_ok(self, client, admin):
        resp = _upload(client, admin, WEBM_BYTES, "clip.webm", "video/webm", "video")
        assert resp.status_code == 201, resp.text
        assert resp.json()["type"] == "video"
        assert resp.json()["url"].endswith(".webm")

    def test_upload_jpeg_and_webp_ok(self, client, admin):
        for content, name, mime in (
            (JPEG_BYTES, "a.jpg", "image/jpeg"),
            (WEBP_BYTES, "b.webp", "image/webp"),
            (MP4_BYTES, "c.mp4", "video/mp4"),
        ):
            resp = _upload(client, admin, content, name, mime, "image" if mime.startswith("image") else "video")
            assert resp.status_code == 201, resp.text

    def test_unauthorized_401(self, client):
        resp = client.post(
            UPLOAD_URL, data={"type": "image"}, files={"file": ("a.png", PNG_BYTES, "image/png")}
        )
        assert resp.status_code == 401

    def test_normal_user_forbidden_403(self, client, normal_user):
        resp = _upload(client, normal_user, PNG_BYTES, "a.png", "image/png", "image")
        assert resp.status_code == 403

    def test_disallowed_extension_415(self, client, admin):
        resp = _upload(client, admin, PNG_BYTES, "evil.txt", "image/png", "image")
        assert resp.status_code == 415

    def test_spoofed_magic_415(self, client, admin):
        """扩展名/MIME 合法但文件头不是图片 → 拒绝（防伪造）。"""
        resp = _upload(client, admin, b"not really an image" * 10, "fake.png", "image/png", "image")
        assert resp.status_code == 415

    def test_oversize_image_413(self, client, admin):
        big = b"\x00" * (10 * 1024 * 1024 + 1)
        resp = _upload(client, admin, big, "big.png", "image/png", "image")
        assert resp.status_code == 413

    def test_invalid_type_422(self, client, admin):
        resp = client.post(
            UPLOAD_URL,
            data={"type": "document"},
            files={"file": ("a.png", PNG_BYTES, "image/png")},
            headers=_auth_headers(admin.id),
        )
        assert resp.status_code == 422
