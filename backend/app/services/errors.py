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
