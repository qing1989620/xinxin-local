"""Public execution facts and bounded waiting notices, without extra model calls."""

import json


TOOL_LABELS = {
    "execute_command": "在主机执行命令", "run_remote_command": "在所选服务器执行命令",
    "deploy_repository": "部署所选仓库", "read_file": "读取工作区文件",
    "write_file": "写入工作区文件", "list_files": "检查工作区目录",
    "read_document": "读取本轮资料", "copy_document_to_workspace": "准备工作区输入文件",
    "publish_file": "保存可下载的产物", "read_task_history": "核对前轮执行记录",
    "plot_csv_tool": "生成并检查图表", "remember": "保存本轮获准的记忆",
    "generate_image_tool": "生成图片",
}
QUIET_TOOLS = {"update_plan", "report_progress", "search_skills", "load_skill", "read_skill_resource"}


class ProgressNarrator:
    def __init__(self, emit, sanitize):
        self.emit, self.sanitize = emit, sanitize
        self.waits = {}

    def note(self, text, **details):
        self.emit("progress.note", {"text": self.sanitize(text, limit=None)[:800], **details})

    def before(self, name, arguments):
        if name in QUIET_TOOLS:
            return
        purpose = self.sanitize(str(arguments.get("purpose", "")), limit=None)[:300].strip()
        label = TOOL_LABELS.get(name, "处理本步操作")
        self.note(f"开始{label}。" + (f"本步目标：{purpose}" if purpose else "正在核对执行结果，完成后接着推进。"), source="platform", tool=name)

    def after(self, name, ok, result):
        if name in QUIET_TOOLS:
            return
        label = TOOL_LABELS.get(name, "本步操作")
        value = result
        if isinstance(result, str):
            try:
                value = json.loads(result)
            except (ValueError, TypeError):
                pass
        if not ok:
            text = f"{label}遇到问题，尚未完成；我会根据返回的错误检查下一步。"
        elif isinstance(value, dict) and "exit_code" in value:
            text = f"这条命令已结束，退出码 {value['exit_code']}。接下来核对产物或继续下一步。"
        else:
            text = f"{label}已返回结果，接下来核对内容并推进。"
        self.note(text, source="platform", tool=name, ok=bool(ok))
        self.finish_waits(name)

    def finish_waits(self, name=None):
        for ident, state in self.waits.items():
            if state.get("done") or not state["notice_at"] or name and state["name"] != name:
                continue
            self.emit("progress.wait", {"command_id": ident, "text": "本步等待已结束，实际结果以工具或停止确认记录为准。", "finished": True})
            state["done"] = True

    def command(self, ident, name, purpose, output, elapsed, byte_count, *, final=False):
        state = self.waits.setdefault(ident, {"bytes": 0, "changed_at": 0, "notice_at": 0, "name": name})
        if byte_count != state["bytes"]:
            state.update(bytes=byte_count, changed_at=elapsed)
        if final:
            if state["notice_at"]:
                self.emit("progress.wait", {"command_id": ident, "text": "本条命令已结束等待，实际结果见后续执行说明。", "finished": True, "elapsed_seconds": elapsed})
            return
        if elapsed < 20 or elapsed - state["notice_at"] < 30 and state["notice_at"]:
            return
        quiet = max(0, int(elapsed - state["changed_at"]))
        lines = output.strip().splitlines()
        last_line = lines[-1].lower() if lines else ""
        if quiet >= 15:
            reason = f"已有 {quiet} 秒没有新输出；进程尚未结束，当前不能仅凭静默判断具体原因。"
        elif any(word in last_line for word in ("download", "fetching", "receiving objects", "下载")):
            reason = "最近输出包含下载或接收数据的信息；速度会影响等待时间，目前尚未返回成功结果。"
        elif any(word in last_line for word in ("compil", "building", "构建", "编译")):
            reason = "最近输出是构建或编译信息，这一步还未结束。"
        elif any(word in last_line for word in ("installing", "resolving", "安装", "解析依赖")):
            reason = "最近输出是依赖安装或解析信息，正在等待该命令返回。"
        else:
            reason = f"仍在接收执行结果，最近一次输出距现在约 {quiet} 秒，尚未结束。"
        goal = self.sanitize(str(purpose), limit=None)[:300].strip()
        text = (f"当前目标：{goal}。" if goal else f"当前正在{TOOL_LABELS.get(name, '运行本条命令')}。")
        text += f"已运行 {int(elapsed)} 秒。{reason} 可以展开终端查看详情，或停止本轮。"
        self.emit("progress.wait", {"command_id": ident, "text": text, "finished": False, "elapsed_seconds": elapsed})
        state["notice_at"] = elapsed
