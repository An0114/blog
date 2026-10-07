"""站点配置读取（services 层）：供 init / auth / mail 等模块共用，避免循环依赖。"""

from sqlalchemy.orm import Session

from app.models.site_config import SiteConfig


def get_site_config(db: Session) -> SiteConfig:
    """获取单行站点配置；不存在则创建（id=1），保证调用方总能读到。

    注意：创建行时会 commit；调用方应避免在会话中挂起其他未提交写入后调用本函数，
    否则会被连带提交。业务上"先取配置、再挂起写"即可规避。
    """
    cfg = db.get(SiteConfig, 1)
    if cfg is None:
        cfg = SiteConfig(id=1)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def email_verify_enabled(db: Session) -> bool:
    """邮箱验证开关（PRD A16）：默认关闭，与现状注册行为一致。"""
    return bool(get_site_config(db).email_verify_enabled)
