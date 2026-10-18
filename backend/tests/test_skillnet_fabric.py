"""SkillNet Fabric 行为：关系扩展、置信度分流、任务必要性重排。"""

import pytest

from app.skillnet.catalog import SkillLibrary
from app.skillnet.schema import Skill
from app.skills import SkillRouter
from app.store import Store


@pytest.fixture()
def router(tmp_path, monkeypatch):
    monkeypatch.setenv("XINXIN_SKILL_ENCODER", "lexical")
    return SkillRouter(Store(tmp_path))


def test_decision_tiers_match_upstream_thresholds():
    assert SkillRouter._decision(20.0)[0] == "auto"
    assert SkillRouter._decision(5.0)[0] == "confirm"
    assert SkillRouter._decision(0.0)[0] == "direct"
    # 重排明确表示"没有适用技能"时，即使词面分很高也直答
    assert SkillRouter._decision(50.0, abstained=True)[0] == "direct"


def test_neighbours_are_undirected():
    base = Skill(name="alpha", description="", domain="测试")
    child = Skill(
        name="beta",
        description="",
        domain="测试",
        relations=[("depend_on", "alpha")],
    )
    library = SkillLibrary([base, child])
    assert ("depend_on", "alpha") in library.neighbours("beta")
    assert ("depend_on", "beta") in library.neighbours("alpha")


def test_fabric_exposes_components_and_decision(router):
    result = router.search("把实验数据画成散点图", k=3, mode="fabric")
    assert result["mode"] == "fabric"
    assert result["components"]["bm25"] is True
    assert result["components"]["graph_expansion"] is True
    # 检索本身不调用模型；重排由 Agent 在拿到候选后单独执行
    assert result["components"]["llm_rerank"] is False
    assert result["decision"] in {"auto", "confirm", "direct"}
    assert result["decision_reason"]
    assert result["candidates"]
    assert result["selection"]["method"] == "retrieval_order"


def test_hybrid_skips_graph_expansion(router):
    result = router.search("把实验数据画成散点图", k=2, mode="hybrid")
    assert result["components"]["graph_expansion"] is False
    assert result["components"]["vector"] is True


def test_apply_rerank_reorders_and_records_reasons(router):
    result = router.search("把实验数据画成散点图", k=3, mode="hybrid")
    first, second = [item["id"] for item in result["candidates"][:2]]
    output = {
        "skills": [second, first],
        "decisions": [
            {"name": second, "reason": "更贴合任务"},
            {"name": first, "reason": "次要"},
        ],
    }
    applied = router.apply_rerank(result, output, k=1)
    assert applied["components"]["llm_rerank"] is True
    assert applied["skills"][0]["id"] == second
    assert applied["skills"][0]["note"] == "更贴合任务"
    assert applied["selection"]["method"] == "task_utility"
    assert applied["selection"]["selected_count"] == 1


def test_apply_rerank_allows_abstention(router):
    result = router.search("把实验数据画成散点图", k=2, mode="hybrid")
    applied = router.apply_rerank(result, {"skills": [], "decisions": []}, k=2)
    assert applied["selection"]["abstained"] is True
    assert applied["skills"] == []
    assert applied["decision"] == "direct"


def test_invalid_rerank_output_falls_back(router):
    result = router.search("把实验数据画成散点图", k=2, mode="hybrid")
    before = [item["id"] for item in result["skills"]]
    applied = router.apply_rerank(result, {"skills": ["not-a-real-skill"]}, k=2)
    assert applied["degraded"] is True
    assert applied["components"]["llm_rerank"] is False
    assert [item["id"] for item in applied["skills"]] == before


def test_parse_rerank_output_tolerates_fences_and_chatter():
    raw = '说明：\n```json\n{"skills": ["a"], "decisions": []}\n```\n以上。'
    assert SkillRouter.parse_rerank_output(raw) == {"skills": ["a"], "decisions": []}
    assert SkillRouter.parse_rerank_output("not json") is None
