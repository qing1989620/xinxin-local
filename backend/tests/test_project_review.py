"""Cross-feature regressions from the whole-project audit; isolated data only."""
import io
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from PIL import Image
from fastapi import HTTPException

from app import imagegen, learning
from app.conversations import purge_conversation
from app.learning_studio import validate
from app.public_text import PublicText
from app.store import uid
from test_platform import client, frames, wait_run
from test_conversation_deletion import fixture_run


def image_provider(monkeypatch, block=None):
    output = io.BytesIO()
    Image.new("RGB", (16, 16), "teal").save(output, "PNG")
    monkeypatch.setattr(imagegen, "providers", lambda: {
        "default": "pollinations", "pollinations": {"available": True, "model": "synthetic"},
    })

    def generate(*args):
        if block:
            block()
        return output.getvalue(), "png", "image/png"

    monkeypatch.setattr(imagegen, "_pollinations", generate)


def image_agent(client):
    client.put("/api/v1/settings", json={"model_api_key": "synthetic-image-agent-key"})
    calls = []

    def provider(request):
        calls.append(True)
        content = frames(tool={"name": "generate_image_tool", "arguments": {"prompt": "A synthetic teal square"}}) if len(calls) == 1 else frames(content="图片已保存。")
        return httpx.Response(200, content=content.encode())

    client.app.state.manager.model_transport = httpx.MockTransport(provider)
    return client.post("/api/v1/runs", json={"task": "Create a synthetic picture", "permission": "workspace", "request_key": "synthetic-image-agent"}).json()["id"]


def test_actual_agent_image_tool_imports_and_registers_its_run_artifact(client, monkeypatch):
    image_provider(monkeypatch)
    ident = image_agent(client)
    assert wait_run(client, ident)["status"] == "completed"
    files = client.app.state.store.all("SELECT * FROM files WHERE run_id=?", (ident,))
    assert len(files) == 1 and files[0]["mime"] == "image/png"
    assert client.get(f"/api/v1/files/{files[0]['id']}/download").status_code == 200


def test_image_cancellation_waits_for_the_owned_thread_without_late_files(client, monkeypatch):
    entered, release = threading.Event(), threading.Event()

    def block():
        entered.set()
        assert release.wait(10)

    image_provider(monkeypatch, block)
    ident = image_agent(client)
    try:
        assert entered.wait(10)
        assert client.post(f"/api/v1/runs/{ident}/cancel").status_code == 200
        assert client.get(f"/api/v1/runs/{ident}").json()["status"] == "cancelling"
        assert not client.app.state.store.all("SELECT id FROM files")
    finally:
        release.set()
    assert wait_run(client, ident)["status"] == "cancelled"
    assert not client.app.state.store.all("SELECT id FROM files")


def test_conversation_deletion_preserves_book_originals_and_removes_exclusive_caches(client):
    store, library = client.app.state.store, client.app.state.library
    cid = client.post("/api/v1/conversations", json={"title": "Synthetic source conversation"}).json()["id"]
    run = fixture_run(client, cid)
    material = ("第一章\n导数描述函数的瞬时变化率，几何意义对应切线斜率。\n" * 10).encode()
    shared = library.save("synthetic-book.txt", material, run_id=run)
    exclusive = library.save("synthetic-exclusive.txt", material, run_id=run)
    book = client.post("/api/v1/learning/books", json={"file_id": shared["id"]}).json()["book"]
    library.previews.mkdir(exist_ok=True)
    for item in (shared, exclusive):
        store.execute("INSERT OR REPLACE INTO file_extractions VALUES(?,?)", (item["id"], '{"synthetic":true}'))
        store.execute("INSERT INTO file_ocr_pages VALUES(?,?,?,0,1)", (item["id"], 1, "synthetic private OCR"))
        (library.previews / f"{item['id']}-1600-1.jpg").write_bytes(b"synthetic preview")
    response = client.delete(f"/api/v1/conversations/{cid}/permanent")
    assert response.status_code == 200, response.text
    assert response.json()["shared_generated_files_retained"] == 1
    assert client.get(f"/api/v1/learning/books/{book['id']}").status_code == 200
    assert library.path(shared["id"]).read_bytes() == material
    for table in ("file_extractions", "file_ocr_pages"):
        assert store.one(f"SELECT * FROM {table} WHERE file_id=?", (shared["id"],))
        assert not store.one(f"SELECT * FROM {table} WHERE file_id=?", (exclusive["id"],))
    assert list(library.previews.glob(shared["id"] + "-*"))
    assert not list(library.previews.glob(exclusive["id"] + "-*"))


