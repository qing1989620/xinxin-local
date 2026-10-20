"""Resend HTTP 通道与域名管理。

全部用打桩的 httpx，验证请求形状、失败提示与密钥不外泄；不发真实邮件。
"""

from fastapi.testclient import TestClient

import app.mail as mail_module
from app.config import Config
from app.main import create_app


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


def setup(tmp_path):
    app = create_app(Config(tmp_path, "synthetic-bootstrap"))
    client = TestClient(app)
    token = client.post(
        "/api/v1/auth/setup",
        json={
            "name": "LocalOwner",
            "password": "synthetic-password-123",
            "setup_code": "synthetic-bootstrap",
        },
    ).json()["token"]
    client.headers["Authorization"] = "Bearer " + token
    return app, client


def configure_resend(client, key="re_synthetic_key"):
    response = client.put(
        "/api/v1/settings/email",
        json={
            "email": "owner@example.com",
            "provider": "resend",
            "resend_from": "Xinxin <no-reply@example.com>",
            "resend_api_key": key,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_resend_sends_expected_http_request(tmp_path, monkeypatch):
    app, client = setup(tmp_path)
    settings = configure_resend(client)
    assert settings["provider"] == "resend" and settings["configured"] is True
    assert settings["resend_configured"] is True
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured.update(url=url, headers=headers, payload=json)
        return FakeResponse(200, {"id": "email_123"})

    monkeypatch.setattr(mail_module.httpx, "post", fake_post)
    response = client.post(
        "/api/v1/auth/email/code", json={"email": "owner@example.com"}
    )
    assert response.status_code == 200
    assert captured["url"] == "https://api.resend.com/emails"
    assert captured["headers"]["Authorization"] == "Bearer re_synthetic_key"
    payload = captured["payload"]
    assert payload["from"] == "Xinxin <no-reply@example.com>"
    assert payload["to"] == ["owner@example.com"]
    assert "验证码" in payload["subject"]
    assert "10 分钟" in payload["text"]
    assert "<html" not in payload["html"] and "font-size:30px" in payload["html"]
    # 密钥与验证码都不回显在设置接口里
    assert "re_synthetic_key" not in client.get("/api/v1/settings/email").text


def test_resend_failure_is_readable_and_invalidates_the_code(tmp_path, monkeypatch):
    app, client = setup(tmp_path)
    configure_resend(client)

    def fake_post(*_, **__):
        return FakeResponse(422, {"name": "validation_error"})

    monkeypatch.setattr(mail_module.httpx, "post", fake_post)
    response = client.post(
        "/api/v1/auth/email/code", json={"email": "owner@example.com"}
    )
    assert response.status_code == 503
    assert "Resend" in response.text and "validation_error" in response.text
    assert app.state.store.one("SELECT used FROM email_codes")["used"] == 1


def test_domains_are_listed_with_dns_records(tmp_path, monkeypatch):
    _, client = setup(tmp_path)
    configure_resend(client)

    def fake_get(url, headers=None, timeout=None):
        assert url == "https://api.resend.com/domains"
        assert headers["Authorization"] == "Bearer re_synthetic_key"
        return FakeResponse(
            200,
            {
                "data": [
                    {
                        "id": "d-1",
                        "name": "example.com",
                        "status": "pending",
                        "region": "us-east-1",
                        "created_at": "2026-10-20 10:00:00",
                        "records": [
                            {
                                "record": "SPF",
                                "name": "send.example.com",
                                "type": "TXT",
                                "value": "v=spf1 include:amazonses.com ~all",
                                "ttl": "Auto",
                                "priority": None,
                                "status": "pending",
                            }
                        ],
                        "extra": "must not leak",
                    }
                ]
            },
        )

    monkeypatch.setattr(mail_module.httpx, "get", fake_get)
    body = client.get("/api/v1/settings/email/domains").json()
    assert body["domains"][0]["name"] == "example.com"
    assert body["domains"][0]["records"][0]["type"] == "TXT"
    assert "extra" not in body["domains"][0]


def test_domain_can_be_added_and_verified(tmp_path, monkeypatch):
    _, client = setup(tmp_path)
    configure_resend(client)
    calls = []

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append((url, json))
        return FakeResponse(200, {"id": "d-2", "status": "not_started"})

    monkeypatch.setattr(mail_module.httpx, "post", fake_post)
    assert (
        client.post(
            "/api/v1/settings/email/domains", json={"name": "mail.example.com"}
        ).status_code
        == 200
    )
    assert calls[0][0] == "https://api.resend.com/domains"
    assert calls[0][1] == {"name": "mail.example.com"}
    assert (
        client.post("/api/v1/settings/email/domains/d-2/verify").status_code == 200
    )
    assert calls[1][0] == "https://api.resend.com/domains/d-2/verify"
    # 非法域名在入参校验阶段就被拒绝
    assert (
        client.post(
            "/api/v1/settings/email/domains", json={"name": "not a domain"}
        ).status_code
        == 422
    )
    assert (
        client.post("/api/v1/settings/email/domains/bad!id/verify").status_code == 400
    )


def test_test_mail_reports_missing_configuration(tmp_path):
    app, client = setup(tmp_path)
    client.put(
        "/api/v1/settings/email",
        json={"email": "owner@example.com", "smtp_password": ""},
    )
    response = client.post("/api/v1/settings/email/test")
    assert response.status_code == 400
    assert "SMTP 授权码" in response.json()["detail"]


def test_test_mail_goes_through_the_configured_transport(tmp_path, monkeypatch):
    app, client = setup(tmp_path)
    configure_resend(client)
    calls = []

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append((url, json))
        return FakeResponse(200, {"id": "email_test"})

    monkeypatch.setattr(mail_module.httpx, "post", fake_post)
    response = client.post("/api/v1/settings/email/test")
    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "provider": "resend",
        "to": "owner@example.com",
    }
    payload = calls[0][1]
    assert payload["subject"] == "Xinxin · 配置测试"
    assert "邮件通道" in payload["text"]
    assert payload["to"] == ["owner@example.com"]


def test_test_mail_failure_is_reported_without_leaking_the_key(tmp_path, monkeypatch):
    app, client = setup(tmp_path)
    configure_resend(client)

    monkeypatch.setattr(
        mail_module.httpx,
        "post",
        lambda *_, **__: FakeResponse(403, {"name": "validation_error"}),
    )
    response = client.post("/api/v1/settings/email/test")
    assert response.status_code == 503
    assert "Resend" in response.text and "re_synthetic_key" not in response.text


def test_resend_requires_key_before_domain_calls(tmp_path):
    app, client = setup(tmp_path)
    assert (
        client.post(
            "/api/v1/settings/email/domains", json={"name": "example.com"}
        ).status_code
        == 400
    )
    assert (
        client.get("/api/v1/settings/email/domains").status_code == 400
    )
