from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Request,
    UploadFile,
    File,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from .agent import TaskManager
from .auth import Auth, password_hash, password_matches
from .config import (
    Config, ROOT, DEFAULT_MODEL_CALLS, DEFAULT_TASK_SECONDS,
    TOKENS_PER_MODEL_CALL, CONTEXT_WINDOW_TOKENS, CONTEXT_INPUT_TOKENS,
)
from .creative import gallery, plot_csv, transform_image
from .conversations import deletion_preview, purge_conversation, batch_deletion_preview, purge_conversations
from .files import FileLibrary, FileTooLarge, UploadConflict
from . import imagegen
from .model import endpoint
from .mail import MailCodes
from .skills import SkillRouter
from .store import Store, encode, now, uid
from .uploads import UploadGuard, finish_upload


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Login(Input):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class Setup(Login):
    setup_code: str = Field(min_length=1, max_length=200)


class Password(Input):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    current: str
    password: str = Field(min_length=10, max_length=256)


class Conversation(Input):
    title: str = Field(default="新对话", min_length=1, max_length=80)


class EmailAddress(Input):
    email: str = Field(
        max_length=254,
        pattern=r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
    )


class EmailRequest(EmailAddress):
    scene: Literal["login", "reset"] = "login"


class EmailLogin(EmailAddress):
    code: str = Field(pattern=r"^\d{6}$")


class EmailReset(EmailLogin):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    password: str = Field(min_length=10, max_length=256)


class EmailSettings(EmailAddress):
    smtp_host: str = Field(default="smtp.qq.com", pattern=r"^[A-Za-z0-9.-]{1,200}$")
    smtp_port: int = Field(default=465, ge=1, le=65535)
    smtp_mode: Literal["ssl", "starttls"] = "ssl"
    smtp_username: str = Field(default="", max_length=254, pattern=r"^[\x21-\x7e]*$")
    smtp_password: str = Field(default="", max_length=500, pattern=r"^[\x21-\x7e]*$")


class ExecutionInput(Input):
    permission: Literal["read", "workspace", "full"] = "read"
    server_id: str | None = None
    max_calls: int = Field(default=DEFAULT_MODEL_CALLS, ge=1, le=128)
    max_seconds: int = Field(default=DEFAULT_TASK_SECONDS, ge=10, le=7200)
    max_total_tokens: int | None = Field(default=None, ge=5000, le=100000000)
    context_window_tokens: Literal[80000, 300000, 1048576] | None = None
    request_key: str = Field(min_length=8, max_length=100)
    file_ids: list[str] = Field(default_factory=list, max_length=10)
    allow_memory: bool = False


class RunInput(ExecutionInput):
    task: str = Field(min_length=1, max_length=12000)
    conversation_id: str | None = None


class ContinueInput(ExecutionInput):
    instruction: str = Field(default="", max_length=4000)


class ConversationSelection(Input):
    ids: list[str] = Field(min_length=1, max_length=100)


class ConversationContext(Input):
    context_window_tokens: Literal[80000, 300000, 1048576]


class Record(Input):
    kind: Literal["article", "collection", "photo", "poem", "resume"]
    payload: dict


class Server(Input):
    name: str = Field(min_length=1, max_length=80)
    host: str = Field(pattern=r"^[A-Za-z0-9_.:-]{1,200}$")
    port: int = Field(default=22, ge=1, le=65535)
    username: str = Field(default="root", pattern=r"^[A-Za-z0-9_.-]{1,80}$")
    workdir: str = Field(default="/srv/xinxin", pattern=r"^/[A-Za-z0-9_./-]{1,200}$")
    host_key: str = Field(default="", max_length=10000)
    private_key: str = Field(default="", max_length=20000)


class Settings(Input):
    model: str | None = Field(default=None, max_length=120)
    model_url: str | None = Field(default=None, max_length=500)
    model_api_key: str | None = Field(
        default=None, max_length=500, pattern=r"^[\x21-\x7e]*$"
    )
    image_url: str | None = Field(default=None, max_length=500)
    image_model: str | None = Field(default=None, max_length=120)
    image_api_key: str | None = Field(
        default=None, max_length=500, pattern=r"^[\x21-\x7e]*$"
    )


class Memory(Input):
    content: str = Field(min_length=1, max_length=1000)
    category: str = Field(default="preference", max_length=30)


class Plot(Input):
    file_id: str
    x: str = Field(max_length=200)
    y: str = Field(max_length=200)
    kind: Literal["line", "bar", "scatter", "hist"] = "line"
    title: str = Field(default="数据观察", max_length=100)
    palette: str = "teal"
    request_key: str = Field(min_length=8, max_length=100)


class ImageTransform(Input):
    file_id: str
    style: Literal["collage", "distillation"]
    instruction: str = Field(default="", max_length=3000)
    request_key: str = Field(min_length=8, max_length=100)


class Schedule(Input):
    title: str = Field(min_length=1, max_length=100)
    task: str = Field(min_length=1, max_length=12000)
    interval_minutes: int = Field(ge=5, le=525600)
    enabled: bool = True
    permission: Literal["read", "workspace", "full"] = "read"
    server_id: str | None = None


class SkillFeedback(Input):
    run_id: str
    reward: float = Field(ge=0, le=1, allow_inf_nan=False)


class ImageRequest(Input):
    prompt: str = Field(min_length=1, max_length=2000)
    width: int = Field(default=1024, ge=256, le=1440)
    height: int = Field(default=1024, ge=256, le=1440)
    provider: str = Field(default="", max_length=40)
    seed: int | None = Field(default=None, ge=0, le=2_000_000)