@pytest.mark.parametrize("mode", ["file", "conversation"])
def test_inflight_preview_cannot_recreate_private_cache_after_deletion(client, monkeypatch, mode):
    store, library = client.app.state.store, client.app.state.library
    cid = client.post("/api/v1/conversations", json={"title": "Synthetic preview lifecycle"}).json()["id"]
    run = fixture_run(client, cid)
    content = io.BytesIO()
    Image.new("RGB", (20, 20), "teal").save(content, "PNG")
    file = library.save("synthetic-preview.png", content.getvalue(), "image/png", run_id=run)
    original_path = library.path(file["id"])
    entered, release, blocked = threading.Event(), threading.Event(), threading.Event()
    original_save = Image.Image.save
    original_lock = library.lifecycle_lock

    class ObservedLock:
        def __enter__(self):
            if not original_lock.acquire(blocking=False):
                blocked.set()
                original_lock.acquire()
        def __exit__(self, *args):
            original_lock.release()

    def pause_save(image, target, *args, **kwargs):
        if str(target).endswith(".tmp"):
            entered.set()
            assert release.wait(10)
        return original_save(image, target, *args, **kwargs)

    library.lifecycle_lock = ObservedLock()
    monkeypatch.setattr(Image.Image, "save", pause_save)
    with ThreadPoolExecutor(2) as pool:
        preview = pool.submit(library.preview, file["id"])
        try:
            assert entered.wait(10)
            deletion = pool.submit(library.delete, file["id"]) if mode == "file" else pool.submit(purge_conversation, store, library, cid)
            assert blocked.wait(10)
            assert not deletion.done()
            assert store.one("SELECT id FROM files WHERE id=?", (file["id"],))
        finally:
            release.set()
        preview.result(timeout=10)
        result = deletion.result(timeout=10)
    if mode == "conversation":
        assert result["deleted"] and not result["cleanup_pending"]
    assert not original_path.exists()
    assert not store.one("SELECT id FROM files WHERE id=?", (file["id"],))
    assert not list(library.previews.glob(file["id"] + "-*"))
    assert library.preview(file["id"]) is None


@pytest.mark.parametrize("stem", [
    'What is printed by print("1  2")? ___',
    'What is printed by this code?\n```python\nif True:\n    print("A B")\n```\n___',
])
def test_question_validation_and_hash_preserve_meaningful_whitespace(stem):
    quote = "Python 字符串内部的空格属于字符串的原始内容。"
    row = {"kind": "fill", "stem": stem, "options": [], "answer": ["1  2"],
           "explanation": "逐字读取字符串内容，并保留代码中的缩进与内部空格。", "tags": ["Python"],
           "difficulty": 1, "source_quote": quote}
    saved, reason = validate(row, {"content": quote}, {"kinds": ["fill"], "difficulty": 0})
    assert not reason and saved["stem"] == stem
    assert learning._hash(stem, "fill") != learning._hash(stem.replace("  ", " "), "fill")


def test_stream_redaction_is_independent_of_chunk_boundaries(client):
    manager = client.app.state.manager
    key = "synthetic-private value with spaces"
    client.app.state.auth.set_secret("audit_sentinel", key)
    samples = [
        f"Normal prefix {key} and safe ending.",
        "Normal prefix authorization: Bearer synthetic_session_123 and safe ending.",
        "Normal prefix password: synthetic_password_123 and safe ending.",
        "-----BEGIN PRIVATE KEY-----\nSYNTHETIC_PRIVATE_BODY\n-----END PRIVATE KEY-----\nSafe.\n-----BEGIN RSA PRIVATE KEY-----\nSECOND_PRIVATE_BODY\n-----END RSA PRIVATE KEY-----\nDone.",
    ]
    for value in samples:
        expected = manager.redact(value, limit=None)
        for split in range(len(value) + 1):
            stream = PublicText(manager.redact, manager.secret_forms())
            actual = stream.feed(value[:split]) + stream.feed(value[split:]) + stream.finish()
            assert actual == expected, (value, split, actual)


def test_cjk_progress_streams_before_model_completion(client):
    manager = client.app.state.manager
    stream = PublicText(manager.redact, manager.secret_forms())
    assert stream.feed("我正在核对这份资料。") == "我正在核对这份资料。"
    assert stream.feed("请稍等") == "请稍等"
    assert stream.finish() == ""


def test_raw_model_credentials_never_reach_events_results_or_checkpoints(client):
    manager, store = client.app.state.manager, client.app.state.store
    key = "synthetic" + "-private-response-key-123"
    client.put("/api/v1/settings", json={"model_api_key": key})
    text = f"A normal reply. The configured value is {key}. End of safe reply."
    chunks = [text[index:index + 3] for index in range(0, len(text), 3)]
    stream = "".join("data: " + json.dumps({"choices": [{"delta": {"content": chunk}, "finish_reason": None}]}) + "\n\n" for chunk in chunks)
    stream += 'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n'
    manager.model_transport = httpx.MockTransport(lambda request: httpx.Response(200, content=stream.encode()))
    ident = client.post("/api/v1/runs", json={"task": "Synthetic response privacy check", "request_key": "synthetic-response-privacy"}).json()["id"]
    run = wait_run(client, ident)
    assert run["status"] == "completed"
    public = "".join(event["data"]["text"] for event in store.events(ident) if event["kind"] == "delta")
    assert public == run["result"] and "[redacted]" in public and key not in public
    for table in ("events", "messages", "run_context", "runs"):
        assert key not in json.dumps(store.all(f"SELECT * FROM {table}"))


