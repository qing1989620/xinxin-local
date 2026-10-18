"""Live end-to-end run against a copy of the real data directory.

Copies only the small state (sqlite + vault key + skills), resets the owner
password inside the COPY, boots uvicorn on a spare port, logs in, submits one
tiny task and waits for the agent loop to finish. Nothing touches the real
data directory.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from app.auth import password_hash  # noqa: E402

PORT = 8021
source = BASE / "data"
target = BASE / ".qa-data" / f"live-{int(time.time())}"
target.mkdir(parents=True, exist_ok=True)
for name in ("xinxin.sqlite3", "vault.key", "bootstrap.code"):
    src = source / name
    if src.exists():
        shutil.copy2(src, target / name)
if (source / "skills").exists():
    shutil.copytree(source / "skills", target / "skills")

db = sqlite3.connect(target / "xinxin.sqlite3")
db.execute("UPDATE owner SET password=? WHERE id=1", (password_hash("live-smoke-password"),))
db.execute("DELETE FROM sessions")
db.commit()
db.close()

env = os.environ.copy()
env["XINXIN_DATA_DIR"] = str(target)
env["XINXIN_CORS_ORIGINS"] = "http://127.0.0.1:5182"
python = str(BASE / ".venv" / "Scripts" / "python.exe")
proc = subprocess.Popen(
    [python, "-X", "utf8", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(PORT), "--workers", "1", "--no-access-log"],
    cwd=str(BASE),
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)

BASE_URL = f"http://127.0.0.1:{PORT}"


def call(method: str, path: str, token: str = "", body=None, timeout=60):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE_URL + path, data=data, method=method,
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode() or "null")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()[:300]


try:
    for _ in range(120):
        try:
            if call("GET", "/health")[0] == 200:
                break
        except Exception:
            pass
        time.sleep(0.5)
    else:
        raise SystemExit("backend did not boot")

    status, result = call("POST", "/api/v1/auth/login", body={"name": "ui", "password": "live-smoke-password"})
    if status != 200:
        # the owner name in the real DB may differ
        con = sqlite3.connect(target / "xinxin.sqlite3")
        owner = con.execute("SELECT name FROM owner WHERE id=1").fetchone()[0]
        con.close()
        status, result = call("POST", "/api/v1/auth/login", body={"name": owner, "password": "live-smoke-password"})
    print("login:", status)
    token = result["token"]

    status, conversation = call("POST", "/api/v1/conversations", token, {"title": "live smoke"})
    cid = conversation["id"]
    print("conversation:", status, cid)

    payload = {
        "task": "请只回复两个字：正常。不要调用任何工具。",
        "conversation_id": cid,
        "permission": "read",
        "max_calls": 3,
        "max_seconds": 180,
        "max_total_tokens": 40000,
        "request_key": uuid.uuid4().hex,
        "allow_memory": False,
    }
    status, run = call("POST", "/api/v1/runs", token, payload, timeout=60)
    print("submit:", status, run if status != 200 else run.get("id"))
    run_id = run["id"] if isinstance(run, dict) else None
    if not run_id:
        raise SystemExit("no run id")

    deadline = time.time() + 240
    state = None
    while time.time() < deadline:
        status, detail = call("GET", f"/api/v1/runs/{run_id}", token)
        state = detail.get("status") if isinstance(detail, dict) else None
        if state in {"completed", "failed", "cancelled", "interrupted"}:
            break
        time.sleep(2)
    print("run status:", state)

    status, activity = call("GET", f"/api/v1/runs/{run_id}/activity", token)
    print("activity:", status)
    if isinstance(activity, dict):
        print("activity keys:", sorted(activity))
        print(json.dumps(activity, ensure_ascii=False)[:1200])

    con = sqlite3.connect(target / "xinxin.sqlite3")
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT kind,data FROM events WHERE run_id=? ORDER BY seq", (run_id,)
    ).fetchall()
    con.close()
    kinds = {}
    for row in rows:
        kinds[row["kind"]] = kinds.get(row["kind"], 0) + 1
    print("event kinds:", kinds)
    for row in rows:
        if row["kind"] == "skills":
            data = json.loads(row["data"])
            print("selected skills:", [s.get("id") for s in data.get("skills", [])], "learning:", data.get("learning_updates"))
        if row["kind"] in {"assistant.message", "message", "delta"}:
            print(row["kind"], ":", row["data"][:300])
    final = [json.loads(r["data"]) for r in rows if r["kind"] in {"assistant.message", "final", "answer"}]
    print("final chunks:", len(final))
    error = [json.loads(r["data"]) for r in rows if r["kind"] == "run.failed"]
    if error:
        print("run error:", json.dumps(error[-1], ensure_ascii=False)[:500])
finally:
    proc.terminate()
    try:
        out, _ = proc.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        out = ""
    tail = (out or "").strip().splitlines()[-6:]
    if tail:
        print("server tail:")
        for line in tail:
            print("  ", line[:200])
    print("data copy:", target)
