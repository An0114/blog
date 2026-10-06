"""动态接口测试：覆盖 PRD A5（倒序/分类筛选/分页）与 A6（删除后 404）及权限。"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
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
