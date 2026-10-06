"""动态接口测试：覆盖 PRD A5（倒序/分类筛选/分页）、A6（删除后 404、媒体级联）及权限。"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.models.media import Media
from app.models.user import User

POSTS_URL = "/api/posts"


@pytest.fixture()
def admin(db_session: Session) -> User:
    return _make_user(db_session, username="admin", email="admin@example.com", role="admin")


@pytest.fixture()
def normal_user(db_session: Session) -> User:
    return _make_user(db_session, username="reader", email="reader@example.com")


def _make_user(db_session: Session, **overrides) -> User:
    data = {
        "username": "user",
        "email": "user@example.com",
        "password": "secret123",
        "role": "user",
        "status": "active",
    }
    data.update(overrides)
    user = User(
        username=data["username"],
        email=data["email"],
        password_hash=hash_password(data["password"]),
        role=data["role"],
        status=data["status"],
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


@pytest.fixture(autouse=True)
def _tmp_upload_dir(tmp_path, monkeypatch):
    """媒体落盘重定向到临时目录，避免污染项目 uploads/。"""
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    return tmp_path


def _make_media(db_session: Session, media_type: str = "image", post_id: int | None = None) -> Media:
    media = Media(type=media_type, file_path=f"{media_type}_{id(Media)}.png", file_size=10, post_id=post_id)
    db_session.add(media)
    db_session.commit()
    db_session.refresh(media)
    return media


def _create_post(client: TestClient, admin: User, **overrides) -> dict:
    payload = {"title": "标题", "content": "正文", "category": "project"}
    payload.update(overrides)
    resp = client.post(POSTS_URL, json=payload, headers=_auth_headers(admin.id))
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestListPosts:
    """PRD A5：默认按时间倒序、分类筛选、分页。"""

    def test_empty_list(self, client):
        resp = client.get(POSTS_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data == {"items": [], "total": 0, "page": 1, "size": 10}

    def test_list_order_desc(self, client, admin):
        _create_post(client, admin, title="first")
        _create_post(client, admin, title="second")
        resp = client.get(POSTS_URL)
        items = resp.json()["items"]
        assert [p["title"] for p in items] == ["second", "first"]

    def test_category_filter(self, client, admin):
        _create_post(client, admin, category="project")
        _create_post(client, admin, category="daily")
        resp = client.get(POSTS_URL, params={"category": "project"})
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["category"] == "project"

    def test_invalid_category_422(self, client):
        resp = client.get(POSTS_URL, params={"category": "hack"})
        assert resp.status_code == 422

    def test_pagination(self, client, admin):
        for i in range(5):
            _create_post(client, admin, title=f"p{i}")
        resp = client.get(POSTS_URL, params={"page": 2, "size": 2})
        data = resp.json()
        assert data["total"] == 5
        assert data["page"] == 2
        assert data["size"] == 2
        assert len(data["items"]) == 2

    def test_page_must_be_positive(self, client):
        assert client.get(POSTS_URL, params={"page": 0}).status_code == 422


class TestGetPost:
    def test_get_ok(self, client, admin):
        created = _create_post(client, admin)
        resp = client.get(f"{POSTS_URL}/{created['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == created["id"]
        assert data["author_id"] == admin.id
        assert data["category"] == "project"

    def test_get_missing_404(self, client):
        resp = client.get(f"{POSTS_URL}/999999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "动态不存在"


class TestCreatePost:
    """仅博主可发布（PRD 角色模型）。"""

    def test_unauthorized_401(self, client):
        resp = client.post(POSTS_URL, json={"title": "t", "content": "c", "category": "project"})
        assert resp.status_code == 401

    def test_normal_user_forbidden_403(self, client, normal_user):
        resp = client.post(
            POSTS_URL,
            json={"title": "t", "content": "c", "category": "project"},
            headers=_auth_headers(normal_user.id),
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "仅博主可执行此操作"

    def test_create_ok(self, client, admin):
        resp = client.post(
            POSTS_URL,
            json={"title": "我的项目", "content": "正文内容", "category": "diary"},
            headers=_auth_headers(admin.id),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "我的项目"
        assert data["category"] == "diary"
        assert data["author_id"] == admin.id


class TestDeletePost:
    """PRD A6：博主删除后列表不再出现、详情返回 404。"""

    def test_delete_ok(self, client, admin):
        created = _create_post(client, admin)
        resp = client.delete(f"{POSTS_URL}/{created['id']}", headers=_auth_headers(admin.id))
        assert resp.status_code == 204
        assert client.get(f"{POSTS_URL}/{created['id']}").status_code == 404

    def test_delete_missing_404(self, client, admin):
        resp = client.delete(f"{POSTS_URL}/999999", headers=_auth_headers(admin.id))
        assert resp.status_code == 404

    def test_normal_user_cannot_delete(self, client, admin, normal_user):
        created = _create_post(client, admin)
        resp = client.delete(
            f"{POSTS_URL}/{created['id']}", headers=_auth_headers(normal_user.id)
        )
        assert resp.status_code == 403
        assert client.get(f"{POSTS_URL}/{created['id']}").status_code == 200

    def test_unauthorized_delete_401(self, client, admin):
        created = _create_post(client, admin)
        assert client.delete(f"{POSTS_URL}/{created['id']}").status_code == 401


class TestPostMedia:
    """发布-媒体关联（TRD：POST /api/posts 携带 media_ids；列表含封面）。"""

    def test_create_with_media_ids_ok(self, client, admin, db_session):
        m1 = _make_media(db_session, "image")
        m2 = _make_media(db_session, "video")
        resp = client.post(
            POSTS_URL,
            json={"title": "带媒体", "content": "正文", "category": "project", "media_ids": [m1.id, m2.id]},
            headers=_auth_headers(admin.id),
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert {m["id"] for m in data["media"]} == {m1.id, m2.id}

    def test_media_ids_missing_404(self, client, admin):
        resp = client.post(
            POSTS_URL,
            json={"title": "t", "content": "c", "category": "project", "media_ids": [999999]},
            headers=_auth_headers(admin.id),
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "部分媒体不存在"

    def test_media_already_bound_409(self, client, admin, db_session):
        first = _create_post(client, admin)
        media = _make_media(db_session, "image")
        media.post_id = first["id"]
        db_session.commit()
        resp = client.post(
            POSTS_URL,
            json={"title": "t2", "content": "c2", "category": "daily", "media_ids": [media.id]},
            headers=_auth_headers(admin.id),
        )
        assert resp.status_code == 409
        assert resp.json()["detail"] == "媒体已被其他动态使用"

    def test_list_cover_url(self, client, admin, db_session):
        image = _make_media(db_session, "image")
        resp = client.post(
            POSTS_URL,
            json={"title": "有封面", "content": "c", "category": "project", "media_ids": [image.id]},
            headers=_auth_headers(admin.id),
        )
        assert resp.status_code == 201
        data = client.get(POSTS_URL).json()
        item = data["items"][0]
        assert item["id"] == resp.json()["id"]
        assert item["cover_url"] == f"/uploads/{image.file_path}"

    def test_list_cover_url_none_without_media(self, client, admin):
        _create_post(client, admin)
        item = client.get(POSTS_URL).json()["items"][0]
        assert item["cover_url"] is None
        assert item["media"] == []

    def test_detail_includes_media(self, client, admin, db_session):
        image = _make_media(db_session, "image")
        created = client.post(
            POSTS_URL,
            json={"title": "详情", "content": "c", "category": "project", "media_ids": [image.id]},
            headers=_auth_headers(admin.id),
        ).json()
        detail = client.get(f"{POSTS_URL}/{created['id']}").json()
        assert detail["media"][0]["url"] == f"/uploads/{image.file_path}"

    def test_delete_removes_media_files(self, client, admin, db_session, _tmp_upload_dir):
        """PRD A6：删除动态后关联媒体文件从磁盘移除。"""
        media = _make_media(db_session, "image")
        stored = Path(_tmp_upload_dir) / media.file_path
        stored.write_bytes(b"fake-image")
        created = client.post(
            POSTS_URL,
            json={"title": "待删", "content": "c", "category": "project", "media_ids": [media.id]},
            headers=_auth_headers(admin.id),
        ).json()
        assert stored.exists()
        resp = client.delete(f"{POSTS_URL}/{created['id']}", headers=_auth_headers(admin.id))
        assert resp.status_code == 204
        assert not stored.exists()  # 磁盘文件已删除
