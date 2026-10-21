import { useEffect, useState } from "react";
import {
  ArrowUpRight,
  Check,
  Download,
  FileText,
  PanelRightClose,
  ShieldCheck,
  Sparkles,
  ThumbsUp,
  ThumbsDown,
  Clock3,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { useNavigate } from "react-router-dom";
import {
  api,
  post,
  download,
  type Run,
  type FileItem,
  type EventItem,
} from "../api";
import { Dialog, Empty, Status, date, size, useToast } from "../ui";

const toolNames: Record<string, string> = {
  write_file: "写入文件",
  read_file: "阅读工作区",
  execute_command: "执行本机命令",
  run_remote_command: "执行服务器命令",
  deploy_repository: "部署仓库",
  search_documents: "检索私人资料",
  read_document: "阅读资料",
  search_skills: "检索技能",
  load_skill: "加载技能",
  update_plan: "更新任务步骤",
  read_task_history: "读取历史执行记录",
  plot_csv_tool: "绘制图表",
  transform_image_tool: "转换图片",
  remember: "保存记忆",
  publish_file: "保存交付物",
  list_files: "查看工作区",
  list_servers: "查看服务器",
  copy_document_to_workspace: "准备文件",
  read_plot_resource: "阅读绘图参考",
  search_content: "检索个人内容",
  create_content_draft: "创建私人草稿",
};
export default function AgentInspector({
  run,
  events,
  files,
  onClose,
}: {
  run: Run | null;
  events: EventItem[];
  files: FileItem[];
  onClose: () => void;
}) {
  const [tab, setTab] = useState("process"),
    [skill, setSkill] = useState<any>(null),
    [rated, setRated] = useState<string[]>([]),
    toast = useToast(),
    navigate = useNavigate();
  useEffect(() => {
    setRated([]);
  }, [run?.id]);
  let storedUsage: Record<string, any> = {};
  try {
    storedUsage = JSON.parse(run?.usage || "{}");
  } catch {
    /* Older interrupted records may omit usage. */
  }
  const selection = [...events].reverse().find((event) => event.kind === "skills")?.data,
    usage =
      [...events].reverse().find((event) => event.kind === "usage")?.data ||
      storedUsage;
  const finished = events.some((event) => event.kind === "finished"),
    hasTool = events.some((event) => event.kind === "tool.started");
  const phases = [
    {
      label: "任务登记",
      done: Boolean(run),
      active: Boolean(run) && !selection,
    },
    {
      label: "选择能力",
      done: Boolean(selection),
      active: Boolean(selection) && !hasTool && !finished,
    },
    {
      label: "执行与验证",
      done: hasTool && finished,
      active: hasTool && !finished,
    },
    { label: "交付结果", done: finished, active: false },
  ];
  const visible = events.filter(
    (event) => !["delta", "usage", "skills"].includes(event.kind),
  );
  async function openSkill(id: string) {
    try {
      setSkill(await api(`/skills/${id}`));
    } catch (error) {
      toast((error as Error).message, true);
    }
  }
  return (
    <aside className="trace-panel inspector-v2">
      <header>
        <div>
          <span className="eyebrow">ACTION CONTEXT</span>
          <h2>任务上下文</h2>
        </div>
        <button
          className="icon-button"
          aria-label="关闭任务上下文"
          onClick={onClose}
        >
          <PanelRightClose size={18} />
        </button>
      </header>
      {run && (
        <div className="inspector-run">
          <Status value={run.status} />
          <span>
            <ShieldCheck size={12} />
            {
              { read: "只读", workspace: "工作区", full: "完整权限" }[
                run.permission
              ]
            }
          </span>
          <button
            className="text-button"
            onClick={() => navigate(`/tasks?run=${run.id}`)}
            aria-label="查看完整任务"
          >
            <ArrowUpRight size={15} />
          </button>
        </div>
      )}
      <div className="inspector-tabs" aria-label="上下文分类">
        {[
          ["process", "过程"],
          ["files", "交付"],
          ["skills", "技能"],
        ].map(([value, label]) => (
          <button
            key={value}
            aria-pressed={tab === value}
            className={tab === value ? "active" : ""}
            onClick={() => setTab(value)}
          >
            {label}
            {value === "files" && files.length > 0 && (
              <small>{files.length}</small>
            )}
          </button>
        ))}
      </div>
      <div className="inspector-content">
        {tab === "process" ? (
          <>
            <div className="phase-track">
              {phases.map((phase, i) => (
                <div
                  key={phase.label}
                  className={`${phase.done ? "done" : ""} ${phase.active ? "active" : ""}`}
                >
                  <span>{phase.done ? <Check size={11} /> : i + 1}</span>
                  <strong>{phase.label}</strong>
                </div>
              ))}
            </div>
            {visible.length ? (
              <ol className="event-list">
                {visible.map((event) => (
                  <li key={event.seq}>
                    <span
                      className={`event-dot ${event.data.ok === false ? "error" : ""}`}
                    />
                    <div>
                      <strong>
                        {event.kind === "tool.started"
                          ? toolNames[event.data.name] || event.data.name
                          : event.kind === "tool.completed"
                            ? event.data.ok === false
                              ? "工具未完成"
                              : "工具已返回"
                            : {
                                queued: "任务已登记",
                                started: "开始执行",
                                finished: "本轮结束",
                                cancelling: "正在停止",
                                artifacts: "交付物已保存",
                                "assistant.progress": "Xinxin 的进度",
                                "budget.exhausted": "本轮预算已达到",
                                "context.restored": "已恢复前轮工具记录",
                                "context.checkpoint_restored": "已恢复持久会话",
                                "context.compacted": "已回收旧上下文",
                                "command.progress": "终端实时输出",
                                "plan.updated": "任务步骤已更新",
                                "tool.cancelled": "命令停止结果",
                              }[event.kind] || event.kind}
                      </strong>
                      {event.kind === "tool.started" && (
                        <small className="tool-identifier">
                          {event.data.name}
                        </small>
                      )}
                      {event.data.error && (
                        <p className="inspector-error">{event.data.error}</p>
                      )}
                      {event.kind === "assistant.progress" && (
                        <p>{event.data.text}</p>
                      )}
                      {event.kind === "command.progress" && (
                        <>
                          <small>执行 {event.data.elapsed_seconds} 秒</small>
                          <pre>{event.data.output || "等待输出…"}</pre>
                        </>
                      )}
                      {event.kind === "context.checkpoint_restored" && (
                        <p>已续接 {event.data.messages} 条消息和工具记录。</p>
                      )}
                      {event.kind === "budget.exhausted" && (
                        <p>
                          {event.data.kind === "calls"
                            ? "模型调用次数"
                            : "累计令牌"}
                          ：{event.data.used} / {event.data.limit}
                        </p>
                      )}
                      {event.kind === "context.restored" && (
                        <p>
                          已读取 {event.data.runs} 轮记录、{event.data.events}{" "}
                          条工具事件，按本轮权限继续。
                        </p>
                      )}
                      {event.kind.startsWith("tool.") && (
                        <details>
                          <summary>
                            {event.kind === "tool.started"
                              ? "查看输入"
                              : "查看结果"}
                          </summary>
                          <pre>{event.data.result || event.data.arguments}</pre>
                        </details>
                      )}
                      <small>{date(event.created)}</small>
                    </div>
                  </li>
                ))}
              </ol>
            ) : (
              <Empty
                title="过程在这里展开"
                description="技能选择、工具调用与交付都有迹可循。"
              />
            )}
          </>
        ) : tab === "files" ? (
          <>
            {files.length ? (
              <div className="inspector-files">
                {files.map((file) => (
                  <button
                    key={file.id}
                    onClick={() =>
                      void download(file).catch((error) =>
                        toast(error.message, true),
                      )
                    }
                  >
                    <FileText size={19} />
                    <span>
                      <strong>{file.name}</strong>
                      <small>{size(file.size)}</small>
                    </span>
                    <Download size={15} />
                  </button>
                ))}
              </div>
            ) : (
              <Empty
                title="等一个可以带走的结果"
                description="实际生成的代码、图表和文档会出现在这里。"
              />
            )}
          </>
        ) : (
          <>
            {selection ? (
              <>
                <div className="routing-caption">
                  <Sparkles size={16} />
                  <span>与本次目标相关的能力</span>
                </div>
                <div className="inspector-skills">
                  {selection.skills?.map((item: any) => (
                    <div key={item.id}>
                      <button onClick={() => void openSkill(item.id)}>
                        <span>
                          <strong>{item.name}</strong>
                          <small>
                            {item.domain} · 相关度{" "}
                            {Number(item.score).toFixed(2)}
                          </small>
                        </span>
                        <ArrowUpRight size={14} />
                      </button>
                      {run?.status === "completed" &&
                        events.some(
                          (event) =>
                            event.kind === "tool.completed" &&
                            event.data.ok === true &&
                            item.tools.includes(event.data.name),
                        ) && (
                          <div className="skill-rating">
                            {rated.includes(item.id) ? (
                              <small>已记录反馈</small>
                            ) : (
                              <>
                                <span>这项能力有帮助吗？</span>
                                {[
                                  [1, ThumbsUp],
                                  [0, ThumbsDown],
                                ].map(([reward, Icon]: any) => (
                                  <button
                                    key={reward}
                                    aria-label={
                                      reward ? "技能有帮助" : "技能需要改进"
                                    }
                                    onClick={async () => {
                                      try {
                                        await post(
                                          `/skills/${item.id}/feedback`,
                                          { run_id: run.id, reward },
                                        );
                                        setRated((old) => [...old, item.id]);
                                        toast("反馈已记录，用于后续技能选择");
                                      } catch (error) {
                                        toast((error as Error).message, true);
                                      }
                                    }}
                                  >
                                    <Icon size={13} />
                                  </button>
                                ))}
                              </>
                            )}
                          </div>
                        )}
                    </div>
                  ))}
                </div>
                {selection.order?.length > 0 && (
                  <div className="dependency-order">
                    <span className="eyebrow">建议调用顺序</span>
                    {selection.order.map((id: string, i: number) => (
                      <button key={id} onClick={() => void openSkill(id)}>
                        <span>{String(i + 1).padStart(2, "0")}</span>
                        {selection.skills?.find((item: any) => item.id === id)
                          ?.name ||
                          selection.dependencies?.find(
                            (item: any) => item.id === id,
                          )?.name ||
                          id}
                        <ArrowUpRight size={12} />
                      </button>
                    ))}
                  </div>
                )}
                <p className="field-help">
                  检索相关度只用于选择能力，执行范围仍由本轮权限决定。
                </p>
              </>
            ) : (
              <Empty
                title="先有目标，再选能力"
                description="发起任务后，查看选择了哪些技能。"
              />
            )}
          </>
        )}
      </div>
      <footer className="inspector-footer">
        <span>
          上下文约{" "}
          {Number(
            usage.context_tokens_estimate || usage.prompt_tokens_last || 0,
          ).toLocaleString()}{" "}
          /{" "}
          {usage.context_window_tokens || run?.context_window_tokens
            ? `${Number(usage.context_window_tokens || run?.context_window_tokens).toLocaleString()} tokens`
            : "旧轮次未记录档位"}
        </span>
        <span>
          <Clock3 size={13} />
          {usage.calls || 0} / {run?.max_calls ?? usage.max_calls ?? "—"} 次调用
        </span>
        <span>
          {(usage.total_tokens || 0).toLocaleString()} /{" "}
          {(
            run?.max_total_tokens ?? usage.max_total_tokens
          )?.toLocaleString() ?? "—"}{" "}
          累计令牌（多次调用合计）
        </span>
      </footer>
      {skill && (
        <Dialog title={skill.name} onClose={() => setSkill(null)} wide>
          <div className="markdown skill-markdown">
            <ReactMarkdown skipHtml>{skill.markdown}</ReactMarkdown>
          </div>
        </Dialog>
      )}
    </aside>
  );
}
