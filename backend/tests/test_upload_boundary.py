import asyncio
import io
import threading

from fastapi import UploadFile
from fastapi.testclient import TestClient
from starlette.datastructures import UploadFile as ParsedFile

from app.config import Config
from app.main import create_app
from app.uploads import UploadGuard


def test_unauthorized_and_oversized_ingress_never_reaches_multipart_spooling(
    tmp_path, monkeypatch
):
    from app import uploads

    monkeypatch.setenv("XINXIN_SKILL_ENCODER", "lexical")
    writes = []
    original = ParsedFile.write

    async def tracked(file, data):
        writes.append(len(data))
        await original(file, data)

    monkeypatch.setattr(ParsedFile, "write", tracked)
    with TestClient(create_app(Config(tmp_path, "setup-test-code"))) as client:
        assert (
            client.post(
                "/api/v1/files", files={"file": ("private.txt", b"x" * 2097152)}
            ).status_code
            == 401
        )
        assert not writes
        setup = client.post(
            "/api/v1/auth/setup",
            json={
                "name": "owner",
                "password": "test-private-password",
                "setup_code": "setup-test-code",
            },
        ).json()
        client.headers["Authorization"] = "Bearer " + setup["token"]
        monkeypatch.setattr(uploads, "MAX_BODY_BYTES", 2048)
        assert (
            client.post(
                "/api/v1/files", files={"file": ("large.txt", b"x" * 3000)}
            ).status_code
            == 413
        )
        assert not writes
        boundary = "testboundary"
        body = (
            b'--testboundary\r\nContent-Disposition: form-data; name="file"; filename="stream.txt"\r\n\r\n'
            + b"x" * 3000
            + b"\r\n--testboundary--\r\n"
        )
        response = client.post(
            "/api/v1/files",
            content=(body[i : i + 256] for i in range(0, len(body), 256)),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        assert response.status_code == 413
        assert not writes and not client.get("/api/v1/files").json()
        assert not list((tmp_path / "files").iterdir())


def test_ingress_concurrency_slot_is_acquired_before_the_application_reads_body():
    async def scenario():
        entered, peak = 0, 0
        release = asyncio.Event()

        class Auth:
            def require(self, _):
                return True

        async def application(scope, receive, send):
            nonlocal entered, peak
            entered += 1
            peak = max(peak, entered)
            await release.wait()
            await receive()
            entered -= 1

        gate = UploadGuard(application, Auth())

        async def request():
            async def receive():
                return {"type": "http.request", "body": b"small", "more_body": False}

            async def send(_):
                pass

            await gate(
                {
                    "type": "http",
                    "method": "POST",
                    "path": "/api/v1/files",
                    "headers": [],
                },
                receive,
                send,
            )

        tasks = [asyncio.create_task(request()) for _ in range(3)]
        for _ in range(10):
            await asyncio.sleep(0)
        assert entered == 2 and peak == 2
        release.set()
        await asyncio.gather(*tasks)
        assert peak == 2

    asyncio.run(scenario())


def test_cancelled_upload_keeps_source_open_until_the_thread_finishes(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("XINXIN_SKILL_ENCODER", "lexical")
    application = create_app(Config(tmp_path, "setup-test-code"))
    endpoint = next(
        route.endpoint
        for route in application.routes
        if getattr(route, "path", "") == "/api/v1/files" and "POST" in route.methods
    )
    entered, release = threading.Event(), threading.Event()
    states = []

    def slow_save(name, source, *_args, **_kwargs):
        entered.set()
        assert release.wait(5)
        states.append(source.closed)
        return {"read": source.read().decode()}

    monkeypatch.setattr(application.state.library, "save_stream", slow_save)

    async def scenario():
        source = UploadFile(filename="cancelled.txt", file=io.BytesIO(b"resource"))
        pending = asyncio.create_task(endpoint(file=source, x_upload_id=None))
        while not entered.is_set():
            await asyncio.sleep(0.001)
        pending.cancel()
        await asyncio.sleep(0.01)
        assert not source.file.closed and not pending.done()
        release.set()
        try:
            await pending
        except asyncio.CancelledError:
            pass
        else:
            raise AssertionError("Cancellation was swallowed")
        assert source.file.closed and states == [False]

    asyncio.run(scenario())
