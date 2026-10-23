import asyncio
import hashlib
import inspect
import shutil
import json
import logging
import os
import re
import shlex
import sys
import threading
from pathlib import Path

from .config import (
    ROOT, DEFAULT_MODEL_CALLS, DEFAULT_TASK_SECONDS, TOKENS_PER_MODEL_CALL,
    CONTEXT_INPUT_TOKENS, CONTEXT_WINDOW_TOKENS, CONTEXT_TIERS,
)
from .execution import Policy, run_command, remote_command
from .model import ModelGateway, ModelBudgetExceeded
from .recovery import previous_work
from .context import context_manager_type, prior_messages, save_context
from .persona import build_system_prompt
from .music import atmosphere as music_atmosphere
from .progress import ProgressNarrator
from .public_text import PublicText, redact_text as redact_public_text
from .store import clean_text, encode, now, uid
from .creative import plot_csv, transform_image, gallery
from .skill_trace import skill_evidence

sys.path.insert(0, str(ROOT / "vendor"))
from tina import Agent, Tools, AgentEvents
from tina.agent.core.executor import ToolsExecutor
from tina.agent.core.context_manager import ContextManager

# Tina's debug file logger writes raw arguments/results before platform redaction.
# The platform's persisted, sanitized events are the execution log.
_tina_logger = logging.getLogger("tina")
_tina_logger.disabled = True
for _handler in tuple(_tina_logger.handlers):
    _handler.close()
    _tina_logger.removeHandler(_handler)


TaskContext = context_manager_type(ContextManager)

class PlatformExecutor(ToolsExecutor):
    def __init__(self, sanitize=str, cancelled=None, on_cancel_result=None, on_start=None):
        super().__init__(max_workers=1)
        self.unresolved = {}
        self.inflight = set()
        self.sanitize = sanitize
        self.cancelled = cancelled
        self.on_cancel_result = on_cancel_result
        self.remote_stop_unconfirmed = False
        self.on_start = on_start

    def _raw_execute(self, tool, arguments):
        # Tina's global stdout redirection is unsuitable for concurrent HTTP jobs.
        result = tool(**arguments)
        return encode(result) if isinstance(result, (dict, list)) else str(result)

    async def aexecute(
        self, calls, tools, _mcp_client=None, timeout=60, events=None, **kwargs
    ):
        # Validate before Tina's generic logger, which may include exception input.
        for call in calls or []:
            name = call["function"]["name"]
            try:
                if (
                    not isinstance(json.loads(call["function"]["arguments"]), dict)
                    or tools.get_tool(name=name) is None
                ):
                    raise ValueError("工具或参数无效")
            except (ValueError, TypeError):
                self.unresolved[name] = "工具或参数无效"
                return [
                    self._tool_call_result(
                        encode({"ok": False, "error": "工具或参数无效，本批未执行"}),
                        item["id"],
                        item["function"]["name"],
                    )
                    for item in calls
                ]
        return await super().aexecute(
            calls, tools, _mcp_client, timeout, events, **kwargs
        )

    async def _async_dispatch(self, name, arguments, tool, timeout):
        if self.cancelled and self.cancelled.is_set():
            return encode({"ok": False, "error": "任务已取消，本步未启动"})
        if tool is None:
            self.unresolved[name] = "未知工具"
            return "未知工具：" + name
        try:
            if self.on_start:
                self.on_start(name, arguments)
            if inspect.iscoroutinefunction(tool):
                result = await tool(**arguments)
            else:
                # Task deadline and the managed process own cancellation.
                pending = asyncio.create_task(
                    asyncio.to_thread(self._raw_execute, tool, arguments)
                )
                self.inflight.add(pending)
                pending.add_done_callback(self.inflight.discard)

                def record_cancel_result(future):
                    if not self.cancelled or not self.cancelled.is_set():
                        return
                    try:
                        value = future.result()
                        parsed = json.loads(value) if isinstance(value, str) else value
                        if isinstance(parsed, dict) and parsed.get("remote_stop_confirmed") is False:
                            self.remote_stop_unconfirmed = True
                        if self.on_cancel_result:
                            self.on_cancel_result(name, self.sanitize(value))
                    except (Exception, asyncio.CancelledError):
                        if name in {"run_remote_command", "deploy_repository"}:
                            self.remote_stop_unconfirmed = True

                pending.add_done_callback(record_cancel_result)
                result = await asyncio.shield(pending)
            structured = result
            if isinstance(result, str):
                try:
                    structured = json.loads(result)
                except (ValueError, TypeError):
                    pass
            if isinstance(structured, dict) and structured.get("ok") is False:
                self.unresolved[name] = "工具执行失败，退出码 " + str(
                    structured.get("exit_code", "unknown")
                )
            else:
                self.unresolved.pop(name, None)
            return self.sanitize(
                encode(result) if isinstance(result, (dict, list)) else str(result)
            )
        except Exception as exc:
            self.unresolved[name] = self.sanitize(str(exc))
            return encode({"ok": False, "error": self.unresolved[name]})

    async def drain(self):
        if self.inflight:
            await asyncio.gather(*list(self.inflight), return_exceptions=True)


