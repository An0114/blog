"""认证接口测试：覆盖 PRD A2 / A3 验收点。"""

from datetime import UTC, datetime, timedelta

from jose import jwt
from sqlalchemy import select

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
ME_URL = "/api/auth/me"


def _register(client, **overrides):
    payload = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "secret123",
    }
    payload.update(overrides)
    return client.post(REGISTER_URL, json=payload)


def _create_user(db_session, **overrides) -> User:
    """直接写库造数据（绕过接口，用于登录 / 鉴权等场景的前置）。"""
    data = {
        "username": "bob",
        "email": "bob@example.com",
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


class TestHealth:
    def test_health_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok", "database": "ok"}


class TestRegister:
    """PRD A2：用户名/邮箱重复明确报错；密码入库为哈希非明文。"""

    def test_register_ok(self, client):
        resp = _register(client)
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] > 0
        assert data["username"] == "alice"
        assert data["email"] == "alice@example.com"
        assert data["role"] == "user"
        assert data["status"] == "active"
        assert "created_at" in data
        # 响应绝不泄露密码相关字段
        assert "password" not in data and "password_hash" not in data

    def test_duplicate_username_409(self, client, db_session):
        _create_user(db_session, username="alice")
        resp = _register(client, email="other@example.com")
        assert resp.status_code == 409
        assert resp.json()["detail"] == "用户名已存在"

    def test_duplicate_email_409(self, client, db_session):
        _create_user(db_session, username="seed_user", email="alice@example.com")
        resp = _register(client, username="bob")
        assert resp.status_code == 409
        assert resp.json()["detail"] == "邮箱已存在"

    def test_email_case_insensitive_duplicate_409(self, client, db_session):
        """邮箱大小写不同视为重复（入库前统一小写）。"""
        _create_user(db_session, email="alice@example.com")
        resp = _register(client, username="bob", email="ALICE@EXAMPLE.COM")
        assert resp.status_code == 409

    def test_password_stored_as_hash(self, client, db_session):
        _register(client)
        user = db_session.scalar(select(User).where(User.username == "alice"))
        assert user is not None
        assert user.password_hash != "secret123"  # 非明文
        assert user.password_hash.startswith("$2b$")  # bcrypt 标识
        assert verify_password("secret123", user.password_hash)  # 可验证

    def test_short_password_422(self, client):
        resp = _register(client, password="123")
        assert resp.status_code == 422

    def test_invalid_email_422(self, client):
        resp = _register(client, email="not-an-email")
        assert resp.status_code == 422

    def test_username_too_short_422(self, client):
        resp = _register(client, username="ab")
        assert resp.status_code == 422


class TestLogin:
    """PRD A3：密码错误拒绝并提示；成功后返回 7 天有效 JWT。"""

    def test_login_ok(self, client, db_session):
        user = _create_user(db_session)
        resp = client.post(LOGIN_URL, json={"email": "bob@example.com", "password": "secret123"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["username"] == "bob"
        assert "password" not in data["user"]
        # token 可解析且 sub 为用户 id、有效期约 7 天
        payload = jwt.decode(data["token"], settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == str(user.id)
        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        assert exp - datetime.now(UTC) > timedelta(days=6)

    def test_wrong_password_401(self, client, db_session):
        _create_user(db_session)
        resp = client.post(LOGIN_URL, json={"email": "bob@example.com", "password": "wrong-pass"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "邮箱或密码错误"

    def test_unknown_email_401(self, client):
        resp = client.post(LOGIN_URL, json={"email": "nobody@example.com", "password": "secret123"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "邮箱或密码错误"

    def test_login_email_case_insensitive(self, client, db_session):
        _create_user(db_session)
        resp = client.post(LOGIN_URL, json={"email": "BOB@example.com", "password": "secret123"})
        assert resp.status_code == 200

    def test_disabled_user_403(self, client, db_session):
        """PRD A8：禁用后无法登录。"""
        _create_user(db_session, status="disabled")
        resp = client.post(LOGIN_URL, json={"email": "bob@example.com", "password": "secret123"})
        assert resp.status_code == 403
        assert resp.json()["detail"] == "账号已被禁用"

    def test_deleted_user_403(self, client, db_session):
        """PRD A8：软删除后无法登录。"""
        _create_user(db_session, status="deleted")
        resp = client.post(LOGIN_URL, json={"email": "bob@example.com", "password": "secret123"})
        assert resp.status_code == 403
        assert resp.json()["detail"] == "账号已注销，无法登录"


class TestMe:
    """PRD A3：/api/auth/me 需登录。"""

    def test_me_without_token_401(self, client):
        resp = client.get(ME_URL)
        assert resp.status_code == 401

    def test_me_with_invalid_token_401(self, client):
        resp = client.get(ME_URL, headers={"Authorization": "Bearer not.a.jwt"})
        assert resp.status_code == 401

    def test_me_with_valid_token_200(self, client, db_session):
        user = _create_user(db_session)
        token = create_access_token(user.id)
        resp = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == user.id
        assert data["username"] == "bob"
        assert "password_hash" not in data

    def test_me_with_expired_token_401(self, client, db_session):
        user = _create_user(db_session)
        now = datetime.now(UTC)
        expired_payload = {
            "sub": str(user.id),
            "iat": now - timedelta(minutes=10),
            "exp": now - timedelta(minutes=1),
        }
        expired = jwt.encode(
            expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )
        resp = client.get(ME_URL, headers={"Authorization": f"Bearer {expired}"})
        assert resp.status_code == 401

    def test_me_disabled_user_403(self, client, db_session):
        user = _create_user(db_session, status="disabled")
        token = create_access_token(user.id)
        resp = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_me_deleted_user_401(self, client, db_session):
        user = _create_user(db_session, status="deleted")
        token = create_access_token(user.id)
        resp = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401
