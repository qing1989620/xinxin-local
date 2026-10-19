"""Local address book: LAN stays stable, tunnel values are validated."""

import json

import pytest
from fastapi.testclient import TestClient

from app.config import Config
from app.main import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    (runtime / "addresses.json").write_text(
        json.dumps(
            {
                "local": "http://127.0.0.1:5180",
                "lan": "http://10.0.0.7:8080",
                "gateway_port": 8080,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("XINXIN_RUNTIME_DIR", str(runtime))
    application = create_app(Config(tmp_path / "data", "network-bootstrap"))
    with TestClient(application) as client:
        token = client.post(
            "/api/v1/auth/setup",
            json={
                "name": "owner",
                "password": "network-test-password",
                "setup_code": "network-bootstrap",
            },
        ).json()["token"]
        client.headers["Authorization"] = "Bearer " + token
        yield client, runtime


def test_lan_address_needs_no_server(client):
    api, _runtime = client
    data = api.get("/api/v1/network").json()
    assert data["local"] == "http://127.0.0.1:5180"
    assert data["lan"] == "http://10.0.0.7:8080"
    assert data["public"] == ""
    assert data["server_required"] is False


def test_public_address_is_read_when_present(client):
    api, runtime = client
    (runtime / "public-url.txt").write_text(
        "https://demo.trycloudflare.com\n", encoding="utf-8"
    )
    data = api.get("/api/v1/network").json()
    assert data["public"] == "https://demo.trycloudflare.com"
    assert data["public_updated"]


def test_address_book_tolerates_bom(client):
    api, runtime = client
    (runtime / "addresses.json").write_text(
        json.dumps(
            {
                "local": "http://127.0.0.1:5180",
                "lan": "http://10.0.0.9:8080",
                "gateway_port": 8080,
            }
        ),
        encoding="utf-8-sig",
    )
    # A BOM must not make the saved LAN value unreadable (it would silently
    # fall back to adapter detection and could pick the wrong interface).
    assert api.get("/api/v1/network").json()["lan"] == "http://10.0.0.9:8080"


def test_public_address_tolerates_bom(client):
    api, runtime = client
    # Windows PowerShell writes BOM-marked text by default; the reader must not
    # treat the marker as part of the scheme.
    (runtime / "public-url.txt").write_text(
        "https://bom.trycloudflare.com\n", encoding="utf-8-sig"
    )
    assert api.get("/api/v1/network").json()["public"] == "https://bom.trycloudflare.com"


@pytest.mark.parametrize(
    "value",
    [
        "http://demo.trycloudflare.com",
        "https://user:pass@demo.trycloudflare.com",
        "https://demo.trycloudflare.com/?x=1",
        "javascript:alert(1)",
    ],
)
def test_unsafe_public_values_are_ignored(client, value):
    api, runtime = client
    (runtime / "public-url.txt").write_text(value, encoding="utf-8")
    assert api.get("/api/v1/network").json()["public"] == ""


def test_network_requires_login(tmp_path):
    application = create_app(Config(tmp_path / "data", "network-bootstrap"))
    with TestClient(application) as api:
        api.post(
            "/api/v1/auth/setup",
            json={
                "name": "owner",
                "password": "network-test-password",
                "setup_code": "network-bootstrap",
            },
        )
        assert api.get("/api/v1/network").status_code == 401
