"""Small, replayable SkillNet views derived from routing and tool events.

No model claims, tool arguments, results or authorization are inferred here.
"""

import json


def skill_evidence(name, arguments, matches, ok):
    """Associate a returned tool with references or selected built-in tools only."""
    cards = matches.get("skills", []) + matches.get("dependencies", [])
    if name in {"load_skill", "read_skill_resource"}:
        ident = arguments.get("name")
        # Successful reads validate the ID in the router. Failed arbitrary IDs
        # must not manufacture a skill card in the conversation.
        if isinstance(ident, str) and (ok or any(card["id"] == ident for card in cards)):
            return [{"id": ident, "kind": "reference", "ok": bool(ok)}]
        return []
    return [
        {"id": card["id"], "kind": "tool", "ok": bool(ok)}
        for card in cards
        if name in card.get("tools", [])
    ]


def route_preview(matches, seq):
    def cards(key):
        return [
            {field: card.get(field, "") for field in ("id", "name", "description", "domain", "note")}
            for card in matches.get(key, [])
        ]

    return {
        "selection_seq": seq,
        "skills": cards("skills"),
        "dependencies": cards("dependencies"),
        "method": matches.get("selection", {}).get("method", "retrieval_order"),
        "evidence": [],
    }


def run_skill_traces(store, run_ids):
    """Batch historical views without loading token streams or tool output bodies."""
    traces = {}
    ids = list(dict.fromkeys(run_ids))
    for start in range(0, len(ids), 400):
        batch = ids[start : start + 400]
        marks = ",".join("?" for _ in batch)
        rows = store.all(
            "SELECT run_id,seq,kind,CASE WHEN kind='skills' THEN data "
            "ELSE json_extract(data,'$.skill_evidence') END AS payload "
            f"FROM events WHERE run_id IN ({marks}) AND (kind='skills' OR "
            "(kind='tool.completed' AND json_type(data,'$.skill_evidence')='array')) "
            "ORDER BY run_id,seq", batch,
        )
        for row in rows:
            payload = json.loads(row["payload"])
            if row["kind"] == "skills":
                traces[row["run_id"]] = route_preview(payload, row["seq"])
            elif row["run_id"] in traces:
                traces[row["run_id"]]["evidence"].extend(
                    {**item, "seq": row["seq"]} for item in payload
                )
    return traces


def with_skill_traces(store, runs):
    traces = run_skill_traces(store, [run["id"] for run in runs])
    return [{**run, "skillnet": traces.get(run["id"])} for run in runs]