@pytest.mark.parametrize("text", [
    '{"password": "syntheticAlpha syntheticBeta"}',
    'Here is JSON: {"nested": [{"api_key": "syntheticAlpha \\"syntheticBeta\\""}]} Done.',
    '{"pa\\u0073sword": ["syntheticAlpha", {"x":"syntheticBeta"}]}',
    '{"password" \n : "syntheticAlpha syntheticBeta"}',
    'JSON: {"password":{"token":"syntheticAlpha", "other":"syntheticBeta"}} Done.',
])
def test_new_json_credentials_are_redacted_even_when_not_in_the_vault(client, text):
    manager = client.app.state.manager
    for split in range(len(text) + 1):
        stream = PublicText(manager.redact, [])
        public = stream.feed(text[:split]) + stream.feed(text[split:]) + stream.finish()
        assert "syntheticAlpha" not in public and "syntheticBeta" not in public
        assert "[redacted]" in public


@pytest.mark.parametrize("known", ["password", "pass", "token"])
@pytest.mark.parametrize("text", [
    '{"password":"syntheticAlpha syntheticBeta"}',
    'JSON: {"password":"syntheticAlpha syntheticBeta"} Done.',
    'password: syntheticAlpha; token: syntheticBeta; Done.',
])
def test_credential_labels_are_removed_before_overlapping_known_values(client, known, text):
    manager, auth = client.app.state.manager, client.app.state.auth
    auth.set_secret("audit_sentinel", known)
    snapshot = manager.secret_forms()
    assert "syntheticAlpha" not in manager.redact(text, limit=None)
    assert "syntheticBeta" not in manager.redact(text, limit=None)
    # A running task must keep the same protection when the setting rotates.
    auth.set_secret("audit_sentinel", "replacement-private-key")
    for split in range(len(text) + 1):
        stream = PublicText(manager.redact, snapshot)
        public = stream.feed(text[:split]) + stream.feed(text[split:]) + stream.finish()
        assert "syntheticAlpha" not in public and "syntheticBeta" not in public
        assert "syntheticAlpha" not in stream.sanitize(text)
        assert "syntheticBeta" not in stream.sanitize(text)


def test_snapshot_redaction_preserves_json_and_redacts_before_truncating(client):
    manager = client.app.state.manager
    known = 'synthetic "quoted" key\\with spaces'
    snapshot = (known, json.dumps(known)[1:-1])
    text = json.dumps({"safe": known, "offset": 6000})
    for split in range(len(text) + 1):
        stream = PublicText(manager.redact, snapshot)
        public = stream.feed(text[:split]) + stream.feed(text[split:]) + stream.finish()
        assert json.loads(public) == {"safe": "[redacted]", "offset": 6000}
    stream = PublicText(manager.redact, ["syntheticLongCredential"])
    assert stream.sanitize("safe syntheticLongCredential end", limit=12) == "safe [redact"


@pytest.mark.parametrize("text", [
    'password: syntheticAlpha syntheticBeta; Done.',
    'Bearer syntheticAlpha syntheticBeta; Done.',
    'authorization: Bearer syntheticAlpha syntheticBeta; Done.',
    '{"output":"password: syntheticAlpha syntheticBeta; Done."}',
])
def test_semantic_redaction_does_not_expose_the_tail_of_known_multiword_credentials(client, text):
    manager, auth = client.app.state.manager, client.app.state.auth
    auth.set_secret("audit_sentinel", "syntheticAlpha syntheticBeta")
    snapshot = manager.secret_forms()
    sanitized = manager.redact(text, limit=None)
    assert "syntheticAlpha" not in sanitized and "syntheticBeta" not in sanitized
    auth.set_secret("audit_sentinel", "replacement-private-key")
    for split in range(len(text) + 1):
        stream = PublicText(manager.redact, snapshot)
        public = stream.feed(text[:split]) + stream.feed(text[split:]) + stream.finish()
        assert "syntheticAlpha" not in public and "syntheticBeta" not in public


