from __future__ import annotations

import os
import base64
import json
import re
import select
import shlex
import shutil
import signal
import subprocess
import threading
import time
import uuid
from pathlib import Path

PERMISSIONS = {"read": 0, "workspace": 1, "full": 2}


class Policy:
    def __init__(self, level, workspace, cancelled=None):
        if level not in PERMISSIONS:
            raise ValueError("未知权限等级")
        self.level, self.workspace = level, Path(workspace).resolve()
        self.cancelled = cancelled or threading.Event()
        self.workspace.mkdir(parents=True, exist_ok=True)

    def require(self, minimum):
        if self.cancelled.is_set():
            raise RuntimeError("任务已取消")
        if PERMISSIONS[self.level] < PERMISSIONS[minimum]:
            raise PermissionError(f"此操作需要{minimum}权限；当前任务为{self.level}")

    def path(self, relative):
        if not relative or "\x00" in relative:
            raise ValueError("路径为空或无效")
        path = (self.workspace / relative).resolve()
        if not path.is_relative_to(self.workspace):
            raise PermissionError("路径超出任务工作区")
        return path


def stop_process(process, scope=None):
    if scope:
        scope.stop()
    elif os.name != "nt":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif process.poll() is None:
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            timeout=8,
        )
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


def process_group_active(pid):
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False


def execute_process(command, cwd, cancelled, timeout=90, *, on_output=None, keep_stdin=False):
    env = {
        k: v
        for k, v in os.environ.items()
        if k.upper()
        in {
            "PATH",
            "SYSTEMROOT",
            "WINDIR",
            "TEMP",
            "TMP",
            "PATHEXT",
            "LANG",
            "LC_ALL",
            "COMSPEC",
        }
    }
    scope = None
    if os.name == "nt":
        from .windows_job import WindowsJob, pipe_ready

        scope = WindowsJob()
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE if keep_stdin else subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        env=env,
        start_new_session=os.name != "nt",
        creationflags=(
            (subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW | 0x4)
            if os.name == "nt"
            else 0
        ),
    )
    try:
        if scope:
            scope.start(process)
    except BaseException:
        process.kill()
        scope.close()
        process.stdout.close()
        raise
    parts, total, over_limit = [], 0, False

    def consume_available():
        nonlocal total, over_limit
        ready = lambda: (
            pipe_ready(process.stdout)
            if scope
            else bool(select.select([process.stdout], [], [], 0)[0])
        )
        while ready():
            block = os.read(process.stdout.fileno(), 4096)
            if not block:
                break
            available = max(0, 65536 - total)
            parts.append(block[:available])
            total += len(block)
            if total > 65536:
                over_limit = True
                break

    started = time.monotonic()
    deadline = started + timeout
    reason = ""
    last_progress, last_size = 0, -1

    def progress(final=False):
        nonlocal last_progress, last_size
        if on_output is None:
            return
        elapsed = time.monotonic() - started
        changed = total != last_size
        if final or elapsed - last_progress >= (0.6 if changed else 4) or last_size < 0:
            raw = b"".join(parts).decode("utf-8", "replace")
            # Do not publish a half-written credential at the end of a line.
            complete = raw if final else raw[: raw.rfind("\n") + 1]
            on_output(complete, round(elapsed, 1), total)
            last_progress, last_size = elapsed, total
    try:
        while True:
            consume_available()
            progress()
            parent_done = process.poll() is not None
            descendants = scope.active() if scope else process_group_active(process.pid)
            if cancelled.is_set() or time.monotonic() > deadline or over_limit:
                reason = (
                    "cancelled"
                    if cancelled.is_set()
                    else "output_limit" if over_limit else "timeout"
                )
                stop_process(process, scope)
                break
            if parent_done and not descendants:
                break
            time.sleep(0.04)
        consume_available()
        if over_limit and not reason:
            reason = "output_limit"
        progress(final=True)
        return {
            "exit_code": process.returncode,
            "output": b"".join(parts).decode("utf-8", "replace"),
            "stopped": reason,
            "ok": process.returncode == 0 and not reason,
        }
    finally:
        if process.stdin:
            process.stdin.close()
        if scope:
            scope.close()
        else:
            stop_process(process)
        process.stdout.close()


def run_command(policy, command, timeout=300, *, on_output=None):
    policy.require("full")
    if not command.strip() or len(command) > 12000:
        raise ValueError("命令为空或过长")
    executable = (
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command]
        if os.name == "nt"
        else ["/bin/sh", "-c", command]
    )
    return execute_process(
        executable, policy.workspace, policy.cancelled, min(timeout, 1800), on_output=on_output
    )


def remote_command(policy, server, key_path, command, known_hosts, timeout=300, *, on_output=None):
    policy.require("full")
    if not re.fullmatch(r"[A-Za-z0-9_.:-]+", server["host"]) or not re.fullmatch(
        r"[A-Za-z0-9_.-]+", server["username"]
    ):
        raise ValueError("服务器地址或用户无效")
    if not command.strip() or len(command) > 64000:
        raise ValueError("命令为空或过长")
    args = [
        "ssh",
        "-T",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        f"UserKnownHostsFile={known_hosts}",
        "-o",
        "ConnectTimeout=10",
        "-o",
        "ServerAliveInterval=5",
        "-o",
        "ServerAliveCountMax=2",
        "-p",
        str(server["port"]),
        "-i",
        str(key_path),
        "--",
        f"{server['username']}@{server['host']}",
    ]
    nonce = uuid.uuid4().hex
    source = Path(__file__).with_name("remote_runner.py").read_text(encoding="utf-8")
    prefix = "python3 -c " + shlex.quote(source)
    duration = max(1, min(1800, int(timeout)))
    encoded = base64.b64encode(command.encode("utf-8")).decode("ascii")
    remote = f"{prefix} run {nonce} {encoded} {duration}"
    result = execute_process(
        args + [remote], policy.workspace, policy.cancelled, duration + 3,
        on_output=on_output, keep_stdin=True,
    )
    if result["stopped"] or policy.cancelled.is_set():
        cleanup = execute_process(
            args + [f"{prefix} stop {nonce}"], policy.workspace, threading.Event(), 5,
        )
        try:
            confirmed = cleanup["ok"] and json.loads(cleanup["output"])["confirmed"]
        except (ValueError, KeyError):
            confirmed = False
        result["remote_stop_confirmed"] = bool(confirmed)
        if not confirmed:
            result["output"] += "\n远端停止尚未确认；不会自动重试原命令，请核对连接和进程。"
    return result
