"""评论接口测试：覆盖 PRD A7（登录可评论/显示用户名/未登录无法提交）与 A6 级联删除。"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.comment import Comment
from app.models.user import User

POSTS_URL = "/api/posts"


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


def _comment_url(post_id: int) -> str:
    return f"{POSTS_URL}/{post_id}/comments"


class TestListComments:
    def test_empty_list(self, client, admin):
        post = _create_post(client, admin)
        resp = client.get(_comment_url(post["id"]))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_order_desc(self, client, admin, user_a, user_b):
        post = _create_post(client, admin)
        client.post(_comment_url(post["id"]), json={"content": "第一条"}, headers=_auth_headers(user_a.id))
        client.post(_comment_url(post["id"]), json={"content": "第二条"}, headers=_auth_headers(user_b.id))
        data = client.get(_comment_url(post["id"])).json()
        assert [c["content"] for c in data] == ["第二条", "第一条"]

    def test_list_missing_post_404(self, client):
        assert client.get(_comment_url(999999)).status_code == 404


class TestCreateComment:
    """PRD A7：登录用户可评论；未登录无法提交。"""

    def test_comment_ok(self, client, admin, user_a):
        post = _create_post(client, admin)
        resp = client.post(_comment_url(post["id"]), json={"content": "写得好"}, headers=_auth_headers(user_a.id))
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["content"] == "写得好"
        assert data["username"] == "alice"
        assert data["user_id"] == user_a.id
        assert data["post_id"] == post["id"]

    def test_unauthenticated_401(self, client, admin):
        post = _create_post(client, admin)
        resp = client.post(_comment_url(post["id"]), json={"content": "hi"})
        assert resp.status_code == 401

    def test_missing_post_404(self, client, user_a):
        resp = client.post(_comment_url(999999), json={"content": "hi"}, headers=_auth_headers(user_a.id))
        assert resp.status_code == 404

    def test_empty_content_422(self, client, admin, user_a):
        post = _create_post(client, admin)
        resp = client.post(_comment_url(post["id"]), json={"content": ""}, headers=_auth_headers(user_a.id))
        assert resp.status_code == 422

    def test_detail_includes_comments(self, client, admin, user_a):
        post = _create_post(client, admin)
        client.post(_comment_url(post["id"]), json={"content": "详情里的评论"}, headers=_auth_headers(user_a.id))
        detail = client.get(f"{POSTS_URL}/{post['id']}").json()
        assert [c["content"] for c in detail["comments"]] == ["详情里的评论"]


class TestDeleteComment:
    """TRD：删除评论的鉴权为评论作者本人。"""

    def test_author_delete_ok(self, client, admin, user_a):
        post = _create_post(client, admin)
        comment = client.post(
            _comment_url(post["id"]), json={"content": "删我"}, headers=_auth_headers(user_a.id)
        ).json()
        resp = client.delete(f"/api/comments/{comment['id']}", headers=_auth_headers(user_a.id))
        assert resp.status_code == 204
        assert client.get(_comment_url(post["id"])).json() == []

    def test_other_user_forbidden_403(self, client, admin, user_a, user_b):
        post = _create_post(client, admin)
        comment = client.post(
            _comment_url(post["id"]), json={"content": "别人的"}, headers=_auth_headers(user_a.id)
        ).json()
        resp = client.delete(f"/api/comments/{comment['id']}", headers=_auth_headers(user_b.id))
        assert resp.status_code == 403
        assert resp.json()["detail"] == "只能删除自己的评论"

    def test_unauthenticated_401(self, client, admin, user_a):
        post = _create_post(client, admin)
        comment = client.post(
            _comment_url(post["id"]), json={"content": "x"}, headers=_auth_headers(user_a.id)
        ).json()
        assert client.delete(f"/api/comments/{comment['id']}").status_code == 401

    def test_missing_404(self, client, user_a):
        resp = client.delete("/api/comments/999999", headers=_auth_headers(user_a.id))
        assert resp.status_code == 404


class TestDeletedUserDisplay:
    """PRD A8：软删除用户的评论保留，展示为"用户已注销"。"""

    def test_deleted_user_comment_shows_placeholder(self, client, admin, user_a, db_session):
        post = _create_post(client, admin)
        comment = client.post(
            _comment_url(post["id"]), json={"content": "注销前发的"}, headers=_auth_headers(user_a.id)
        ).json()
        user_a.status = "deleted"
        db_session.commit()
        data = client.get(_comment_url(post["id"])).json()
        assert data[0]["id"] == comment["id"]
        assert data[0]["username"] == "用户已注销"


class TestCascadeOnPostDelete:
    """PRD A6：删除动态后其评论记录一并删除。"""

    def test_comments_cascade_when_post_deleted(self, client, admin, user_a, db_session):
        post = _create_post(client, admin)
        client.post(_comment_url(post["id"]), json={"content": "c1"}, headers=_auth_headers(user_a.id))
        client.post(_comment_url(post["id"]), json={"content": "c2"}, headers=_auth_headers(user_a.id))
        assert len(db_session.scalars(select(Comment)).all()) == 2
        resp = client.delete(f"{POSTS_URL}/{post['id']}", headers=_auth_headers(admin.id))
        assert resp.status_code == 204
        assert len(db_session.scalars(select(Comment)).all()) == 0
