"""Own a Windows command's descendants before its first instruction runs."""

import msvcrt
import uuid

import psutil
import pywintypes
import win32api
import win32con
import win32job
import win32pipe
import win32process


class WindowsJob:
    def __init__(self):
        self.handle = win32job.CreateJobObject(None, "Xinxin-" + uuid.uuid4().hex)
        limits = win32job.QueryInformationJobObject(
            self.handle, win32job.JobObjectExtendedLimitInformation
        )
        limits["BasicLimitInformation"][
            "LimitFlags"
        ] |= win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        win32job.SetInformationJobObject(
            self.handle, win32job.JobObjectExtendedLimitInformation, limits
        )

    def start(self, process):
        # Popen used CREATE_SUSPENDED: children cannot escape assignment by racing it.
        handle = win32api.OpenProcess(
            win32con.PROCESS_SET_QUOTA | win32con.PROCESS_TERMINATE, False, process.pid
        )
        try:
            win32job.AssignProcessToJobObject(self.handle, handle)
        finally:
            win32api.CloseHandle(handle)
        threads = psutil.Process(process.pid).threads()
        if not threads:
            raise RuntimeError("命令主线程不可用")
        for thread in threads:
            handle = win32api.OpenThread(
                win32con.THREAD_SUSPEND_RESUME, False, thread.id
            )
            try:
                win32process.ResumeThread(handle)
            finally:
                win32api.CloseHandle(handle)

    def active(self):
        return (
            win32job.QueryInformationJobObject(
                self.handle, win32job.JobObjectBasicAccountingInformation
            )["ActiveProcesses"]
            > 0
        )

    def stop(self):
        win32job.TerminateJobObject(self.handle, 1)

    def close(self):
        win32api.CloseHandle(self.handle)


def pipe_ready(file):
    try:
        return win32pipe.PeekNamedPipe(msvcrt.get_osfhandle(file.fileno()), 0)[1] > 0
    except pywintypes.error as exc:
        if exc.winerror == 109:  # All writers have closed their handles.
            return False
        raise
