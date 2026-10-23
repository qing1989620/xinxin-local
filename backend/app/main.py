from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal
from weakref import WeakValueDictionary

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
from fastapi.responses import FileResponse, StreamingResponse, Response
from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

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
from . import learning, learning_studio, learning_imports, learning_quality, learning_visual, music
from .model import ModelGateway, endpoint
from .network import local_addresses
from .mail import MailCodes
from .skills import SkillRouter
from .skill_trace import with_skill_traces
from .store import Store, encode, now, uid
from .runtime import source_fingerprint
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
    provider: Literal["smtp", "resend"] = "smtp"
    smtp_host: str = Field(default="smtp.qq.com", pattern=r"^[A-Za-z0-9.-]{1,200}$")
    smtp_port: int = Field(default=465, ge=1, le=65535)
    smtp_mode: Literal["ssl", "starttls"] = "ssl"
    smtp_username: str = Field(default="", max_length=254, pattern=r"^[\x21-\x7e]*$")
    smtp_password: str = Field(default="", max_length=500, pattern=r"^[\x21-\x7e]*$")
    resend_from: str = Field(default="", max_length=320)
    resend_api_key: str = Field(default="", max_length=200, pattern=r"^[\x21-\x7e]*$")


class DomainInput(Input):
    name: str = Field(
        max_length=253,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9-]{0,62}(\.[A-Za-z0-9][A-Za-z0-9-]{0,62})+$",
    )


class MusicPlay(Input):
    id: str = Field(min_length=1, max_length=120)
    source: str = Field(default="netease", max_length=20)
    name: str = Field(min_length=1, max_length=200)
    artist: str = Field(default="", max_length=200)
    album: str = Field(default="", max_length=200)


class BookCreate(Input):
    file_id: str = Field(min_length=1, max_length=64)
    title: str = Field(default="", max_length=120)
    subject: str = Field(default="", max_length=40)


class QuestionGen(Input):
    chapter_id: str = Field(min_length=1, max_length=64)
    count: int = Field(default=12, ge=1, le=24)


class LearningImport(BookCreate):
    request_key: str = Field(min_length=8, max_length=80)


class SourceCorrection(Input):
    content: str = Field(min_length=24, max_length=8000)


class LearningGeneration(Input):
    source_ids: list[str] = Field(default_factory=list, max_length=40)
    count: int = Field(default=12, ge=1, le=24)
    kinds: list[Literal["single", "fill", "short"]] = Field(default=["single", "fill", "short"], min_length=1, max_length=3)
    difficulty: int = Field(default=0, ge=0, le=3)
    focus: str = Field(default="", max_length=240)
    request_key: str = Field(min_length=8, max_length=80)
    resume_job_id: str = Field(default="", max_length=64)
    mode: Literal["auto", "original", "practice"] = "auto"
    analyze_only: bool = False
    read_mode: Literal["text", "pdf"] = "text"
    page_ranges: dict[str, tuple[StrictInt, StrictInt]] = Field(default_factory=dict, max_length=40)


class QuizStart(Input):
    book_id: str = Field(default="", max_length=64)
    chapter_id: str = Field(default="", max_length=64)
    count: int = Field(default=8, ge=1, le=30)
    difficulty: int = Field(default=0, ge=0, le=3)
    mode: Literal["all", "mistakes"] = "all"


class QuizAnswer(Input):
    question_id: str = Field(min_length=1, max_length=64)
    answer: str = Field(default="", max_length=4000)
    answers: list[Annotated[str, Field(max_length=500)]] | None = Field(default=None, min_length=1, max_length=8)
    retry_grading: bool = False


class ExplainRequest(Input):
    message: str = Field(default="", max_length=2000)
    mode: Literal["teacher", "xinxin"] = "teacher"
    session_id: str = Field(default="", max_length=64)


class TrackRef(Input):
    id: str = Field(min_length=1, max_length=120)
    source: str = Field(default="netease", max_length=20)
    name: str = Field(min_length=1, max_length=200)
    artist: str = Field(default="", max_length=200)
    album: str = Field(default="", max_length=200)
    cover: str = Field(default="", max_length=500)


class PlaylistCreate(Input):
    name: str = Field(min_length=1, max_length=60)


class PlaylistName(Input):
    name: str = Field(min_length=1, max_length=60)


class MusicScoreItem(Input):
    id: str = Field(min_length=1, max_length=120)
    source: str = Field(default="netease", max_length=20)
    name: str = Field(min_length=1, max_length=200)
    artist: str = Field(default="", max_length=200)
    album: str = Field(default="", max_length=200)


