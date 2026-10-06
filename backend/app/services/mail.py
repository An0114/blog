"""邮件发送服务（二期：邮箱验证/找回密码）。

- 配置了 SMTP（.env 的 SMTP_HOST/USER/PASSWORD）时真实发送；
- 未配置时把邮件内容输出到后端日志（开发/联调模式，上线前配置 SMTP 即生效）。
"""

import logging
import smtplib
from email.header import Header
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    """发送纯文本邮件；SMTP 未配置时降级为日志输出（不抛错）。"""
    if not settings.smtp_host:
        logger.warning(
            "【邮件未发送：未配置 SMTP】收件人=%s 主题=%s\n%s", to, subject, body
        )
        return
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = settings.mail_from
    msg["To"] = to
    try:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
    except (smtplib.SMTPException, OSError) as exc:
        # 发送失败不阻断业务（验证/重置流程可重试）；记录日志便于排查
        logger.error("邮件发送失败 to=%s subject=%s: %s", to, subject, exc)
