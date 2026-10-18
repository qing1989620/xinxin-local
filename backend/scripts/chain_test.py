"""Full public chain: HTTPS tunnel -> Caddy -> backend, with real auth.

Boots a throw-away copy of the live data, a second Caddy on 8081 and a quick
Cloudflare tunnel, then walks the exact client path: login, CORS preflight,
upload/download, run submission, SSE replay until the end event.

Nothing touches the live data directory.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import uuid
from pathlib import Path

import httpx

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parent
RUNTIME = ROOT / ".runtime"
PYTHON = BASE / ".venv/Scripts/python.exe"
CADDY = ROOT / "tools/caddy.exe"
CLOUDFLARED = ROOT / "tools/cloudflared.exe"

sys.path.insert(0, str(BASE))
from app.auth import password_hash  # noqa: E402

BACKEND_PORT, GATEWAY_PORT = 8031, 8081
PASSWORD = "chain-test-password"

target = BASE / ".qa-data" / f"chain-{int(time.time())}"
target.mkdir(parents=True, exist_ok=True)
if (BASE / "data" / "xinxin.sqlite3").exists():
    src_db = sqlite3.connect(BASE / "data" / "xinxin.sqlite3")
    dst_db = sqlite3.connect(target / "xinxin.sqlite3")
    try:
        src_db.backup(dst_db)
    finally:
        dst_db.close()
        src_db.close()
for name in ("vault.key", "bootstrap.code"):
    if (BASE / "data" / name).exists():
        shutil.copy2(BASE / "data" / name, target / name)
if (BASE / "data" / "skills").exists():
    shutil.copytree(BASE / "data" / "skills", target / "skills")
db = sqlite3.connect(target / "xinxin.sqlite3")
db.execute("UPDATE owner SET password=? WHERE id=1", (password_hash(PASSWORD),))
db.execute("DELETE FROM sessions")
db.commit()
db.close()

caddyfile = RUNTIME / "chain-Caddyfile"
caddyfile.write_text(
    """{
  admin off
}
http://:%d {
  @api path /api/* /health
  handle @api {
    reverse_proxy 127.0.0.1:%d {
      flush_interval -1
    }
  }
  handle {
    respond "chain-ok" 200
  }
}
"""
    % (GATEWAY_PORT, BACKEND_PORT),
    encoding="utf-8",
)

env = os.environ.copy()
env["XINXIN_DATA_DIR"] = str(target)
env["XINXIN_CORS_ORIGINS"] = f"http://127.0.0.1:{GATEWAY_PORT}"
env["XINXIN_SKILLNET_MODE"] = "fabric"
env["XINXIN_SKILLNET_RERANK"] = "1"
env["XDG_DATA_HOME"] = str(RUNTIME / "caddy-data")
env.pop("XINXIN_HTTP_PROXY", None)

backend = caddy = tunnel = None
tunnel_log = RUNTIME / "chain-tunnel.log"
failures: list[str] = []


def step(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f" | {detail}"))
    if not ok:
        failures.append(f"{name}: {detail}")


def wait_http(url, timeout=90):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if httpx.get(url, timeout=5, trust_env=False).status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


try:
    backend = subprocess.Popen(
        [str(PYTHON), "-X", "utf8", "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", str(BACKEND_PORT), "--workers", "1",
         "--no-access-log"],
        cwd=str(BASE), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
    )
    step("backend boot", wait_http(f"http://127.0.0.1:{BACKEND_PORT}/health", 120))

    caddy = subprocess.Popen(
        [str(CADDY), "run", "--config", str(caddyfile), "--adapter", "caddyfile"],
        cwd=str(ROOT), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
    )
    step("gateway boot", wait_http(f"http://127.0.0.1:{GATEWAY_PORT}/health", 30))

    if tunnel_log.exists():
        tunnel_log.unlink()
    tunnel = subprocess.Popen(
        [str(CLOUDFLARED), "tunnel", "--url", f"http://127.0.0.1:{GATEWAY_PORT}",
         "--no-autoupdate"],
        cwd=str(ROOT), env=env, stdout=open(tunnel_log, "w", encoding="utf-8", errors="ignore"),
        stderr=subprocess.STDOUT,
    )
    public = ""
    deadline = time.time() + 90
    while time.time() < deadline and not public:
        time.sleep(1)
        try:
            text = tunnel_log.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        match = re.search(r"https://[A-Za-z0-9\-]+\.trycloudflare\.com", text)
        if match:
            public = match.group(0)
    step("tunnel url", bool(public), "no trycloudflare url in log")
    if not public:
        raise SystemExit(1)
    print("public:", public)

    # Mirror Start-Tunnel.ps1: once the public origin exists, whitelist it and
    # restart the backend so the running process serves the new allowlist.
    env["XINXIN_CORS_ORIGINS"] = f"http://127.0.0.1:{GATEWAY_PORT},{public}"
    backend.terminate()
    backend.wait(timeout=20)
    backend = subprocess.Popen(
        [str(PYTHON), "-X", "utf8", "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", str(BACKEND_PORT), "--workers", "1",
         "--no-access-log"],
        cwd=str(BASE), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
    )
    step(
        "backend restart with public origin",
        wait_http(f"http://127.0.0.1:{BACKEND_PORT}/health", 120),
    )

    step("public health", wait_http(f"{public}/health", 90))
    client = httpx.Client(base_url=public, timeout=60, trust_env=False)

    owner = sqlite3.connect(target / "xinxin.sqlite3")
    name = owner.execute("SELECT name FROM owner WHERE id=1").fetchone()[0]
    owner.close()
    login = client.post("/api/v1/auth/login", json={"name": name, "password": PASSWORD})
    step("login over https", login.status_code == 200, login.text[:200])
    token = login.json().get("token", "")
    auth = {"Authorization": f"Bearer {token}"}

    preflight = client.options(
        "/api/v1/files",
        headers={
            "Origin": public,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,x-upload-id",
        },
    )
    step(
        "cors preflight",
        preflight.status_code == 200 and preflight.headers.get("access-control-allow-origin") == public,
        f"{preflight.status_code} {preflight.headers.get('access-control-allow-origin')}",
    )

    payload = b"date,value\n2026-01-01,1\n2026-01-02,3\n"
    filename = "链路测试.csv"
    upload = client.post(
        "/api/v1/files",
        headers={**auth, "X-Upload-ID": "chain-" + uuid.uuid4().hex[:12]},
        files={"file": (filename, payload, "text/csv")},
    )
    step("upload over https", upload.status_code == 200, upload.text[:200])
    file_id = upload.json().get("id", "") if upload.status_code == 200 else ""
    if file_id:
        download = client.get(
            f"/api/v1/files/{file_id}/download",
            headers={**auth, "Origin": public},
        )
        step(
            "download roundtrip",
            download.status_code == 200 and download.content == payload,
            f"{download.status_code} {len(download.content)}",
        )
        disposition = download.headers.get("content-disposition", "")
        step(
            "non-ascii filename",
            "attachment" in disposition and "filename*" in disposition,
            disposition[:200],
        )
        step(
            "exposed content-disposition",
            "content-disposition" in download.headers.get("access-control-expose-headers", "").lower(),
            download.headers.get("access-control-expose-headers", ""),
        )
        anonymous = client.get(
            "/api/v1/files",
            headers={"Origin": public},
        )
        step(
            "401 still carries cors",
            anonymous.status_code == 401
            and anonymous.headers.get("access-control-allow-origin") == public,
            f"{anonymous.status_code} {anonymous.headers.get('access-control-allow-origin')}",
        )

    conversation = client.post("/api/v1/conversations", headers=auth, json={"title": "chain"})
    cid = conversation.json()["id"]
    submit = client.post(
        "/api/v1/runs",
        headers=auth,
        json={
            "task": "请只回复四个字：链路正常。不要调用工具。",
            "conversation_id": cid,
            "permission": "read",
            "max_calls": 4,
            "max_seconds": 180,
            "request_key": "chain-" + uuid.uuid4().hex,
        },
    )
    step("submit run", submit.status_code == 200, submit.text[:300])
    run_id = submit.json().get("id", "")
    kinds: dict[str, int] = {}
    ended = False
    last_seq = 0
    if run_id:
        try:
            with client.stream("GET", f"/api/v1/runs/{run_id}/events", headers=auth) as stream:
                for line in stream.iter_lines():
                    if line.startswith("event: end"):
                        ended = True
                        break
                    if not line.startswith("data: "):
                        continue
                    try:
                        event = json.loads(line[6:])
                    except ValueError:
                        continue
                    kinds[event.get("kind", "?")] = kinds.get(event.get("kind", "?"), 0) + 1
                    last_seq = max(last_seq, int(event.get("seq", 0)))
        except Exception as exc:  # noqa: BLE001
            step("sse stream", False, str(exc))
        step("sse end marker", ended, str(kinds))
        if ended and last_seq:
            replay_seqs = []
            with client.stream(
                "GET",
                f"/api/v1/runs/{run_id}/events",
                headers={**auth, "Last-Event-ID": str(last_seq)},
            ) as replay:
                for line in replay.iter_lines():
                    if line.startswith("event: end"):
                        break
                    if line.startswith("data: "):
                        try:
                            replay_seqs.append(json.loads(line[6:]).get("seq", 0))
                        except ValueError:
                            pass
            step(
                "sse resume from cursor",
                all(seq > last_seq for seq in replay_seqs),
                f"last={last_seq} replayed={replay_seqs[:5]}",
            )
        step("sse core events", all(k in kinds for k in ("started", "skills", "finished")), str(kinds))

    detail = client.get(f"/api/v1/runs/{run_id}", headers=auth).json() if run_id else {}
    step("run completed", detail.get("status") == "completed", f"{detail.get('status')} {detail.get('error','')[:200]}")

    skills_event = None
    if run_id:
        con = sqlite3.connect(target / "xinxin.sqlite3")
        row = con.execute(
            "SELECT data FROM events WHERE run_id=? AND kind='skills' ORDER BY seq LIMIT 1",
            (run_id,),
        ).fetchone()
        con.close()
        if row:
            skills_event = json.loads(row[0])
    step(
        "fabric rerank ran",
        bool(skills_event and skills_event.get("components", {}).get("llm_rerank")),
        json.dumps((skills_event or {}).get("components", {}))[:200],
    )
    if file_id:
        removed = client.delete(f"/api/v1/files/{file_id}", headers=auth)
        step("delete uploaded file", removed.status_code == 200, removed.text[:120])
    client.close()
finally:
    for proc in (tunnel, caddy, backend):
        if proc and proc.poll() is None:
            proc.terminate()
    time.sleep(1)
    for proc in (tunnel, caddy, backend):
        if proc and proc.poll() is None:
            proc.kill()
    if tunnel_log.exists():
        tail = tunnel_log.read_text(encoding="utf-8", errors="ignore")[-1200:]
        print("tunnel tail:", tail.replace("\n", " ")[-400:])
    shutil.rmtree(target, ignore_errors=True)
    print("failures:", len(failures))
    for item in failures:
        print(" -", item)
    sys.exit(1 if failures else 0)
