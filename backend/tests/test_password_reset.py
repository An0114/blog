"""找回密码接口测试（二期）：发送重置链接、重置、令牌一次性、防枚举。"""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.email_token import EmailToken
from app.models.user import User

FORGOT_URL = "/api/auth/forgot-password"
RESET_URL = "/api/auth/reset-password"
LOGIN_URL = "/api/auth/login"


@pytest.fixture()
def user(db_session: Session) -> User:
    user = User(
        username="alice",
        email="alice@example.com",
        password_hash=hash_password("old-pass-123"),
        role="user",
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _reset_token(db_session: Session, user_id: int) -> EmailToken:
    return db_session.scalar(
        select(EmailToken)
        .where(EmailToken.user_id == user_id, EmailToken.purpose == "reset_password")
        .order_by(EmailToken.id.desc())
    )


class TestForgotPassword:
    def test_known_email_creates_token(self, client, user, db_session):
        resp = client.post(FORGOT_URL, json={"email": "alice@example.com"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["message"]
        token = _reset_token(db_session, user.id)
        assert token is not None
        assert token.used is False

    def test_unknown_email_still_200(self, client, db_session):
        """防邮箱枚举：不存在的邮箱同样返回成功。"""
        resp = client.post(FORGOT_URL, json={"email": "nobody@example.com"})
        assert resp.status_code == 200
        assert len(db_session.scalars(select(EmailToken)).all()) == 0

    def test_invalid_email_format_422(self, client):
        assert client.post(FORGOT_URL, json={"email": "not-an-email"}).status_code == 422


class TestResetPassword:
    def test_reset_ok_and_login_with_new_password(self, client, user, db_session):
        client.post(FORGOT_URL, json={"email": "alice@example.com"})
        token = _reset_token(db_session, user.id)
        resp = client.post(RESET_URL, json={"token": token.token, "new_password": "new-pass-456"})
        assert resp.status_code == 200, resp.text
        # 旧密码失效
        old = client.post(LOGIN_URL, json={"email": "alice@example.com", "password": "old-pass-123"})
        assert old.status_code == 401
        # 新密码可登录
        new = client.post(LOGIN_URL, json={"email": "alice@example.com", "password": "new-pass-456"})
        assert new.status_code == 200

    def test_token_single_use(self, client, user, db_session):
        client.post(FORGOT_URL, json={"email": "alice@example.com"})
        token = _reset_token(db_session, user.id)
        assert client.post(RESET_URL, json={"token": token.token, "new_password": "new-pass-456"}).status_code == 200
        second = client.post(RESET_URL, json={"token": token.token, "new_password": "another-789"})
        assert second.status_code == 400
        assert second.json()["detail"] == "验证链接无效或已过期"

    def test_invalid_token_400(self, client):
        resp = client.post(RESET_URL, json={"token": "bad", "new_password": "new-pass-456"})
        assert resp.status_code == 400

    def test_short_password_422(self, client, user, db_session):
        client.post(FORGOT_URL, json={"email": "alice@example.com"})
        token = _reset_token(db_session, user.id)
        resp = client.post(RESET_URL, json={"token": token.token, "new_password": "123"})
        assert resp.status_code == 422

    def test_reset_for_deleted_user_rejected(self, client, user, db_session):
        client.post(FORGOT_URL, json={"email": "alice@example.com"})
        token = _reset_token(db_session, user.id)
        user.status = "deleted"
        db_session.commit()
        resp = client.post(RESET_URL, json={"token": token.token, "new_password": "new-pass-456"})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "验证链接无效或已过期"
