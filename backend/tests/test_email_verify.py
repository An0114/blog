"""邮箱验证接口测试（二期）：发送请求、confirm、一次性令牌、权限。"""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.email_token import EmailToken
from app.models.user import User

VERIFY_REQUEST_URL = "/api/auth/verify-email/request"
VERIFY_CONFIRM_URL = "/api/auth/verify-email/confirm"


@pytest.fixture()
def user(db_session: Session) -> User:
    user = User(
        username="alice",
        email="alice@example.com",
        password_hash=hash_password("secret123"),
        role="user",
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def _latest_token(db_session: Session, user_id: int, purpose: str) -> EmailToken:
    return db_session.scalar(
        select(EmailToken)
        .where(EmailToken.user_id == user_id, EmailToken.purpose == purpose)
        .order_by(EmailToken.id.desc())
    )


class TestRequestVerifyEmail:
    def test_request_ok(self, client, user, db_session):
        resp = client.post(VERIFY_REQUEST_URL, headers=_auth_headers(user.id))
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["message"]
        assert data["expires_minutes"] == 30
        token = _latest_token(db_session, user.id, "verify_email")
        assert token is not None
        assert token.used is False

    def test_requires_login_401(self, client):
        assert client.post(VERIFY_REQUEST_URL).status_code == 401

    def test_already_verified_400(self, client, user, db_session):
        user.email_verified = True
        db_session.commit()
        resp = client.post(VERIFY_REQUEST_URL, headers=_auth_headers(user.id))
        assert resp.status_code == 400
        assert resp.json()["detail"] == "邮箱已验证，无需重复验证"


class TestConfirmVerifyEmail:
    def test_confirm_ok(self, client, user, db_session):
        client.post(VERIFY_REQUEST_URL, headers=_auth_headers(user.id))
        token = _latest_token(db_session, user.id, "verify_email")
        resp = client.post(VERIFY_CONFIRM_URL, json={"token": token.token})
        assert resp.status_code == 200, resp.text
        assert resp.json()["email_verified"] is True

    def test_token_single_use(self, client, user, db_session):
        client.post(VERIFY_REQUEST_URL, headers=_auth_headers(user.id))
        token = _latest_token(db_session, user.id, "verify_email")
        assert client.post(VERIFY_CONFIRM_URL, json={"token": token.token}).status_code == 200
        second = client.post(VERIFY_CONFIRM_URL, json={"token": token.token})
        assert second.status_code == 400
        assert second.json()["detail"] == "验证链接无效或已过期"

    def test_invalid_token_400(self, client):
        resp = client.post(VERIFY_CONFIRM_URL, json={"token": "not-a-token"})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "验证链接无效或已过期"

    def test_register_user_email_unverified(self, client):
        """既有行为不破坏：新注册用户 email_verified=false，登录响应带该字段。"""
        resp = client.post(
            "/api/auth/register",
            json={"username": "bob", "email": "bob@example.com", "password": "secret123"},
        )
        assert resp.status_code == 201
        assert resp.json()["email_verified"] is False
        login = client.post(
            "/api/auth/login", json={"email": "bob@example.com", "password": "secret123"}
        )
        assert login.status_code == 200
        assert login.json()["user"]["email_verified"] is False
