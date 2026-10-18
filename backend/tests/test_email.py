import time
import threading
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.main import create_app
from app.config import Config


def setup(tmp_path, monkeypatch):
    app = create_app(Config(tmp_path, "synthetic-bootstrap"))
    client = TestClient(app)
    owner = client.post(
        "/api/v1/auth/setup",
        json={
            "name": "LocalOwner",
            "password": "synthetic-password-123",
            "setup_code": "synthetic-bootstrap",
        },
    ).json()
    client.headers["Authorization"] = "Bearer " + owner["token"]
    mail = app.state.mail
    sent = []
    monkeypatch.setattr(
        mail, "_send", lambda email, code, scene: sent.append((email, code, scene))
    )
    assert (
        client.put(
            "/api/v1/settings/email",
            json={
                "email": "owner@example.com",
                "smtp_password": "synthetic-smtp-secret",
            },
        ).status_code
        == 200
    )
    return app, client, sent


def test_codes_are_private_persistent_purpose_bound_single_use(tmp_path, monkeypatch):
    app, client, sent = setup(tmp_path, monkeypatch)
    assert (
        client.post(
            "/api/v1/auth/email/code", json={"email": "other@example.com"}
        ).status_code
        == 200
    )
    assert not sent
    payload = {"email": "OWNER@example.com", "scene": "login"}
    assert client.post("/api/v1/auth/email/code", json=payload).status_code == 200
    code = sent[0][1]
    row = app.state.store.one("SELECT * FROM email_codes")
    assert code not in row["digest"] and len(row["digest"]) == 64
    assert client.post("/api/v1/auth/email/code", json=payload).status_code == 429
    restarted = TestClient(create_app(Config(tmp_path, "synthetic-bootstrap")))
    assert restarted.post("/api/v1/auth/email/code", json=payload).status_code == 429
    assert (
        client.post(
            "/api/v1/auth/email/reset",
            json={
                "email": "owner@example.com",
                "code": code,
                "password": "replacement-password",
            },
        ).status_code
        == 400
    )
    response = client.post(
        "/api/v1/auth/email/login", json={"email": "owner@example.com", "code": code}
    )
    assert response.status_code == 200 and response.json()["name"] == "LocalOwner"
    assert (
        client.post(
            "/api/v1/auth/email/login",
            json={"email": "owner@example.com", "code": code},
        ).status_code
        == 400
    )
    assert "synthetic-smtp-secret" not in client.get("/api/v1/settings/email").text
    assert client.post("/api/v1/auth/register", json={}).status_code == 404


def test_wrong_codes_exhaust_attempts_and_expiry(tmp_path, monkeypatch):
    app, client, sent = setup(tmp_path, monkeypatch)
    client.post("/api/v1/auth/email/code", json={"email": "owner@example.com"})
    code = sent[0][1]
    wrong = "111111" if code != "111111" else "222222"
    for _ in range(5):
        assert (
            client.post(
                "/api/v1/auth/email/login",
                json={"email": "owner@example.com", "code": wrong},
            ).status_code
            == 400
        )
    row = app.state.store.one("SELECT attempts,used FROM email_codes")
    assert row == {"attempts": 5, "used": 1}
    assert (
        client.post(
            "/api/v1/auth/email/login",
            json={"email": "owner@example.com", "code": code},
        ).status_code
        == 400
    )
    app.state.store.execute(
        "UPDATE email_codes SET created=?,expires=?,used=0,attempts=0",
        (time.time() - 601, time.time() - 1),
    )
    assert (
        client.post(
            "/api/v1/auth/email/login",
            json={"email": "owner@example.com", "code": code},
        ).status_code
        == 400
    )


def test_email_reset_revokes_sessions_preserves_password_spaces(tmp_path, monkeypatch):
    app, client, sent = setup(tmp_path, monkeypatch)
    client.post(
        "/api/v1/auth/email/code", json={"email": "owner@example.com", "scene": "reset"}
    )
    password = "  replacement-password  "
    response = client.post(
        "/api/v1/auth/email/reset",
        json={"email": "owner@example.com", "code": sent[0][1], "password": password},
    )
    assert response.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401
    assert (
        client.post(
            "/api/v1/auth/login", json={"name": "LocalOwner", "password": password}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"name": "LocalOwner", "password": password.strip()},
        ).status_code
        == 401
    )


def test_delivery_failure_never_exposes_smtp_secret(tmp_path, monkeypatch):
    app, client, sent = setup(tmp_path, monkeypatch)

    def fail(*_):
        raise RuntimeError("provider exposed synthetic-smtp-secret")

    monkeypatch.setattr(app.state.mail, "_send", fail)
    response = client.post(
        "/api/v1/auth/email/code", json={"email": "owner@example.com"}
    )
    assert response.status_code == 503 and "synthetic-smtp-secret" not in response.text
    assert app.state.store.one("SELECT used FROM email_codes")["used"] == 1
    response = client.put(
        "/api/v1/settings/email",
        json={"email": "owner@example.com", "smtp_password": "synthetic\nsecret"},
    )
    assert response.status_code == 422 and "synthetic" not in response.text


def test_parallel_code_consumption_has_one_winner(tmp_path, monkeypatch):
    app, client, sent = setup(tmp_path, monkeypatch)
    client.post("/api/v1/auth/email/code", json={"email": "owner@example.com"})
    barrier = threading.Barrier(2)

    def consume(_):
        barrier.wait()
        return client.post(
            "/api/v1/auth/email/login",
            json={"email": "owner@example.com", "code": sent[0][1]},
        ).status_code

    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(consume, range(2))) == [200, 400]


def test_unconfigured_mail_reports_unavailable_without_claiming_delivery(tmp_path):
    app = create_app(Config(tmp_path, "synthetic-bootstrap"))
    client = TestClient(app)
    assert client.get("/api/v1/auth/status").json()["email_enabled"] is False
    assert (
        client.post(
            "/api/v1/auth/email/code", json={"email": "owner@example.com"}
        ).status_code
        == 503
    )
    assert client.get("/api/v1/settings/email").status_code == 401


def test_smtp_uses_one_tls_and_credentials_snapshot_during_config_change(
    tmp_path, monkeypatch
):
    from app.mail import MailCodes
    import app.mail as mail_module

    app, client, sent = setup(tmp_path, monkeypatch)
    config = {
        "email": "owner@example.com",
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_mode": "starttls",
        "smtp_username": "owner@example.com",
        "smtp_password": "synthetic-smtp-secret",
    }
    app.state.mail.configure(config)
    observed = []

    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            self.tls = False
            app.state.mail.configure(
                {
                    **config,
                    "smtp_host": "other.example.com",
                    "smtp_mode": "ssl",
                    "smtp_password": "replacement-synthetic-secret",
                }
            )

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def starttls(self, context):
            assert context.check_hostname
            self.tls = True

        def login(self, username, password):
            assert self.tls
            observed.append((username, password))

        def send_message(self, message):
            pass

    monkeypatch.setattr(mail_module.smtplib, "SMTP", FakeSMTP)
    MailCodes._send(app.state.mail, "owner@example.com", "123456", "login")
    assert observed == [("owner@example.com", "synthetic-smtp-secret")]
