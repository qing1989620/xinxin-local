"""SkillNet 完整语料与生图通路的测试。"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from app import imagegen
from app.files import FileLibrary
from app.skills import EXECUTABLE_PRIOR, SkillRouter
from app.store import Store


@pytest.fixture(scope="module")
def router(tmp_path_factory):
    return SkillRouter(Store(tmp_path_factory.mktemp("corpus-store")))


def test_corpus_loads_full_skillnet_library(router):
    status = router.corpus_status
    assert status["available"] is True
    assert status["skills"] == 1881
    assert status["seed"] == 76
    assert status["community"] == 1769
    assert status["evolved"] == 36
    # 平台自有技能仍在库内
    assert len(router.all()) == status["skills"] + 7


def test_corpus_domains_and_relations_are_declared_only(router):
    graph = router.graph()
    assert graph["skill_count"] == len(router.all())
    assert graph["edge_count"] > 2000
    assert set(graph["relation_types"]) == {"compose_with", "depend_on", "similar_to"}
    present = {node["id"] for node in graph["nodes"]}
    for edge in graph["edges"]:
        assert edge["source"] in present and edge["target"] in present


def test_seed_skill_detail_exposes_contract(router):
    detail = router.detail("literature-review")
    assert detail["corpus_source"] == "seed"
    assert detail["passport"]["capability"]
    assert detail["passport"]["steps"]
    assert detail["markdown"]


def test_community_resource_reads_are_integrity_checked(router, tmp_path, monkeypatch):
    name = "gh-scientific-13c-metabolic-flux-d6d252"
    detail = router.detail(name)
    assert detail["corpus_source"] == "github"
    assert detail["resources"], "社区技能应带已登记资源清单"
    assert detail["provenance"]["repository"].startswith("K-Dense")
    first = detail["resources"][0]["path"]
    record = router.read_skill_resource(name, first)
    assert record["sha256"] and record["bytes"] > 0
    with pytest.raises(ValueError, match="完整性"):
        from app import skillnet_corpus

        skill = router.library.get(name)
        manifest = skillnet_corpus.package_manifest(skill)
        entry = next(f for f in manifest["files"] if f["path"] == first)
        assert entry["bytes"] == record["bytes"]
        # 篡改只在临时副本上进行，真实语料文件保持只读
        source = skillnet_corpus._package_dir(skill) / first
        sandbox = tmp_path / first
        sandbox.parent.mkdir(parents=True, exist_ok=True)
        sandbox.write_bytes(source.read_bytes() + b"tampered")
        # _package_dir 返回包根，relative 路径（含 assets/ 等子目录）在其下拼接
        monkeypatch.setattr(skillnet_corpus, "_package_dir", lambda _skill: tmp_path)
        router.read_skill_resource(name, first)
    with pytest.raises(ValueError):
        router.read_skill_resource(name, "../../etc/passwd")


def test_seed_modules_are_verified_against_manifest(router, tmp_path, monkeypatch):
    """种子数据模块经 importlib 执行，必须与 manifest 登记的 sha256 一致。"""
    from app import skillnet_corpus

    manifest = skillnet_corpus._read_manifest()
    declared = manifest.get("seed_modules")
    assert isinstance(declared, dict) and declared, "manifest 应登记种子模块哈希"
    for relative, expected in declared.items():
        path = (skillnet_corpus.CORPUS / relative).resolve()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    # 哈希不符时拒绝加载：搭一个只含种子模块的最小语料副本，改动一个字节
    sandbox = tmp_path / "corpus"
    (sandbox / "seed").mkdir(parents=True)
    shutil.copy(skillnet_corpus.SEED_CATALOG, sandbox / "seed/catalog_data.py")
    shutil.copy(skillnet_corpus.SEED_BUSINESS, sandbox / "seed/business_skills.py")
    (sandbox / "manifest.json").write_text(json.dumps(manifest), "utf-8")
    victim = sandbox / next(iter(declared))
    victim.write_bytes(victim.read_bytes() + b"# tampered")
    monkeypatch.setattr(skillnet_corpus, "CORPUS", sandbox)
    monkeypatch.setattr(skillnet_corpus, "MANIFEST", sandbox / "manifest.json")
    monkeypatch.setattr(skillnet_corpus, "SEED_CATALOG", sandbox / "seed/catalog_data.py")
    monkeypatch.setattr(skillnet_corpus, "SEED_BUSINESS", sandbox / "seed/business_skills.py")
    with pytest.raises(ValueError, match="种子模块完整性"):
        skillnet_corpus.load(force=True)


def test_network_model_card_is_honest_about_research_status(router):
    card = router.network_model()
    assert card["available"] is True
    latest = card["versions"][-1]
    assert latest["version"] == "network-model-v2"
    assert latest["stage"] == "research_candidate_not_admitted"
    assert latest["recommended_shadow_alpha"] == 0.0
    assert latest["score_kind"] == "learned_relevance_not_success_probability"
    probe = latest["probe"]
    assert probe["available"] is True
    assert probe["weights_sha256_ok"] is True
    structural = probe["structural"]
    assert structural["shapes_ok"] is True
    assert structural["parameters_actual"] == structural["parameters_declared"] == 110596
    assert probe["catalog_rows"] == 1881
    assert probe["corpus_skills"] == 1881
    assert set(probe["drift_cosine"]) == {"q", "s", "g"}
    for cosine in probe["drift_cosine"].values():
        # 原始低秩增量以强度 1 施加会明显扰动表示（含负余弦）；
        # 这正是独立校准选择强度 0 的原因，探针只如实呈现，不做评价。
        assert -1.0 <= cosine <= 1.0
    assert "recommended_shadow_alpha=0" in probe["note"]


def test_evolved_skills_carry_run_statistics(router):
    detail = router.detail("high-temp-oxidation-coating-recipe-dev")
    assert detail["generation"] > 0
    assert detail["corpus_source"] not in ("seed", "github")
    assert detail["passport"]["steps"]


def test_executable_prior_keeps_platform_skills_actionable(router, monkeypatch):
    """检索分接近时，注册了平台工具的技能应排在只读资料之前。"""
    monkeypatch.setattr(
        router.bm25,
        "search",
        lambda *_a, **_k: [("scientific-plotting", 10), ("gh-claude-remember-68a207", 9)],
    )
    monkeypatch.setattr(router.vector, "search", lambda *_a, **_k: [])
    result = router.search("plot this", k=2)
    assert result["skills"][0]["id"] == "scientific-plotting"
    assert EXECUTABLE_PRIOR > 0


def test_search_stays_fast_with_full_corpus(router):
    import time

    start = time.monotonic()
    result = router.search("把实验数据画成散点图并导出脚本")
    assert result["skills"]
    assert time.monotonic() - start < 5.0


# ----------------------------------------------------------------------
# 生图
# ----------------------------------------------------------------------

@pytest.fixture()
def library(tmp_path):
    return FileLibrary(Store(tmp_path / "store"))


def test_skill_activity_endpoint_aggregates_run_states(tmp_path):
    from fastapi.testclient import TestClient

    from app.config import Config
    from app.main import _selected_skill_ids, create_app

    rows = [{"data": json.dumps({"skills": [{"id": "a"}, {"id": "b"}]})}]
    assert _selected_skill_ids(rows) == ["a", "b"]
    assert _selected_skill_ids([{"data": "not json"}]) == []
    assert _selected_skill_ids([{"data": json.dumps({"skills": "nope"})}]) == []
    assert _selected_skill_ids([{"data": json.dumps(["a"])}]) == ["a"]
    application = create_app(Config(tmp_path, "local-bootstrap"))
    with TestClient(application) as client:
        response = client.post(
            "/api/v1/auth/setup",
            json={
                "name": "主人",
                "password": "private-test-password",
                "setup_code": "local-bootstrap",
            },
        )
        client.headers["Authorization"] = "Bearer " + response.json()["token"]
        body = client.get("/api/v1/skills/activity").json()
        assert isinstance(body["running"], list)
        assert isinstance(body["finished"], list)
        for item in body["finished"]:
            assert item["state"] in ("done", "failed")
            assert item["id"] and item["run_id"]


def test_providers_report_free_default(library):
    providers = imagegen.providers()
    assert providers["default"] == "pollinations"
    assert providers["pollinations"]["available"] is True
    assert providers["openrouter"]["available"] is bool(
        __import__("os").getenv("OPENROUTER_API_KEY")
    )


def test_generate_rejects_empty_prompt(library):
    with pytest.raises(ValueError, match="描述"):
        imagegen.generate(library, "  ")


def test_generate_rejects_unknown_provider(library):
    with pytest.raises(ValueError, match="档位"):
        imagegen.generate(library, "x", provider="nope")


def test_generate_accepts_default_provider_aliases(library, monkeypatch):
    """provider 为 "" / "default" / None 都归位到默认档，不得抛 TypeError。"""
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64

    class FakeResponse:
        status_code = 200
        content = png

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, url):
            return FakeResponse()

    monkeypatch.setattr(imagegen.httpx, "Client", FakeClient)
    for alias in ("", "default", None, "  DEFAULT  "):
        record = imagegen.generate(library, "a calm lake", provider=alias)
        assert record["image"]["provider"] == "pollinations"


def test_openrouter_payload_shapes_are_both_accepted():
    """旧式 image_url data URL 与新式 b64_json 都能取出 base64 数据。"""
    legacy = {"image_url": {"url": "data:image/png;base64,AAAA"}}
    legacy_str = {"image_url": "data:image/png;base64,CCCC"}
    modern = {"b64_json": "BBBB"}
    assert imagegen._image_bytes_from_payload(legacy) == "AAAA"
    assert imagegen._image_bytes_from_payload(legacy_str) == "CCCC"
    assert imagegen._image_bytes_from_payload(modern) == "BBBB"
    assert imagegen._image_bytes_from_payload({}) == ""
    assert imagegen._image_bytes_from_payload({"image_url": {"url": "https://x"}}) == ""


def test_generate_rejects_non_image_payload(library, monkeypatch):
    class FakeResponse:
        status_code = 200
        content = b"You are being rate limited. Slow down."

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, url):
            self.url = url
            return FakeResponse()

    monkeypatch.setattr(imagegen.httpx, "Client", FakeClient)
    with pytest.raises(ValueError, match="没有返回图片"):
        imagegen.generate(library, "a red circle")


def test_generate_saves_verified_image(library, monkeypatch):
    png = (
        b"\x89PNG\r\n\x1a\n"
        + b"\x00" * 64
    )

    class FakeResponse:
        status_code = 200
        content = png

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, url):
            assert "nologo=true" in url
            return FakeResponse()

    monkeypatch.setattr(imagegen.httpx, "Client", FakeClient)
    record = imagegen.generate(library, "a quiet teal moon", width=512, height=512)
    assert record["mime"] == "image/png"
    assert record["image"]["provider"] == "pollinations"
    assert record["image"]["bytes"] == len(png)
    assert library.path(record["id"]).read_bytes() == png
    assert imagegen.recent(library)[0]["file_id"] == record["id"]
