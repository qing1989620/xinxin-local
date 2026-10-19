import { useEffect, useRef, useState, type ReactNode } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import {
  ArrowUpRight,
  CheckCircle2,
  Circle,
  Download,
  RefreshCw,
  Search,
  Square,
  X,
} from "lucide-react";
import {
  api,
  post,
  download,
  watchRun,
  type Run,
  type EventItem,
} from "../api";
import { parseJson } from "../safeJson";
import {
  Empty,
  ErrorState,
  Loading,
  PageHeader,
  Status,
  date,
  useResource,
  useToast,
  Dialog,
  useMedia,
} from "../ui";

function TaskDetailShell({
  children,
  onClose,
}: {
  children: ReactNode;
  onClose: () => void;
}) {
  const compact = useMedia("(max-width: 1050px)");
  return compact ? (
    <Dialog title="任务详情" onClose={onClose}>
      <section className="task-detail-content">{children}</section>
    </Dialog>
  ) : (
    <aside className="task-detail">{children}</aside>
  );
}

export default function TasksPage() {
  const { data, error, reload } = useResource<Run[]>("/runs"),
    [params, setParams] = useSearchParams(),
    navigate = useNavigate(),
    toast = useToast();
  const [filter, setFilter] = useState("all"),
    [query, setQuery] = useState(""),
    [detail, setDetail] = useState<Run | null>(null),
    [events, setEvents] = useState<EventItem[]>([]);
  const id = params.get("run");
  const currentId = useRef(id);
  currentId.current = id;
  async function load(id: string) {
    const result = await api<Run>(`/runs/${id}`);
    if (currentId.current === id) setDetail(result);
  }
  useEffect(() => {
    setDetail(null);
    setEvents([]);
    if (!id) return;
    void load(id).catch((error) => toast(error.message, true));
    const controller = new AbortController();
    watchRun(
      id,
      (event) => {
        setEvents((old) =>
          old.some((item) => item.seq === event.seq) ? old : [...old, event],
        );
        if (event.kind === "finished") {
          reload();
          void load(id).catch((error) => toast(error.message, true));
        }
        if (event.kind === "started")
          setDetail((old) =>
            old?.id === id ? { ...old, status: "running" } : old,
          );
      },
      controller.signal,
    ).catch((error) => toast(error.message, true));
    return () => controller.abort();
  }, [id]);
  useEffect(() => {
    if (
      data?.some((run) =>
        ["queued", "running", "cancelling"].includes(run.status),
      )
    ) {
      const timer = setInterval(reload, 5000);
      return () => clearInterval(timer);
    }
  }, [data]);
  if (error) return <ErrorState message={error} retry={reload} />;
  if (!data) return <Loading />;
  const visible = data.filter(
    (run) =>
      (filter === "all" ||
        (filter === "active"
          ? ["queued", "running", "cancelling"].includes(run.status)
          : run.status === filter)) &&
      run.task.toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <div className="page-enter">
      <PageHeader
        overline="ACTIONS & OUTCOMES"
        title="任务与交付"
        description="任务在后端持续执行。回到这里，继续查看过程与交付。"
        action={
          <button className="button primary" onClick={() => navigate("/agent")}>
            新建任务 <ArrowUpRight size={17} />
          </button>
        }
      />
      <div className="toolbar">
        <div className="segmented">
          {[
            ["all", "全部"],
            ["active", "进行中"],
            ["completed", "已完成"],
            ["failed", "失败"],
          ].map(([value, label]) => (
            <button
              key={value}
              className={filter === value ? "selected" : ""}
              onClick={() => setFilter(value)}
            >
              {label}
            </button>
          ))}
        </div>
        <label className="search-field compact">
          <Search size={16} />
          <input
            aria-label="搜索任务"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="寻找一件事"
          />
        </label>
        <button className="icon-button" aria-label="刷新任务" onClick={reload}>
          <RefreshCw size={16} />
        </button>
      </div>
      <div className={`tasks-grid ${id ? "with-detail" : ""}`}>
        <section className="list-panel">
          {visible.length ? (
            visible.map((run) => (
              <button
                key={run.id}
                className={`task-list-row ${id === run.id ? "selected" : ""}`}
                onClick={() => setParams({ run: run.id })}
              >
                <span className="task-leading">
                  {run.status === "completed" ? (
                    <CheckCircle2 size={19} strokeWidth={1.4} />
                  ) : (
                    <Circle size={19} strokeWidth={1.2} />
                  )}
                </span>
                <div>
                  <strong>{run.task.split("\n")[0]}</strong>
                  <small>
                    {date(run.created)} ·{" "}
                    {
                      { read: "只读", workspace: "工作区", full: "完整权限" }[
                        run.permission
                      ]
                    }
                  </small>
                </div>
                <Status value={run.status} />
                <ArrowUpRight size={16} />
              </button>
            ))
          ) : (
            <Empty
              title={query ? "没有找到这件事" : "下一件重要的事，还没开始"}
              description="从 Agent 对话发起，或在工具页直接创建绘图任务。"
            />
          )}
        </section>
        {id && (
          <TaskDetailShell onClose={() => setParams({})}>
            <header>
              <span className="eyebrow">ACTION DETAIL</span>
              <button
                className="icon-button"
                aria-label="关闭任务详情"
                onClick={() => setParams({})}
              >
                <X size={18} />
              </button>
            </header>
            {detail ? (
              <>
                <Status value={detail.status} />
                <h2>{detail.task.split("\n")[0]}</h2>
                <div className="detail-meta">
                  <span>权限</span>
                  <strong>
                    {
                      { read: "只读", workspace: "工作区", full: "完整" }[
                        detail.permission
                      ]
                    }
                  </strong>
                  <span>创建</span>
                  <strong>{date(detail.created)}</strong>
                  <span>用量</span>
                  <strong>
                    {parseJson<{ total_tokens?: number }>(
                      detail.usage,
                      {},
                    ).total_tokens || 0}{" "}
                    tokens
                  </strong>
                </div>
                {["queued", "running", "cancelling"].includes(
                  detail.status,
                ) && (
                  <button
                    className="button secondary"
                    onClick={async () => {
                      try {
                        await post(`/runs/${id}/cancel`, {});
                        await load(id);
                        reload();
                      } catch (error) {
                        toast((error as Error).message, true);
                      }
                    }}
                  >
                    <Square size={14} />
                    停止任务
                  </button>
                )}
                {detail.error && (
                  <div className="form-error" role="alert">
                    {detail.error}
                  </div>
                )}
                <button
                  className="text-button"
                  onClick={() =>
                    navigate(`/agent?conversation=${detail.conversation_id}`)
                  }
                >
                  回到对话 <ArrowUpRight size={16} />
                </button>
                <h3 className="detail-section">交付物</h3>
                {detail.files?.length ? (
                  detail.files.map((file) => (
                    <button
                      className="artifact-item"
                      key={file.id}
                      onClick={() =>
                        void download(file).catch((error) =>
                          toast(error.message, true),
                        )
                      }
                    >
                      <Download size={16} />
                      {file.name}
                      <ArrowUpRight size={14} />
                    </button>
                  ))
                ) : (
                  <p className="muted small-text">此任务暂未产生文件交付物。</p>
                )}
                <h3 className="detail-section">过程记录</h3>
                <ol className="event-list">
                  {events
                    .filter(
                      (event) =>
                        event.kind !== "delta" && event.kind !== "usage",
                    )
                    .map((event) => (
                      <li key={event.seq}>
                        <span className="event-dot" />
                        <div>
                          <strong>
                            {{
                              queued: "任务已登记",
                              started: "开始执行",
                              skills: "选择技能",
                              "tool.started": "调用工具",
                              "tool.completed": "工具返回",
                              finished: "任务结束",
                              artifacts: "交付物已保存",
                              cancelling: "正在停止",
                              "assistant.progress": "Xinxin 的进度",
                              "budget.exhausted": "本轮预算已达到",
                              "context.restored": "已恢复前轮工具记录",
                            }[event.kind] || event.kind}
                          </strong>
                          {event.data.name && <code>{event.data.name}</code>}
                          {event.kind === "assistant.progress" && (
                            <p>{event.data.text}</p>
                          )}
                          {event.kind === "tool.completed" && (
                            <details>
                              <summary>查看返回结果</summary>
                              <pre>{event.data.result}</pre>
                            </details>
                          )}
                          <small>{date(event.created)}</small>
                        </div>
                      </li>
                    ))}
                </ol>
              </>
            ) : (
              <Loading />
            )}
          </TaskDetailShell>
        )}
      </div>
    </div>
  );
}
