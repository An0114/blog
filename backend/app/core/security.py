"""密码哈希与 JWT 签发/校验。

- 密码：passlib 的 bcrypt 方案（AGENTS.md 红线 1），数据库内绝无明文。
- 会话：python-jose 签发 HS256 JWT，有效期由配置控制（PRD A3：7 天）。
"""

from datetime import datetime, timedelta, timezone

import bcrypt as _bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# passlib 1.7.4 与 bcrypt>=4.1 的兼容补丁一：bcrypt 4.1 起移除了 __about__ 模块，
# 不补齐只是触发一次无害的版本探测告警；补齐后日志保持干净。
if not hasattr(_bcrypt, "__about__"):
    _bcrypt.__about__ = type("_About", (), {"__version__": _bcrypt.__version__})()

# passlib 1.7.4 与 bcrypt>=5.0 的兼容补丁二：bcrypt 5.0 对 >72 字节密码直接抛
# ValueError，而 passlib 启动时的 wrap-bug 检测内部使用 128 字节测试串，导致后端
# 加载崩溃。按 bcrypt 规范在调用前截断到 72 字节，行为与旧版 bcrypt 的静默截断一致。
from passlib.handlers import bcrypt as _passlib_bcrypt  # noqa: E402

_ORIGINAL_CALC_CHECKSUM = _passlib_bcrypt._BcryptBackend._calc_checksum


def _calc_checksum_truncate_72(self, secret):  # type: ignore[no-untyped-def]
    if isinstance(secret, str):
        secret = secret.encode("utf-8")
    if len(secret) > 72:
        secret = secret[:72]
    return _ORIGINAL_CALC_CHECKSUM(self, secret)


_passlib_bcrypt._BcryptBackend._calc_checksum = _calc_checksum_truncate_72

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """返回 bcrypt 哈希串（形如 $2b$12$...），用于入库。"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """校验明文密码与哈希是否匹配。"""
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(user_id: int) -> str:
    """签发 JWT，sub 存用户 ID，过期时间按配置（默认 7 天）。"""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    """校验并解析 JWT，返回 sub（用户 ID 字符串）；无效或过期返回 None。"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except JWTError:
        return None
