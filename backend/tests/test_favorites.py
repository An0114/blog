"""收藏接口测试（三期）：toggle、我的收藏列表、详情/列表收藏数、未登录 401、级联清理。"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.favorite import PostFavorite
from app.models.user import User

POSTS_URL = "/api/posts"
ME_URL = "/api/me"


@pytest.fixture()
def admin(db_session: Session) -> User:
    return _make_user(db_session, username="admin", email="admin@example.com", role="admin")


@pytest.fixture()
def user_a(db_session: Session) -> User:
    return _make_user(db_session, username="alice", email="alice@example.com")


@pytest.fixture()
def user_b(db_session: Session) -> User:
    return _make_user(db_session, username="bob", email="bob@example.com")


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


def _create_post(client: TestClient, admin: User) -> dict:
    resp = client.post(
        POSTS_URL,
        json={"title": "帖子", "content": "正文", "category": "project"},
        headers=_auth_headers(admin.id),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _favorite_url(post_id: int) -> str:
    return f"{POSTS_URL}/{post_id}/favorite"


class TestToggleFavorite:
    def test_favorite_then_unfavorite(self, client, admin, user_a):
        post = _create_post(client, admin)
        url = _favorite_url(post["id"])
        first = client.post(url, headers=_auth_headers(user_a.id))
        assert first.status_code == 200, first.text
        assert first.json() == {"favorited": True, "favorite_count": 1}
        second = client.post(url, headers=_auth_headers(user_a.id))
        assert second.json() == {"favorited": False, "favorite_count": 0}

    def test_multiple_users_count(self, client, admin, user_a, user_b):
        post = _create_post(client, admin)
        url = _favorite_url(post["id"])
        client.post(url, headers=_auth_headers(user_a.id))
        resp = client.post(url, headers=_auth_headers(user_b.id))
        assert resp.json() == {"favorited": True, "favorite_count": 2}

    def test_unauthenticated_401(self, client, admin):
        post = _create_post(client, admin)
        assert client.post(_favorite_url(post["id"])).status_code == 401

    def test_missing_post_404(self, client, user_a):
        resp = client.post(_favorite_url(999999), headers=_auth_headers(user_a.id))
        assert resp.status_code == 404
        assert resp.json()["detail"] == "动态不存在"


class TestFavoriteInResponses:
    def test_list_contains_favorite_count(self, client, admin, user_a):
        post = _create_post(client, admin)
        client.post(_favorite_url(post["id"]), headers=_auth_headers(user_a.id))
        data = client.get(POSTS_URL).json()
        assert data["items"][0]["favorite_count"] == 1
        assert data["items"][0]["favorited"] is False  # 列表条目不带 favorited（未登录视角）

    def test_detail_favorited_for_anonymous(self, client, admin, user_a):
        post = _create_post(client, admin)
        client.post(_favorite_url(post["id"]), headers=_auth_headers(user_a.id))
        detail = client.get(f"{POSTS_URL}/{post['id']}").json()
        assert detail["favorite_count"] == 1
        assert detail["favorited"] is False

    def test_detail_favorited_for_authenticated(self, client, admin, user_a, user_b):
        post = _create_post(client, admin)
        client.post(_favorite_url(post["id"]), headers=_auth_headers(user_a.id))
        detail_a = client.get(
            f"{POSTS_URL}/{post['id']}", headers=_auth_headers(user_a.id)
        ).json()
        assert detail_a["favorited"] is True
        detail_b = client.get(
            f"{POSTS_URL}/{post['id']}", headers=_auth_headers(user_b.id)
        ).json()
        assert detail_b["favorited"] is False


class TestMyFavorites:
    def test_list_my_favorites_only_mine(self, client, admin, user_a, user_b):
        post1 = _create_post(client, admin)
        post2 = _create_post(client, admin)
        client.post(_favorite_url(post1["id"]), headers=_auth_headers(user_a.id))
        client.post(_favorite_url(post2["id"]), headers=_auth_headers(user_a.id))
        client.post(_favorite_url(post1["id"]), headers=_auth_headers(user_b.id))
        data = client.get(f"{ME_URL}/favorites", headers=_auth_headers(user_a.id)).json()
        assert data["total"] == 2
        # 按收藏时间倒序：后收藏的 post2 在前
        assert data["items"][0]["id"] == post2["id"]
        assert data["items"][1]["id"] == post1["id"]
        assert "favorited_at" in data["items"][0]

    def test_empty_when_none(self, client, user_a):
        data = client.get(f"{ME_URL}/favorites", headers=_auth_headers(user_a.id)).json()
        assert data == {"items": [], "total": 0, "page": 1, "size": 10}

    def test_unauthenticated_401(self, client):
        assert client.get(f"{ME_URL}/favorites").status_code == 401


class TestCascade:
    def test_favorites_cascade_when_post_deleted(self, client, admin, user_a, db_session):
        post = _create_post(client, admin)
        client.post(_favorite_url(post["id"]), headers=_auth_headers(user_a.id))
        client.post(_favorite_url(post["id"]), headers=_auth_headers(admin.id))
        assert len(db_session.scalars(select(PostFavorite)).all()) == 2
        resp = client.delete(f"{POSTS_URL}/{post['id']}", headers=_auth_headers(admin.id))
        assert resp.status_code == 204
        assert len(db_session.scalars(select(PostFavorite)).all()) == 0
