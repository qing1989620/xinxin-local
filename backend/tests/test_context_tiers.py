import asyncio
import json
import threading

import httpx
import pytest

from app.agent import PlatformExecutor, TaskContext
from app.context import token_count
from test_platform import client, frames, wait_run


def test_context_tier_is_persistent_frozen_per_run_and_part_of_retry_identity(client):
    entered, release = threading.Event(), threading.Event()
    client.put("/api/v1/settings", json={"model_api_key": "offline-tier-key"})
    cid = client.post("/api/v1/conversations", json={"title": "tier fixture"}).json()["id"]
    assert client.get(f"/api/v1/conversations/{cid}").json()["context_window_tokens"] == 1048576
    assert client.put(f"/api/v1/conversations/{cid}/context", json={"context_window_tokens": 80000}).status_code == 200
    assert client.put(f"/api/v1/conversations/{cid}/context", json={"context_window_tokens": 1000000}).status_code == 422

    async def provider(request):
        entered.set()
        while not release.is_set():
            await asyncio.sleep(.01)
        return httpx.Response(200, content=frames(content="tier accepted").encode())

    client.app.state.manager.model_transport = httpx.MockTransport(provider)
    payload = {"conversation_id": cid, "task": "use selected tier", "request_key": "tier-retry", "context_window_tokens": 80000}
    run = client.post("/api/v1/runs", json=payload).json()
    try:
        assert entered.wait(3)
        assert run["context_window_tokens"] == 80000
        assert client.post("/api/v1/runs", json=payload).json()["id"] == run["id"]
        assert client.post("/api/v1/runs", json={**payload, "context_window_tokens": 300000}).status_code == 400
        assert client.put(f"/api/v1/conversations/{cid}/context", json={"context_window_tokens": 300000}).status_code == 409
    finally:
        release.set()
    result = wait_run(client, run["id"])
    assert result["status"] == "completed"
    assert json.loads(result["usage"])["context_window_tokens"] == 80000
    assert client.put(f"/api/v1/conversations/{cid}/context", json={"context_window_tokens": 300000}).status_code == 200
    resumed = client.post("/api/v1/runs", json={"conversation_id": cid, "task": "continue with new tier", "request_key": "tier-next"}).json()
    assert wait_run(client, resumed["id"])["context_window_tokens"] == 300000
    assert client.get(f"/api/v1/runs/{run['id']}").json()["context_window_tokens"] == 80000


def test_local_cancel_error_does_not_claim_an_unconfirmed_remote_stop():
    async def scenario():
        flag = threading.Event()
        executor = PlatformExecutor(cancelled=flag)

        def local_failure():
            flag.set()
            raise ValueError("local cancelled operation")

        await executor._async_dispatch("read_file", {}, local_failure, 60)
        await executor.drain()
        assert not executor.remote_stop_unconfirmed

    asyncio.run(scenario())


@pytest.mark.parametrize("tier", [80000, 300000, 1048576])
def test_actual_bpe_history_beyond_300k_survives_only_in_the_selected_full_window(tier):
    large = "context window proof is persistent.\n" * 70000
    measured = token_count(large)
    assert 300000 < measured < 1048576 - 32768
    compacted = []
    context = TaskContext("current goal", max_length=tier - 32768, on_compact=compacted.append)
    context.set_system_message("current permissions")
    context.messages.extend([
        {"role": "user", "content": "initial goal"},
        {"role": "assistant", "content": large},
    ])
    context.add_user_message("current goal")
    retained = any(item.get("content") == large for item in context.get_messages())
    assert retained is (tier == 1048576)
    assert bool(compacted) is (tier != 1048576)
    assert any(item.get("content") == "initial goal" for item in context.get_messages())
    assert any(item.get("content") == "current goal" for item in context.get_messages())
