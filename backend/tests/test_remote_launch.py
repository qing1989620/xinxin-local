import base64
from contextlib import contextmanager
import threading
from types import SimpleNamespace

import pytest

from app import remote_runner


def test_stop_confirmation_waits_for_a_launch_already_inside_the_critical_section(tmp_path, monkeypatch):
    lock = threading.Lock()
    launching, allow_launch, stop_returned = threading.Event(), threading.Event(), threading.Event()
    launched = []

    @contextmanager
    def command_lock(directory):
        with lock:
            yield

    class Child:
        pid, returncode = 123, 0
        def poll(self):
            return 0
        def wait(self, timeout):
            return 0

    def popen(*args, **kwargs):
        launching.set()
        assert allow_launch.wait(3)
        launched.append(True)
        return Child()

    # No real process, stdin, signals or /tmp access in this portable race fixture.
    monkeypatch.setattr(remote_runner, "job_directory", lambda nonce: tmp_path)
    monkeypatch.setattr(remote_runner, "command_lock", command_lock)
    monkeypatch.setattr(remote_runner, "connection_closed", lambda: False)
    monkeypatch.setattr(remote_runner, "process_identity", lambda pid: "same-process")
    monkeypatch.setattr(remote_runner, "stop_group", lambda record: True)
    monkeypatch.setattr(remote_runner.subprocess, "Popen", popen)
    monkeypatch.setattr(remote_runner, "sys", SimpleNamespace(stdout=None, stderr=None, stdin=SimpleNamespace(buffer=SimpleNamespace(read=lambda n: allow_launch.wait(3)))))
    result = {}
    errors = []

    def invoke(key, operation):
        try:
            result[key] = operation()
        except BaseException as exc:
            errors.append(exc)
        finally:
            if key == "stop":
                stop_returned.set()

    run = threading.Thread(target=invoke, args=("code", lambda: remote_runner.run("fixture", base64.b64encode(b"synthetic").decode(), 30)))
    stop = threading.Thread(target=invoke, args=("stop", lambda: remote_runner.cancel("fixture")))
    run.start()
    assert launching.wait(2)
    stop.start()
    assert not stop_returned.wait(.1)
    allow_launch.set()
    run.join(3)
    stop.join(3)
    assert not run.is_alive() and not stop.is_alive()
    assert not errors and result["code"] in {0, 125}
    assert launched == [True] and result["stop"]["confirmed"]
    assert remote_runner.run("fixture", base64.b64encode(b"synthetic").decode(), 30) == 125
    assert launched == [True]  # A late starter observes the durable cancellation marker.


@pytest.mark.parametrize("cleanup_confirmed", [True, False])
def test_failed_process_registration_cleans_child_before_unlock_and_never_falsely_confirms(tmp_path, monkeypatch, cleanup_confirmed):
    cleanup = []
    lock = threading.Lock()

    @contextmanager
    def command_lock(directory):
        with lock:
            yield

    def stop(record, *, owned_child=False):
        assert lock.locked()
        assert owned_child
        cleanup.append(record["pid"])
        return cleanup_confirmed

    def failed_save(*args):
        raise OSError("synthetic disk failure")

    monkeypatch.setattr(remote_runner, "job_directory", lambda nonce: tmp_path)
    monkeypatch.setattr(remote_runner, "command_lock", command_lock)
    monkeypatch.setattr(remote_runner, "connection_closed", lambda: False)
    monkeypatch.setattr(remote_runner, "process_identity", lambda pid: "same-process")
    monkeypatch.setattr(remote_runner.subprocess, "Popen", lambda *args, **kwargs: SimpleNamespace(pid=123, wait=lambda timeout: 0))
    monkeypatch.setattr(remote_runner, "save_record", failed_save)
    monkeypatch.setattr(remote_runner, "stop_group", stop)
    with pytest.raises(OSError, match="disk failure"):
        remote_runner.run("fixture", base64.b64encode(b"synthetic").decode(), 30)
    assert cleanup == [123]
    assert remote_runner.cancel("fixture")["confirmed"] is cleanup_confirmed


def test_failed_proc_identity_read_still_signals_and_reaps_the_owned_child(tmp_path, monkeypatch):
    calls = []

    @contextmanager
    def command_lock(directory):
        yield

    def failed_identity(pid):
        calls.append("identity")
        raise OSError("synthetic proc read failure")

    monkeypatch.setattr(remote_runner, "job_directory", lambda nonce: tmp_path)
    monkeypatch.setattr(remote_runner, "command_lock", command_lock)
    monkeypatch.setattr(remote_runner, "connection_closed", lambda: False)
    monkeypatch.setattr(remote_runner, "process_identity", failed_identity)
    monkeypatch.setattr(remote_runner, "living_group", lambda group: False)
    monkeypatch.setattr(remote_runner, "signal", SimpleNamespace(SIGTERM=15, SIGKILL=9))
    monkeypatch.setattr(remote_runner.os, "killpg", lambda group, sig: calls.append("signal"), raising=False)
    monkeypatch.setattr(remote_runner.subprocess, "Popen", lambda *args, **kwargs: SimpleNamespace(pid=123, wait=lambda timeout: calls.append("wait")))
    with pytest.raises(OSError, match="proc read failure"):
        remote_runner.run("fixture", base64.b64encode(b"synthetic").decode(), 30)
    assert calls == ["identity", "signal", "wait"]
    assert remote_runner.cancel("fixture")["confirmed"]
