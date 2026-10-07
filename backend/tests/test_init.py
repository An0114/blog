"""站点初始化接口测试（PRD A16 / TRD Task 16）。

覆盖：状态判定（user 表 admin 推导）、初始化成功、重复初始化 409、查重 409、
图标格式/大小校验、SMTP 缺失 400、邮箱验证开关对注册/登录的影响。
"""

import base64

from sqlalchemy import select

from app.core.security import hash_password, verify_password
from app.models.email_token import EmailToken
from app.models.site_config import SiteConfig
from app.models.user import User

STATUS_URL = "/api/admin/init/status"
INIT_URL = "/api/admin/init"
REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"

# 1x1 透明 PNG（合法图标）
PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


def _init_payload(**overrides):
    payload = {
        "username": "blogger",
        "email": "blogger@example.com",
        "password": "secret123",
        "email_verify_enabled": False,
    }
    payload.update(overrides)
    return payload


def _create_admin(db_session, **overrides) -> User:
    """直接写库造 admin（绕过初始化接口，用于"已初始化"场景前置）。"""
    data = {
        "username": "admin_seed",
        "email": "admin_seed@example.com",
        "password": "secret123",
        "role": "admin",
    }
    data.update(overrides)
    user = User(
        username=data["username"],
        email=data["email"],
        password_hash=hash_password(data["password"]),
        role=data["role"],
        status="active",
        email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestInitStatus:
    """PRD A16：initialized 由 user 表是否存在 admin 推导。"""

    def test_status_not_initialized(self, client, db_session):
        resp = client.get(STATUS_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["initialized"] is False
        assert data["email_verify_enabled"] is False
        assert data["has_site_icon"] is False

    def test_status_initialized_when_admin_exists(self, client, db_session):
        _create_admin(db_session)
        resp = client.get(STATUS_URL)
        assert resp.status_code == 200
        assert resp.json()["initialized"] is True

    def test_status_syncs_site_config(self, client, db_session):
        """无 admin 时 status 会创建 site_configs 行并保持 is_initialized=false。"""
        client.get(STATUS_URL)
        config = db_session.get(SiteConfig, 1)
        assert config is not None
        assert config.is_initialized is False

    def test_status_reflects_icon_and_email_flag(self, client, db_session):
        _create_admin(db_session)
        config = db_session.get(SiteConfig, 1)
        if config is None:
            config = SiteConfig(id=1)
            db_session.add(config)
            db_session.commit()
        config.email_verify_enabled = True
        config.site_icon_url = "/uploads/site_icon/abc.png"
        db_session.commit()
        resp = client.get(STATUS_URL)
        assert resp.json()["email_verify_enabled"] is True
        assert resp.json()["has_site_icon"] is True


class TestInit:
    """PRD A16：初始化创建博主账户 + 站点配置。"""

    def test_init_ok(self, client, db_session):
        resp = client.post(INIT_URL, json=_init_payload())
        assert resp.status_code == 201
        data = resp.json()
        assert data["message"]
        assert data["admin"]["username"] == "blogger"
        assert data["admin"]["role"] == "admin"
        assert data["admin"]["email_verified"] is True  # 站长免邮箱验证
        assert "password" not in data["admin"] and "password_hash" not in data["admin"]
        # 库内校验：admin 已创建、密码为 bcrypt 哈希、站点配置落库
        user = db_session.scalar(select(User).where(User.username == "blogger"))
        assert user is not None
        assert user.role == "admin"
        assert user.password_hash != "secret123"
        assert verify_password("secret123", user.password_hash)
        config = db_session.get(SiteConfig, 1)
        assert config is not None
        assert config.is_initialized is True
        assert config.email_verify_enabled is False

    def test_init_with_icon_stores_file(self, client, db_session, monkeypatch, tmp_path):
        monkeypatch.setattr("app.services.init.settings.upload_dir", str(tmp_path))
        resp = client.post(
            INIT_URL,
            json=_init_payload(site_icon_base64=f"data:image/png;base64,{PNG_B64}"),
        )
        assert resp.status_code == 201
        config = db_session.get(SiteConfig, 1)
        assert config is not None and config.site_icon_url is not None
        assert config.site_icon_url.startswith("/uploads/site_icon/")
        assert config.site_icon_url.endswith(".png")
        # 文件确实落盘
        relative = config.site_icon_url.removeprefix("/uploads/")
        assert (tmp_path / relative).exists()

    def test_init_twice_409(self, client, db_session):
        client.post(INIT_URL, json=_init_payload())
        resp = client.post(INIT_URL, json=_init_payload(username="another", email="x@example.com"))
        assert resp.status_code == 409
        assert resp.json()["detail"] == "站点已初始化"

    def test_init_conflict_with_existing_admin_409(self, client, db_session):
        _create_admin(db_session)
        resp = client.post(INIT_URL, json=_init_payload())
        assert resp.status_code == 409
        assert resp.json()["detail"] == "站点已初始化"

    def test_init_duplicate_username_409(self, client, db_session):
        # 普通用户占用 blogger 用户名（站点未初始化，才走查重分支）
        _create_admin(db_session, username="blogger", email="seed@example.com", role="user")
        resp = client.post(INIT_URL, json=_init_payload())
        assert resp.status_code == 409
        assert resp.json()["detail"] == "用户名已存在"

    def test_init_duplicate_email_409(self, client, db_session):
        # 普通用户占用 blogger 邮箱（站点未初始化，才走查重分支）
        _create_admin(db_session, username="seed_user", email="blogger@example.com", role="user")
        resp = client.post(INIT_URL, json=_init_payload())
        assert resp.status_code == 409
        assert resp.json()["detail"] == "邮箱已存在"

    def test_init_short_password_422(self, client):
        resp = client.post(INIT_URL, json=_init_payload(password="123"))
        assert resp.status_code == 422

    def test_init_bad_icon_format_400(self, client, monkeypatch, tmp_path):
        monkeypatch.setattr("app.services.init.settings.upload_dir", str(tmp_path))
        not_image = base64.b64encode(b"not an image at all").decode()
        resp = client.post(
            INIT_URL, json=_init_payload(site_icon_base64=f"data:image/png;base64,{not_image}")
        )
        assert resp.status_code == 400
        assert "格式" in resp.json()["detail"]

    def test_init_oversize_icon_400(self, client):
        # 构造 1MB+ 的合法 PNG 头 + 填充（魔数通过、长度超限）
        big = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * (1024 * 1024 + 16)).decode()
        resp = client.post(INIT_URL, json=_init_payload(site_icon_base64=big))
        assert resp.status_code == 400
        assert "1MB" in resp.json()["detail"]

    def test_init_email_verify_requires_smtp_400(self, client):
        resp = client.post(
            INIT_URL, json=_init_payload(email_verify_enabled=True, smtp_host=None)
        )
        assert resp.status_code == 400
        assert "SMTP" in resp.json()["detail"]

    def test_init_email_verify_with_smtp_ok(self, client, db_session):
        resp = client.post(
            INIT_URL,
            json=_init_payload(
                email_verify_enabled=True,
                smtp_host="smtp.example.com",
                smtp_port=465,
                smtp_user="blog@example.com",
                smtp_password="smtp-pass",
            ),
        )
        assert resp.status_code == 201
        config = db_session.get(SiteConfig, 1)
        assert config is not None
        assert config.email_verify_enabled is True
        assert config.smtp_host == "smtp.example.com"
        assert config.smtp_password == "smtp-pass"


class TestEmailVerifySwitch:
    """PRD A16：邮箱验证开关对注册 / 登录的影响。"""

    def _enable_email_verify(self, db_session) -> None:
        config = db_session.get(SiteConfig, 1)
        if config is None:
            config = SiteConfig(id=1)
            db_session.add(config)
        config.email_verify_enabled = True
        db_session.commit()

    def test_register_with_switch_off_no_token(self, client, db_session):
        """默认关闭：注册行为与现状一致，不生成验证令牌。"""
        resp = client.post(
            REGISTER_URL,
            json={"username": "alice", "email": "alice@example.com", "password": "secret123"},
        )
        assert resp.status_code == 201
        assert resp.json()["email_verified"] is False
        token = db_session.scalar(
            select(EmailToken).where(EmailToken.purpose == "verify_email")
        )
        assert token is None

    def test_register_with_switch_on_creates_token(self, client, db_session):
        """开关开启：注册后自动创建验证令牌（email_verified 保持 false）。"""
        self._enable_email_verify(db_session)
        resp = client.post(
            REGISTER_URL,
            json={"username": "alice", "email": "alice@example.com", "password": "secret123"},
        )
        assert resp.status_code == 201
        assert resp.json()["email_verified"] is False
        token = db_session.scalar(
            select(EmailToken).where(EmailToken.purpose == "verify_email")
        )
        assert token is not None

    def test_login_unverified_blocked_when_switch_on(self, client, db_session):
        """开关开启：未验证邮箱的用户登录被拒（403），验证后可登录。"""
        self._enable_email_verify(db_session)
        client.post(
            REGISTER_URL,
            json={"username": "alice", "email": "alice@example.com", "password": "secret123"},
        )
        resp = client.post(
            LOGIN_URL, json={"email": "alice@example.com", "password": "secret123"}
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "邮箱未验证，请先完成邮箱验证"
        # 完成验证后可登录
        token = db_session.scalar(
            select(EmailToken).where(EmailToken.purpose == "verify_email")
        )
        assert token is not None
        user = db_session.scalar(select(User).where(User.username == "alice"))
        user.email_verified = True
        db_session.commit()
        resp = client.post(
            LOGIN_URL, json={"email": "alice@example.com", "password": "secret123"}
        )
        assert resp.status_code == 200

    def test_login_unverified_allowed_when_switch_off(self, client, db_session):
        """默认关闭：未验证邮箱不影响登录（既有 A3 行为不变）。"""
        client.post(
            REGISTER_URL,
            json={"username": "alice", "email": "alice@example.com", "password": "secret123"},
        )
        resp = client.post(
            LOGIN_URL, json={"email": "alice@example.com", "password": "secret123"}
        )
        assert resp.status_code == 200

    def test_admin_login_ignores_unverified_rule(self, client, db_session):
        """开关开启时 admin（初始化即已验证）仍可正常登录。"""
        self._enable_email_verify(db_session)
        admin = _create_admin(db_session, username="boss", email="boss@example.com")
        assert admin.email_verified is True
        resp = client.post(
            LOGIN_URL, json={"email": "boss@example.com", "password": "secret123"}
        )
        assert resp.status_code == 200
