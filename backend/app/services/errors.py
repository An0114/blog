"""业务层领域异常：与 HTTP 层解耦，由 main.py 全局处理器统一转成 {detail} 响应。"""


class ServiceError(Exception):
    """业务异常基类；status_code 对应该错误的 HTTP 状态码。"""

    status_code: int = 500
    detail: str = "服务器内部错误"

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class DuplicateError(ServiceError):
    """资源已存在（注册时用户名 / 邮箱重复）。"""

    status_code = 409


class InvalidCredentialsError(ServiceError):
    """邮箱或密码错误。"""

    status_code = 401


class AccountDisabledError(ServiceError):
    """账号被禁用或已注销，无法登录。"""

    status_code = 403


class PermissionDeniedError(ServiceError):
    """无权执行操作（如删除他人评论）。"""

    status_code = 403
    detail = "无权执行此操作"


class AlreadyInitializedError(ServiceError):
    """站点已初始化（存在 admin 用户），再次调用 init 被拒绝。"""

    status_code = 409
    detail = "站点已初始化"


class ConfigError(ServiceError):
    """站点配置不合法（如 SMTP 缺失、网站图标格式/大小不符）。"""

    status_code = 400


class EmailNotVerifiedError(ServiceError):
    """邮箱验证开关开启时，未验证邮箱的用户禁止登录。"""

    status_code = 403
    detail = "邮箱未验证，请先完成邮箱验证"
