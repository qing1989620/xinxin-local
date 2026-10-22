"""Real native Caddy -> real isolated backend; no owner data or processes."""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

from app.uploads import MAX_BODY_BYTES
from app.files import MAX_UPLOAD

ROOT = Path(__file__).resolve().parents[2]


def test_all_gateway_configurations_match_upload_body_budget():
    for config in [ROOT / "Caddyfile.local", *(ROOT / "frontend/deploy").glob("Caddyfile*")]:
        assert f"max_size {MAX_BODY_BYTES}" in config.read_text(encoding="utf-8")
    assert "Get-XinxinFileHash $caddyfilePath" in (ROOT / "Start-Xinxin-Local.ps1").read_text(encoding="utf-8-sig")


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


@pytest.mark.skipif(sys.platform != "win32", reason="Native Windows integration; source configuration test runs on every platform")
def test_real_gateway_accepts_256_mib_and_rejects_one_byte_more(tmp_path):
    caddy = ROOT / "tools/caddy.exe"
    if not caddy.exists():
        pytest.skip("Install the project's native Caddy to exercise the gateway process")
    api_port, gateway_port = free_port(), free_port()
    env = os.environ | {"XINXIN_LOG_DIR": str(tmp_path / "logs"), "PYTHONUNBUFFERED": "1"}
    config = (ROOT / "Caddyfile.local").read_text(encoding="utf-8")
    config = "{\n admin off\n auto_https off\n}\n" + config.replace("http://:{$XINXIN_GATEWAY_PORT:8080}", f"http://127.0.0.1:{gateway_port}").replace("127.0.0.1:8010", f"127.0.0.1:{api_port}")
    config_path = tmp_path / "Caddyfile"
    config_path.write_text(config, encoding="utf-8")
    script = "from pathlib import Path; import sys,uvicorn; from app.config import Config; from app.main import create_app; uvicorn.run(create_app(Config(Path(sys.argv[1]),'synthetic-gateway-bootstrap')),host='127.0.0.1',port=int(sys.argv[2]),log_level='error')"
    processes = []
    with (tmp_path / "processes.log").open("wb") as log:
        try:
            processes.append(subprocess.Popen([sys.executable, "-c", script, str(tmp_path / "data"), str(api_port)], cwd=ROOT / "backend", env=env, stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW))
            processes.append(subprocess.Popen([str(caddy), "run", "--config", str(config_path), "--adapter", "caddyfile"], cwd=tmp_path, env=env, stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW))
            with httpx.Client(base_url=f"http://127.0.0.1:{gateway_port}", timeout=120, trust_env=False) as client:
                for _ in range(150):
                    try:
                        if client.get("/health").status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    time.sleep(.1)
                else:
                    pytest.fail("Isolated gateway/backend did not become ready")
                setup = client.post("/api/v1/auth/setup", json={"name": "SyntheticGatewayOwner", "password": "synthetic-gateway-password-123", "setup_code": "synthetic-gateway-bootstrap"})
                assert setup.status_code == 200, setup.text
                client.headers["Authorization"] = "Bearer " + setup.json()["token"]
                payload = tmp_path / "boundary.bin"
                with payload.open("wb") as stream:
                    stream.seek(MAX_UPLOAD - 1)
                    stream.write(b"\0")
                with payload.open("rb") as stream:
                    accepted = client.post("/api/v1/files", files={"file": ("synthetic-boundary.bin", stream, "application/octet-stream")})
                assert accepted.status_code == 200, accepted.text
                assert accepted.json()["size"] == MAX_UPLOAD
                assert client.delete(f"/api/v1/files/{accepted.json()['id']}").status_code == 200
                with payload.open("ab") as stream:
                    stream.write(b"\0")
                with payload.open("rb") as stream:
                    rejected = client.post("/api/v1/files", files={"file": ("synthetic-over-limit.bin", stream, "application/octet-stream")})
                assert rejected.status_code == 413, rejected.text
                assert client.get("/api/v1/files").json() == []
                assert not list((tmp_path / "data/files").iterdir())
        finally:
            # Only Popen handles created here are terminated; never kill by port.
            for process in reversed(processes):
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)