def test_old_password_login_cannot_issue_after_completed_password_change(client, monkeypatch):
    auth = client.app.state.auth
    entered, release, blocked = threading.Event(), threading.Event(), threading.Event()
    lock = auth.lock

    class ObservedLock:
        def __enter__(self):
            if not lock.acquire(blocking=False):
                blocked.set()
                lock.acquire()

        def __exit__(self, *args):
            lock.release()

    auth.lock = ObservedLock()
    original_issue = auth.issue

    def paused_issue():
        if threading.current_thread().name.startswith("old-login"):
            entered.set()
            assert release.wait(10)
        return original_issue()

    monkeypatch.setattr(auth, "issue", paused_issue)
    with ThreadPoolExecutor(1, thread_name_prefix="old-login") as old_pool, ThreadPoolExecutor(1) as change_pool:
        old = old_pool.submit(auth.login, "主人", "private-test-password", "synthetic-peer")
        try:
            assert entered.wait(10)

            def change():
                return client.put("/api/v1/auth/password", json={"current": "private-test-password", "password": "new-private-password-123"})

            new = change_pool.submit(change)
            assert blocked.wait(10)
            assert not new.done()
        finally:
            release.set()
        old_token = old.result(timeout=10)
        changed = new.result(timeout=10)
    assert changed.status_code == 200
    with pytest.raises(HTTPException) as error:
        auth.require("Bearer " + old_token)
    assert error.value.status_code == 401
    assert auth.require("Bearer " + changed.json()["token"])


def email_codes(client):
    assert client.put("/api/v1/settings/email", json={"email": "owner@example.com", "smtp_password": "synthetic-mail-key"}).status_code == 200
    mail, store = client.app.state.mail, client.app.state.store
    for scene, code in [("login", "123456"), ("reset", "654321")]:
        store.execute("INSERT INTO email_codes(id,scene,digest,expires,created,peer_hash) VALUES(?,?,?,?,?,?)", (
            uid(), scene, mail.digest("owner@example.com", scene, code), time.time() + 600, time.time(), "synthetic-peer"))


@pytest.mark.parametrize("first", ["login", "reset", "binding"])
def test_email_credential_transitions_are_serialized(client, monkeypatch, first):
    email_codes(client)
    auth, mail = client.app.state.auth, client.app.state.mail
    entered, release, blocked = threading.Event(), threading.Event(), threading.Event()
    original_lock = auth.lock

    class ObservedLock:
        def __enter__(self):
            if not original_lock.acquire(blocking=False):
                blocked.set()
                original_lock.acquire()
        def __exit__(self, *args):
            original_lock.release()

    auth.lock = ObservedLock()
    if first == "binding":
        original = mail.configure
        def pause(values):
            original(values)
            entered.set()
            assert release.wait(10)
        monkeypatch.setattr(mail, "configure", pause)
    else:
        original = auth.issue
        def pause():
            if not entered.is_set():
                entered.set()
                assert release.wait(10)
            return original()
        monkeypatch.setattr(auth, "issue", pause)

    def login():
        return client.post("/api/v1/auth/email/login", json={"email": "owner@example.com", "code": "123456"})
    def reset():
        return client.post("/api/v1/auth/email/reset", json={"email": "owner@example.com", "code": "654321", "password": "new-mail-password-123"})
    def binding():
        return client.put("/api/v1/settings/email", json={"email": "replacement@example.com", "smtp_password": "synthetic-mail-key"})

    with ThreadPoolExecutor(2) as pool:
        initial = pool.submit({"login": login, "reset": reset, "binding": binding}[first])
        try:
            assert entered.wait(10)
            subsequent = pool.submit(reset if first == "login" else login)
            assert blocked.wait(10)
        finally:
            release.set()
        initial, subsequent = initial.result(timeout=10), subsequent.result(timeout=10)
    assert initial.status_code == 200
    assert subsequent.status_code == (200 if first == "login" else 400)
    if first == "login":
        with pytest.raises(HTTPException):
            auth.require(initial.json()["token"])
        assert auth.require(subsequent.json()["token"])


def test_revoked_identity_waiting_to_change_email_cannot_mutate_after_reset(client, monkeypatch):
    email_codes(client)
    auth = client.app.state.auth
    verified, release = threading.Event(), threading.Event()
    original = auth.require

    def pause(authorization):
        value = original(authorization)
        if not verified.is_set():
            verified.set()
            assert release.wait(10)
        return value

    monkeypatch.setattr(auth, "require", pause)
    with ThreadPoolExecutor(1) as pool:
        pending = pool.submit(client.put, "/api/v1/settings/email", json={"email": "stale@example.com", "smtp_password": "synthetic-mail-key"})
        try:
            assert verified.wait(10)
            reset = client.post("/api/v1/auth/email/reset", json={"email": "owner@example.com", "code": "654321", "password": "new-mail-password-123"})
            assert reset.status_code == 200
        finally:
            release.set()
        assert pending.result(timeout=10).status_code == 401
    assert auth.secret("owner_email") == "owner@example.com"