def safe_summary(value, limit=12000):
    return redact_public_text(str(value), limit=limit)


class TaskManager:
    def __init__(self, store, auth, config, library, router):
        self.store, self.auth, self.config = store, auth, config
        self.library, self.router = library, router
        self.tasks, self.cancellations = {}, {}
        self.semaphore = asyncio.Semaphore(config.task_concurrency)
        self.maintenance = threading.Event()
        self.model_transport = None

    def model_config(self):
        return (
            self.store.setting("model_url", self.config.model_url),
            self.store.setting("model", self.config.model),
            self.auth.secret("model_api_key", self.config.api_key),
        )

    def secret_forms(self):
        keys = [self.config.api_key]
        vault_key = self.store.directory / "vault.key"
        if vault_key.is_file():
            keys.append(vault_key.read_text(encoding="ascii").strip())
        for row in self.store.all("SELECT key FROM settings WHERE key LIKE 'secret:%'"):
            keys.append(self.auth.secret(row["key"][7:]))
        return sorted({
            form
            for key in keys
            if key
            for form in (
                key,
                json.dumps(key, ensure_ascii=False)[1:-1],
                json.dumps(key, ensure_ascii=True)[1:-1],
            )
        }, key=len, reverse=True)

    def redact(self, value, limit=16000, *, known_forms=()):
        text = str(value)
        forms = sorted(set(self.secret_forms()) | set(known_forms), key=len, reverse=True)

        def redact_text(text):
            return redact_public_text(text, forms, limit)

        def redact_data(data):
            if isinstance(data, str):
                return redact_text(data)
            if isinstance(data, list):
                return [redact_data(item) for item in data]
            if isinstance(data, dict):
                secret_fields = {
                    "apikey",
                    "password",
                    "secret",
                    "authorization",
                    "token",
                    "privatekey",
                    "modelapikey",
                    "smtppassword",
                }
                cleaned = {}
                for key, item in data.items():
                    clean_key = redact_text(key)
                    suffix = 1
                    while clean_key in cleaned:
                        clean_key = f"{redact_text(key)} [{suffix}]"
                        suffix += 1
                    cleaned[clean_key] = (
                        "[redacted]"
                        if key.lower().replace("_", "").replace("-", "")
                        in secret_fields
                        else redact_data(item)
                    )
                return cleaned
            return data

        try:
            structured = json.loads(text)
        except (ValueError, TypeError):
            structured = None
        if isinstance(structured, (dict, list)):
            # Redact values before serialization so escaping/cursors stay valid.
            result = encode(redact_data(structured))
            return (
                result
                if limit is None or len(result) <= limit
                else encode({"truncated": True, "preview": result[:6000]})
            )
        return redact_text(text)

    def conversation(self, title="新对话"):
        ident = uid()
        self.store.execute(
            "INSERT INTO conversations(id,title,created,updated) VALUES(?,?,?,?)",
            (ident, title[:80], now(), now()),
        )
        return ident

    async def submit(
        self,
        task,
        conversation_id=None,
        permission="read",
        server_id=None,
        max_calls=DEFAULT_MODEL_CALLS,
        max_seconds=DEFAULT_TASK_SECONDS,
        request_key=None,
        operation=None,
        operation_input=None,
        allow_memory=False,
        max_total_tokens=None,
        context_window_tokens=None,
        resume_of=None,
        message_text=None,
    ):
        if self.maintenance.is_set():
            raise ValueError("正在清理对话与整理存储，请稍后提交任务")
        signature_input = [
            task, conversation_id, permission, server_id, max_calls, max_seconds,
            operation_input, bool(allow_memory),
        ]
        if max_total_tokens is not None:
            signature_input.append({"max_total_tokens": max_total_tokens})
        if context_window_tokens is not None:
            if context_window_tokens not in CONTEXT_TIERS:
                raise ValueError("上下文档位只能选择80K、300K或1000K")
            signature_input.append({"context_window_tokens": context_window_tokens})
        if resume_of:
            signature_input.append({"resume_of": resume_of})
        signature = hashlib.sha256(
            encode(signature_input).encode()
        ).hexdigest()
        if request_key:
            existing = self.store.one(
                "SELECT * FROM runs WHERE request_key=?", (request_key,)
            )
            if existing:
                if (
                    existing.get("request_signature")
                    and existing["request_signature"] != signature
                ):
                    raise ValueError("相同请求标识不能用于不同任务")
                return existing
        if not operation and not self.model_config()[2]:
            raise ValueError("请先在设置中配置 DeepSeek API 密钥")
        if permission not in {"read", "workspace", "full"}:
            raise ValueError("未知权限等级")
        if allow_memory and permission == "read":
            raise ValueError("允许保存记忆还需要工作区权限")
        if server_id and not self.store.one(
            "SELECT id FROM records WHERE id=? AND kind='server'", (server_id,)
        ):
            raise ValueError("目标服务器不存在")
        cid = conversation_id or self.conversation(task[:40])
        if not self.store.one("SELECT id FROM conversations WHERE id=?", (cid,)):
            raise ValueError("对话不存在")
        if self.store.one("SELECT archived FROM conversations WHERE id=?", (cid,))[
            "archived"
        ]:
            raise ValueError("此对话已归档，请先恢复或开启新对话")
        active = self.store.one(
            "SELECT id FROM runs WHERE conversation_id=? AND status IN ('queued','running','cancelling')",
            (cid,),
        )
        if active:
            raise ValueError("此对话已有运行中的任务，请等待或取消")
        if resume_of:
            parent = self.store.one("SELECT * FROM runs WHERE id=? AND conversation_id=?", (resume_of, cid))
            latest = self.store.one("SELECT id FROM runs WHERE conversation_id=? ORDER BY created DESC,rowid DESC LIMIT 1", (cid,))
            if not parent or parent["status"] not in {"failed", "cancelled", "interrupted", "completed"}:
                raise ValueError("只能续接此对话中已经结束的任务")
            if not latest or latest["id"] != resume_of:
                raise ValueError("此任务之后已有新轮次，请继续最新一轮，避免重复执行")
        if context_window_tokens is not None:
            self.store.execute(
                "INSERT INTO conversation_options VALUES(?,?) ON CONFLICT(conversation_id) "
                "DO UPDATE SET context_window_tokens=excluded.context_window_tokens", (cid, context_window_tokens),
            )
        choice = self.store.one("SELECT context_window_tokens FROM conversation_options WHERE conversation_id=?", (cid,))
        context_window_tokens = choice["context_window_tokens"] if choice else CONTEXT_WINDOW_TOKENS
        ident = uid()
        self.store.execute(
            "INSERT INTO runs(id,conversation_id,task,status,permission,server_id,max_calls,max_seconds,created,updated,request_key,request_signature,allow_memory,max_total_tokens,context_window_tokens,resume_of) VALUES(?,?,?,'queued',?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                ident,
                cid,
                task,
                permission,
                server_id,
                max_calls,
                max_seconds,
                now(),
                now(),
                request_key,
                signature,
                int(allow_memory),
                max_total_tokens if max_total_tokens is not None else max_calls * TOKENS_PER_MODEL_CALL,
                context_window_tokens,
                resume_of,
            ),
        )
        self.store.message(cid, "user", message_text if message_text is not None else task, run_id=ident)
        self.store.event(
            ident, "queued", {"permission": permission, "server_id": server_id}
        )
        if resume_of:
            self.store.event(ident, "context.continued", {"from_run_id": resume_of, "fresh_budget": True, "max_calls": max_calls, "max_seconds": max_seconds})
        flag = threading.Event()
        self.cancellations[ident] = flag
        self.tasks[ident] = asyncio.create_task(self._run(ident, flag, operation))

        def completed(_):
            self.tasks.pop(ident, None)
            self.cancellations.pop(ident, None)

        self.tasks[ident].add_done_callback(completed)
        return self.store.one("SELECT * FROM runs WHERE id=?", (ident,))

    def cancel(self, ident):
        run = self.store.one("SELECT * FROM runs WHERE id=?", (ident,))
        if not run:
            raise ValueError("任务不存在")
        if run["status"] not in {"queued", "running"}:
            return run
        if ident in self.cancellations:
            self.cancellations[ident].set()
        self.store.execute(
            "UPDATE runs SET status=?,updated=? WHERE id=?",
            ("cancelled" if run["status"] == "queued" else "cancelling", now(), ident),
        )
        self.store.event(ident, "cancelling", {})
        # Wake suspended model I/O; process tools observe the cancellation flag.
        if ident in self.tasks:
            self.tasks[ident].cancel()
        if run["status"] == "queued":
            self.store.event(
                ident, "finished", {"status": "cancelled", "error": "排队任务已取消"}
            )
        return self.store.one("SELECT * FROM runs WHERE id=?", (ident,))

    def _tools(self, run, flag, progress=None, *, sanitize=None):
        redact = sanitize or self.redact
        policy = Policy(
            run["permission"],
            self.store.directory / "workspaces" / run["conversation_id"],
            flag,
        )
        tools = Tools(tools_executor=PlatformExecutor(
            redact, cancelled=flag,
            on_cancel_result=lambda name, result: self.store.event(run["id"], "tool.cancelled", {
                "name": name, "result": result,
            }),
            on_start=progress.before if progress else None,
        ))

        def command_progress(name, purpose=""):
            command_id = uid()

            def emit(output, elapsed, byte_count):
                sanitized = redact(output, limit=None)
                self.store.event(run["id"], "command.progress", {
                    "command_id": command_id, "name": name,
                    "elapsed_seconds": elapsed, "output_bytes": byte_count,
                    "output": sanitized[-5000:], "truncated": len(sanitized) > 5000,
                })
                if progress:
                    progress.command(command_id, name, purpose, sanitized, elapsed, byte_count)

            return emit

        @tools.register()
        def report_progress(summary: str, next_step: str = ""):
            """Tell the owner what tool evidence confirms, what is happening, and what comes next. Brief public explanation, never hidden reasoning or invented success."""
            if not summary.strip() or len(summary) > 600 or len(next_step) > 300:
                raise ValueError("进度说明需简短，摘要最多600字，下一步最多300字")
            text = summary.strip() + ("\n接下来：" + next_step.strip() if next_step.strip() else "")
            if progress:
                progress.note(text, source="agent")
            else:
                self.store.event(run["id"], "progress.note", {"text": redact(text), "source": "agent"})
            return {"reported": True}

        @tools.register()
        def update_plan(steps: list[dict[str, str]]):
            """Publish a concise task plan, then update statuses as actual work progresses. Each step has id, title, status (pending/in_progress/completed/blocked/cancelled). Plans do not grant permissions or prove completion."""
            policy.require("read")
            if not 1 <= len(steps) <= 24:
                raise ValueError("计划需要1至24个步骤")
            ids = set()
            for step in steps:
                if set(step) != {"id", "title", "status"} or not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", step["id"]):
                    raise ValueError("计划步骤字段无效")
                if step["id"] in ids or not 1 <= len(step["title"]) <= 180:
                    raise ValueError("计划步骤重复或标题过长")
                if step["status"] not in {"pending", "in_progress", "completed", "blocked", "cancelled"}:
                    raise ValueError("计划状态无效")
                ids.add(step["id"])
            cleaned = json.loads(redact(encode(steps), limit=None))
            self.store.execute(
                "INSERT INTO run_plan VALUES(?,?,?,?) ON CONFLICT(run_id) DO UPDATE SET "
                "steps=excluded.steps,updated=excluded.updated",
                (run["id"], run["conversation_id"], encode(cleaned), now()),
            )
            self.store.event(run["id"], "plan.updated", {"steps": cleaned})
            return {"steps": cleaned}

        @tools.register()
        def search_skills(query: str):
            """Search available skill summaries for a task."""
            return self.router.search(query)

        @tools.register()
        def load_skill(name: str, offset: int = 0):
            """Load a skill instruction page after discovery; follow next_offset until null."""
            return self.router.load(name, offset)

        @tools.register()
        def read_task_history(run_id: str = "", after: int = 0):
            """Read a page of persisted task/tool facts in this conversation only; use next_after to continue. Empty run_id lists recent runs."""
            policy.require("read")
            if not run_id:
                return self.store.all(
                    "SELECT id,task,status,error FROM runs WHERE conversation_id=? "
                    "AND id<>? ORDER BY created DESC LIMIT 30", (run["conversation_id"], run["id"]),
                )
            if not self.store.one(
                "SELECT id FROM runs WHERE id=? AND conversation_id=?", (run_id, run["conversation_id"]),
            ):
                raise ValueError("任务不属于当前对话")
            rows = self.store.all(
                "SELECT seq,kind,data FROM events WHERE run_id=? AND seq>? "
                "AND kind NOT IN ('delta','usage','skills','command.progress') ORDER BY seq LIMIT 8",
                (run_id, max(0, int(after))),
            )
            return {
                "events": [{**row, "data": json.loads(row["data"])} for row in rows],
                "next_after": rows[-1]["seq"] if rows else None,
            }

        @tools.register()
        def read_skill_resource(name: str, path: str, offset: int = 0):
            """Read a listed skill reference/script as data, never execute it. Follow next_offset."""
            return self.router.packages.read(name, path, offset)

        @tools.register()
        def search_documents(query: str):
            """Search the owner's private documents; return excerpts and file references."""
            return self.library.search(query)

        @tools.register()
        def read_document(file_id: str, offset: int = 0, limit: int = 12000):
            """Read one page of private document text. Follow next_offset until null to read the full document."""
            return self.library.read(file_id, offset, min(limit, 6000))

        @tools.register()
        def list_files(path: str = "."):
            """List files in the current task workspace only."""
            policy.require("read")
            directory = policy.path(path)
            return [
                {"name": p.name, "directory": p.is_dir()}
                for p in list(directory.iterdir())[:150]
            ]

        @tools.register()
        def read_file(path: str):
            """Read a UTF-8 file inside the current task workspace."""
            policy.require("read")
            target = policy.path(path)
            if target.stat().st_size > 200000:
                raise ValueError("文件过大，请分块处理")
            return target.read_text(encoding="utf-8", errors="replace")

        @tools.register()
        def write_file(path: str, content: str):
            """Write a UTF-8 file inside the task workspace; requires workspace permission."""
            policy.require("workspace")
            content = clean_text(content)
            if len(content.encode()) > 500000:
                raise ValueError("写入内容过大")
            target = policy.path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            saved = self.library.save(target.name, content.encode(), run_id=run["id"])
            return {"written": path, "artifact": saved}

        @tools.register()
        def copy_document_to_workspace(file_id: str, path: str):
            """Copy a registered private file into this task workspace for code processing; requires workspace permission."""
            policy.require("workspace")
            target = policy.path(path)
            if target.exists():
                raise ValueError("目标文件已存在，请换一个名称")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.library.path(file_id), target)
            return {"path": path, "source_file_id": file_id}

        @tools.register()
        def publish_file(path: str):
            """Save a generated workspace file as an authenticated downloadable artifact; requires workspace permission."""
            policy.require("workspace")
            target = policy.path(path)
            if not target.is_file():
                raise ValueError("文件不存在")
            with target.open("rb") as source:
                return self.library.save_stream(target.name, source, run_id=run["id"])

        @tools.register()
        def execute_command(command: str, timeout: int = 300, purpose: str = ""):
            """Run on the backend host with live output; full permission. timeout is 1–1800 seconds. Do not detach with nohup or &: cancellation owns this command group."""
            return run_command(policy, command, timeout, on_output=command_progress("execute_command", purpose))

        @tools.register()
        def list_servers():
            """List registered servers without credentials."""
            return [
                {"id": row["id"], **json.loads(row["payload"])}
                for row in self.store.all("SELECT * FROM records WHERE kind='server'")
            ]

        @tools.register()
        def run_remote_command(command: str, timeout: int = 300, purpose: str = ""):
            """Execute on the selected Linux/Python3 SSH server with live output. Full permission; timeout 1–1800 seconds. Do not detach with nohup or &: cancellation owns the process group. Use an explicit service manager for lasting services."""
            policy.require("full")
            if not run["server_id"]:
                raise ValueError("当前任务未选择目标服务器")
            server = json.loads(
                self.store.one(
                    "SELECT payload FROM records WHERE id=? AND kind='server'",
                    (run["server_id"],),
                )["payload"]
            )
            key = self.auth.secret("ssh:" + run["server_id"])
            if not key or not server.get("host_key"):
                raise ValueError("请先配置服务器私钥及已验证的 SSH 主机公钥")
            secrets_dir = self.store.directory / "ssh-runtime"
            secrets_dir.mkdir(exist_ok=True)
            key_path, hosts = (
                secrets_dir / (run["id"] + ".key"),
                secrets_dir / (run["id"] + ".hosts"),
            )
            key_path.write_text(key.rstrip() + "\n", encoding="utf-8")
            hosts.write_text(server["host_key"] + "\n", encoding="utf-8")
            try:
                key_path.chmod(0o600)
                return remote_command(
                    policy, server, key_path, command, hosts, timeout,
                    on_output=command_progress("run_remote_command", purpose),
                )
            finally:
                key_path.unlink(missing_ok=True)
                hosts.unlink(missing_ok=True)

        @tools.register()
        def deploy_repository(repository: str, app_name: str):
            """Deploy a GitHub repository containing compose.yaml/docker-compose.yml with Docker Compose on the selected server; health checks must pass."""
            if not re.fullmatch(
                r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?",
                repository,
            ) or not re.fullmatch(r"[a-z][a-z0-9-]{1,40}", app_name):
                raise ValueError("仓库地址或应用名称无效")
            if not run["server_id"]:
                raise ValueError("请为当前任务选择服务器")
            server = json.loads(
                self.store.one(
                    "SELECT payload FROM records WHERE id=?", (run["server_id"],)
                )["payload"]
            )
            target = server.get("workdir", "/srv/xinxin") + "/" + app_name
            command = (
                "set -eu; target="
                + shlex.quote(target)
                + "; if [ -e \"$target\" ]; then echo '目标目录已存在，请先检查，未覆盖'; exit 2; fi; git clone --depth 1 -- "
                + shlex.quote(repository)
                + ' "$target"; cd "$target"; docker compose config --quiet; docker compose up -d --build --wait --wait-timeout 90; docker compose ps'
            )
            return run_remote_command(command)

        @tools.register()
        def plot_csv_tool(
            file_id: str, x: str, y: str, kind: str = "line", title: str = "Data study"
        ):
            """Render a private CSV to PNG/PDF and reproducible code; requires workspace permission."""
            policy.require("workspace")
            return plot_csv(
                self.library,
                file_id,
                x,
                y,
                kind,
                title,
                run_id=run["id"],
                cancelled=flag,
            )

        @tools.register()
        def list_gallery():
            """List reference chart styles with provenance retained."""
            return gallery()

        @tools.register()
        def read_plot_resource(path: str):
            """Read a bundled plotting stage, gallery style card or Python reference. Paths are relative to the plotting skill root."""
            root = (ROOT / "resources/plot").resolve()
            target = (root / path).resolve()
            if (
                not target.is_relative_to(root)
                or target.suffix not in {".md", ".py", ".json"}
                or not target.is_file()
            ):
                raise ValueError("只可读取绘图库中的说明、样式卡和参考代码")
            if target.stat().st_size > 100000:
                raise ValueError("参考内容过大")
            return target.read_text(encoding="utf-8")

        @tools.register()
        async def transform_image_tool(file_id: str, style: str, instruction: str = ""):
            """Transform a supplied photo using collage or distillation and the configured image service; requires workspace permission."""
            policy.require("workspace")
            return await transform_image(
                self.library, self.auth, file_id, style, instruction, run["id"]
            )

        @tools.register()
        def generate_image_tool(
            prompt: str, width: int = 1024, height: int = 1024, provider: str = ""
        ):
            """Generate a new image from a text description; requires workspace permission."""
            policy.require("workspace")
            from . import imagegen

            record = imagegen.generate(
                self.library,
                prompt,
                width,
                height,
                provider or None,
                run_id=run["id"],
                cancelled=flag,
            )
            return {
                "file_id": record["id"],
                "name": record["name"],
                "mime": record["mime"],
                "size": record["size"],
                "provider": record["image"]["provider"],
                "model": record["image"]["model"],
                "prompt": record["image"]["prompt"],
                "note": "图片已生成并登记到文件库，可用 publish_file 交付，或在文件页下载。",
            }

        @tools.register()
        def list_memories():
            """Read the owner's editable long-term memories."""
            return self.store.all(
                "SELECT * FROM memories ORDER BY created DESC LIMIT 50"
            )

        @tools.register()
        def remember(content: str, category: str = "preference"):
            """Save an explicitly requested owner preference or fact; requires workspace permission."""
            policy.require("workspace")
            if not run.get("allow_memory"):
                raise PermissionError("主人没有为本轮开启保存记忆")
            if not content.strip() or len(content) > 1000:
                raise ValueError("记忆内容为空或过长")
            self.store.execute(
                "INSERT INTO memories VALUES(?,?,?,?)",
                (uid(), content, category[:30], now()),
            )
            return "已保存，可在记忆页编辑或删除"

        @tools.register()
        def search_content(query: str):
            """Search private articles, collections, photos, poems and resume records."""
            return [
                {
                    "id": row["id"],
                    "kind": row["kind"],
                    "payload": json.loads(row["payload"]),
                }
                for row in self.store.all(
                    "SELECT * FROM records WHERE kind!='server' AND payload LIKE ? LIMIT 20",
                    ("%" + query + "%",),
                )
            ]

        @tools.register()
        def create_content_draft(kind: str, title: str, content: str):
            """Create a private article or poem draft requested by the owner; requires workspace permission."""
            policy.require("workspace")
            if (
                kind not in {"article", "poem"}
                or not title.strip()
                or not content.strip()
                or len(content) > 100000
            ):
                raise ValueError(
                    "只可创建有标题和正文的私人文章或诗词草稿，正文上限 10 万字"
                )
            ident = uid()
            self.store.execute(
                "INSERT INTO records VALUES(?,?,?,?,?)",
                (
                    ident,
                    kind,
                    encode(
                        {"title": title[:200], "content": content, "published": False}
                    ),
                    now(),
                    now(),
                ),
            )
            return {"id": ident, "kind": kind, "published": False}

        return tools

    async def _run(self, ident, flag, operation):
        async with self.semaphore:
            await self._execute_run(ident, flag, operation)

    async def _execute_run(self, ident, flag, operation):
        text, status, error = "", "failed", ""
        tools, pending_operation, context, progress = None, None, None, None
        public_text = PublicText(self.redact, [])
        def sanitize(value, limit=16000):
            return public_text.sanitize(value, limit=limit)
        try:
            run = self.store.one("SELECT * FROM runs WHERE id=?", (ident,))
            public_text = PublicText(self.redact, self.secret_forms)
            if flag.is_set():
                raise asyncio.CancelledError()
            self.store.execute(
                "UPDATE runs SET status='running',updated=? WHERE id=?",
                (now(), ident),
            )
            self.store.event(ident, "started", {})
            async with asyncio.timeout(run["max_seconds"]):
                if operation:
                    pending_operation = asyncio.create_task(operation(ident, flag))
                    output = await asyncio.shield(pending_operation)
                    text = encode(output)
                    self.store.event(ident, "artifacts", output)
                else:
                    url, model, key = self.model_config()

                    def usage(value):
                        self.store.execute(
                            "UPDATE runs SET usage=? WHERE id=?",
                            (encode(value), ident),
                        )
                        self.store.event(ident, "usage", value)

                    gateway = ModelGateway(
                        url,
                        model,
                        key,
                        usage,
                        flag,
                        run["max_calls"],
                        max_tokens=run["max_total_tokens"],
                        transport=self.model_transport,
                        context_window_tokens=run["context_window_tokens"],
                    )
                    progress = ProgressNarrator(lambda kind, data: self.store.event(ident, kind, data), sanitize)
                    tools, events = self._tools(run, flag, progress, sanitize=sanitize), AgentEvents()

                    def before(name, arguments):
                        if flag.is_set():
                            raise RuntimeError("任务已取消")
                        self.store.event(
                            ident,
                            "tool.started",
                            {
                                "name": name,
                                "arguments": sanitize(encode(arguments)),
                            },
                        )
                        return name, arguments

                    def after(name, arguments, result):
                        ok = name not in tools.tools_executor.unresolved
                        progress.after(name, ok, result)
                        self.store.event(
                            ident,
                            "tool.completed",
                            {
                                "name": name,
                                "result": sanitize(result),
                                "ok": ok,
                                "skill_evidence": skill_evidence(name, arguments, matches, ok),
                            },
                        )
                        return name, arguments, result

                    events.add_before_tool_call_handler(before)
                    events.add_after_tool_call_handler(after)
                    matches = self.router.search(
                        run["task"], mode=self.router.agent_mode
                    )
                    if (
                        self.router.agent_mode == "fabric"
                        and self.router.rerank_enabled
                        and key
                        and run["max_calls"] >= 2
                    ):
                        # Fabric 的 LLM 重排会多花一次模型调用；预算只够一次时
                        # 跳过并按检索顺序执行，不把本轮预算吃光。
                        try:
                            messages = self.router.rerank_messages(run["task"], matches)
                            if messages:
                                reply = await gateway.apredict(
                                    messages, stream=False, temperature=0.0
                                )
                                output = self.router.parse_rerank_output(
                                    reply.get("content", "")
                                )
                                if output is None:
                                    raise ValueError("重排输出不是合法 JSON")
                                matches = self.router.apply_rerank(matches, output, k=4)
                        except Exception as exc:  # noqa: BLE001 - 路由降级不应中断任务
                            matches["components"]["llm_rerank"] = False
                            matches["degraded"] = True
                            matches["degraded_reason"] = (
                                "llm_rerank skipped: " + type(exc).__name__
                            )
                    elif self.router.agent_mode == "fabric":
                        matches["degraded_reason"] = (
                            "llm_rerank skipped: no model key or max_calls < 2"
                        )
                    self.store.event(ident, "skills", matches)
                    memories = self.store.all(
                        "SELECT content FROM memories ORDER BY created DESC LIMIT 20"
                    )
                    recovery = previous_work(self.store, run)
                    if recovery:
                        self.store.event(ident, "context.restored", {
                            "runs": len(recovery),
                            "events": sum(len(item["events"]) for item in recovery),
                        })
                    mood, ambient = music_atmosphere(self.store)
                    prompt = build_system_prompt(
                        run,
                        matches,
                        memories,
                        self.store.directory
                        / "workspaces"
                        / run["conversation_id"],
                        recovery=recovery,
                        mood=mood,
                        ambient=ambient,
                    )
                    context = TaskContext(
                        run["task"],
                        max_length=run["context_window_tokens"] - 32768,
                        checkpoint=lambda messages: save_context(self.store, run, messages, public_text.sanitize),
                        on_compact=lambda details: self.store.event(ident, "context.compacted", details),
                    )
                    agent = Agent(
                        llm=gateway,
                        tools=tools,
                        events=events,
                        system_prompt=prompt,
                        context_manager=context,
                        max_tool_loop=run["max_calls"],
                        max_context_length=CONTEXT_INPUT_TOKENS,
                        max_tool_result_length=64000,
                    )
                    history, restored = prior_messages(self.store, run)
                    context.messages.extend(history)
                    if history:
                        self.store.event(ident, "context.checkpoint_restored", {
                            "messages": len(history), "from_checkpoint": restored,
                            "context_window_tokens": run["context_window_tokens"],
                        })
                    answered = False
                    async for chunk in agent.apredict(instruction=run["task"]):
                        if chunk.get("tool_calls"):
                            tail = public_text.finish()
                            if tail:
                                self.store.event(ident, "delta", {"text": tail})
                            if text:
                                self.store.event(
                                    ident, "assistant.progress", {"text": public_text.sanitize(text)}
                                )
                            text = ""
                            answered = False
                            continue
                        if chunk.get("role") == "assistant" and chunk.get(
                            "content"
                        ):
                            delta = chunk["content"]
                            text += delta
                            answered = True
                            visible = public_text.feed(delta)
                            if visible:
                                self.store.event(ident, "delta", {"text": visible})
                    tail = public_text.finish()
                    if tail:
                        self.store.event(ident, "delta", {"text": tail})
                    if not answered:
                        gateway.check_budget()
                        raise RuntimeError(
                            "任务未形成最终答复，可能已达到工具调用预算"
                        )
                    if tools.tools_executor.unresolved:
                        raise RuntimeError(
                            "仍有未完成的工具操作："
                            + safe_summary(tools.tools_executor.unresolved)
                        )
                status = "completed"
        except asyncio.CancelledError:
            flag.set()
            status, error = "cancelled", "任务已取消；已发送的外部模型请求无法撤回。"
        except TimeoutError:
            flag.set()
            status, error = "failed", "任务超过时间预算，已停止本地受管执行。"
        except ModelBudgetExceeded as exc:
            error = str(exc)
            self.store.event(ident, "budget.exhausted", {
                "kind": exc.kind, "used": exc.used, "limit": exc.limit,
            })
        except Exception as exc:
            error = self.redact(str(exc))
        finally:
            async def finish():
                nonlocal text, error
                text = public_text.sanitize(text)
                error = public_text.sanitize(error)
                if flag.is_set():
                    if tools:
                        await tools.tools_executor.drain()
                        if tools.tools_executor.remote_stop_unconfirmed:
                            error = "本轮已停止继续调度，但远端命令的停止尚未确认；请检查服务器连接与进程。"
                    if pending_operation:
                        pending_operation.cancel()
                        await asyncio.gather(pending_operation, return_exceptions=True)
                # A queued cancellation is persisted before the coroutine wakes.
                # Do not emit its terminal event twice if it was waiting for a slot.
                current = self.store.one("SELECT status FROM runs WHERE id=?", (ident,))
                if current and current["status"] == "cancelled":
                    self.tasks.pop(ident, None)
                    self.cancellations.pop(ident, None)
                    return
                if text and status != "completed":
                    self.store.event(ident, "assistant.progress", {"text": text})
                    text = ""
                if text:
                    self.store.message(
                        self.store.one(
                            "SELECT conversation_id FROM runs WHERE id=?", (ident,)
                        )["conversation_id"],
                        "assistant",
                        text,
                        run_id=ident,
                    )
                if context is not None:
                    save_context(self.store, run, context.messages, public_text.sanitize)
                if progress:
                    progress.finish_waits()
                self.store.execute(
                    "UPDATE runs SET status=?,result=?,error=?,updated=? WHERE id=?",
                    (status, text, error, now(), ident),
                )
                self.store.event(ident, "finished", {"status": status, "error": error})
                self.tasks.pop(ident, None)
                self.cancellations.pop(ident, None)

            cleanup = asyncio.create_task(finish())
            while not cleanup.done():
                try:
                    await asyncio.shield(cleanup)
                except asyncio.CancelledError:
                    flag.set()
            await cleanup

    async def close(self):
        tasks = list(self.tasks.values())
        for ident in list(self.tasks):
            self.cancel(ident)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
