import io
import shutil
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.config import ROOT
from app.files import FileLibrary, FileTooLarge, UploadConflict
from app.skill_packages import SkillPackages
from app.skills import SkillRouter
from app.store import Store


def test_curated_resources_are_real_attributed_and_integrity_checked(tmp_path):
    packages = SkillPackages()
    assert len(packages.cards) == 30
    for card in packages.cards.values():
        assert len(card["revision"]) == 40 and card["source_url"].startswith(
            "https://github.com/"
        )
        assert not card["execution_verified"]
        for item in card["files"]:
            page = packages.read(card["id"], item["path"])
            assert page["sha256"] == item["sha256"]
            import json

            assert len(json.dumps(page, ensure_ascii=False)) < 16000
    ident = "gh-claude-docker-development-521176"
    for path in [
        "../catalog.json",
        "scripts/../../catalog.json",
        "C:/secret",
        "..\\secret",
        "not-listed.py",
    ]:
        with pytest.raises(ValueError):
            packages.read(ident, path)
    copy = tmp_path / "skills"
    shutil.copytree(ROOT / "resources/skills", copy)
    target = copy / "packages" / ident / "SKILL.md"
    raw = target.read_bytes()
    target.write_bytes(b"x" + raw[1:])
    with pytest.raises(ValueError, match="完整性"):
        SkillPackages(copy).read(ident)


def test_explicit_skill_selection_keeps_prerequisites_and_progressive_disclosure(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("XINXIN_SKILL_ENCODER", "lexical")
    router = SkillRouter(Store(tmp_path))
    ident = "gh-claude-docker-development-521176"
    result = router.search(f"请使用 {ident} 帮我检查配置")
    assert result["skills"][0]["id"] == ident
    assert result["order"].index("server-deployment") < result["order"].index(ident)
    assert not result["execution_verified"] and result["authorization"] == "independent"
    full = router.load(ident)["markdown"]
    pages, offset = [], 0
    while True:
        page = router.load(ident, offset)
        pages.append(page["markdown"])
        assert "execute_command" not in page["tools"]
        assert page["resources"] and page["provenance"]["license"]
        offset = page["next_offset"]
        if offset is None:
            break
    assert "".join(pages) == full


def test_stream_upload_retries_are_atomic_under_concurrency(tmp_path):
    library = FileLibrary(Store(tmp_path))

    def upload():
        return library.save_stream(
            "notes.md",
            io.BytesIO(b"shared-private-resource"),
            request_id="same-upload-key",
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: upload(), range(2)))
    assert results[0]["id"] == results[1]["id"]
    assert len(library.store.all("SELECT * FROM files")) == 1
    assert len(list(library.root.iterdir())) == 1
    with pytest.raises(UploadConflict):
        library.save_stream(
            "notes.md", io.BytesIO(b"changed"), request_id="same-upload-key"
        )
    assert len(list(library.root.iterdir())) == 1
    library.delete(results[0]["id"])
    assert not list(library.root.iterdir())
    assert not library.store.all("SELECT * FROM uploads")


def test_stream_limit_cleans_partial_files_and_keeps_unindexed_originals(
    tmp_path, monkeypatch
):
    from app import files

    library = FileLibrary(Store(tmp_path))
    monkeypatch.setattr(files, "MAX_UPLOAD", 8)
    with pytest.raises(FileTooLarge):
        library.save_stream("large.zip", io.BytesIO(b"123456789"))
    with pytest.raises(ValueError, match="为空"):
        library.save("empty.txt", b"")
    assert not list(library.root.iterdir())
    monkeypatch.setattr(files, "MAX_EXTRACT", 2)
    saved = library.save("data.txt", b"12345678")
    assert not saved["indexed"] and saved["parse_error"]
    assert library.path(saved["id"]).read_bytes() == b"12345678"
    assert library.get(saved["id"])["size"] == 8


def test_upload_roundtrip_retry_and_authorization(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from app import files
    from app.config import Config
    from app.main import create_app

    monkeypatch.setenv("XINXIN_SKILL_ENCODER", "lexical")
    with TestClient(create_app(Config(tmp_path, "local-code"))) as client:
        payload = {
            "file": ("phone-resource.txt", b"mobile upload content", "text/plain")
        }
        assert client.post("/api/v1/files", files=payload).status_code == 401
        response = client.post(
            "/api/v1/auth/setup",
            json={
                "name": "owner",
                "password": "private-test-password",
                "setup_code": "local-code",
            },
        )
        client.headers["Authorization"] = "Bearer " + response.json()["token"]
        headers = {"X-Upload-ID": "phone-upload-retry-1"}
        first = client.post("/api/v1/files", headers=headers, files=payload)
        assert first.status_code == 200
        repeated = client.post("/api/v1/files", headers=headers, files=payload)
        assert repeated.json()["id"] == first.json()["id"]
        assert len(client.get("/api/v1/files").json()) == 1
        assert (
            client.get(f"/api/v1/files/{first.json()['id']}/download").content
            == payload["file"][1]
        )
        changed = client.post(
            "/api/v1/files",
            headers=headers,
            files={"file": ("phone-resource.txt", b"different", "text/plain")},
        )
        assert changed.status_code == 409
        monkeypatch.setattr(files, "MAX_UPLOAD", 2)
        assert client.post("/api/v1/files", files=payload).status_code == 413
        assert len(client.get("/api/v1/files").json()) == 1
