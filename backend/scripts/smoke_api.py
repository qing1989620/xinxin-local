"""API smoke test on a throw-away data dir.

Boots the real app through TestClient, initializes an owner account, then
walks every read endpoint plus a few writes. Prints one line per endpoint so a
failure is obvious instead of hiding inside a big assertion dump.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

data = BASE / ".qa-data" / f"smoke-{int(time.time())}"
data.mkdir(parents=True, exist_ok=True)
os.environ["XINXIN_DATA_DIR"] = str(data)
os.environ["XINXIN_CORS_ORIGINS"] = "http://localhost:5180"

from fastapi.testclient import TestClient  # noqa: E402
from app.config import Config  # noqa: E402
from app.main import create_app  # noqa: E402

cfg = Config.from_env()
app = create_app(cfg)
client = TestClient(app)

failures: list[str] = []


def call(method: str, path: str, expect=(200,), **kwargs):
    started = time.perf_counter()
    try:
        response = client.request(method, path, **kwargs)
    except Exception as exc:  # noqa: BLE001
        failures.append(f"{method} {path} -> EXC {type(exc).__name__}: {exc}")
        print(f"FAIL {method:6} {path:55} EXC {type(exc).__name__}: {exc}")
        return None
    elapsed = (time.perf_counter() - started) * 1000
    ok = response.status_code in expect
    body = response.text[:160].replace("\n", " ")
    print(
        f"{'ok  ' if ok else 'FAIL'} {method:6} {path:55} "
        f"{response.status_code} {elapsed:7.1f}ms {body if not ok else ''}"
    )
    if not ok:
        failures.append(f"{method} {path} -> {response.status_code} {body}")
    try:
        return response.json()
    except Exception:  # noqa: BLE001
        return response.text


status = call("GET", "/api/v1/auth/status")
code = cfg.data_dir / "bootstrap.code"
token = ""
if status and not status.get("configured"):
    setup_code = code.read_text(encoding="utf-8").strip() if code.exists() else ""
    result = call(
        "POST",
        "/api/v1/auth/setup",
        json={"name": "smoke", "password": "smoke-test-password", "setup_code": setup_code},
    )
    token = (result or {}).get("token", "")
else:
    # A pre-existing owner is not a failure; log in with the smoke password if possible.
    result = call(
        "POST",
        "/api/v1/auth/login",
        json={"name": "smoke", "password": "smoke-test-password"},
        expect=(200, 401),
    )
    token = (result or {}).get("token", "")

headers = {"Authorization": f"Bearer {token}"} if token else {}
print("token:", "yes" if token else "no")

GETS = [
    "/api/v1/auth/me",
    "/api/v1/dashboard",
    "/api/v1/conversations",
    "/api/v1/runs",
    "/api/v1/skills",
    "/api/v1/skills/status",
    "/api/v1/skills/graph",
    "/api/v1/skills/network-model",
    "/api/v1/skills/activity",
    "/api/v1/skills?q=%E7%94%BB%E5%9B%BE",
    "/api/v1/images/providers",
    "/api/v1/images",
    "/api/v1/records?kind=article",
    "/api/v1/files",
    "/api/v1/files/search?q=test",
    "/api/v1/servers",
    "/api/v1/memories",
    "/api/v1/settings",
    "/api/v1/settings/email",
    "/api/v1/tools/gallery",
    "/api/v1/schedules",
    "/api/v1/audit",
]
for path in GETS:
    call("GET", path, headers=headers)

skills = call("GET", "/api/v1/skills", headers=headers)
if isinstance(skills, list) and skills:
    first = skills[0]["id"]
    call("GET", f"/api/v1/skills/{first}", headers=headers)

search = call("GET", "/api/v1/skills?q=%E6%8A%80%E8%83%BD", headers=headers)
if isinstance(search, dict) and search.get("skills"):
    top = search["skills"][0]["id"]
    print("top skill:", top, search["skills"][0].get("score"))
    detail = call("GET", f"/api/v1/skills/{top}", headers=headers)
    print("  detail keys:", sorted(detail)[:8] if isinstance(detail, dict) else type(detail).__name__)

memory = call(
    "POST",
    "/api/v1/memories",
    headers=headers,
    json={"content": "smoke test memory", "category": "fact"},
)
if isinstance(memory, dict) and memory.get("id"):
    call("PUT", f"/api/v1/memories/{memory['id']}", headers=headers, json={"content": "smoke test memory v2"})
    call("DELETE", f"/api/v1/memories/{memory['id']}", headers=headers)

record = call(
    "POST",
    "/api/v1/records?kind=article",
    headers=headers,
    json={"kind": "article", "payload": {"title": "smoke", "body": "hello"}},
)
if isinstance(record, dict) and record.get("id"):
    call(
        "PUT",
        f"/api/v1/records/{record['id']}",
        headers=headers,
        json={"kind": "article", "payload": {"title": "smoke2"}},
    )
    call("DELETE", f"/api/v1/records/{record['id']}", headers=headers)

conversation = call("POST", "/api/v1/conversations", headers=headers, json={"title": "smoke"})
if isinstance(conversation, dict) and conversation.get("id"):
    cid = conversation["id"]
    call("GET", f"/api/v1/conversations/{cid}", headers=headers)
    call("PUT", f"/api/v1/conversations/{cid}", headers=headers, json={"title": "smoke2"})
    call("GET", f"/api/v1/conversations/{cid}/deletion-preview", headers=headers)
    call("DELETE", f"/api/v1/conversations/{cid}", headers=headers)

call("GET", "/health")
call("GET", "/openapi.json")

print()
print(f"failures: {len(failures)}")
for item in failures:
    print(" -", item)
shutil.rmtree(data, ignore_errors=True)
sys.exit(1 if failures else 0)
