"""草稿箱接口测试（三期）：CRUD、仅博主、发布（生成动态+绑定媒体+删除草稿）。"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.draft import Draft
from app.models.media import Media
from app.models.user import User

DRAFTS_URL = "/api/drafts"
POSTS_URL = "/api/posts"


@pytest.fixture()
def admin(db_session: Session) -> User:
    return _make_user(db_session, username="admin", email="admin@example.com", role="admin")


@pytest.fixture()
def user_a(db_session: Session) -> User:
    return _make_user(db_session, username="alice", email="alice@example.com")


def _make_user(db_session: Session, **overrides) -> User:
    data = {
        "username": "user",
        "email": "user@example.com",
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


def _auth_headers(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def _create_media(db_session: Session, admin: User, media_type: str = "image") -> Media:
    """创建一条未绑定动态的媒体记录（post_id 为空，模拟"先上传后绑定"）。"""
    media = Media(
        type=media_type, file_path=f"{media_type}_{id(Media)}.png", file_size=10, post_id=None
    )
    db_session.add(media)
    db_session.commit()
    db_session.refresh(media)
    return media


def _create_draft(client: TestClient, admin: User, **overrides) -> dict:
    payload = {"title": "草稿", "content": "待完善", "category": "daily", "media_ids": []}
    payload.update(overrides)
    resp = client.post(DRAFTS_URL, json=payload, headers=_auth_headers(admin.id))
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestDraftCrud:
    def test_create_draft(self, client, admin):
        data = _create_draft(client, admin, media_ids=[1, 2])
        assert data["title"] == "草稿"
        assert data["category"] == "daily"
        assert data["media_ids"] == [1, 2]  # 保存草稿不校验媒体占用

    def test_list_drafts_newest_first(self, client, admin):
        _create_draft(client, admin, title="第一份")
        _create_draft(client, admin, title="第二份")
        data = client.get(DRAFTS_URL, headers=_auth_headers(admin.id)).json()
        assert data["total"] == 2
        assert data["items"][0]["title"] == "第二份"
        assert data["items"][1]["title"] == "第一份"

    def test_get_draft(self, client, admin):
        draft = _create_draft(client, admin)
        data = client.get(
            f"{DRAFTS_URL}/{draft['id']}", headers=_auth_headers(admin.id)
        ).json()
        assert data["id"] == draft["id"]
        assert data["content"] == "待完善"

    def test_update_draft_full_replace(self, client, admin):
        draft = _create_draft(client, admin)
        resp = client.put(
            f"{DRAFTS_URL}/{draft['id']}",
            json={"title": "改后", "content": "新内容", "category": "project", "media_ids": [9]},
            headers=_auth_headers(admin.id),
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["title"] == "改后"
        assert resp.json()["media_ids"] == [9]

    def test_delete_draft(self, client, admin, db_session):
        draft = _create_draft(client, admin)
        resp = client.delete(
            f"{DRAFTS_URL}/{draft['id']}", headers=_auth_headers(admin.id)
        )
        assert resp.status_code == 204
        assert db_session.get(Draft, draft["id"]) is None

    def test_missing_draft_404(self, client, admin):
        assert client.get(
            f"{DRAFTS_URL}/999999", headers=_auth_headers(admin.id)
        ).status_code == 404
        assert client.delete(
            f"{DRAFTS_URL}/999999", headers=_auth_headers(admin.id)
        ).status_code == 404


class TestDraftAuth:
    def test_unauthenticated_401(self, client):
        assert client.post(DRAFTS_URL, json={"title": "t", "content": "c", "category": "daily"}).status_code == 401
        assert client.get(DRAFTS_URL).status_code == 401

    def test_non_admin_forbidden(self, client, user_a):
        resp = client.post(
            DRAFTS_URL,
            json={"title": "t", "content": "c", "category": "daily"},
            headers=_auth_headers(user_a.id),
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "仅博主可执行此操作"
        assert client.get(DRAFTS_URL, headers=_auth_headers(user_a.id)).status_code == 403


class TestPublishDraft:
    def test_publish_creates_post_and_removes_draft(
        self, client, admin, db_session
    ):
        media = _create_media(db_session, admin)
        draft = _create_draft(client, admin, title="定稿", media_ids=[media.id])
        resp = client.post(
            f"{DRAFTS_URL}/{draft['id']}/publish", headers=_auth_headers(admin.id)
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["title"] == "定稿"
        # 草稿已删除
        assert db_session.get(Draft, draft["id"]) is None
        # 动态出现在列表，媒体已绑定
        data = client.get(POSTS_URL).json()
        assert data["items"][0]["id"] == resp.json()["id"]
        assert data["items"][0]["media"][0]["id"] == media.id

    def test_publish_missing_draft_404(self, client, admin):
        resp = client.post(
            f"{DRAFTS_URL}/999999/publish", headers=_auth_headers(admin.id)
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "草稿不存在"

    def test_publish_with_unknown_media_404(self, client, admin):
        draft = _create_draft(client, admin, media_ids=[999999])
        resp = client.post(
            f"{DRAFTS_URL}/{draft['id']}/publish", headers=_auth_headers(admin.id)
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "部分媒体不存在"
        # 发布失败草稿保留
        assert client.get(
            f"{DRAFTS_URL}/{draft['id']}", headers=_auth_headers(admin.id)
        ).status_code == 200

    def test_publish_with_bound_media_409(self, client, admin, db_session):
        media = _create_media(db_session, admin)
        # 先把媒体绑定到已发布动态
        resp = client.post(
            POSTS_URL,
            json={"title": "占用", "content": "正文", "category": "project", "media_ids": [media.id]},
            headers=_auth_headers(admin.id),
        )
        assert resp.status_code == 201, resp.text
        draft = _create_draft(client, admin, media_ids=[media.id])
        resp = client.post(
            f"{DRAFTS_URL}/{draft['id']}/publish", headers=_auth_headers(admin.id)
        )
        assert resp.status_code == 409
        assert resp.json()["detail"] == "媒体已被其他动态使用"
