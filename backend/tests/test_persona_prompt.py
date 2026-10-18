from app.persona import MAX_SYSTEM_PROMPT_CHARS, build_system_prompt


def _run():
    return {
        "permission": "read",
        "server_id": None,
        "allow_memory": False,
        "max_calls": 8,
        "max_total_tokens": 40000,
        "context_window_tokens": 80000,
        "max_seconds": 600,
        "resume_of": None,
    }


def test_compressed_prompt_keeps_routed_skill_ids(tmp_path):
    # Long skill cards force the prompt over budget, so build_system_prompt has
    # to compress candidate_skills into {"selected_ids": [...]}. The ids must
    # survive; reading the wrong key would silently drop all skill context.
    matches = {
        "query": "画一张图",
        "skills": [
            {"id": f"skill-{i}", "description": "很长的技能说明" * 400}
            for i in range(8)
        ],
        "dependencies": [],
        "order": [f"skill-{i}" for i in range(8)],
    }
    prompt = build_system_prompt(_run(), matches, [], tmp_path)
    assert len(prompt) <= MAX_SYSTEM_PROMPT_CHARS
    assert "selected_ids" in prompt
    assert "skill-0" in prompt
    assert '"description"' not in prompt


def test_short_prompt_keeps_full_skill_cards(tmp_path):
    matches = {
        "query": "画图",
        "skills": [{"id": "scientific-plotting", "description": "画图技能"}],
        "dependencies": [],
    }
    prompt = build_system_prompt(_run(), matches, [], tmp_path)
    assert "scientific-plotting" in prompt
    assert '"query"' not in prompt


def test_tool_evidence_survives_before_skill_compression(tmp_path):
    # 16 candidates + long cards used to make the trimmer drop previous_work
    # events (the evidence a resumed task depends on) before touching skills.
    matches = {
        "query": "继续核对",
        "skills": [
            {"id": f"skill-{i}", "description": "技能说明" * 600}
            for i in range(10)
        ],
        "candidates": [
            {"id": f"skill-{i}", "description": "候选卡" * 500} for i in range(16)
        ],
        "dependencies": [],
    }
    recovery = [
        {
            "run_id": "prev-run",
            "task": "创建文件并核对内容",
            "status": "failed",
            "permission_then": "workspace",
            "server_id_then": None,
            "error": "预算用尽",
            "events": [
                {
                    "seq": 7,
                    "kind": "tool.started",
                    "name": "write_file",
                    "arguments": '{"path":"resume-marker.txt"}',
                }
            ],
        }
    ]
    prompt = build_system_prompt(_run(), matches, [], tmp_path, recovery=recovery)
    assert "resume-marker.txt" in prompt
    assert "selected_ids" in prompt
    # 候选审计数据不进提示
    assert "候选卡" not in prompt
