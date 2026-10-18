"""Token-aware conversation checkpoints, separate from the model-call budget."""

import json
from functools import lru_cache
from pathlib import Path

from tokenizers import Tokenizer

from .config import CONTEXT_INPUT_TOKENS, ROOT
from .store import encode, now


@lru_cache(maxsize=1)
def tokenizer():
    return Tokenizer.from_file(str(ROOT / "resources/deepseek-tokenizer/tokenizer.json"))


def token_count(text):
    return len(tokenizer().encode(text, add_special_tokens=False).ids)


def message_groups(messages):
    groups = []
    for message in messages:
        if message.get("role") == "tool" and groups and groups[-1][0].get("tool_calls"):
            groups[-1].append(message)
        else:
            groups.append([message])
    return groups


def complete_history(messages):
    result = []
    for group in message_groups(messages):
        first = group[0]
        if first.get("role") in {"system", "tool"}:
            continue
        if first.get("tool_calls"):
            expected = {call["id"] for call in first["tool_calls"]}
            actual = {item.get("tool_call_id") for item in group[1:]}
            if expected != actual:
                continue
        result.extend(group)
    return result


def prior_messages(store, run):
    cursor = store.one(
        "SELECT rowid cursor FROM messages WHERE conversation_id=? AND role='user' "
        "ORDER BY rowid DESC LIMIT 1", (run["conversation_id"],),
    )["cursor"]
    saved = store.one(
        "SELECT * FROM run_context WHERE conversation_id=? AND run_id<>? "
        "ORDER BY updated DESC LIMIT 1", (run["conversation_id"], run["id"]),
    )
    history = json.loads(saved["messages"]) if saved else []
    after = saved["message_cursor"] if saved else 0
    history.extend(store.all(
        "SELECT role,content FROM messages WHERE conversation_id=? AND rowid>? "
        "AND rowid<? ORDER BY rowid", (run["conversation_id"], after, cursor),
    ))
    return complete_history(history), bool(saved)


def save_context(store, run, messages, sanitize):
    cleaned = []
    for message in messages:
        if message.get("role") == "system":
            continue
        item = dict(message)
        if isinstance(item.get("content"), str):
            item["content"] = sanitize(item["content"], limit=None)
        if item.get("tool_calls"):
            item["tool_calls"] = json.loads(sanitize(encode(item["tool_calls"]), limit=None))
        cleaned.append(item)
    cursor = store.one(
        "SELECT COALESCE(MAX(rowid),0) cursor FROM messages WHERE conversation_id=?",
        (run["conversation_id"],),
    )["cursor"]
    store.execute(
        "INSERT INTO run_context VALUES(?,?,?,?,?) ON CONFLICT(run_id) DO UPDATE SET "
        "messages=excluded.messages,message_cursor=excluded.message_cursor,updated=excluded.updated",
        (run["id"], run["conversation_id"], encode(cleaned), cursor, now()),
    )


def context_manager_type(base):
    class TaskContext(base):
        """Keep current and initial goals; trim whole exchanges only at the token window."""

        def __init__(self, instruction, max_length=CONTEXT_INPUT_TOKENS, checkpoint=None, on_compact=None):
            super().__init__(max_length=max_length, max_tool_result_length=64000)
            self.instruction = instruction
            self.checkpoint = checkpoint
            self.on_compact = on_compact
            self.measured = {}

        def add_tool_calls(self, calls=None, *, tool_calls=None):
            result = super().add_tool_calls(tool_calls if tool_calls is not None else calls)
            self.limit_messages()
            return result

        def limit_messages(self):
            current = next((
                item for item in reversed(self.messages)
                if item.get("role") == "user" and item.get("content") == self.instruction
            ), None)
            initial = next((item for item in self.messages if item.get("role") == "user"), None)
            groups = message_groups(self.messages)
            sizes = []
            cache = {}
            for group in groups:
                raw = encode(group)
                size = self.measured.get(raw)
                if size is None:
                    size = token_count(raw) + 8
                sizes.append(size)
                cache[raw] = size
            self.measured = cache
            before = sum(sizes)
            removed = 0
            while sum(sizes) > self.max_length:
                removable = next((
                    index for index, group in enumerate(groups[:-1])
                    if not any(item.get("role") == "system" or item is current or item is initial for item in group)
                ), None)
                if removable is None:
                    raise RuntimeError("本轮内容超过模型上下文窗口；完整任务仍保留，请分批读取输出或压缩历史后继续。")
                groups.pop(removable)
                sizes.pop(removable)
                removed += 1
            self.messages[:] = [message for group in groups for message in group]
            if removed and self.on_compact:
                self.on_compact({
                    "removed_groups": removed, "tokens_before": before,
                    "tokens_after": sum(sizes), "input_limit_tokens": self.max_length,
                    "history_preserved_in_events": True,
                })
            if self.checkpoint and current is not None:
                self.checkpoint(self.messages)

    return TaskContext
