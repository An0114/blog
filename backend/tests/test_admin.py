"""管理端接口测试：覆盖 PRD A8（列表/禁用无法登录/软删除保留评论）与权限。"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.comment import Comment
from app.models.user import User

ADMIN_USERS_URL = "/api/admin/users"
POSTS_URL = "/api/posts"
LOGIN_URL = "/api/auth/login"


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


def _create_post(client: TestClient, admin: User) -> dict:
    resp = client.post(
        POSTS_URL,
        json={"title": "帖子", "content": "正文", "category": "project"},
        headers=_auth_headers(admin.id),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestListUsers:
    def test_admin_ok(self, client, admin, normal_user):
        resp = client.get(ADMIN_USERS_URL, headers=_auth_headers(admin.id))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        names = {u["username"] for u in data["items"]}
        assert names == {"admin", "reader"}

    def test_pagination(self, client, admin, db_session):
        for i in range(5):
            _make_user(db_session, username=f"u{i}", email=f"u{i}@example.com")
        resp = client.get(ADMIN_USERS_URL, params={"page": 2, "size": 2}, headers=_auth_headers(admin.id))
        data = resp.json()
        assert data["total"] == 6
        assert len(data["items"]) == 2

    def test_normal_user_forbidden_403(self, client, normal_user):
        assert client.get(ADMIN_USERS_URL, headers=_auth_headers(normal_user.id)).status_code == 403

    def test_unauthenticated_401(self, client):
        assert client.get(ADMIN_USERS_URL).status_code == 401


class TestUpdateStatus:
    """PRD A8：禁用后无法登录；启用后恢复。"""

    def test_disable_user(self, client, admin, normal_user):
        resp = client.patch(
            f"{ADMIN_USERS_URL}/{normal_user.id}",
            json={"status": "disabled"},
            headers=_auth_headers(admin.id),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "disabled"
        # 禁用后登录被拒
        login = client.post(LOGIN_URL, json={"email": "reader@example.com", "password": "secret123"})
        assert login.status_code == 403
        assert login.json()["detail"] == "账号已被禁用"

    def test_enable_user_restores_login(self, client, admin, db_session):
        user = _make_user(db_session, username="r2", email="r2@example.com", status="disabled")
        client.patch(
            f"{ADMIN_USERS_URL}/{user.id}", json={"status": "active"}, headers=_auth_headers(admin.id)
        )
        resp = client.post(LOGIN_URL, json={"email": "r2@example.com", "password": "secret123"})
        assert resp.status_code == 200

    def test_missing_user_404(self, client, admin):
        resp = client.patch(
            f"{ADMIN_USERS_URL}/999999", json={"status": "disabled"}, headers=_auth_headers(admin.id)
        )
        assert resp.status_code == 404

    def test_soft_deleted_user_404(self, client, admin, db_session):
        user = _make_user(db_session, username="gone", email="gone@example.com", status="deleted")
        resp = client.patch(
            f"{ADMIN_USERS_URL}/{user.id}", json={"status": "active"}, headers=_auth_headers(admin.id)
        )
        assert resp.status_code == 404

    def test_self_operation_400(self, client, admin):
        resp = client.patch(
            f"{ADMIN_USERS_URL}/{admin.id}", json={"status": "disabled"}, headers=_auth_headers(admin.id)
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "不能对博主自身执行此操作"

    def test_invalid_status_422(self, client, admin, normal_user):
        resp = client.patch(
            f"{ADMIN_USERS_URL}/{normal_user.id}", json={"status": "frozen"}, headers=_auth_headers(admin.id)
        )
        assert resp.status_code == 422


class TestDeleteUser:
    """PRD A8：软删除后无法登录、记录保留、历史评论保留并标注注销。"""

    def test_soft_delete_user(self, client, admin, normal_user, db_session):
        resp = client.delete(f"{ADMIN_USERS_URL}/{normal_user.id}", headers=_auth_headers(admin.id))
        assert resp.status_code == 204
        db_session.expire_all()  # 丢弃 identity map 缓存，重新读库
        stored = db_session.get(User, normal_user.id)
        assert stored is not None  # 记录保留
        assert stored.status == "deleted"
        login = client.post(LOGIN_URL, json={"email": "reader@example.com", "password": "secret123"})
        assert login.status_code == 403

    def test_deleted_user_comments_kept(self, client, admin, normal_user, db_session):
        """软删除用户的评论保留并显示"用户已注销"。"""
        post = _create_post(client, admin)
        client.post(
            f"{POSTS_URL}/{post['id']}/comments",
            json={"content": "再见"},
            headers=_auth_headers(normal_user.id),
        )
        client.delete(f"{ADMIN_USERS_URL}/{normal_user.id}", headers=_auth_headers(admin.id))
        comments = client.get(f"{POSTS_URL}/{post['id']}/comments").json()
        assert len(comments) == 1
        assert comments[0]["username"] == "用户已注销"
        assert len(db_session.scalars(select(Comment)).all()) == 1  # 评论记录保留

    def test_self_delete_400(self, client, admin):
        resp = client.delete(f"{ADMIN_USERS_URL}/{admin.id}", headers=_auth_headers(admin.id))
        assert resp.status_code == 400

    def test_missing_user_404(self, client, admin):
        resp = client.delete(f"{ADMIN_USERS_URL}/999999", headers=_auth_headers(admin.id))
        assert resp.status_code == 404

    def test_already_deleted_404(self, client, admin, db_session):
        user = _make_user(db_session, username="gone2", email="gone2@example.com", status="deleted")
        resp = client.delete(f"{ADMIN_USERS_URL}/{user.id}", headers=_auth_headers(admin.id))
        assert resp.status_code == 404
