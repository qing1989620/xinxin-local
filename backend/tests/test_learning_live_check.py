"""No external calls: live diagnostic must reserve quota and keep traces private."""
import asyncio
import json
import os
import subprocess
import sys
from types import SimpleNamespace

import httpx
import pytest

from scripts.check_learning_http import BoundedTransport


def test_importing_live_http_helper_cannot_initialize_an_owner_database(tmp_path):
    result = subprocess.run([sys.executable, "-c", "import sys; import scripts.check_learning_http; assert 'app.main' not in sys.modules"],
                            env=os.environ | {"XINXIN_DATA_DIR": str(tmp_path)}, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "xinxin.sqlite3").exists()


def test_live_http_budget_counts_failure_and_never_records_keys_or_images(tmp_path, monkeypatch):
    ledger = tmp_path / "calls.private.json"
    ledger.write_text('{"calls":29,"tokens":0}', encoding="utf-8")
    args = SimpleNamespace(ledger=ledger, ledger_limit=30, max_calls=2, allow_host="api.deepseek.com")
    requests = []
    def response(request):
        requests.append(request)
        return httpx.Response(503, json={"error": "synthetic service failure"})
    monkeypatch.setattr(httpx, "AsyncHTTPTransport", lambda: httpx.MockTransport(response))
    transport = BoundedTransport(args, tmp_path)
    async def run():
        async with httpx.AsyncClient(transport=transport) as client:
            payload = {"messages": [{"role": "user", "content": [
                {"type": "text", "text": "synthetic source"},
                {"type": "image_url", "image_url": {"url": "synthetic private image"}}]}]}
            first = await client.post("https://api.deepseek.com/chat/completions", json=payload, headers={"Authorization": "Bearer synthetic-private-key"})
            assert first.status_code == 503
            with pytest.raises(RuntimeError, match="调用上限"):
                await client.post("https://api.deepseek.com/chat/completions", json=payload)
            with pytest.raises(RuntimeError, match="未授权"):
                await client.post("https://other.example/chat/completions", json=payload)
    asyncio.run(run())
    assert len(requests) == 1 and json.loads(ledger.read_text())["calls"] == 30
    trace = next(tmp_path.glob("http-trace-*.private.json")).read_text(encoding="utf-8")
    assert "synthetic source" in trace
    assert "synthetic-private-key" not in trace and "synthetic private image" not in trace