class MusicScore(Input):
    tracks: list[MusicScoreItem] = Field(default_factory=list, max_length=30)


class MusicSetting(Input):
    influence: bool | None = None
    influence_level: int | None = Field(default=None, ge=1, le=4, strict=True)
    sensitivity_level: int | None = Field(default=None, ge=1, le=4, strict=True)

    @model_validator(mode="after")
    def matching_levels(self):
        if self.influence_level is not None and self.sensitivity_level is not None and self.influence_level != self.sensitivity_level:
            raise ValueError("感受指数不能同时设置为两个不同档位")
        return self


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
    backend_build = source_fingerprint(ROOT)
    config = config or Config.from_env()
    store = Store(config.data_dir)
    learning_quality.quarantine_legacy(store)
    auth = Auth(store)
    mail = MailCodes(store, auth)
    library = FileLibrary(store)
    router = SkillRouter(store)
    manager = TaskManager(store, auth, config, library, router)
    learning_lock = asyncio.Lock()
    learning_request_locks = WeakValueDictionary()

    def learning_request_lock(key):
        lock = learning_request_locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            learning_request_locks[key] = lock
        return lock

    def model_gateway(max_tokens: int = 4096):
        """单次调用的模型网关；没配密钥时返回 None，调用方自行降级。"""
        url, model, key = manager.model_config()
        if not key:
            return None
        return ModelGateway(
            url,
            model,
            key,
            record_usage=lambda value: None,
            cancelled=asyncio.Event(),
            max_calls=1,
            max_tokens=max_tokens,
            transport=manager.model_transport,
        )

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
        return {"status": "ok", "product": "Xinxin", "version": "0.1.0", "build": backend_build, "capabilities": {"music_sensitivity": 2}}

    @app.get("/api/v1/network", dependencies=[Depends(owner)])
    def network():
        return local_addresses()

    @app.get("/api/v1/auth/status")
    def auth_status():
        return {
            "configured": bool(store.one("SELECT id FROM owner")),
            "registration": "disabled",
            "email_enabled": mail.enabled(),
        }

    @app.post("/api/v1/auth/setup")
    def setup(body: Setup):
        with auth.lock:
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
        with auth.lock:
            mail.consume(body.email.strip().lower(), "login", body.code, lambda db: None)
            store.audit("owner.email_login", {})
            return {
                "token": auth.issue(),
                "name": store.one("SELECT name FROM owner WHERE id=1")["name"],
            }

    @app.post("/api/v1/auth/email/reset")
    def email_reset(body: EmailReset):
        with auth.lock:
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
            "email": config["email"],
            "provider": config["provider"],
            "smtp_host": config["smtp_host"],
            "smtp_port": config["smtp_port"],
            "smtp_mode": config["smtp_mode"],
            "smtp_username": config["smtp_username"],
            "resend_from": config["resend_from"],
            "resend_configured": bool(config["resend_api_key"]),
            "configured": mail.enabled(),
        }

    @app.put("/api/v1/settings/email")
    def save_email_settings(body: EmailSettings, token=Depends(owner)):
        with auth.lock:
            auth.require(token)
            mail.configure(body.model_dump())
            store.audit("email.configured", {"provider": body.provider})
            return email_settings()

    @app.post("/api/v1/settings/email/test", dependencies=[Depends(owner)])
    def test_email_settings():
        """只发给绑定邮箱，不占用验证码配额。"""
        return mail.test_delivery()

    @app.get("/api/v1/settings/email/domains", dependencies=[Depends(owner)])
    def email_domains():
        return {"domains": mail.domains()}

    @app.post("/api/v1/settings/email/domains", dependencies=[Depends(owner)])
    def add_email_domain(body: DomainInput):
        result = mail.add_domain(body.name)
        store.audit("email.domain_added", {"name": body.name})
        return result

    @app.post(
        "/api/v1/settings/email/domains/{domain_id}/verify",
        dependencies=[Depends(owner)],
    )
    def verify_email_domain(domain_id: str):
        result = mail.verify_domain(domain_id)
        store.audit("email.domain_verified", {"id": domain_id})
        return result

    # ------------------------------------------------------------------
    # 背景音乐：GD 音乐台 JSON 代理 + 情绪聚合
    # 音频不经过本机：这里只返回 CDN 直链，由客户端播放。
    # ------------------------------------------------------------------
    @app.get("/api/v1/music/search", dependencies=[Depends(owner)])
    def music_search(
        q: str = Query(min_length=1, max_length=80),
        source: str = "netease",
        page: int = Query(default=1, ge=1, le=20),
    ):
        result = music.client.search(q.strip(), source, page)
        keys = music.favorite_keys(store)
        for track in result.get("tracks", []):
            key = f"{track.get('source') or source}:{track.get('id')}"
            track["favorited"] = key in keys
        return result

    @app.get("/api/v1/music/url", dependencies=[Depends(owner)])
    def music_url(
        id: str = Query(min_length=1, max_length=120),
        source: str = "netease",
        br: int = 320,
    ):
        return music.client.url(id, source, br)

    @app.get("/api/v1/music/lyric", dependencies=[Depends(owner)])
    def music_lyric(id: str = Query(min_length=1, max_length=120), source: str = "netease"):
        return music.client.lyric(id, source)

    @app.get("/api/v1/music/pic", dependencies=[Depends(owner)])
    def music_pic(id: str = Query(min_length=1, max_length=120), source: str = "netease"):
        return music.client.pic(id, source)

    @app.get("/api/v1/music/mood", dependencies=[Depends(owner)])
    def music_mood():
        return {
            "mood": music.current_mood(store),
            "plays": music.recent_plays(store),
        }

    @app.get("/api/v1/music/favorites", dependencies=[Depends(owner)])
    def music_favorites():
        return {"favorites": music.favorites(store), "keys": sorted(music.favorite_keys(store))}

    @app.post("/api/v1/music/favorites", dependencies=[Depends(owner)])
    def music_favorite(body: TrackRef):
        try:
            return music.add_favorite(store, body.model_dump())
        except ValueError as error:
            raise HTTPException(400, str(error))

    @app.delete("/api/v1/music/favorites", dependencies=[Depends(owner)])
    def music_unfavorite(key: str = Query(min_length=1, max_length=160)):
        return music.remove_favorite(store, key)

    @app.get("/api/v1/music/playlists", dependencies=[Depends(owner)])
    def music_playlists():
        return {"playlists": music.playlists(store)}

    @app.post("/api/v1/music/playlists", dependencies=[Depends(owner)])
    def music_playlist_create(body: PlaylistCreate):
        try:
            return {"playlist": music.create_playlist(store, body.name)}
        except ValueError as error:
            raise HTTPException(400, str(error))

    @app.put("/api/v1/music/playlists/{playlist_id}", dependencies=[Depends(owner)])
    def music_playlist_rename(playlist_id: str, body: PlaylistName):
        try:
            return {"playlist": music.rename_playlist(store, playlist_id, body.name)}
        except ValueError as error:
            raise HTTPException(404, str(error))

    @app.delete("/api/v1/music/playlists/{playlist_id}", dependencies=[Depends(owner)])
    def music_playlist_delete(playlist_id: str):
        return music.delete_playlist(store, playlist_id)

    @app.get("/api/v1/music/playlists/{playlist_id}", dependencies=[Depends(owner)])
    def music_playlist_items(playlist_id: str):
        try:
            return music.playlist_items(store, playlist_id)
        except ValueError as error:
            raise HTTPException(404, str(error))

    @app.post("/api/v1/music/playlists/{playlist_id}/tracks", dependencies=[Depends(owner)])
    def music_playlist_add(playlist_id: str, body: TrackRef):
        try:
            return music.add_to_playlist(store, playlist_id, body.model_dump())
        except ValueError as error:
            raise HTTPException(404, str(error))

    @app.delete("/api/v1/music/playlists/{playlist_id}/tracks", dependencies=[Depends(owner)])
    def music_playlist_remove(playlist_id: str, key: str = Query(min_length=1, max_length=160)):
        return music.remove_from_playlist(store, playlist_id, key)

    @app.post("/api/v1/music/score", dependencies=[Depends(owner)])
    async def music_score(body: MusicScore):
        """按歌曲校准情绪：缓存优先，未命中的一次批量问模型。"""
        return await music.score_tracks(
            store, model_gateway(), [item.model_dump() for item in body.tracks]
        )

    @app.post("/api/v1/music/play", dependencies=[Depends(owner)])
    def music_play(body: MusicPlay):
        return {"ok": True, "mood": music.record_play(store, body.model_dump())}

    @app.delete("/api/v1/music/mood", dependencies=[Depends(owner)])
    def music_clear_mood():
        music.clear_plays(store)
        return {"ok": True, "mood": music.current_mood(store)}

    @app.put("/api/v1/music/settings", dependencies=[Depends(owner)])
    def music_settings(body: MusicSetting):
        if body.influence is not None:
            music.set_influence(store, body.influence)
        if body.influence_level is not None:
            music.set_influence_level(store, body.influence_level)
        elif body.sensitivity_level is not None:
            music.set_influence_level(store, body.sensitivity_level)
        return {"ok": True, "mood": music.current_mood(store)}

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

    @app.put("/api/v1/auth/password")
    def password(body: Password, token=Depends(owner)):
        with auth.lock:
            auth.require(token)
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
            "runs": with_skill_traces(store, store.all(
                "SELECT * FROM runs WHERE conversation_id=? ORDER BY created DESC",
                (ident,),
            )),
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
            **with_skill_traces(store, [require_row("runs", ident)])[0],
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

    @app.get("/api/v1/files/{ident}/preview", dependencies=[Depends(owner)])
    def file_preview(ident: str, size: int = Query(1600)):
        """有界预览图：长边 480 / 1600，JPEG，磁盘缓存。

        前端画廊、缩略图、正文配图都优先走这里；原图动辄数 MB，
        预览图通常只有几十到一两百 KB。非图片返回 404，前端会回退原图。
        """
        size = 1600 if size not in (480, 1600) else size
        try:
            cached = library.preview(ident, size)
        except ValueError:
            raise
        except Exception:  # noqa: BLE001 -- 解码失败等任何异常都不该 500
            raise HTTPException(404, "此文件暂时无法生成预览") from None
        if cached is None:
            raise HTTPException(404, "此文件没有预览图")
        return FileResponse(
            cached,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "private, max-age=604800",
                "X-Content-Type-Options": "nosniff",
            },
        )

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
        if store.one("SELECT i.id FROM learning_imports i JOIN runs r ON r.id=i.run_id WHERE i.file_id=? AND r.status IN ('queued','running','cancelling')", (ident,)):
            raise HTTPException(409, "资料正在识别，请先停止任务再删除原文件")
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

    def _file_text(file_id: str) -> dict:
        row = store.one("SELECT * FROM files WHERE id=?", (file_id,))
        if not row:
            raise HTTPException(404, "先在「私人资料」里上传这份文件")
        data = dict(row)
        if not data.get("text"):
            try:
                from .document_text import extract_document
                data["text"], metadata = extract_document(library.path(file_id))
                data["pages"] = metadata.get("pages", 0)
            except ValueError:
                raise HTTPException(404, "这份文件已经不在资料库里了")
            except Exception:
                data["text"] = ""
        return data

    @app.post("/api/v1/learning/imports", dependencies=[Depends(owner)])
    async def learning_import_start(body: LearningImport):
        try:
            async with learning_lock:
                return {"job": await learning_imports.start(store, library, manager, body.model_dump())}
        except ValueError as error:
            raise HTTPException(409, str(error))

    @app.get("/api/v1/learning/imports", dependencies=[Depends(owner)])
    def learning_import_latest():
        row = store.one("SELECT id FROM learning_imports ORDER BY created DESC,rowid DESC LIMIT 1")
        return {"job": learning_imports.snapshot(store, row["id"]) if row else None}

    @app.get("/api/v1/learning/imports/{ident}", dependencies=[Depends(owner)])
    def learning_import_status(ident: str):
        try:
            return {"job": learning_imports.snapshot(store, ident)}
        except ValueError as error:
            raise HTTPException(404, str(error))

    @app.get("/api/v1/learning/books", dependencies=[Depends(owner)])
    def learning_books():
        return {"books": learning.list_books(store)}

    @app.post("/api/v1/learning/books", dependencies=[Depends(owner)])
    def learning_add_book(body: BookCreate):
        try:
            book = learning.create_book(
                store, library, _file_text(body.file_id), body.title, body.subject
            )
        except ValueError as error:
            raise HTTPException(400, str(error))
        return {"book": book}

    @app.get("/api/v1/learning/books/{book_id}", dependencies=[Depends(owner)])
    def learning_book(book_id: str):
        try:
            return {"book": learning.get_book(store, book_id)}
        except ValueError as error:
            raise HTTPException(404, str(error))

    @app.delete("/api/v1/learning/books/{book_id}", dependencies=[Depends(owner)])
    async def learning_remove_book(book_id: str):
        try:
            async with learning_lock:
                return learning.delete_book(store, book_id)
        except ValueError as error:
            raise HTTPException(404, str(error))

    @app.get("/api/v1/learning/chapters/{chapter_id}", dependencies=[Depends(owner)])
    def learning_chapter(chapter_id: str):
        try:
            return {"chapter": learning.chapter(store, chapter_id)}
        except ValueError as error:
            raise HTTPException(404, str(error))

    @app.post("/api/v1/learning/books/{book_id}/questions", dependencies=[Depends(owner)])
    async def learning_generate(book_id: str, body: QuestionGen):
        try:
            book = learning.get_book(store, book_id)
            chapter = learning.chapter(store, body.chapter_id)
        except ValueError as error:
            raise HTTPException(404, str(error))
        if chapter["book_id"] != book_id:
            raise HTTPException(400, "这一章不属于这本书")
        try:
            # Keep the old synchronous response, but use the exact same durable
            # analysis/generation/review path so old clients cannot bypass it.
            async with learning_lock:
                listing = learning_studio.sources(store, library, book_id)
                candidates = [unit for unit in listing["sources"] if unit["chapter_id"] == chapter["id"] and unit["eligible"]]
                if not candidates:
                    raise ValueError("这一章没有可考查的知识正文或完整练习题")
                # Spread the requested total across the whole chapter, including
                # its final fragments, rather than repeatedly testing its opening.
                amount = min(body.count, len(candidates), learning_studio.MAX_SOURCES)
                selected = [candidates[round(index * (len(candidates) - 1) / (amount - 1))] for index in range(amount)] if amount > 1 else candidates[:1]
                base, extra = divmod(body.count, amount)
                allocations = {unit["id"]: base + (index < extra) for index, unit in enumerate(selected)}
                payload = LearningGeneration(source_ids=list(allocations), count=max(allocations.values()), request_key=uid()).model_dump()
                job = await learning_studio.start(store, library, manager, book_id, payload, allocations=allocations)
            pending = manager.tasks.get(job["run_id"])
            if pending:
                await asyncio.shield(pending)
            result = learning_studio.snapshot(store, job["id"])
            if result["status"] == "failed" and any("模型未返回有效题目数组" in item["error"] for item in result["items"]):
                raise ValueError("模型这次没返回可解析的题目；本次任务已保留，可在学习工作室重试")
            rows = store.all("SELECT * FROM questions WHERE generation_id=? ORDER BY created,rowid", (job["id"],))
            return {"created": [learning.format_question(row) for row in rows],
                    "skipped": sum(item["rejected"] + item["duplicates"] for item in result["items"]), "job": result}
        except ValueError as error:
            raise HTTPException(409, str(error))

    @app.get("/api/v1/learning/questions", dependencies=[Depends(owner)])
    def learning_questions(
        book_id: str = Query(default="", max_length=64),
        chapter_id: str = Query(default="", max_length=64),
    ):
        return {"questions": learning.list_questions(store, book_id, chapter_id)}

    @app.get("/api/v1/learning/books/{book_id}/sources", dependencies=[Depends(owner)])
    def learning_sources(book_id: str):
        try:
            result = learning_studio.sources(store, library, book_id)
            book = learning.get_book(store, book_id)
            try:
                pdf = bool(book["file_id"] and library.path(book["file_id"]).suffix.lower() == ".pdf")
            except ValueError:
                pdf = False
            model_url, model_name, _ = manager.model_config()
            supported = ModelGateway(model_url, model_name, "", lambda _: None, asyncio.Event()).supports_learning_images()
            result["image_reading"] = {"pdf": pdf, "available": pdf and supported, "max_pages": learning_visual.MAX_JOB_PAGES,
                "reason": "" if pdf and supported else "当前模型尚未接入图片读取，需要 DeepSeek Flash 官方接口" if pdf else "原页读取适用于 PDF 资料"}
            return result
        except ValueError as error:
            raise HTTPException(404, str(error))

    @app.get("/api/v1/learning/sources/{source_id}", dependencies=[Depends(owner)])
    def learning_source(source_id: str, offset: int = Query(default=0, ge=-1, le=1)):
        try:
            return {"source": learning_studio.source(store, source_id, offset)}
        except ValueError as error:
            raise HTTPException(404, str(error))

    @app.put("/api/v1/learning/sources/{source_id}", dependencies=[Depends(owner)])
    async def learning_source_correct(source_id: str, body: SourceCorrection):
        try:
            async with learning_lock:
                return {"source": learning_studio.correct_source(store, source_id, body.content)}
        except ValueError as error:
            raise HTTPException(409, str(error))

    @app.get("/api/v1/learning/sources/{source_id}/pages/{page}", dependencies=[Depends(owner)])
    def learning_source_page(source_id: str, page: int):
        try:
            unit = learning_studio.source(store, source_id)
            if page not in learning_visual.page_range(unit):
                raise ValueError("此页不在当前片段的来源范围")
            path = learning_visual.pdf_path(store, library, unit)
            content = learning_visual.render_page(path, page, size=1600)
            return Response(content, media_type="image/jpeg", headers={"Cache-Control": "no-store"})
        except (ValueError, OSError):
            raise HTTPException(404, "无法打开此 PDF 原页，请核对原文件和页码")

    @app.get("/api/v1/learning/books/{book_id}/generation", dependencies=[Depends(owner)])
    def learning_generation_latest(book_id: str):
        return {"job": learning_studio.latest(store, book_id)}

    @app.get("/api/v1/learning/generations/{job_id}", dependencies=[Depends(owner)])
    def learning_generation(job_id: str):
        try:
            return {"job": learning_studio.snapshot(store, job_id)}
        except ValueError as error:
            raise HTTPException(404, str(error))

    @app.post("/api/v1/learning/books/{book_id}/generations", dependencies=[Depends(owner)])
    async def learning_generation_start(book_id: str, body: LearningGeneration):
        try:
            payload = body.model_dump()
            for field in ("read_mode", "page_ranges"):
                if field not in body.model_fields_set:
                    payload.pop(field)
            async with learning_lock:
                return {"job": await learning_studio.start(store, library, manager, book_id, payload)}
        except ValueError as error:
            raise HTTPException(409, str(error))

    @app.post("/api/v1/learning/quiz", dependencies=[Depends(owner)])
    def learning_quiz(body: QuizStart):
        try:
            return {"session": learning.start_quiz(store, body.book_id, body.chapter_id, body.count, body.difficulty, body.mode)}
        except ValueError as error:
            raise HTTPException(409, str(error))

    @app.get("/api/v1/learning/quiz/{session_id}", dependencies=[Depends(owner)])
    def learning_quiz_state(session_id: str):
        try:
            return {"session": learning.quiz_state(store, session_id)}
        except ValueError as error:
            raise HTTPException(404, str(error))

    @app.post("/api/v1/learning/quiz/{session_id}/answer", dependencies=[Depends(owner)])
    async def learning_answer(session_id: str, body: QuizAnswer):
        try:
            if body.answers is not None and (body.answer or body.retry_grading):
                raise ValueError("答案数组不能与文字答案或重判同时提交")
            async with learning_request_lock(("grade", session_id, body.question_id)):
                return await learning.submit_answer(
                    store, model_gateway(max_tokens=12000), session_id, body.question_id, body.answer,
                    answers=body.answers, retry_grading=body.retry_grading,
                )
        except ValueError as error:
            raise HTTPException(400, str(error))

    @app.get("/api/v1/learning/questions/{question_id}/tutor", dependencies=[Depends(owner)])
    def learning_tutor_history(question_id: str, mode: Literal["teacher", "xinxin"] = "teacher",
                               session_id: str = Query(default="", max_length=64), previous: bool = False):
        if not store.one("SELECT id FROM questions WHERE id=?", (question_id,)):
            raise HTTPException(404, "题目不存在")
        attempt = learning.tutor_attempt(store, question_id, session_id)
        previous_count = store.one("SELECT count(*) n FROM tutor_messages WHERE question_id=? AND mode=? AND session_id!=?", (question_id, mode, session_id))["n"] if session_id else 0
        previous_history = store.all("SELECT role,content,created FROM tutor_messages WHERE question_id=? AND mode=? AND session_id!=? ORDER BY created,rowid", (question_id, mode, session_id)) if previous and attempt and session_id else []
        return {"history": learning.tutor_history(store, question_id, mode, session_id), "mode": mode,
                "previous_count": previous_count, "previous_history": previous_history}

    @app.post("/api/v1/learning/questions/{question_id}/explain", dependencies=[Depends(owner)])
    async def learning_explain(question_id: str, body: ExplainRequest):
        try:
            async with learning_request_lock(("tutor", question_id, body.mode, body.session_id)):
                return await learning.explain(store, model_gateway(max_tokens=12000), question_id, body.message, body.mode, body.session_id)
        except ValueError as error:
            raise HTTPException(409, str(error))

    @app.get("/api/v1/learning/stats", dependencies=[Depends(owner)])
    def learning_stats():
        return learning.stats(store)

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
