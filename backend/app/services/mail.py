"""邮件发送服务（二期：邮箱验证/找回密码；PRD A16：SMTP 配置支持站点表覆盖）。

- SMTP 参数来源优先级：调用方传入的 SmtpConfig（站点初始化配置）> .env（兜底）；
- 全部未配置时把邮件内容输出到后端日志（开发/联调模式，上线前配置 SMTP 即生效）。
"""

import logging
import smtplib
from dataclasses import dataclass
from email.header import Header
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SmtpConfig:
    """站点表 SMTP 配置（site_configs），用于覆盖 .env 默认值。"""

    host: str
    port: int = 465
    user: str = ""
    password: str = ""
    mail_from: str | None = None


def send_email(
    to: str,
    subject: str,
    body: str,
    smtp: SmtpConfig | None = None,
) -> None:
    """发送纯文本邮件；SMTP 未配置时降级为日志输出（不抛错）。

    smtp 参数来自站点初始化配置（页面配置优先）；为 None 时回退 .env。
    """
    host = (smtp.host if smtp else None) or settings.smtp_host
    if not host:
        logger.warning(
            "【邮件未发送：未配置 SMTP】收件人=%s 主题=%s\n%s", to, subject, body
        )
        return
    port = (smtp.port if smtp else None) or settings.smtp_port
    user = (smtp.user if smtp else None) or settings.smtp_user
    password = (smtp.password if smtp else None) or settings.smtp_password
    mail_from = (smtp.mail_from if smtp and smtp.mail_from else None) or settings.mail_from
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = mail_from
    msg["To"] = to
    try:
        with smtplib.SMTP_SSL(host, port, timeout=10) as server:
            server.login(user, password)
            server.send_message(msg)
    except (smtplib.SMTPException, OSError) as exc:
        # 发送失败不阻断业务（验证/重置流程可重试）；记录日志便于排查
        logger.error("邮件发送失败 to=%s subject=%s: %s", to, subject, exc)
