"""A per-command remote process group, controlled through SSH stdin and a nonce."""

import base64
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import select
import signal
import subprocess
import sys
import time


def process_identity(pid):
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        return fields[19]
    except FileNotFoundError:
        return None


def living_group(group):
    for item in Path("/proc").iterdir():
        if not item.name.isdigit():
            continue
        try:
            fields = (item / "stat").read_text().rsplit(")", 1)[1].split()
            if fields[0] != "Z" and int(fields[2]) == group:
                return True
        except (FileNotFoundError, ProcessLookupError):
            pass
    return False


def stop_group(record, *, owned_child=False):
    group = record["pid"]
    # An unreaped child created by this supervisor cannot have a reused PID.
    identity = None if owned_child else process_identity(group)
    if identity is not None and identity != record["identity"] and not owned_child:
        raise RuntimeError("Remote process identity changed; refusing to signal it")
    for sig, wait in ((signal.SIGTERM, 0.4), (signal.SIGKILL, 1.5)):
        try:
            os.killpg(group, sig)
        except ProcessLookupError:
            return True
        end = time.monotonic() + wait
        while time.monotonic() < end:
            if not living_group(group):
                return True
            time.sleep(0.03)
    return not living_group(group)


def job_directory(nonce):
    if not re.fullmatch(r"[a-f0-9]{32}", nonce):
        raise ValueError("Invalid command identity")
    directory = Path("/tmp") / ("xinxin-command-" + nonce)
    directory.mkdir(mode=0o700, exist_ok=True)
    if directory.is_symlink() or directory.stat().st_uid != os.getuid():
        raise RuntimeError("Remote command directory ownership mismatch")
    return directory


def save_record(directory, record):
    temporary = directory / (".record-" + str(os.getpid()))
    temporary.write_text(json.dumps(record))
    temporary.chmod(0o600)
    temporary.replace(directory / "process.json")


@contextmanager
def command_lock(directory):
    # Both SSH processes serialize launch/registration and stop confirmation.
    import fcntl
    descriptor = os.open(directory / ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        os.close(descriptor)


def cancel(nonce):
    directory = job_directory(nonce)
    with command_lock(directory):
        (directory / "cancel").touch(mode=0o600)
        path = directory / "process.json"
        if not path.exists():
            if (directory / "launching").exists():
                return {"confirmed": False, "state": "launch_registration_unknown"}
            # The launch check holds the same lock, so a late starter cannot launch.
            return {"confirmed": True, "state": "not_started"}
        record = json.loads(path.read_text())
    if record.get("state") != "running" and record.get("confirmed_stopped"):
        return {"confirmed": True, "state": "already_stopped"}
    stopped = stop_group(record)
    return {"confirmed": stopped, "state": "stopped" if stopped else "unconfirmed"}


def connection_closed():
    # Poll the raw SSH control descriptor. A blocked daemon BufferedReader causes
    # CPython to abort at shutdown, even after the command itself succeeded.
    descriptor = sys.stdin.fileno()
    ready, _, _ = select.select([descriptor], [], [], 0)
    return bool(ready) and not os.read(descriptor, 1)


def run(nonce, encoded, timeout):
    directory = job_directory(nonce)
    command = base64.b64decode(encoded, validate=True).decode("utf-8")
    with command_lock(directory):
        if connection_closed() or (directory / "cancel").exists():
            return 125
        intent = directory / "launching"
        intent.touch(mode=0o600)
        process = subprocess.Popen(
            ["/bin/sh", "-c", command], stdin=subprocess.DEVNULL,
            stdout=sys.stdout, stderr=sys.stderr, start_new_session=True,
        )
        record = {"pid": process.pid, "identity": None, "state": "running"}
        try:
            record["identity"] = process_identity(process.pid)
            save_record(directory, record)
        except BaseException:
            # Registration failure must not release an untracked live child.
            stopped = stop_group(record, owned_child=True)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                stopped = False
            if stopped:
                intent.unlink(missing_ok=True)
            raise
    deadline = time.monotonic() + timeout
    reason = "finished"
    try:
        while process.poll() is None:
            if connection_closed() or (directory / "cancel").exists():
                reason = "cancelled"
                break
            if time.monotonic() >= deadline:
                reason = "timeout"
                break
            time.sleep(0.04)
    finally:
        if connection_closed() or (directory / "cancel").exists():
            reason = "cancelled"
        stopped = stop_group(record)
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            stopped = False
        with command_lock(directory):
            save_record(directory, {**record, "state": reason, "confirmed_stopped": stopped})
    return 124 if reason == "timeout" else 125 if reason == "cancelled" else process.returncode


if __name__ == "__main__":
    if sys.argv[1] == "stop":
        print(json.dumps(cancel(sys.argv[2])))
    else:
        raise SystemExit(run(sys.argv[2], sys.argv[3], min(1800, max(1, int(sys.argv[4])))))
