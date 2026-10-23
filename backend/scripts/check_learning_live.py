"""Opt-in, bounded real-model smoke check. Never writes the owner's database.

Private test material/results go only to backend/.qa-data. Nothing is sent unless
--live and the exact configured --allow-host are supplied by the operator.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sqlite3
import sys
import threading
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cryptography.fernet import Fernet
from app.config import Config
from app.learning_studio import analyze, execute, generate_batch, review_batch, snapshot, solve_blind
from app import learning_visual as visual
from app.model import ModelGateway
from app.store import Store, encode, now, uid


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--allow-host", default="")
    parser.add_argument("--read-mode", choices=("text", "pdf"), default="text")
    parser.add_argument("--mode", choices=("auto", "original", "practice"), default="auto")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--pipeline", action="store_true", help="Run the production generation/review/save/recovery loop in the isolated check database")
    action.add_argument("--review-saved", action="store_true", help="Recheck previously saved private questions using the current production critic")
    action.add_argument("--solve-saved", action="store_true", help="Blind-solve private saved questions without showing their answers or explanations")
    parser.add_argument("--pages", help="Optional PDF physical page range inside this source, e.g. 4-6")
    parser.add_argument("--count", type=int, choices=range(1, 7), default=3)
    parser.add_argument("--max-calls", type=int, choices=range(1, 13), default=3)
    parser.add_argument("--ledger", type=Path, required=True, help="Private cumulative call ledger for this explicit authorization")
    parser.add_argument("--ledger-limit", type=int, choices=range(1, 13), default=12, help="Cumulative authorized calls, at most 12")
    parser.add_argument("--reuse-check", type=Path, help="Reuse an earlier private check's material analysis")
    return parser.parse_args()


async def check(args):
    if not args.live or not args.allow_host:
        raise ValueError("未启用真实调用；需要 --live 和已授权的 --allow-host")
    config = Config.from_env()
    with sqlite3.connect(config.data_dir.joinpath("xinxin.sqlite3").as_uri() + "?mode=ro", uri=True) as owner:
        owner.row_factory = sqlite3.Row
        def setting(name, default=""):
            row = owner.execute("SELECT value FROM settings WHERE key=?", (name,)).fetchone()
            return json.loads(row[0]) if row else default
        url, model = setting("model_url", config.model_url), setting("model", config.model)
        if urlsplit(url).hostname != args.allow_host:
            raise ValueError("当前模型目的地与授权主机不一致，未发送")
        row = owner.execute("SELECT s.*,c.title AS chapter_title,b.file_id FROM learning_sources s JOIN book_chapters c ON c.id=s.chapter_id JOIN books b ON b.id=s.book_id WHERE s.id=?", (args.source_id,)).fetchone()
        if not row:
            raise ValueError("找不到指定学习片段")
        unit = dict(row)
        original = owner.execute("SELECT path FROM files WHERE id=?", (unit["file_id"],)).fetchone()
        path = Path(original[0]).resolve() if original else None
        encrypted = setting("secret:model_api_key")
        key = Fernet(config.data_dir.joinpath("vault.key").read_bytes()).decrypt(encrypted.encode()).decode() if encrypted else config.api_key
    if not key:
        raise ValueError("未配置模型密钥")
    if args.pages:
        pages = [int(value) for value in args.pages.split("-")]
        start, end = pages[0], pages[-1]
        if args.read_mode != "pdf" or not unit["page_from"] or not unit["page_from"] <= start <= end <= unit["page_to"] or end - start > 2:
            raise ValueError("诊断原页必须在此片段内，单次最多 3 页")
        unit |= {"page_from": start, "page_to": end}
    elif args.read_mode == "pdf" and (unit["page_to"] or 0) - (unit["page_from"] or 0) > 2:
        raise ValueError("请通过 --pages 明确选择此片段内最多 3 页用于诊断")
    ledger_path = args.ledger.resolve()
    private_root = Path(__file__).resolve().parents[1] / ".qa-data"
    if not ledger_path.is_relative_to(private_root.resolve()):
        raise ValueError("调用台账必须位于 backend/.qa-data")
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {"calls": 0, "tokens": 0}
    baseline_calls, baseline_tokens = ledger["calls"], ledger["tokens"]
    if baseline_calls + args.max_calls > args.ledger_limit:
        raise ValueError(f"本次检查将超过已授权的累计 {args.ledger_limit} 次调用上限")
    check_path = args.reuse_check.resolve() if args.reuse_check else ledger_path.parent / ("check-" + str(now()))
    if not check_path.is_relative_to(private_root.resolve()) or (args.reuse_check and not (check_path / "xinxin.sqlite3").is_file()):
        raise ValueError("复用检查必须位于 backend/.qa-data 且数据库已存在")
    store = Store(check_path)
    if args.reuse_check:
        saved = store.one("SELECT * FROM learning_sources WHERE id=?", (unit["id"],))
        if not saved or any(saved[field] != unit[field] for field in ("content", "page_from", "page_to")):
            raise ValueError("此前检查的材料或页码与本次不一致")
    else:
        with store.connect(write=True) as db:
            db.execute("INSERT INTO books(id,file_id,title,created,updated) VALUES(?,?,?,?,?)", (unit["book_id"], unit["file_id"], "私有诊断副本", now(), now()))
            db.execute("INSERT INTO book_chapters(id,book_id,idx,title,content,created) VALUES(?,?,?,?,?,?)", (unit["chapter_id"], unit["book_id"], 0, unit["chapter_title"], unit["content"], now()))
            db.execute("INSERT INTO learning_sources VALUES(?,?,?,?,?,?,?,?)", tuple(unit[field] for field in ("id", "book_id", "chapter_id", "idx", "label", "content", "page_from", "page_to")))
    class SourceFile:
        def path(self, ident):
            if ident != unit["file_id"] or path is None or not path.is_relative_to(config.data_dir.joinpath("files").resolve()):
                raise ValueError("原文件路径不在主人资料库内")
            return path
    flag = threading.Event()
    def usage(value):
        ledger_path.write_text(encode({"calls": baseline_calls + value["calls"], "tokens": baseline_tokens + value["total_tokens"]}), encoding="utf-8")
    gateway = ModelGateway(url, model, key, usage, flag, max_calls=args.max_calls, max_tokens=args.max_calls * 16000)
    print("stage: material analysis", flush=True)
    analysis = await analyze(store, gateway, unit, flag, read_mode=args.read_mode, library=SourceFile())
    if not analysis["eligible"]:
        raise ValueError(analysis["reason"])
    if args.read_mode == "pdf":
        unit |= {"content": analysis["source_text"], "page_spans": analysis["page_spans"], "source_method": "pdf_images"}
    options = {"kinds": ["single", "fill", "short"], "difficulty": 0, "mode": args.mode, "focus": "",
               "count": args.count, "read_mode": args.read_mode, "analyze_only": False, "page_ranges": {}}
    if args.review_saved or args.solve_saved:
        if not args.reuse_check:
            raise ValueError("复核既有题目必须指定隔离诊断目录")
        candidates = store.all("SELECT * FROM questions WHERE source_id=? ORDER BY created,rowid", (unit["id"],))
        if not 1 <= len(candidates) <= 6:
            raise ValueError("仅可复核隔离目录中的 1～6 道题")
        for row in candidates:
            for key in ("options", "tags", "source_pages"):
                row[key] = json.loads(row[key])
        if args.solve_saved:
            images = await visual.image_messages(SourceFile().path(unit["file_id"]), sorted({page for row in candidates for page in row["source_pages"]}), flag) if args.read_mode == "pdf" else []
            solutions = await solve_blind(gateway, unit, candidates, images)
            store.directory.joinpath("blind-" + str(now()) + ".private.json").write_text(json.dumps(solutions, ensure_ascii=False, indent=2), encoding="utf-8")
            print(encode({"blind_solved": len(solutions), "solvable": sum(row["solvable"] for row in solutions),
                          "calls": gateway.calls, "tokens": gateway.tokens, "owner_database_written": False}))
            return 0
        print("stage: current independent review of saved private questions", flush=True)
        decisions = await review_batch(gateway, unit, analysis, candidates, [], store=store, library=SourceFile(), flag=flag)
        store.directory.joinpath("recheck-" + str(now()) + ".private.json").write_text(json.dumps({"questions": candidates, "reviews": decisions}, ensure_ascii=False, indent=2), encoding="utf-8")
        accepted = sum(decision[0] for decision in decisions)
        print(encode({"reviewed": len(candidates), "accepted": accepted, "rejected": len(candidates) - accepted,
                      "calls": gateway.calls, "tokens": gateway.tokens, "owner_database_written": False}))
        return 0
    if args.pipeline:
        job_id, run_id = uid(), uid()
        with store.connect(write=True) as db:
            db.execute("INSERT INTO runs(id,conversation_id,task,status,permission,max_calls,max_seconds,created,updated) VALUES(?,?,?,'running','read',?,900,?,?)",
                       (run_id, "private-check", "隔离真实出题验证", args.max_calls, now(), now()))
            db.execute("INSERT INTO learning_generations VALUES(?,?,?,?,?,?,?)", (job_id, unit["book_id"], run_id, job_id, job_id, encode(options), now()))
            db.execute("INSERT INTO learning_generation_items(job_id,source_id,target) VALUES(?,?,?)", (job_id, unit["id"], args.count))
        print("stage: production generation, review and incremental save", flush=True)
        await execute(store, gateway, job_id, run_id, flag, library=SourceFile())
        store.execute("UPDATE runs SET status='completed' WHERE id=?", (run_id,))
        job = snapshot(store, job_id)
        saved = store.all("SELECT kind,stem,answer,explanation,source_quote,source_pages,origin FROM questions WHERE generation_id=?", (job_id,))
        result = json.dumps({"analysis": analysis, "job": job, "accepted_questions": saved}, ensure_ascii=False, indent=2)
        store.directory.joinpath("results-" + job_id + ".private.json").write_text(result, encoding="utf-8")
        store.directory.joinpath("results.private.json").write_text(result, encoding="utf-8")
        print(encode({"mode": args.read_mode, "generation_mode": args.mode, "pipeline": True,
            "status": job["status"], "target": job["target"], "accepted": job["created_count"],
            "exercises": len(analysis["exercises"]), "calls": gateway.calls, "tokens": gateway.tokens,
            "owner_database_written": False}))
        return 0 if saved else 1
    reasons = []
    print("stage: question generation", flush=True)
    candidates, rejected, duplicates = await generate_batch(gateway, unit, analysis,
        options, args.count, [], reasons, [])
    store.directory.joinpath("candidates.private.json").write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")
    print("stage: independent review; candidates=" + str(len(candidates)), flush=True)
    decisions = await review_batch(gateway, unit, analysis, candidates, [], store=store, library=SourceFile(), flag=flag) if candidates else []
    accepted = [row for row, decision in zip(candidates, decisions) if decision[0]]
    store.directory.joinpath("results.private.json").write_text(json.dumps({"analysis": analysis, "candidates": candidates, "reviews": decisions}, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {"mode": args.read_mode, "knowledge_points": len(analysis["knowledge_points"]), "exercises": len(analysis["exercises"]),
        "analysis_skipped": analysis.get("skipped_entries", 0), "candidates": len(candidates), "accepted": len(accepted),
        "invalid": rejected, "duplicates": duplicates, "calls": gateway.calls, "tokens": gateway.tokens,
        "owner_database_written": False, "reasons": reasons}
    print(encode(result))
    return 0 if accepted else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        raise SystemExit(asyncio.run(check(arguments())))
    except (ValueError, RuntimeError) as error:
        print(str(error))
        raise SystemExit(1)
