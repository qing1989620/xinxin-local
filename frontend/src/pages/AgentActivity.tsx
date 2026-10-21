import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { EventItem, Run } from "../api";
import SkillNetTrace from "./SkillNetTrace";

const names: Record<string, string> = {
  execute_command: "主机终端",
  run_remote_command: "远端终端",
  read_file: "读取文件",
  write_file: "写入文件",
  list_files: "查看目录",
  search_skills: "检索技能",
  load_skill: "读取技能",
  read_document: "读取资料",
  deploy_repository: "部署仓库",
  read_task_history: "读取历史执行记录",
};

export function activityEvents(events: EventItem[]) {
  const latest = new Map<string, number>();
  for (const event of events) {
    if (event.kind === "command.progress")
      latest.set(event.data.command_id, event.seq);
    if (event.kind === "plan.updated") latest.set("plan", event.seq);
    if (event.kind === "progress.wait")
      latest.set(`wait:${event.data.command_id}`, event.seq);
  }
  const narrated = events.some((event) => event.kind === "progress.note");
  return events.filter((event) => {
    if (event.kind === "command.progress")
      return latest.get(event.data.command_id) === event.seq;
    if (event.kind === "plan.updated") return latest.get("plan") === event.seq;
    if (event.kind === "progress.wait")
      return (
        latest.get(`wait:${event.data.command_id}`) === event.seq &&
        !event.data.finished
      );
    if (["update_plan", "report_progress"].includes(event.data.name))
      return false;
    if (narrated && event.kind === "tool.started") return false;
    return [
      "assistant.progress",
      "progress.note",
      "context.continued",
      "tool.started",
      "tool.completed",
      "tool.cancelled",
      "context.compacted",
      "context.checkpoint_restored",
      "context.restored",
    ].includes(event.kind);
  });
}

export default function AgentActivity({
  run,
  events,
  showSkills = true,
}: {
  run: Run;
  events: EventItem[];
  showSkills?: boolean;
}) {
  const visible = activityEvents(events);
  const stopping = run.status === "cancelling";
  return (
    <section className="agent-activity" aria-label="本轮执行过程">
      <header>
        <strong>执行过程</strong>
        <span>
          {stopping
            ? "正在停止"
            : ["running", "queued"].includes(run.status)
              ? "进行中"
              : run.status === "completed"
                ? "本轮完成"
                : run.status === "cancelled"
                  ? "已停止"
                  : "本轮已结束"}
        </span>
      </header>
      {showSkills && <SkillNetTrace run={run} events={events} />}
      {stopping && (
        <p className="activity-stopping" role="status">
          已收到停止请求，正在结束命令并确认远端状态。已创建的文件和已启动的独立服务不会自动回滚。
        </p>
      )}
      {!visible.length && (
        <p className="muted">{["queued", "running", "cancelling"].includes(run.status)
          ? "正在读取上下文，等待第一条执行进度。"
          : "本轮执行已结束，结果和可用记录会保留在此对话。"}</p>
      )}
      <ol>
        {visible.map((event) => (
          <li
            key={event.seq}
            className={`activity-${event.kind.replaceAll(".", "-")}`}
          >
            {event.kind === "progress.note" ||
            event.kind === "progress.wait" ? (
              <div
                className={`activity-narration ${event.kind === "progress.wait" ? "activity-waiting" : ""}`}
              >
                <small>
                  {event.data.source === "agent"
                    ? "Xinxin · 进度"
                    : event.kind === "progress.wait"
                      ? "等待说明"
                      : "执行状态"}
                </small>
                <p>
                  {event.kind === "progress.wait" &&
                  !["running", "queued", "cancelling"].includes(run.status)
                    ? "本轮已经结束；本步最终状态请查看后续工具结果。"
                    : String(event.data.text || "")}
                </p>
              </div>
            ) : event.kind === "assistant.progress" ? (
              <div className="activity-message">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  skipHtml
                  components={{ img: ({ alt }) => <span>[图片：{alt}]</span> }}
                >
                  {String(event.data.text || "")}
                </ReactMarkdown>
              </div>
            ) : event.kind === "plan.updated" ? (
              <div className="activity-plan">
                <strong>任务步骤</strong>
                <ol>
                  {(event.data.steps || []).map((step: any) => (
                    <li key={step.id}>
                      <span data-state={step.status}>
                        {(
                          {
                            pending: "待执行",
                            in_progress: "进行中",
                            completed: "已完成",
                            blocked: "受阻",
                            cancelled: "已停止",
                          } as Record<string, string>
                        )[step.status] || step.status}
                      </span>
                      {step.title}
                    </li>
                  ))}
                </ol>
                <small>步骤状态由 Agent 更新；执行结果以工具记录为准。</small>
              </div>
            ) : event.kind === "command.progress" ? (
              <details className="activity-terminal">
                <summary>
                  <strong>{names[event.data.name] || "终端"}</strong>
                  <span>
                    执行用时 {event.data.elapsed_seconds} 秒 ·{" "}
                    {Number(event.data.output_bytes || 0).toLocaleString()} 字节
                  </span>
                  <span>展开日志</span>
                </summary>
                <pre aria-label="命令实时输出">
                  {event.data.output || "命令运行中，等待输出…"}
                </pre>
                {event.data.truncated && (
                  <small>显示最近输出，完整受控结果见执行详情。</small>
                )}
              </details>
            ) : event.kind.startsWith("tool.") ? (
              <details
                className={event.data.ok === false ? "activity-error" : ""}
              >
                <summary>
                  {event.kind === "tool.started"
                    ? "调用"
                    : event.kind === "tool.cancelled"
                      ? "停止收尾"
                      : event.data.ok === false
                        ? "执行遇到问题"
                        : "已返回"}{" "}
                  · {names[event.data.name] || event.data.name}
                </summary>
                <pre>
                  {String(event.data.result || event.data.arguments || "")}
                </pre>
              </details>
            ) : (
              <p className="activity-context">
                {event.kind === "context.continued"
                  ? `已接上原任务与前轮进度。本轮使用新的预算（最多 ${event.data.max_calls} 次调用），已完成的操作会先核对再继续。`
                  : event.kind === "context.compacted"
                    ? `接近上下文窗口，已回收 ${event.data.removed_groups} 组旧交换；原始执行记录仍可读取。`
                    : event.kind === "context.checkpoint_restored"
                      ? `已续接 ${event.data.messages} 条持久消息和工具记录。`
                      : `已恢复前轮 ${event.data.events} 条工具事实。`}
              </p>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}
