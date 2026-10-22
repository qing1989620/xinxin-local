"""文件媒体链路：历史绝对路径自愈、有界预览图、下载可用性。

这些用例对应一个真实故障：本地版从云端项目整目录复制后，`files.path`
仍指向上一个项目的绝对路径，`FileLibrary.path()` 的库根校验让所有
下载/预览返回 400，前端表现为"图片全部加载失败"。
"""

import io
import os
import sqlite3

from fastapi.testclient import TestClient
from PIL import Image

from app.config import Config
from app.files import FileLibrary
from app.main import create_app
from app.store import Store


def png_bytes(width=2400, height=1200) -> bytes:
    # 噪声图：PNG 压不动（接近真实照片），才能验证预览确实变小。
    buffer = io.BytesIO()
    Image.frombytes("RGB", (width, height), os.urandom(width * height * 3)).save(
        buffer, "PNG"
    )
    return buffer.getvalue()


def owner_client(tmp_path, monkeypatch):
    monkeypatch.setenv("XINXIN_SKILL_ENCODER", "lexical")
    client = TestClient(create_app(Config(tmp_path, "setup-test-code")))
    client.__enter__()
    setup = client.post(
        "/api/v1/auth/setup",
        json={
            "name": "owner",
            "password": "test-private-password",
            "setup_code": "setup-test-code",
        },
    ).json()
    client.headers["Authorization"] = "Bearer " + setup["token"]
    return client


def test_download_survives_paths_copied_from_another_install(tmp_path, monkeypatch):
    client = owner_client(tmp_path, monkeypatch)
    try:
        uploaded = client.post(
            "/api/v1/files", files={"file": ("photo.png", png_bytes(64, 64))}
        ).json()
        # 模拟"整个数据目录被复制到新位置"：记录里仍是旧安装的绝对路径，
        # 文件实体按 id 命名已经复制到当前库。
        db = sqlite3.connect(tmp_path / "xinxin.sqlite3")
        db.execute(
            "UPDATE files SET path=? WHERE id=?",
            (
                "D:/an-old-install/backend/data/files/" + uploaded["id"] + ".png",
                uploaded["id"],
            ),
        )
        db.commit()
        db.close()
        response = client.get(f"/api/v1/files/{uploaded['id']}/download")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        # 启动时的自愈写过库：再来一次也不会反复改。
        store = Store(tmp_path)
        library = FileLibrary(store)
        assert library.path(uploaded["id"]).is_file()
        assert str(library.path(uploaded["id"])).startswith(str(library.root))
    finally:
        client.__exit__(None, None, None)


def test_preview_is_bounded_and_cached(tmp_path, monkeypatch):
    client = owner_client(tmp_path, monkeypatch)
    try:
        original = png_bytes(2400, 1200)
        uploaded = client.post(
            "/api/v1/files", files={"file": ("wide.png", original)}
        ).json()
        first = client.get(f"/api/v1/files/{uploaded['id']}/preview")
        assert first.status_code == 200
        assert first.headers["content-type"] == "image/jpeg"
        assert len(first.content) < len(original) / 2
        with Image.open(io.BytesIO(first.content)) as image:
            assert max(image.size) <= 1600
        # 第二次命中磁盘缓存：字节完全一致。
        second = client.get(f"/api/v1/files/{uploaded['id']}/preview")
        assert second.content == first.content
        # 缩略尺寸也受支持。
        small = client.get(f"/api/v1/files/{uploaded['id']}/preview?size=480")
        assert small.status_code == 200
        with Image.open(io.BytesIO(small.content)) as image:
            assert max(image.size) <= 480
    finally:
        client.__exit__(None, None, None)


def test_preview_rejects_non_images_so_the_client_falls_back(tmp_path, monkeypatch):
    client = owner_client(tmp_path, monkeypatch)
    try:
        uploaded = client.post(
            "/api/v1/files", files={"file": ("notes.txt", b"plain text")}
        ).json()
        preview = client.get(f"/api/v1/files/{uploaded['id']}/preview")
        assert preview.status_code == 404
        # 回退路径仍然拿得到原文件。
        assert client.get(f"/api/v1/files/{uploaded['id']}/download").status_code == 200
    finally:
        client.__exit__(None, None, None)


def test_surrogate_text_from_pdf_extraction_is_cleaned_before_sqlite(
    tmp_path, monkeypatch
):
    """真实故障：all.pdf 抽取出落单 UTF-16 代理项（数学字体常见），
    sqlite 绑定参数按 UTF-8 编码直接抛 UnicodeEncodeError，上传报
    "'utf-8' codec can't encode character '\\ud835' ... surrogates not allowed"。
    """
    from app.files import FileLibrary

    client = owner_client(tmp_path, monkeypatch)
    try:
        # 模拟 pypdf 输出：一对合法代理项（应合成正式码点）+ 一个落单代理项。
        broken = "角\ud835\udc1a色\ud835标"
        monkeypatch.setattr(
            "app.document_text.extract_document", lambda _path, **_options: (broken, {"complete": True})
        )
        response = client.post(
            "/api/v1/files",
            files={"file": ("数学分析.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )
        assert response.status_code == 200
        saved = response.json()
        assert saved["name"] == "数学分析.pdf"
        text = client.get(f"/api/v1/files/{saved['id']}/text").json()["text"]
        # 合法代理对合成 U+1D41A；落单代理项被替换，全串可按 UTF-8 编码。
        assert "\U0001d41a" in text
        assert all(not (0xD800 <= ord(ch) <= 0xDFFF) for ch in text)
        text.encode("utf-8")
    finally:
        client.__exit__(None, None, None)


def test_store_binding_and_filename_survive_lone_surrogates(tmp_path):
    from app.store import Store, clean_text

    assert clean_text("好\ud835的") == "好\ufffd的"
    assert clean_text("好\ud835\udc1a的") == "好\U0001d41a的"
    assert clean_text("干净文本") == "干净文本"

    store = Store(tmp_path / "data")
    store.set_setting("probe", "值\ud835存")
    assert "\ud835" not in store.setting("probe")
    store.execute("INSERT INTO memories VALUES(?,?,?,?)", ("m1", "忆\ud835记", "misc", 1))
    row = store.one("SELECT content FROM memories WHERE id=?", ("m1",))
    assert "\ud835" not in row["content"]