def _selected_skill_ids(events: list) -> list[str]:
    """从 skills 事件行里取出被选中的技能 ID（数据形如 {"skills": [...]}）。"""
    names: list[str] = []
    for event in events:
        try:
            data = json.loads(event["data"])
        except (ValueError, TypeError, KeyError):
            continue
        skills = data.get("skills") if isinstance(data, dict) else data
        if not isinstance(skills, list):
            continue
        for skill in skills:
            ident = skill.get("id") if isinstance(skill, dict) else skill
            if isinstance(ident, str) and ident:
                names.append(ident)
    return names


def create_app(config=None):
    config = config or Config.from_env()
    store = Store(config.data_dir)
    auth = Auth(store)
    mail = MailCodes(store, auth)
    library = FileLibrary(store)
    router = SkillRouter(store)
    manager = TaskManager(store, auth, config, library, router)

    async def scheduled_jobs():
        while True:
            await asyncio.sleep(15)
            for row in store.all(
                "SELECT * FROM schedules WHERE enabled=1 AND next_at<=?", (now(),)
            ):
                try:
                    # Only one process may lease a due occurrence.
                    claimed = store.execute(
                        "UPDATE schedules SET next_at=? WHERE id=? AND next_at=?",
                        (
                            now() + row["interval_minutes"] * 60000,
                            row["id"],
                            row["next_at"],
                        ),
                    )
                    if claimed:
                        await manager.submit(
                            row["task"],
                            permission=row["permission"],
                            server_id=row["server_id"],
                            request_key=f"schedule:{row['id']}:{row['next_at']}",
                        )
                except Exception as exc:
                    store.audit(
                        "schedule.failed", {"id": row["id"], "error": str(exc)[:300]}
                    )

    @asynccontextmanager
    async def lifespan(app):
        scheduler = asyncio.create_task(scheduled_jobs())
        yield
        scheduler.cancel()
        await asyncio.gather(scheduler, return_exceptions=True)
        await manager.close()

    app = FastAPI(title="Xinxin Private Agent", version="0.1.0", lifespan=lifespan)
    app.state.store, app.state.auth, app.state.manager = store, auth, manager
    app.state.library, app.state.router, app.state.config = library, router, config
    app.state.mail = mail
    app.add_middleware(UploadGuard, auth=auth)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.origins),
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "Last-Event-ID", "X-Upload-ID"],
        expose_headers=["Content-Disposition"],
    )

    def owner(authorization: str | None = Header(default=None)):
        return auth.require(authorization)

    def require_row(table, ident):
        if table not in {
            "runs",
            "files",
            "records",
            "memories",
            "schedules",
            "conversations",
        }:
            raise ValueError("未知表")
        row = store.one(f"SELECT * FROM {table} WHERE id=?", (ident,))
        if not row:
            raise HTTPException(404, "内容不存在")
        return row

    @app.exception_handler(ValueError)
    async def value_error(request, exc):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        from fastapi.responses import JSONResponse

        # Pydantic's default input/context can echo passwords and private keys.
        return JSONResponse(
            status_code=422,
            content={
                "detail": [
                    {
                        "loc": list(error["loc"]),
                        "type": error["type"],
                        "msg": "字段格式或长度不符合要求",
                    }
                    for error in exc.errors()
                ]
            },
        )

    @app.get("/health")
    def health():
        return {"status": "ok", "product": "Xinxin", "version": "0.1.0"}

    @app.get("/api/v1/auth/status")
    def auth_status():
        return {
            "configured": bool(store.one("SELECT id FROM owner")),
            "registration": "disabled",
            "email_enabled": mail.enabled(),
        }

    @app.post("/api/v1/auth/setup")
    def setup(body: Setup):
        if len(body.password) < 10:
            raise HTTPException(422, "密码至少 10 个字符")
        if not hmac.compare_digest(body.setup_code, config.setup_token):
            raise HTTPException(403, "初始化码不正确，请查看后端 data/bootstrap.code")
        try:
            store.execute(
                "INSERT INTO owner VALUES(1,?,?)",
                (body.name, password_hash(body.password)),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(409, "主人账号已初始化，不能公开注册") from None
        store.audit("owner.created", {})
        return {"token": auth.issue(), "name": body.name}

    @app.post("/api/v1/auth/login")
    def login(body: Login, request: Request):
        token = auth.login(
            body.name, body.password, request.client.host if request.client else "local"
        )
        return {"token": token, "name": body.name}

    @app.post("/api/v1/auth/email/code")
    def email_code(body: EmailRequest, request: Request):
        return mail.send(
            body.email.strip().lower(),
            body.scene,
            request.client.host if request.client else "local",
        )

    @app.post("/api/v1/auth/email/login")
    def email_login(body: EmailLogin):
        mail.consume(body.email.strip().lower(), "login", body.code, lambda db: None)
        store.audit("owner.email_login", {})
        return {
            "token": auth.issue(),
            "name": store.one("SELECT name FROM owner WHERE id=1")["name"],
        }

    @app.post("/api/v1/auth/email/reset")
    def email_reset(body: EmailReset):
        def update(db):
            db.execute(
                "UPDATE owner SET password=? WHERE id=1",
                (password_hash(body.password),),
            )
            db.execute("DELETE FROM sessions")
            db.execute("UPDATE email_codes SET used=1")

        mail.consume(body.email.strip().lower(), "reset", body.code, update)
        store.audit("owner.password_reset", {})
        return {
            "token": auth.issue(),
            "name": store.one("SELECT name FROM owner WHERE id=1")["name"],
        }

    @app.get("/api/v1/settings/email", dependencies=[Depends(owner)])
    def email_settings():
        config = mail.configuration()
        return {
            **{key: value for key, value in config.items() if key != "smtp_password"},
            "configured": bool(config["smtp_password"]),
        }

    @app.put("/api/v1/settings/email", dependencies=[Depends(owner)])
    def save_email_settings(body: EmailSettings):
        mail.configure(body.model_dump())
        store.audit("email.configured", {})
        return email_settings()

    @app.get("/api/v1/auth/me", dependencies=[Depends(owner)])
    def me():
        return {"name": store.one("SELECT name FROM owner WHERE id=1")["name"]}

    @app.post("/api/v1/auth/logout")
    def logout(token=Depends(owner)):
        store.execute(
            "DELETE FROM sessions WHERE hash=?",
            (hashlib.sha256(token.encode()).hexdigest(),),
        )
        return {"ok": True}

    @app.put("/api/v1/auth/password", dependencies=[Depends(owner)])
    def password(body: Password):
        row = store.one("SELECT password FROM owner WHERE id=1")
        if not password_matches(body.current, row["password"]):
            raise HTTPException(400, "原密码不正确")
        with store.connect(write=True) as db:
            db.execute(
                "UPDATE owner SET password=? WHERE id=1",
                (password_hash(body.password),),
            )
            db.execute("DELETE FROM sessions")
        return {"token": auth.issue()}

    @app.get("/api/v1/dashboard", dependencies=[Depends(owner)])
    def dashboard():
        counts = {
            row["kind"]: row["n"]
            for row in store.all("SELECT kind,COUNT(*) n FROM records GROUP BY kind")
        }
        counts["files"] = store.one("SELECT COUNT(*) n FROM files")["n"]
        today = (now() + 28800000) // 86400000
        days = {
            row["day"]: row
            for row in store.all(
                "SELECT CAST((created+28800000)/86400000 AS INTEGER) day,COUNT(*) total,SUM(status='completed') completed FROM runs WHERE created>=? GROUP BY day",
                ((today - 6) * 86400000 - 28800000,),
            )
        }
        return {
            "daily_activity": [
                {
                    "timestamp": day * 86400000 - 28800000,
                    "total": days.get(day, {}).get("total", 0),
                    "completed": days.get(day, {}).get("completed", 0),
                }
                for day in range(today - 6, today + 1)
            ],
            "task_counts": {
                row["status"]: row["n"]
                for row in store.all(
                    "SELECT status,COUNT(*) n FROM runs GROUP BY status"
                )
            },
            "servers": counts.get("server", 0),
            "automations": store.one(
                "SELECT COUNT(*) n FROM schedules WHERE enabled=1"
            )["n"],
            "counts": counts,
            "tasks": store.all("SELECT * FROM runs ORDER BY created DESC LIMIT 5"),
            "recent_files": [
                library.get(row["id"])
                for row in store.all(
                    "SELECT id FROM files ORDER BY created DESC LIMIT 4"
                )
            ],
            "model_configured": bool(manager.model_config()[2]),
            "model": manager.model_config()[1],
            "skills": len(router.all()),
            "active_tasks": store.one(
                "SELECT COUNT(*) n FROM runs WHERE status IN ('queued','running','cancelling')"
            )["n"],
        }

    @app.get("/api/v1/conversations", dependencies=[Depends(owner)])
    def conversations(archived: bool = False):
        return store.all(
            "SELECT * FROM conversations WHERE archived=? ORDER BY updated DESC LIMIT 200",
            (int(archived),),
        )

    @app.post("/api/v1/conversations", dependencies=[Depends(owner)])
    def new_conversation(body: Conversation):
        return {"id": manager.conversation(body.title)}

    @app.get("/api/v1/conversations/{ident}", dependencies=[Depends(owner)])
    def conversation(ident: str):
        row = require_row("conversations", ident)
        choice = store.one("SELECT context_window_tokens FROM conversation_options WHERE conversation_id=?", (ident,))
        return {
            **row,
            "context_window_tokens": choice["context_window_tokens"] if choice else CONTEXT_WINDOW_TOKENS,
            "messages": store.all(
                "SELECT m.*,mr.run_id FROM messages m LEFT JOIN message_runs mr "
                "ON mr.message_id=m.id WHERE m.conversation_id=? ORDER BY m.created,m.rowid",
                (ident,),
            ),
            "runs": store.all(
                "SELECT * FROM runs WHERE conversation_id=? ORDER BY created DESC",
                (ident,),
            ),
        }

    @app.put("/api/v1/conversations/{ident}/context", dependencies=[Depends(owner)])
    async def change_conversation_context(ident: str, body: ConversationContext):
        require_row("conversations", ident)
        if manager.maintenance.is_set() or store.one(
            "SELECT id FROM runs WHERE conversation_id=? AND status IN ('queued','running','cancelling') LIMIT 1", (ident,),
        ):
            raise HTTPException(409, "请等待本轮结束后再切换上下文档位")
        store.execute(
            "INSERT INTO conversation_options VALUES(?,?) ON CONFLICT(conversation_id) "
            "DO UPDATE SET context_window_tokens=excluded.context_window_tokens", (ident, body.context_window_tokens),
        )
        return {"context_window_tokens": body.context_window_tokens}

    @app.get("/api/v1/conversations/{ident}/deletion-preview", dependencies=[Depends(owner)])
    async def preview_conversation_deletion(ident: str):
        require_row("conversations", ident)
        return await asyncio.to_thread(deletion_preview, store, ident)

    @app.delete("/api/v1/conversations/{ident}/permanent", dependencies=[Depends(owner)])
    async def erase_conversation(ident: str):
        require_row("conversations", ident)
        return await erase_selected([ident])

    @app.post("/api/v1/conversations/batch/deletion-preview", dependencies=[Depends(owner)])
    async def preview_batch_conversation_deletion(body: ConversationSelection):
        return await asyncio.to_thread(batch_deletion_preview, store, body.ids)

    @app.post("/api/v1/conversations/batch/permanent", dependencies=[Depends(owner)])
    async def erase_batch_conversations(body: ConversationSelection):
        return await erase_selected(body.ids)

    async def erase_selected(ids):
        if manager.maintenance.is_set() or store.one(
            "SELECT id FROM runs WHERE status IN ('queued','running','cancelling') LIMIT 1"
        ):
            raise HTTPException(409, "请先停止运行任务，再永久删除对话")
        manager.maintenance.set()
        pending = asyncio.create_task(asyncio.to_thread(purge_conversations, store, library, ids))
        try:
            return await asyncio.shield(pending)
        finally:
            try:
                while not pending.done():
                    try:
                        await asyncio.shield(pending)
                    except asyncio.CancelledError:
                        continue
            finally:
                manager.maintenance.clear()

    @app.delete("/api/v1/conversations/{ident}", dependencies=[Depends(owner)])
    def delete_conversation(ident: str):
        require_row("conversations", ident)
        if store.one(
            "SELECT id FROM runs WHERE conversation_id=? AND status IN ('queued','running','cancelling')",
            (ident,),
        ):
            raise HTTPException(409, "请先停止此对话的运行任务")
        store.execute(
            "UPDATE conversations SET archived=1,updated=? WHERE id=?", (now(), ident)
        )
        return {"ok": True}

    @app.put("/api/v1/conversations/{ident}", dependencies=[Depends(owner)])
    def rename_conversation(ident: str, body: Conversation):
        require_row("conversations", ident)
        store.execute(
            "UPDATE conversations SET title=?,updated=? WHERE id=?",
            (body.title, now(), ident),
        )
        return require_row("conversations", ident)

    @app.post("/api/v1/conversations/{ident}/restore", dependencies=[Depends(owner)])
    def restore_conversation(ident: str):
        require_row("conversations", ident)
        store.execute(
            "UPDATE conversations SET archived=0,updated=? WHERE id=?", (now(), ident)
        )
        return require_row("conversations", ident)

    @app.get("/api/v1/runs", dependencies=[Depends(owner)])
    def runs(limit: int = Query(default=100, ge=1, le=200)):
        return store.all("SELECT * FROM runs ORDER BY created DESC LIMIT ?", (limit,))

    @app.post("/api/v1/runs", dependencies=[Depends(owner)])
    async def submit(body: RunInput):
        task = body.task
        if body.file_ids:
            attachments = [library.get(ident) for ident in body.file_ids]
            task += "\n\n本轮附件（使用文件工具读取）：" + encode(
                [{"id": f["id"], "name": f["name"]} for f in attachments]
            )
        existing = store.one(
            "SELECT max_calls,max_seconds FROM runs WHERE request_key=?",
            (body.request_key,),
        )
        calls, seconds = body.max_calls, body.max_seconds
        if existing:
            if "max_calls" not in body.model_fields_set:
                calls = existing["max_calls"]
            if "max_seconds" not in body.model_fields_set:
                seconds = existing["max_seconds"]
        return await manager.submit(
            task,
            body.conversation_id,
            body.permission,
            body.server_id,
            calls,
            seconds,
            body.request_key,
            allow_memory=body.allow_memory,
            max_total_tokens=body.max_total_tokens,
            context_window_tokens=body.context_window_tokens,
        )

    @app.get("/api/v1/runs/{ident}", dependencies=[Depends(owner)])
    def run_detail(ident: str):
        return {
            **require_row("runs", ident),
            "files": [
                library.get(row["id"])
                for row in store.all("SELECT id FROM files WHERE run_id=?", (ident,))
            ],
        }

    @app.post("/api/v1/runs/{ident}/continue", dependencies=[Depends(owner)])
    async def continue_run(ident: str, body: ContinueInput):
        parent = require_row("runs", ident)
        original, visited = parent, {ident}
        while original.get("resume_of"):
            previous = original["resume_of"]
            if previous in visited or len(visited) >= 128:
                raise HTTPException(400, "任务续接链异常，请从当前对话核对后重试")
            visited.add(previous)
            original = store.one("SELECT * FROM runs WHERE id=? AND conversation_id=?", (previous, parent["conversation_id"]))
            if not original:
                raise HTTPException(400, "原任务记录缺失，无法安全续接")
        task = (
            "继续完成以下原任务目标（原文中的旧预算和旧权限不适用于本轮）：\n"
            + original["task"]
            + "\n\n本轮续接要求：先根据检查点、工具记录、计划和实际文件/服务状态确认前轮已完成的部分，"
            "从未完成处继续；不盲目重放命令、不重复创建或覆盖。使用本轮新的预算、所选权限、服务器和记忆授权。"
        )
        if body.instruction:
            task += "\n主人本轮补充：\n" + body.instruction
        if body.file_ids:
            task += "\n本轮新增附件（使用文件工具读取）：" + encode([
                {"id": item["id"], "name": item["name"]} for item in (library.get(file) for file in body.file_ids)
            ])
        return await manager.submit(
            task, parent["conversation_id"], body.permission, body.server_id,
            body.max_calls, body.max_seconds, body.request_key,
            allow_memory=body.allow_memory, max_total_tokens=body.max_total_tokens,
            context_window_tokens=body.context_window_tokens, resume_of=ident,
            message_text="继续原任务。" + ("\n补充：" + body.instruction if body.instruction else ""),
        )

    @app.get("/api/v1/runs/{ident}/activity", dependencies=[Depends(owner)])
    def activity(ident: str):
        require_row("runs", ident)
        rows = store.all(
            "SELECT * FROM events WHERE run_id=? AND kind NOT IN ('delta','usage','skills') "
            "ORDER BY seq DESC LIMIT 5000", (ident,),
        )
        commands = set()
        result = []
        for row in rows:
            data = json.loads(row["data"])
            if row["kind"] == "command.progress":
                command = data["command_id"]
                if command in commands:
                    continue
                commands.add(command)
            result.append({**row, "data": data})
        return list(reversed(result))

    @app.post("/api/v1/runs/{ident}/cancel", dependencies=[Depends(owner)])
    async def cancel(ident: str):
        return manager.cancel(ident)

    @app.get("/api/v1/runs/{ident}/events", dependencies=[Depends(owner)])
    async def events(
        ident: str,
        request: Request,
        after: int = Query(default=0, ge=0),
        last_event_id: str | None = Header(default=None),
    ):
        require_row("runs", ident)
        if last_event_id:
            if not last_event_id.isdigit() or len(last_event_id) > 12:
                raise HTTPException(400, "无效事件游标")
            after = max(after, int(last_event_id))

        async def stream():
            cursor = after
            heartbeat = 0
            while not await request.is_disconnected():
                batch = store.events(ident, cursor)
                for event in batch:
                    yield f"id: {event['seq']}\ndata: {encode(event)}\n\n"
                    cursor = event["seq"]
                run = require_row("runs", ident)
                if run["status"] not in {
                    "queued",
                    "running",
                    "cancelling",
                } and not store.events(ident, cursor):
                    yield "event: end\ndata: {}\n\n"
                    return
                heartbeat += 1
                if heartbeat % 50 == 0:
                    yield ": keep-alive\n\n"
                await asyncio.sleep(0.2)

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/v1/skills", dependencies=[Depends(owner)])
    def skills(q: str = Query(default="", max_length=2000)):
        return router.search(q) if q else router.all()

    @app.get("/api/v1/skills/status", dependencies=[Depends(owner)])
    def skill_status():
        return {**router.status(), "corpus": router.corpus_status}

    @app.get("/api/v1/skills/graph", dependencies=[Depends(owner)])
    def skill_graph():
        return router.graph()

    @app.get("/api/v1/skills/network-model", dependencies=[Depends(owner)])
    def skill_network_model():
        return router.network_model()

    @app.get("/api/v1/skills/activity", dependencies=[Depends(owner)])
    def skill_activity(recent: int = Query(default=8, ge=1, le=30)):
        """技能运行态：完全聚合既有 runs/events，不新增存储。

        - running：处于 queued/running/cancelling 的运行中，router 已选中的技能
        - done/failed：最近结束的运行按状态映射（completed→done；
          failed/cancelled/interrupted→failed），取每个运行最后一条
          skills 事件里选中的技能。
        """
        active_runs = store.all(
            "SELECT id FROM runs WHERE status IN ('queued','running','cancelling') "
            "ORDER BY created DESC LIMIT 20",
        )
        running: list[str] = []
        for row in active_runs:
            events = store.all(
                "SELECT data FROM events WHERE run_id=? AND kind='skills' "
                "ORDER BY seq DESC LIMIT 1",
                (row["id"],),
            )
            running.extend(_selected_skill_ids(events))
        finished: list[dict] = []
        for row in store.all(
            "SELECT id,status FROM runs WHERE status NOT IN "
            "('queued','running','cancelling') ORDER BY updated DESC LIMIT ?",
            (recent,),
        ):
            events = store.all(
                "SELECT data FROM events WHERE run_id=? AND kind='skills' "
                "ORDER BY seq DESC LIMIT 1",
                (row["id"],),
            )
            state = "done" if row["status"] == "completed" else "failed"
            for name in _selected_skill_ids(events):
                finished.append({"id": name, "state": state, "run_id": row["id"]})
        return {"running": sorted(set(running)), "finished": finished}

    @app.get("/api/v1/images/providers", dependencies=[Depends(owner)])
    def image_providers():
        return imagegen.providers()

    @app.get("/api/v1/images", dependencies=[Depends(owner)])
    def images(limit: int = Query(default=60, ge=1, le=200)):
        return imagegen.recent(library, limit)

    @app.post("/api/v1/images", dependencies=[Depends(owner)])
    async def create_image(body: ImageRequest):
        return await asyncio.to_thread(
            imagegen.generate,
            library,
            body.prompt,
            body.width,
            body.height,
            body.provider or None,
            body.seed,
        )

    @app.get("/api/v1/skills/{name}", dependencies=[Depends(owner)])
    def skill(name: str):
        return router.detail(name)

    @app.get("/api/v1/skills/{name}/resource", dependencies=[Depends(owner)])
    def skill_resource(name: str, path: str = Query(min_length=1, max_length=400)):
        return router.read_skill_resource(name, path)

    @app.post("/api/v1/skills/{name}/feedback", dependencies=[Depends(owner)])
    def skill_feedback(name: str, body: SkillFeedback):
        run = require_row("runs", body.run_id)
        if run["status"] != "completed":
            raise ValueError("只有完成的任务可以提供技能反馈")
        evidence = [
            {**event, "data": json.loads(event["data"])}
            for event in store.all(
                "SELECT kind,data FROM events WHERE run_id=? AND kind IN ('skills','tool.completed') ORDER BY seq",
                (body.run_id,),
            )
        ]
        selected = {
            skill["id"]
            for event in evidence
            if event["kind"] == "skills"
            for skill in event["data"].get("skills", [])
        }
        if name not in selected or not any(
            event["kind"] == "tool.completed"
            and event["data"].get("ok") is True
            and event["data"].get("name") in router.tools.get(name, [])
            for event in evidence
        ):
            raise ValueError("该任务没有此技能的选择与工具执行证据")
        marker = "skill-feedback:" + body.run_id + ":" + name
        with router.lock:
            if store.setting(marker) is not None:
                raise ValueError("此任务已提交过该技能的反馈")
            router.bandit.update(run["task"], name, body.reward)
            with store.connect(write=True) as db:
                db.execute(
                    "INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    ("skill-policy", encode(router.bandit.state_dict())),
                )
                db.execute(
                    "INSERT INTO settings VALUES(?,?)", (marker, encode(body.reward))
                )
        return {"ok": True, "updates": router.bandit.n_updates}

    @app.get("/api/v1/records", dependencies=[Depends(owner)])
    def records(
        kind: Literal["article", "collection", "photo", "poem", "resume"],
        q: str = Query(default="", max_length=200),
    ):
        return [
            {**row, "payload": json.loads(row["payload"])}
            for row in store.all(
                "SELECT * FROM records WHERE kind=? AND payload LIKE ? ORDER BY updated DESC LIMIT 500",
                (kind, "%" + q + "%"),
            )
        ]

    def save_record(body, ident=None):
        if len(encode(body.payload).encode()) > 500000:
            raise ValueError("内容过长")
        if (
            body.kind in {"article", "collection", "photo"}
            and not str(
                body.payload.get("title") or body.payload.get("name") or ""
            ).strip()
        ):
            raise ValueError("请填写标题")
        if body.kind == "poem" and not str(body.payload.get("content", "")).strip():
            raise ValueError("请填写诗词内容")
        if body.payload.get("file_id"):
            library.get(body.payload["file_id"])
        ident = ident or uid()
        existing = store.one("SELECT kind FROM records WHERE id=?", (ident,))
        if existing and existing["kind"] != body.kind:
            raise ValueError("内容类型不能变更")
        store.execute(
            "INSERT INTO records VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,updated=excluded.updated",
            (ident, body.kind, encode(body.payload), now(), now()),
        )
        return {**require_row("records", ident), "payload": body.payload}

    @app.post("/api/v1/records", dependencies=[Depends(owner)])
    def add_record(body: Record):
        return save_record(body)

    @app.put("/api/v1/records/{ident}", dependencies=[Depends(owner)])
    def update_record(ident: str, body: Record):
        require_row("records", ident)
        return save_record(body, ident)

    @app.delete("/api/v1/records/{ident}", dependencies=[Depends(owner)])
    def delete_record(ident: str):
        row = require_row("records", ident)
        if row["kind"] == "server":
            raise HTTPException(400, "使用服务器专属接口")
        store.execute("DELETE FROM records WHERE id=?", (ident,))
        store.audit("content.deleted", {"id": ident, "kind": row["kind"]})
        return {"ok": True}

    @app.get("/api/v1/files", dependencies=[Depends(owner)])
    def files(q: str = Query(default="", max_length=200)):
        return [
            library.get(row["id"])
            for row in store.all(
                "SELECT id FROM files WHERE name LIKE ? ORDER BY created DESC LIMIT 500",
                ("%" + q + "%",),
            )
        ]

    @app.post("/api/v1/files", dependencies=[Depends(owner)])
    async def upload(
        file: UploadFile = File(...),
        x_upload_id: str | None = Header(
            default=None, min_length=8, max_length=80, pattern=r"^[a-zA-Z0-9-]+$"
        ),
    ):
        try:
            worker = asyncio.create_task(
                asyncio.to_thread(
                    library.save_stream,
                    file.filename or "file",
                    file.file,
                    file.content_type,
                    request_id=x_upload_id,
                )
            )
            return await finish_upload(worker)
        except FileTooLarge as exc:
            raise HTTPException(413, str(exc)) from None
        except UploadConflict as exc:
            raise HTTPException(409, str(exc)) from None
        finally:
            await file.close()

    @app.get("/api/v1/files/search", dependencies=[Depends(owner)])
    def search_files(q: str = Query(min_length=1, max_length=2000)):
        return library.search(q)

    @app.get("/api/v1/files/{ident}/text", dependencies=[Depends(owner)])
    def file_text(
        ident: str,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=12000, ge=1, le=16000),
    ):
        return library.read(ident, offset, limit)

    @app.get("/api/v1/files/{ident}/metadata", dependencies=[Depends(owner)])
    def file_metadata(ident: str):
        return library.get(ident)

    @app.get("/api/v1/files/{ident}/columns", dependencies=[Depends(owner)])
    def file_columns(ident: str):
        if not library.get(ident)["name"].lower().endswith(".csv"):
            raise ValueError("请选择 CSV 文件")
        import pandas as pd

        try:
            return {"columns": list(pd.read_csv(library.path(ident), nrows=0).columns)}
        except Exception:
            raise ValueError("无法读取 CSV 列，请检查文件编码与格式") from None

    @app.get("/api/v1/files/{ident}/download", dependencies=[Depends(owner)])
    def download(ident: str, inline: bool = False):
        row = library.get(ident)
        safe_image = row["mime"] in {
            "image/png",
            "image/jpeg",
            "image/webp",
            "image/gif",
        }
        return FileResponse(
            library.path(ident),
            media_type=row["mime"] if safe_image else "application/octet-stream",
            filename=row["name"],
            content_disposition_type=(
                "inline" if inline and safe_image else "attachment"
            ),
            headers={
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "Content-Security-Policy": "sandbox; default-src 'none'",
            },
        )

    @app.delete("/api/v1/files/{ident}", dependencies=[Depends(owner)])
    def delete_file(ident: str):
        library.delete(ident)
        return {"ok": True}

    @app.get("/api/v1/servers", dependencies=[Depends(owner)])
    def servers():
        return [
            {
                "id": row["id"],
                **json.loads(row["payload"]),
                "key_configured": bool(auth.secret("ssh:" + row["id"])),
            }
            for row in store.all(
                "SELECT * FROM records WHERE kind='server' ORDER BY created DESC"
            )
        ]

    @app.post("/api/v1/servers", dependencies=[Depends(owner)])
    def add_server(body: Server):
        ident = uid()
        payload = body.model_dump(exclude={"private_key"})
        if body.private_key:
            auth.set_secret("ssh:" + ident, body.private_key)
        store.execute(
            "INSERT INTO records VALUES(?,?,?,?,?)",
            (ident, "server", encode(payload), now(), now()),
        )
        return {"id": ident, **payload, "key_configured": bool(body.private_key)}

    @app.delete("/api/v1/servers/{ident}", dependencies=[Depends(owner)])
    def delete_server(ident: str):
        row = require_row("records", ident)
        if row["kind"] != "server":
            raise HTTPException(404, "服务器不存在")
        if store.one(
            "SELECT id FROM runs WHERE server_id=? AND status IN ('queued','running','cancelling')",
            (ident,),
        ):
            raise HTTPException(409, "请先停止该服务器的活动任务")
        store.execute("DELETE FROM records WHERE id=?", (ident,))
        store.execute("DELETE FROM settings WHERE key=?", ("secret:ssh:" + ident,))
        return {"ok": True}

    @app.put("/api/v1/servers/{ident}", dependencies=[Depends(owner)])
    def update_server(ident: str, body: Server):
        row = require_row("records", ident)
        if row["kind"] != "server":
            raise HTTPException(404, "服务器不存在")
        if store.one(
            "SELECT id FROM runs WHERE server_id=? AND status IN ('queued','running','cancelling')",
            (ident,),
        ):
            raise HTTPException(409, "请先停止该服务器的活动任务，再修改连接信息")
        payload = body.model_dump(exclude={"private_key"})
        if body.private_key:
            auth.set_secret("ssh:" + ident, body.private_key)
        store.execute(
            "UPDATE records SET payload=?,updated=? WHERE id=?",
            (encode(payload), now(), ident),
        )
        store.audit("server.updated", {"id": ident})
        return {
            "id": ident,
            **payload,
            "key_configured": bool(auth.secret("ssh:" + ident)),
        }

    @app.get("/api/v1/memories", dependencies=[Depends(owner)])
    def memories():
        return store.all("SELECT * FROM memories ORDER BY created DESC")

    @app.post("/api/v1/memories", dependencies=[Depends(owner)])
    def memory(body: Memory):
        ident = uid()
        store.execute(
            "INSERT INTO memories VALUES(?,?,?,?)",
            (ident, body.content, body.category, now()),
        )
        return {"id": ident, **body.model_dump()}

    @app.put("/api/v1/memories/{ident}", dependencies=[Depends(owner)])
    def update_memory(ident: str, body: Memory):
        require_row("memories", ident)
        store.execute(
            "UPDATE memories SET content=?,category=? WHERE id=?",
            (body.content, body.category, ident),
        )
        return {"id": ident, **body.model_dump()}

    @app.delete("/api/v1/memories/{ident}", dependencies=[Depends(owner)])
    def delete_memory(ident: str):
        store.execute("DELETE FROM memories WHERE id=?", (ident,))
        return {"ok": True}

    @app.get("/api/v1/settings", dependencies=[Depends(owner)])
    def settings():
        url, model, key = manager.model_config()
        return {
            "model_url": url,
            "model": model,
            "model_configured": bool(key),
            "image_url": store.setting("image_url", ""),
            "image_model": store.setting("image_model", "gpt-image-1"),
            "image_configured": bool(auth.secret("image_api_key")),
            "zine_installed": (
                store.directory / "skills/scenes-gathered-zine-v1-3/SKILL.md"
            ).exists(),
            "registration": "disabled",
            "context_window_tokens": CONTEXT_WINDOW_TOKENS,
            "context_input_budget_tokens": CONTEXT_INPUT_TOKENS,
            "context_counting": "DeepSeek-V4.1 BPE with protocol/output reserve",
            "context_tiers": [{"label": "80K", "tokens": 80000}, {"label": "300K", "tokens": 300000}, {"label": "1000K", "tokens": CONTEXT_WINDOW_TOKENS}],
            "execution_defaults": {
                "max_calls": DEFAULT_MODEL_CALLS, "max_seconds": DEFAULT_TASK_SECONDS,
                "max_total_tokens": DEFAULT_MODEL_CALLS * TOKENS_PER_MODEL_CALL,
            },
            "execution_limits": {"max_calls": 128, "max_seconds": 7200, "max_total_tokens": 100000000},
            "capabilities": {
                "run_token_budget": True, "run_recovery": True,
                "context_checkpoints": True, "command_progress": True,
                "managed_ssh_cancellation": True,
                "conversation_delete": True,
                "context_tiers": True,
                "public_progress": True,
                "run_continuation": True,
                "conversation_batch_delete": True,
            },
        }

    @app.put("/api/v1/settings", dependencies=[Depends(owner)])
    def save_settings(body: Settings):
        values = body.model_dump(exclude_none=True)
        if "model" in values and not values["model"]:
            raise ValueError("模型 ID 不能为空")
        if "model_url" in values and not values["model_url"]:
            raise ValueError("对话接口地址不能为空")
        for key, value in values.items():
            if key.endswith("_url") and value:
                endpoint(value)
        for key, value in values.items():
            if key.endswith("api_key"):
                if value:
                    auth.set_secret(key, value)
            else:
                store.set_setting(key, value)
        return settings()

    @app.get("/api/v1/tools/gallery", dependencies=[Depends(owner)])
    def chart_gallery():
        return gallery()

    @app.get("/api/v1/tools/gallery/{name}", dependencies=[Depends(owner)])
    def gallery_image(name: str):
        if name not in {row["id"] for row in gallery()}:
            raise HTTPException(404, "样图不存在")
        return FileResponse(
            ROOT / "resources/plot/gallery" / (name + ".png"),
            media_type="image/png",
            headers={"Cache-Control": "private, max-age=3600"},
        )

    @app.get("/api/v1/tools/gallery/{name}/reference", dependencies=[Depends(owner)])
    def gallery_reference(name: str):
        card = next((row for row in gallery() if row["id"] == name), None)
        if not card:
            raise HTTPException(404, "样例不存在")
        folder = ROOT / "resources/plot/gallery"
        code = folder / (name + ".py")
        return {
            **card,
            "markdown": (folder / (name + ".md")).read_text(encoding="utf-8"),
            "code": code.read_text(encoding="utf-8") if code.is_file() else None,
            "source": "liouhai/plot-is-all-you-need",
            "license": "说明与脚本 MIT；图像的原始权利归各自作者，见 THIRD_PARTY.md",
        }

    @app.post("/api/v1/tools/plot", dependencies=[Depends(owner)])
    async def make_plot(body: Plot):
        library.path(body.file_id)

        async def operation(ident, flag):
            worker = asyncio.create_task(
                asyncio.to_thread(
                    plot_csv,
                    library,
                    body.file_id,
                    body.x,
                    body.y,
                    body.kind,
                    body.title,
                    body.palette,
                    ident,
                    flag,
                )
            )
            try:
                return await asyncio.shield(worker)
            except asyncio.CancelledError:
                await asyncio.gather(worker, return_exceptions=True)
                raise

        return await manager.submit(
            "绘图 · " + body.title,
            permission="workspace",
            request_key=body.request_key,
            operation=operation,
            operation_input=body.model_dump(exclude={"request_key"}),
        )

    @app.post("/api/v1/tools/image", dependencies=[Depends(owner)])
    async def make_image(body: ImageTransform):
        if not settings()["image_configured"] or not settings()["image_url"]:
            raise HTTPException(503, "请先配置图像生成服务")

        async def operation(ident, flag):
            return await transform_image(
                library, auth, body.file_id, body.style, body.instruction, ident
            )

        return await manager.submit(
            "拾景 · " + ("实景拼贴" if body.style == "collage" else "影像蒸馏"),
            permission="workspace",
            request_key=body.request_key,
            operation=operation,
            operation_input=body.model_dump(exclude={"request_key"}),
        )

    @app.get("/api/v1/schedules", dependencies=[Depends(owner)])
    def schedules():
        return store.all("SELECT * FROM schedules ORDER BY next_at")

    @app.post("/api/v1/schedules", dependencies=[Depends(owner)])
    def add_schedule(body: Schedule):
        ident = uid()
        if body.server_id:
            server = require_row("records", body.server_id)
            if server["kind"] != "server":
                raise ValueError("目标服务器不存在")
        store.execute(
            "INSERT INTO schedules(id,title,task,interval_minutes,next_at,enabled,permission,server_id) VALUES(?,?,?,?,?,?,?,?)",
            (
                ident,
                body.title,
                body.task,
                body.interval_minutes,
                now() + body.interval_minutes * 60000,
                int(body.enabled),
                body.permission,
                body.server_id,
            ),
        )
        return {"id": ident, **body.model_dump()}

    @app.put("/api/v1/schedules/{ident}", dependencies=[Depends(owner)])
    def update_schedule(ident: str, body: Schedule):
        previous = require_row("schedules", ident)
        if body.server_id:
            server = require_row("records", body.server_id)
            if server["kind"] != "server":
                raise ValueError("目标服务器不存在")
        store.execute(
            "UPDATE schedules SET title=?,task=?,interval_minutes=?,enabled=?,permission=?,server_id=?,next_at=? WHERE id=?",
            (
                body.title,
                body.task,
                body.interval_minutes,
                int(body.enabled),
                body.permission,
                body.server_id,
                (
                    now() + body.interval_minutes * 60000
                    if (
                        body.interval_minutes != previous["interval_minutes"]
                        or (body.enabled and not previous["enabled"])
                    )
                    else previous["next_at"]
                ),
                ident,
            ),
        )
        return {"id": ident, **body.model_dump()}

    @app.delete("/api/v1/schedules/{ident}", dependencies=[Depends(owner)])
    def delete_schedule(ident: str):
        store.execute("DELETE FROM schedules WHERE id=?", (ident,))
        return {"ok": True}

    @app.get("/api/v1/audit", dependencies=[Depends(owner)])
    def audit():
        return store.all("SELECT * FROM audit ORDER BY created DESC LIMIT 200")

    return app


app = create_app()
