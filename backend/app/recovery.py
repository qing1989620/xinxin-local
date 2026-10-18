"""Bounded, read-only evidence for another turn; never replay tool calls."""

import json

from .store import encode

MAX_RECOVERY_CHARS = 14000


def excerpt(value, limit):
    text = str(value or "")
    if len(text) <= limit:
        return text
    half = (limit - 24) // 2
    return text[:half] + "\n[中间已截断]\n" + text[-half:]


def previous_work(store, run):
    rows = store.all(
        "SELECT id,task,status,permission,server_id,error FROM runs "
        "WHERE conversation_id=? AND id<>? AND created<=? "
        "ORDER BY created DESC,rowid DESC LIMIT 20",
        (run["conversation_id"], run["id"], run["created"]),
    )
    failed = []
    for row in rows:
        if row["status"] == "completed":
            break
        failed.append(row)
    selected = failed[:3]
    if len(failed) > 3:
        selected.append(failed[-1])
    context = [
        {
            "run_id": row["id"],
            "task": excerpt(row["task"], 1800),
            "status": row["status"],
            "permission_then": row["permission"],
            "server_id_then": row["server_id"],
            "error": excerpt(row["error"], 700),
            "events": [],
        }
        for row in selected
    ]
    while len(encode(context)) > MAX_RECOVERY_CHARS:
        for item in context:
            for key in ("task", "error"):
                item[key] = excerpt(item[key], max(80, len(item[key]) // 2))
    for item in context[:3]:
        events = store.all(
            "SELECT seq,kind,data FROM events WHERE run_id=? "
            "AND kind IN ('tool.started','tool.completed') ORDER BY seq DESC LIMIT 16",
            (item["run_id"],),
        )
        # Keep actual event order; parallel calls cannot be paired by name alone.
        for event in events:
            data = json.loads(event["data"])
            entry = {
                "seq": event["seq"], "kind": event["kind"], "name": data.get("name"),
            }
            if event["kind"] == "tool.started":
                entry["arguments"] = excerpt(data.get("arguments"), 600)
            else:
                entry["ok"] = data.get("ok")
                entry["result"] = excerpt(data.get("result"), 1000)
            item["events"].append(entry)
            if len(encode(context)) > MAX_RECOVERY_CHARS:
                item["events"].pop()
                break
        item["events"].sort(key=lambda event: event["seq"])
    return context
