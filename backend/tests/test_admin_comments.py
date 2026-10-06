"""二期功能测试：博主删除任意评论、评论管理（列表/删除）、权限边界。"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.user import User

POSTS_URL = "/api/posts"
ADMIN_COMMENTS_URL = "/api/admin/comments"


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


def _create_comment(client: TestClient, post_id: int, user: User, content: str = "评论") -> dict:
    resp = client.post(
        f"{POSTS_URL}/{post_id}/comments",
        json={"content": content},
        headers=_auth_headers(user.id),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestAdminDeleteComment:
    """二期：博主可删除任意评论（作者本人删除为既有行为，不受影响）。"""

    def test_admin_deletes_others_comment(self, client, admin, user_a):
        post = _create_post(client, admin)
        comment = _create_comment(client, post["id"], user_a)
        resp = client.delete(f"/api/comments/{comment['id']}", headers=_auth_headers(admin.id))
        assert resp.status_code == 204
        assert client.get(f"{POSTS_URL}/{post['id']}/comments").json() == []

    def test_author_still_deletes_own(self, client, admin, user_a):
        post = _create_post(client, admin)
        comment = _create_comment(client, post["id"], user_a)
        resp = client.delete(f"/api/comments/{comment['id']}", headers=_auth_headers(user_a.id))
        assert resp.status_code == 204

    def test_other_user_still_forbidden_403(self, client, admin, user_a, user_b):
        post = _create_post(client, admin)
        comment = _create_comment(client, post["id"], user_a)
        resp = client.delete(f"/api/comments/{comment['id']}", headers=_auth_headers(user_b.id))
        assert resp.status_code == 403
        assert resp.json()["detail"] == "只能删除自己的评论"

    def test_missing_comment_404(self, client, admin):
        resp = client.delete("/api/comments/999999", headers=_auth_headers(admin.id))
        assert resp.status_code == 404


class TestAdminCommentList:
    def test_list_requires_admin(self, client, user_a):
        assert client.get(ADMIN_COMMENTS_URL, headers=_auth_headers(user_a.id)).status_code == 403
        assert client.get(ADMIN_COMMENTS_URL).status_code == 401

    def test_list_ok(self, client, admin, user_a, user_b):
        post = _create_post(client, admin)
        _create_comment(client, post["id"], user_a, "A 的评论")
        _create_comment(client, post["id"], user_b, "B 的评论")
        data = client.get(ADMIN_COMMENTS_URL, headers=_auth_headers(admin.id)).json()
        assert data["total"] == 2
        contents = [c["content"] for c in data["items"]]
        assert contents == ["B 的评论", "A 的评论"]  # 倒序
        first = data["items"][0]
        assert first["post_title"] == "帖子"
        assert first["username"] == "bob"

    def test_list_pagination(self, client, admin, user_a, db_session):
        post = _create_post(client, admin)
        for i in range(5):
            _create_comment(client, post["id"], user_a, f"c{i}")
        data = client.get(ADMIN_COMMENTS_URL, params={"page": 2, "size": 2}, headers=_auth_headers(admin.id)).json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

    def test_list_shows_deleted_user_placeholder(self, client, admin, user_a, db_session):
        post = _create_post(client, admin)
        _create_comment(client, post["id"], user_a)
        user_a.status = "deleted"
        db_session.commit()
        data = client.get(ADMIN_COMMENTS_URL, headers=_auth_headers(admin.id)).json()
        assert data["items"][0]["username"] == "用户已注销"


class TestAdminCommentDelete:
    def test_admin_delete_from_list(self, client, admin, user_a):
        post = _create_post(client, admin)
        comment = _create_comment(client, post["id"], user_a)
        resp = client.delete(f"{ADMIN_COMMENTS_URL}/{comment['id']}", headers=_auth_headers(admin.id))
        assert resp.status_code == 204
        assert client.get(f"{POSTS_URL}/{post['id']}/comments").json() == []
        assert client.get(ADMIN_COMMENTS_URL, headers=_auth_headers(admin.id)).json()["total"] == 0

    def test_normal_user_forbidden_403(self, client, admin, user_a, user_b):
        post = _create_post(client, admin)
        comment = _create_comment(client, post["id"], user_a)
        resp = client.delete(f"{ADMIN_COMMENTS_URL}/{comment['id']}", headers=_auth_headers(user_b.id))
        assert resp.status_code == 403

    def test_missing_404(self, client, admin):
        resp = client.delete(f"{ADMIN_COMMENTS_URL}/999999", headers=_auth_headers(admin.id))
        assert resp.status_code == 404
