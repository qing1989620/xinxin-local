import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowUpRight,
  ArrowRight,
  ArrowUp,
  Server,
  Files,
  Code2,
  Sparkles,
  Plus,
  Activity,
  CheckCircle2,
  MessageSquare,
  ShieldCheck,
  RefreshCw,
  Clock3,
  BookOpen,
  ChevronRight,
  PanelTop,
} from "lucide-react";
import { type FileItem, type Run } from "../api";
import {
  Empty,
  ErrorState,
  Loading,
  Status,
  date,
  size,
  useResource,
} from "../ui";

type Summary = {
  counts: Record<string, number>;
  tasks: Run[];
  recent_files: FileItem[];
  model_configured: boolean;
  model: string;
  skills: number;
  active_tasks: number;
  servers: number;
  automations: number;
  task_counts: Record<string, number>;
  daily_activity: { timestamp: number; total: number; completed: number }[];
};
const quickActions = [
  {
    icon: Server,
    title: "部署项目",
    description: "检查仓库、构建与健康状态",
    prompt:
      "帮我从 GitHub 部署一个网站，先检查仓库和目标服务器，给出可验证的步骤。",
  },
  {
    icon: Files,
    title: "整理资料",
    description: "检索、归纳与文件处理",
    prompt: "帮我整理私人资料，先查看可用文件，再提出归档方案。",
  },
  {
    icon: Code2,
    title: "编写代码",
    description: "从实现到测试与交付",
    prompt: "帮我完成一个编程任务，先明确目标，在工作区实现并验证。",
  },
];
export default function Dashboard({ name }: { name: string }) {
  const { data, error, reload } = useResource<Summary>("/dashboard"),
    navigate = useNavigate();
  const [draft, setDraft] = useState(""),
    [filter, setFilter] = useState("all"),
    [day, setDay] = useState(6),
    [node, setNode] = useState("agent");
  useEffect(() => {
    if (!data?.active_tasks) return;
    const timer = setInterval(reload, 5000);
    return () => clearInterval(timer);
  }, [data?.active_tasks]);
  if (error) return <ErrorState message={error} retry={reload} />;
  if (!data) return <Loading />;
  const hour = new Date().getHours(),
    greeting = hour < 11 ? "早上好" : hour < 18 ? "下午好" : "晚上好";
  const total = Object.values(data.task_counts || {}).reduce(
      (a, b) => a + b,
      0,
    ),
    completed = data.task_counts?.completed || 0;
  const recent = data.tasks.filter(
    (task) =>
      filter === "all" ||
      (filter === "active"
        ? ["queued", "running", "cancelling"].includes(task.status)
        : task.status === filter),
  );
  const nodes = [
    {
      id: "agent",
      label: "Agent",
      sub: data.model_configured ? "模型已配置" : "等待连接模型",
      icon: MessageSquare,
      to: "/agent",
      count: "中心",
    },
    {
      id: "skills",
      label: "技能",
      sub: "按目标选择合适的能力",
      icon: Sparkles,
      to: "/skills",
      count: String(data.skills),
    },
    {
      id: "files",
      label: "资料",
      sub: "私人文件与检索上下文",
      icon: Files,
      to: "/files",
      count: String(data.counts.files || 0),
    },
    {
      id: "servers",
      label: "服务器",
      sub: "由任务权限控制执行",
      icon: Server,
      to: "/servers",
      count: String(data.servers || 0),
    },
  ];
  const selected = nodes.find((item) => item.id === node)!;
  function start(event: FormEvent) {
    event.preventDefault();
    if (draft.trim()) navigate("/agent", { state: { prompt: draft } });
  }
  const activity =
    data.daily_activity ||
    Array.from({ length: 7 }, (_, i) => ({
      timestamp: Date.now() - (6 - i) * 86400000,
      total: 0,
      completed: 0,
    }));
  const max = Math.max(1, ...activity.map((item) => item.total));
  return (
    <div className="dashboard dashboard-v2 page-enter">
      <div className="desk-heading">
        <div>
          <p className="eyebrow">YOUR PERSONAL COMMAND CENTER</p>
          <h1>
            {greeting}，{name}
            <span className="heading-period">.</span>
          </h1>
          <p>把今天想做的事，交给一个有序的空间。</p>
        </div>
        <div className="desk-date">
          <span>
            {new Intl.DateTimeFormat("zh-CN", {
              month: "long",
              day: "numeric",
              weekday: "long",
            }).format(Date.now())}
          </span>
          <button
            className="icon-button"
            aria-label="刷新工作台"
            onClick={reload}
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>
      <div className="desk-hero-grid">
        <section className="mission-card">
          <div className="mission-top">
            <span className="agent-seal">
              <Sparkles size={23} strokeWidth={1.4} />
            </span>
            <span>
              <strong>从一个目标开始</strong>
              <small>你的私人执行助理</small>
            </span>
            <span className="subtle-badge">
              <ShieldCheck size={13} />
              权限由你掌握
            </span>
          </div>
          <form onSubmit={start}>
            <label className="mission-label" htmlFor="mission-input">
              今天，想完成什么？
            </label>
            <textarea
              id="mission-input"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="部署一个网站，处理一份资料，或把一个想法写成代码…"
              rows={3}
              maxLength={12000}
            />
            <div className="mission-footer">
              <span>
                <span
                  className={`connection-dot ${data.model_configured ? "ready" : ""}`}
                />
                {data.model_configured ? "DeepSeek Flash" : "等待配置模型"}
              </span>
              <button className="button primary" disabled={!draft.trim()}>
                交给 Agent <ArrowUp size={16} />
              </button>
            </div>
          </form>
          <div className="mission-presets">
            {quickActions.map((action) => (
              <button
                key={action.title}
                onClick={() => setDraft(action.prompt)}
              >
                <action.icon size={14} />
                {action.title}
                <Plus size={12} />
              </button>
            ))}
          </div>
        </section>
        <section className="resource-console">
          <header>
            <div>
              <span className="eyebrow">CONNECTED WORKSPACE</span>
              <h2>一个空间，协同工作。</h2>
            </div>
            <span className="console-mark">X / 01</span>
          </header>
          <div className="constellation">
            <svg viewBox="0 0 340 160" aria-hidden="true">
              <path d="M170 78 L57 40 M170 78 L282 40 M170 78 L170 140" />
              <circle cx="170" cy="78" r="48" className="orbit" />
            </svg>
            <button
              className={`node-agent ${node === "agent" ? "selected" : ""}`}
              onClick={() => setNode("agent")}
              aria-pressed={node === "agent"}
            >
              <span className="brand-mark">x</span>
              <span>Agent</span>
            </button>
            {nodes.slice(1).map((item, i) => (
              <button
                key={item.id}
                className={`resource-node node-${i} ${node === item.id ? "selected" : ""}`}
                aria-pressed={node === item.id}
                onClick={() => setNode(item.id)}
              >
                <item.icon size={17} />
                <strong>{item.label}</strong>
                <small>{item.count}</small>
              </button>
            ))}
          </div>
          <button
            className="console-selection"
            onClick={() => navigate(selected.to)}
          >
            <span>
              <strong>{selected.label}</strong>
              <small>{selected.sub}</small>
            </span>
            <ArrowUpRight size={18} />
          </button>
        </section>
      </div>
      <section className="desk-metrics" aria-label="空间概览">
        {[
          {
            title: "进行中的任务",
            value: data.active_tasks,
            caption: "查看行动过程",
            icon: Activity,
            to: "/tasks",
          },
          {
            title: "已完成的行动",
            value: completed,
            caption: `累计 ${total} 项任务`,
            icon: CheckCircle2,
            to: "/tasks",
          },
          {
            title: "私人资料",
            value: data.counts.files || 0,
            caption: "文件与交付物",
            icon: Files,
            to: "/files",
          },
          {
            title: "可用技能",
            value: data.skills,
            caption: "按目标发现与调用",
            icon: Sparkles,
            to: "/skills",
          },
        ].map((metric) => (
          <button
            key={metric.title}
            className="metric-card"
            onClick={() => navigate(metric.to)}
          >
            <span>
              <metric.icon size={16} />
              {metric.title}
              <ArrowUpRight size={14} />
            </span>
            <strong>{String(metric.value).padStart(2, "0")}</strong>
            <small>{metric.caption}</small>
          </button>
        ))}
      </section>
      <div className="desk-main-grid">
        <section className="desk-panel action-panel">
          <header className="desk-panel-header">
            <div>
              <span className="eyebrow">RECENT ACTIONS</span>
              <h2>最近的行动</h2>
            </div>
            <button className="text-button" onClick={() => navigate("/tasks")}>
              查看全部
              <ArrowUpRight size={15} />
            </button>
          </header>
          <div className="panel-tabs" aria-label="筛选最近任务">
            {[
              ["all", "全部"],
              ["active", "进行中"],
              ["completed", "已完成"],
              ["failed", "失败"],
            ].map(([value, label]) => (
              <button
                key={value}
                className={filter === value ? "active" : ""}
                aria-pressed={filter === value}
                onClick={() => setFilter(value)}
              >
                {label}
                {value === "all" && <small>{data.tasks.length}</small>}
              </button>
            ))}
          </div>
          {recent.length ? (
            <div className="desk-task-list">
              {recent.map((task) => (
                <button
                  key={task.id}
                  onClick={() => navigate(`/tasks?run=${task.id}`)}
                >
                  <span className={`task-state-icon ${task.status}`}>
                    <CheckCircle2 size={18} />
                  </span>
                  <span>
                    <strong>{task.task.split("\n")[0]}</strong>
                    <small>
                      {date(task.created)} ·{" "}
                      {
                        { read: "只读", workspace: "工作区", full: "完整权限" }[
                          task.permission
                        ]
                      }
                    </small>
                  </span>
                  <Status value={task.status} />
                  <ChevronRight size={15} />
                </button>
              ))}
            </div>
          ) : (
            <Empty
              title={
                filter === "all" ? "留一件事，给 Agent" : "这里暂时没有任务"
              }
              description="每个行动都有过程，每次交付都可回看。"
              action={
                <button
                  className="text-button"
                  onClick={() => navigate("/agent")}
                >
                  开始对话
                  <ArrowRight size={15} />
                </button>
              }
            />
          )}
        </section>
        <section className="desk-panel activity-panel">
          <header className="desk-panel-header">
            <div>
              <span className="eyebrow">THE LAST SEVEN DAYS</span>
              <h2>行动节奏</h2>
            </div>
            <Activity size={18} />
          </header>
          <div className="activity-summary">
            <strong>
              {activity.reduce((sum, item) => sum + item.total, 0)}
              <small>项任务</small>
            </strong>
            <span>最近 7 天</span>
          </div>
          <div className="activity-chart" aria-label="每天的实际任务量">
            {activity.map((item, i) => (
              <button
                key={item.timestamp}
                aria-pressed={day === i}
                className={day === i ? "selected" : ""}
                onClick={() => setDay(i)}
                title={`${item.total} 项任务，${item.completed} 项完成`}
              >
                <span className="bar-track">
                  <span style={{ height: `${(item.total / max) * 100}%` }} />
                </span>
                <small>
                  {new Intl.DateTimeFormat("zh-CN", {
                    weekday: "narrow",
                  }).format(item.timestamp)}
                </small>
              </button>
            ))}
          </div>
          <div className="activity-selected">
            <span>
              {new Intl.DateTimeFormat("zh-CN", {
                month: "short",
                day: "numeric",
              }).format(activity[day].timestamp)}
            </span>
            <strong>
              {activity[day].total} 项任务 · {activity[day].completed} 项完成
            </strong>
          </div>
          <button
            className="text-button"
            onClick={() => navigate("/schedules")}
          >
            <Clock3 size={15} />
            {data.automations
              ? `${data.automations} 项自动化已启用`
              : "安排一项定期行动"}
            <ArrowUpRight size={15} />
          </button>
        </section>
      </div>
      <div className="desk-bottom-grid">
        <section className="desk-panel">
          <header className="desk-panel-header">
            <div>
              <span className="eyebrow">KEEP CLOSE</span>
              <h2>放在手边的资料</h2>
            </div>
            <button className="text-button" onClick={() => navigate("/files")}>
              <Plus size={15} />
              添加资料
            </button>
          </header>
          {data.recent_files.length ? (
            <div className="desk-file-list">
              {data.recent_files.map((file) => (
                <button key={file.id} onClick={() => navigate("/files")}>
                  <span className="file-ext">
                    {file.name.split(".").pop()?.slice(0, 4)}
                  </span>
                  <span>
                    <strong>{file.name}</strong>
                    <small>
                      {size(file.size)} ·{" "}
                      {file.indexed ? "可检索正文" : "原文件已保存"}
                    </small>
                  </span>
                  <ArrowUpRight size={15} />
                </button>
              ))}
            </div>
          ) : (
            <Empty
              title="让资料成为下一次对话的上下文"
              description="上传文档、表格或图片，从文件本身出发。"
            />
          )}
        </section>
        <section className="personal-desk-card">
          <div className="personal-desk-art" aria-hidden="true">
            <span>留白</span>
            <i />
            <b>XINXIN / PRIVATE COLLECTION</b>
          </div>
          <div>
            <span className="eyebrow">THE PERSONAL SIDE</span>
            <h2>也留住，自己的片段。</h2>
            <p>文章、影像、诗词，还有走过的经历。</p>
            <div className="personal-links">
              {[
                ["article", "文章"],
                ["collection", "合集"],
                ["photo", "相册"],
                ["poem", "诗词"],
                ["resume", "简历"],
              ].map(([kind, label]) => (
                <button
                  key={kind}
                  onClick={() => navigate(`/content?kind=${kind}`)}
                >
                  {label}
                  <ArrowUpRight size={12} />
                </button>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
