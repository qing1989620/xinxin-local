"""Real Windows launcher checks, on isolated ports/data/process manifests."""

import json
import os
import shutil
import socket
import sqlite3
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
POWERSHELL = shutil.which("powershell.exe")


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


@pytest.mark.skipif(os.name != "nt" or not POWERSHELL, reason="Windows desktop launcher")
def test_launcher_reuses_current_build_updates_owned_services_and_preserves_active_tasks(tmp_path):
    if not (ROOT / "backend/.venv/Scripts/python.exe").exists() or not (ROOT / "frontend/node_modules/vite/bin/vite.js").exists():
        pytest.skip("Local runtime dependencies unavailable")
    runtime, data = tmp_path / "runtime", tmp_path / "data"
    backend_port, frontend_port = free_port(), free_port()
    manifest = runtime / "processes.json"
    command = [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "Start-Xinxin-Local.ps1"),
               "-NoBrowser", "-NoGateway", "-BackendPort", str(backend_port), "-FrontendPort", str(frontend_port),
               "-RuntimeDirectory", str(runtime), "-DataDirectory", str(data)]

    def start(selected_data=None):
        # Detached Windows children can inherit capture pipes. Use files so
        # communicate() does not wait for a long-running service to close them.
        out, err = tmp_path / "launcher.out.txt", tmp_path / "launcher.err.txt"
        with out.open("wb") as stdout, err.open("wb") as stderr:
            requested = command if selected_data is None else command[:-1] + [str(selected_data)]
            result = subprocess.run(requested, cwd=ROOT, stdout=stdout, stderr=stderr, timeout=150)
        return subprocess.CompletedProcess(command, result.returncode, out.read_text(encoding="utf-8", errors="replace"), err.read_text(encoding="utf-8", errors="replace"))

    def entries():
        return {item["role"]: item for item in json.loads(manifest.read_text(encoding="utf-8-sig"))["services"]}

    def mark_stale(role):
        content = json.loads(manifest.read_text(encoding="utf-8-sig"))
        for item in content["services"]:
            if item["role"] == role:
                item["fingerprint"] = "synthetic-older-build"
        manifest.write_text(json.dumps(content), encoding="utf-8-sig")

    try:
        first = start()
        assert first.returncode == 0, first.stdout + first.stderr
        before = entries()
        assert before["backend"]["fingerprint"] and before["frontend"]["fingerprint"]
        # Legacy manifests do not have a port; the listener may be the
        # Windows venv launcher's child rather than the recorded parent PID.
        without_port = json.loads(manifest.read_text(encoding="utf-8-sig"))
        for item in without_port["services"]:
            item.pop("port")
        # UTF-8 without a BOM is also valid; Chinese data paths must not be
        # interpreted as the Windows ANSI code page by PowerShell 5.1.
        manifest.write_text(json.dumps(without_port, ensure_ascii=False), encoding="utf-8")
        assert start().returncode == 0
        assert {k: v["id"] for k, v in entries().items()} == {k: v["id"] for k, v in before.items()}

        # Configuration identity matters even when the code build is current.
        mismatch = start(tmp_path / "other-data")
        assert mismatch.returncode != 0 and "data directory differs" in mismatch.stderr
        assert entries()["backend"]["id"] == before["backend"]["id"]
        known_manifest = manifest.read_bytes()
        unknown = json.loads(known_manifest.decode("utf-8-sig"))
        for item in unknown["services"]:
            if item["role"] == "backend":
                item.pop("data_directory")
        manifest.write_text(json.dumps(unknown), encoding="utf-8-sig")
        uncertain = start()
        assert uncertain.returncode != 0 and "Cannot verify the managed backend data directory" in uncertain.stderr
        assert entries()["backend"]["id"] == before["backend"]["id"]
        manifest.write_bytes(known_manifest)

        mark_stale("backend")
        with sqlite3.connect(data / "xinxin.sqlite3") as db:
            db.execute("INSERT INTO runs(id,conversation_id,task,status,permission,max_calls,max_seconds,created,updated) VALUES('synthetic-running','synthetic','synthetic','running','read',1,60,1,1)")
        changed_data = start(tmp_path / "other-data")
        assert changed_data.returncode != 0 and "data directory differs" in changed_data.stderr
        assert entries()["backend"]["id"] == before["backend"]["id"]
        blocked = start()
        assert blocked.returncode != 0 and "active tasks" in blocked.stderr
        assert entries()["backend"]["id"] == before["backend"]["id"]
        with sqlite3.connect(data / "xinxin.sqlite3") as db:
            db.execute("DELETE FROM runs WHERE id='synthetic-running'")

        updated = start()
        assert updated.returncode == 0, updated.stdout + updated.stderr
        after = entries()
        assert after["backend"]["id"] != before["backend"]["id"]
        assert after["frontend"]["id"] == before["frontend"]["id"]
        mark_stale("frontend")
        refreshed = start()
        assert refreshed.returncode == 0, refreshed.stdout + refreshed.stderr
        assert entries()["frontend"]["id"] != after["frontend"]["id"]
        assert entries()["backend"]["id"] == after["backend"]["id"]
        # A crashed process with a stale running row must recover at startup.
        with sqlite3.connect(data / "xinxin.sqlite3") as db:
            db.execute("INSERT INTO runs(id,conversation_id,task,status,permission,max_calls,max_seconds,created,updated) VALUES('crashed-task','synthetic','synthetic','running','read',1,60,1,1)")
        stopped_backend = subprocess.run(["taskkill.exe", "/PID", str(entries()["backend"]["id"]), "/T", "/F"], capture_output=True, timeout=15)
        assert stopped_backend.returncode == 0
        recovered = start()
        assert recovered.returncode == 0, recovered.stdout + recovered.stderr
        with sqlite3.connect(data / "xinxin.sqlite3") as db:
            assert db.execute("SELECT status FROM runs WHERE id='crashed-task'").fetchone()[0] == "interrupted"
    finally:
        # Stop only process identities recorded by this test's dedicated manifest.
        if manifest.exists():
            script = """param([string]$Manifest)
$saved = Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json
foreach($entry in $saved.services){
  $instance=Get-Process -Id $entry.id -ErrorAction SilentlyContinue
  if($instance -and $instance.StartTime.ToUniversalTime().Ticks -eq [long]$entry.start_ticks){
    & (Join-Path $env:SystemRoot 'System32/taskkill.exe') /PID $instance.Id /T /F | Out-Null
  }
}
"""
            cleanup = tmp_path / "stop-fixture.ps1"
            cleanup.write_text(script, encoding="utf-8-sig")
            stopped = subprocess.run([POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(cleanup), "-Manifest", str(manifest)], capture_output=True, timeout=30)
            assert stopped.returncode == 0
