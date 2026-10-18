"""Probe the real Fabric router against one query.

Copies the live state to .qa-data, then runs retrieval + the model rerank
directly (no agent loop). Prints candidates, selected skills and decisions so
the routing quality is visible without spending a full task budget.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import sys
import threading
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

source = BASE / "data"
target = BASE / ".qa-data" / f"probe-{int(time.time())}"
target.mkdir(parents=True, exist_ok=True)
for name in ("xinxin.sqlite3", "vault.key"):
    if (source / name).exists():
        shutil.copy2(source / name, target / name)
if (source / "skills").exists():
    shutil.copytree(source / "skills", target / "skills")

os.environ["XINXIN_DATA_DIR"] = str(target)
os.environ["XINXIN_SKILLNET_MODE"] = "fabric"
os.environ["XINXIN_SKILLNET_RERANK"] = "1"

from app.config import Config  # noqa: E402
from app.model import ModelGateway  # noqa: E402
from app.skills import SkillRouter  # noqa: E402
from app.store import Store  # noqa: E402

config = Config.from_env()
store = Store(config.data_dir)
router = SkillRouter(store)

QUERY = sys.argv[1] if len(sys.argv) > 1 else "把实验数据画成散点图并导出可复现脚本"


async def main() -> None:
    matches = router.search(QUERY, k=4, mode="fabric")
    print("mode:", matches["mode"], "| candidates:", len(matches["candidates"]))
    for item in matches["candidates"]:
        print(f"  {item['id'][:52]:54} {item['score']:.4f}  {list(item['channels'])}")
    print("decision:", matches["decision"], "-", matches["decision_reason"])

    row = store.one("SELECT value FROM settings WHERE key='model'")
    import json

    model = json.loads(row["value"]) if row else "deepseek-flash"
    url_row = store.one("SELECT value FROM settings WHERE key='model_url'")
    url = json.loads(url_row["value"]) if url_row else config.model_url
    from app.auth import Auth

    key = Auth(store).secret("model_api_key")
    if not key:
        print("no model key configured; skipping rerank")
        return

    gateway = ModelGateway(
        url=url,
        model=model,
        key=key,
        record_usage=lambda _usage: None,
        cancelled=threading.Event(),
        max_calls=4,
    )
    messages = router.rerank_messages(QUERY, matches)
    reply = await gateway.apredict(messages, stream=False, temperature=0.0)
    output = router.parse_rerank_output(reply.get("content", ""))
    print("\nrerank output:", json.dumps(output, ensure_ascii=False)[:600])
    applied = router.apply_rerank(matches, output, k=4)
    print("\nllm_rerank:", applied["components"]["llm_rerank"], "degraded:", applied["degraded"])
    print("selection:", applied["selection"]["method"], "abstained:", applied["selection"]["abstained"])
    for item in applied["skills"]:
        print(f"  -> {item['id']}  note={item.get('note', '')[:60]}")
    print("order:", applied["order"])


asyncio.run(main())
shutil.rmtree(target, ignore_errors=True)
