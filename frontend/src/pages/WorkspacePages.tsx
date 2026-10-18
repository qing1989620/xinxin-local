import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import GalleryExplorer from "./GalleryExplorer";
import EmailSettings from "./EmailSettings";
import {
  ArrowUpRight,
  Bookmark,
  Check,
  ChevronRight,
  Clock3,
  Code2,
  ExternalLink,
  Image,
  LockKeyhole,
  Palette,
  Pencil,
  Pause,
  Play,
  Plus,
  Search,
  Server,
  Shield,
  Sparkles,
  Trash2,
  WandSparkles,
} from "lucide-react";
import {
  api,
  post,
  put,
  remove,
  upload,
  setSession,
  stableRequestKey,
  acknowledgeRequest,
  type FileItem,
  type Run,
  type ServerItem,
} from "../api";
import {
  Dialog,
  Empty,
  ErrorState,
  Loading,
  PageHeader,
  PrivateImage,
  date,
  useResource,
  useToast,
} from "../ui";

export function ServersPage() {
  const { data, error, reload } = useResource<ServerItem[]>("/servers"),
    [dialog, setDialog] = useState(false),
    [busy, setBusy] = useState(false),
    [editing, setEditing] = useState<string | null>(null),
    toast = useToast(),
    navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    host: "",
    port: 22,
    username: "root",
    workdir: "/srv/xinxin",
    host_key: "",
    private_key: "",
  });
  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      if (editing) await put(`/servers/${editing}`, form);
      else await post("/servers", form);
      setEditing(null);
      setDialog(false);
      setForm({
        name: "",
        host: "",
        port: 22,
        username: "root",
        workdir: "/srv/xinxin",
        host_key: "",
        private_key: "",
      });
      reload();
      toast("服务器已登记，连接将在任务执行时验证");
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      setBusy(false);
    }
  }
  if (error) return <ErrorState message={error} retry={reload} />;
  if (!data) return <Loading />;
  return (
    <div className="page-enter">
      <PageHeader
        overline="YOUR INFRASTRUCTURE"
        title="服务器"
        description="把云端机器登记到私人空间，让 Agent 在你授予的权限内工作。"
        action={
          <button className="button primary" onClick={() => setDialog(true)}>
            <Plus size={17} />
            添加服务器
          </button>
        }
      />
      <div className="context-note">
        <Shield size={18} />
        <p>
          权限在每次任务中单独选择。登记服务器不会自动执行命令，也不会开放公开访问。
        </p>
      </div>
      {data.length ? (
        <div className="resource-grid">
          {data.map((server) => (
            <article className="server-card" key={server.id}>
              <div className="card-top">
                <span className="resource-icon">
                  <Server size={24} strokeWidth={1.3} />
                </span>
                <span className="subtle-badge">待连接验证</span>
              </div>
              <h2>{server.name}</h2>
              <p className="mono">
                {server.username}@{server.host}:{server.port}
              </p>
              <div className="server-facts">
                <span>工作目录</span>
                <strong>{server.workdir}</strong>
                <span>SSH 凭据</span>
                <strong>{server.key_configured ? "已配置" : "未配置"}</strong>
                <span>主机公钥</span>
                <strong>{server.host_key ? "已登记" : "待登记"}</strong>
              </div>
              <div className="card-actions">
                <button
                  className="icon-button"
                  aria-label={`编辑服务器 ${server.name}`}
                  onClick={() => {
                    setEditing(server.id);
                    setForm({
                      name: server.name,
                      host: server.host,
                      port: server.port,
                      username: server.username,
                      workdir: server.workdir,
                      host_key: server.host_key,
                      private_key: "",
                    });
                    setDialog(true);
                  }}
                >
                  <Pencil size={16} />
                </button>
                <button
                  className="text-button"
                  onClick={() =>
                    navigate("/agent", {
                      state: {
                        serverId: server.id,
                        prompt: `先检查服务器「${server.name}」的运行情况，说明可用部署环境。未经核验不要宣布部署完成。`,
                      },
                    })
                  }
                >
                  交给 Agent <ArrowUpRight size={16} />
                </button>
                <button
                  className="icon-button"
                  aria-label={`删除服务器 ${server.name}`}
                  onClick={async () => {
                    if (
                      !confirm(`移除服务器「${server.name}」的登记和本地凭据？`)
                    )
                      return;
                    try {
                      await remove(`/servers/${server.id}`);
                      reload();
                    } catch (error) {
                      toast((error as Error).message, true);
                    }
                  }}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <Empty
          title="先登记一台属于你的服务器"
          description="主机地址和 SSH 凭据保存在后端，手机只负责发出任务。"
          action={
            <button
              className="button secondary"
              onClick={() => setDialog(true)}
            >
              添加第一台服务器 <ArrowUpRight size={16} />
            </button>
          }
        />
      )}
      <section className="editorial-note">
        <p className="eyebrow">FROM REPOSITORY TO REALITY</p>
        <h2>检查 → 构建 → 部署 → 验证</h2>
        <p>
          内置 Docker Compose 部署工具；其他项目可由 Agent 在完整权限下通过 SSH
          分步处理。真实结果会回到任务记录。
        </p>
      </section>
      {dialog && (
        <Dialog
          title={editing ? "编辑服务器" : "登记服务器"}
          onClose={() => {
            setDialog(false);
            setEditing(null);
            setForm({
              name: "",
              host: "",
              port: 22,
              username: "root",
              workdir: "/srv/xinxin",
              host_key: "",
              private_key: "",
            });
          }}
        >
          <form className="form-stack" onSubmit={save}>
            <label>
              名称
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="我的云服务器"
                required
              />
            </label>
            <div className="form-columns">
              <label>
                主机地址
                <input
                  value={form.host}
                  onChange={(e) => setForm({ ...form, host: e.target.value })}
                  placeholder="IP 或域名，不含协议"
                  required
                />
              </label>
              <label>
                SSH 端口
                <input
                  type="number"
                  min={1}
                  max={65535}
                  value={form.port}
                  onChange={(e) =>
                    setForm({ ...form, port: Number(e.target.value) })
                  }
                  required
                />
              </label>
            </div>
            <div className="form-columns">
              <label>
                用户名
                <input
                  value={form.username}
                  onChange={(e) =>
                    setForm({ ...form, username: e.target.value })
                  }
                  required
                />
              </label>
              <label>
                部署工作目录
                <input
                  value={form.workdir}
                  onChange={(e) =>
                    setForm({ ...form, workdir: e.target.value })
                  }
                  required
                />
              </label>
            </div>
            <details className="advanced-settings">
              <summary>
                SSH 连接凭据 <ChevronRight size={16} />
              </summary>
              <label>
                私钥
                <textarea
                  value={form.private_key}
                  onChange={(e) =>
                    setForm({ ...form, private_key: e.target.value })
                  }
                  rows={5}
                  autoComplete="off"
                  placeholder={
                    editing
                      ? "留空保留已保存的私钥"
                      : "-----BEGIN OPENSSH PRIVATE KEY-----"
                  }
                />
              </label>
              <label>
                已验证的主机公钥
                <textarea
                  value={form.host_key}
                  onChange={(e) =>
                    setForm({ ...form, host_key: e.target.value })
                  }
                  rows={3}
                  placeholder="known_hosts 格式；请核对服务器指纹"
                />
              </label>
              <p className="field-help">
                私钥加密保存在后端；连接始终验证主机公钥。可以先登记，补齐凭据后再发起执行任务。
              </p>
            </details>
            <div className="dialog-actions">
              <button
                type="button"
                className="button secondary"
                onClick={() => setDialog(false)}
              >
                取消
              </button>
              <button className="button primary" disabled={busy}>
                {busy ? "正在保存…" : "保存服务器"}
                <ArrowUpRight size={16} />
              </button>
            </div>
          </form>
        </Dialog>
      )}
    </div>
  );
}

type SkillItem = {
  id: string;
  name: string;
  description: string;
  domain: string;
  tools: string[];
  source: string;
  score?: number;
};
export { default as SkillsPage } from "./SkillsPage";

type MemoryItem = {
  id: string;
  content: string;
  category: string;
  created: number;
};
export function MemoriesPage() {
  const { data, error, reload } = useResource<MemoryItem[]>("/memories"),
    [dialog, setDialog] = useState(false),
    [content, setContent] = useState(""),
    [category, setCategory] = useState("preference"),
    [editing, setEditing] = useState<string | null>(null),
    toast = useToast();
  if (error) return <ErrorState message={error} retry={reload} />;
  if (!data) return <Loading />;
  return (
    <div className="page-enter">
      <PageHeader
        overline="A CONTINUING UNDERSTANDING"
        title="长期记忆"
        description="少一些重复解释，多一点长期理解。这里的每条记忆，都由你掌握。"
        action={
          <button
            className="button primary"
            onClick={() => {
              setEditing(null);
              setContent("");
              setCategory("preference");
              setDialog(true);
            }}
          >
            <Plus size={17} />
            添加记忆
          </button>
        }
      />
      {data.length ? (
        <div className="memory-grid">
          {data.map((memory) => (
            <article key={memory.id} className="memory-card">
              <div className="card-top">
                <span className="eyebrow">
                  {{
                    preference: "偏好",
                    fact: "事实",
                    project: "项目",
                    habit: "习惯",
                  }[memory.category] || memory.category}
                </span>
                <button
                  className="icon-button"
                  aria-label="删除这条记忆"
                  onClick={async () => {
                    try {
                      await remove(`/memories/${memory.id}`);
                      reload();
                    } catch (error) {
                      toast((error as Error).message, true);
                    }
                  }}
                >
                  <Trash2 size={16} />
                </button>
              </div>
              <p>{memory.content}</p>
              <small>{date(memory.created)}</small>
              <button
                className="text-button"
                onClick={() => {
                  setEditing(memory.id);
                  setContent(memory.content);
                  setCategory(memory.category);
                  setDialog(true);
                }}
              >
                <Pencil size={14} />
                编辑记忆
              </button>
            </article>
          ))}
        </div>
      ) : (
        <Empty
          title="慢慢认识，也由你决定记住什么"
          description="可以添加习惯、表达偏好和项目背景，或在有工作区权限的对话中明确让 Agent 记住。"
        />
      )}
      {dialog && (
        <Dialog
          title={editing ? "编辑记忆" : "留下一条记忆"}
          onClose={() => setDialog(false)}
        >
          <form
            className="form-stack"
            onSubmit={async (event) => {
              event.preventDefault();
              try {
                if (editing)
                  await put(`/memories/${editing}`, { content, category });
                else await post("/memories", { content, category });
                setContent("");
                setDialog(false);
                reload();
              } catch (error) {
                toast((error as Error).message, true);
              }
            }}
          >
            <label>
              类别
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                <option value="preference">偏好</option>
                <option value="fact">事实</option>
                <option value="project">项目</option>
                <option value="habit">习惯</option>
              </select>
            </label>
            <label>
              记住什么
              <textarea
                rows={5}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                required
                maxLength={1000}
                placeholder="例如：我偏好简洁的中文回复，重要结论附上证据。"
              />
            </label>
            <div className="dialog-actions">
              <button className="button primary">
                保存记忆 <Check size={16} />
              </button>
            </div>
          </form>
        </Dialog>
      )}
    </div>
  );
}

type ScheduleItem = {
  id: string;
  title: string;
  task: string;
  interval_minutes: number;
  next_at: number;
  enabled: boolean;
  permission: string;
  server_id: string | null;
};
export function SchedulesPage() {
  const { data, error, reload } = useResource<ScheduleItem[]>("/schedules"),
    [dialog, setDialog] = useState(false),
    [title, setTitle] = useState(""),
    [task, setTask] = useState(""),
    [minutes, setMinutes] = useState(1440),
    [permission, setPermission] = useState("read"),
    [serverId, setServerId] = useState(""),
    [editing, setEditing] = useState<ScheduleItem | null>(null),
    servers = useResource<ServerItem[]>("/servers"),
    toast = useToast();
  if (error) return <ErrorState message={error} retry={reload} />;
  if (!data) return <Loading />;
  return (
    <div className="page-enter">
      <PageHeader
        overline="STEADY, QUIET PROGRESS"
        title="自动化"
        description="以固定间隔创建 Agent 任务。后端运行时持续调度，记录每一次结果。"
        action={
          <button
            className="button primary"
            onClick={() => {
              setEditing(null);
              setTitle("");
              setTask("");
              setMinutes(1440);
              setPermission("read");
              setServerId("");
              setDialog(true);
            }}
          >
            <Plus size={17} />
            创建自动化
          </button>
        }
      />
      <div className="context-note">
        <Shield size={18} />
        <p>
          每项自动化单独保存权限和目标服务器，之后按这个范围运行。可以随时暂停、编辑或删除。
        </p>
      </div>
      {data.length ? (
        <div className="list-panel">
          {data.map((schedule) => (
            <article key={schedule.id} className="schedule-row">
              <span className="resource-icon">
                <Clock3 size={22} strokeWidth={1.3} />
              </span>
              <div>
                <h3>{schedule.title}</h3>
                <p>{schedule.task}</p>
                <small>
                  每 {schedule.interval_minutes} 分钟 · 下次{" "}
                  {date(schedule.next_at)} ·{" "}
                  {
                    { read: "只读", workspace: "工作区", full: "完整权限" }[
                      schedule.permission
                    ]
                  }
                </small>
              </div>
              <span className="subtle-badge">
                {schedule.enabled ? "已启用" : "已暂停"}
              </span>
              <button
                className="icon-button"
                aria-label={`${schedule.enabled ? "暂停" : "启用"}自动化 ${schedule.title}`}
                onClick={async () => {
                  try {
                    await put(`/schedules/${schedule.id}`, {
                      title: schedule.title,
                      task: schedule.task,
                      interval_minutes: schedule.interval_minutes,
                      permission: schedule.permission,
                      server_id: schedule.server_id,
                      enabled: !schedule.enabled,
                    });
                    reload();
                  } catch (error) {
                    toast((error as Error).message, true);
                  }
                }}
              >
                {schedule.enabled ? <Pause size={16} /> : <Play size={16} />}
              </button>
              <button
                className="icon-button"
                aria-label={`编辑自动化 ${schedule.title}`}
                onClick={() => {
                  setEditing(schedule);
                  setTitle(schedule.title);
                  setTask(schedule.task);
                  setMinutes(schedule.interval_minutes);
                  setPermission(schedule.permission);
                  setServerId(schedule.server_id || "");
                  setDialog(true);
                }}
              >
                <Pencil size={16} />
              </button>
              <button
                className="icon-button"
                aria-label={`删除自动化 ${schedule.title}`}
                onClick={async () => {
                  if (!confirm("删除这个自动化？已有任务会保留。")) return;
                  try {
                    await remove(`/schedules/${schedule.id}`);
                    reload();
                  } catch (error) {
                    toast((error as Error).message, true);
                  }
                }}
              >
                <Trash2 size={16} />
              </button>
            </article>
          ))}
        </div>
      ) : (
        <Empty
          title="重复的事情，可以交给时间"
          description="创建你的第一个定期任务。后端关闭期间不会运行，也不会自动补跑错过的任务。"
        />
      )}
      {dialog && (
        <Dialog
          title={editing ? "编辑定期行动" : "创建定期行动"}
          onClose={() => setDialog(false)}
        >
          <form
            className="form-stack"
            onSubmit={async (event) => {
              event.preventDefault();
              try {
                const payload = {
                  title,
                  task,
                  interval_minutes: minutes,
                  enabled: editing ? Boolean(editing.enabled) : true,
                  permission,
                  server_id: serverId || null,
                };
                if (editing) await put(`/schedules/${editing.id}`, payload);
                else await post("/schedules", payload);
                setDialog(false);
                setTitle("");
                setTask("");
                reload();
              } catch (error) {
                toast((error as Error).message, true);
              }
            }}
          >
            <label>
              名称
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                maxLength={100}
              />
            </label>
            <label>
              每隔多少分钟
              <input
                type="number"
                min={5}
                max={525600}
                value={minutes}
                onChange={(e) => setMinutes(Number(e.target.value))}
                required
              />
            </label>
            <label>
              让 Agent 做什么
              <textarea
                rows={5}
                value={task}
                onChange={(e) => setTask(e.target.value)}
                required
                maxLength={12000}
              />
            </label>
            <div className="form-columns">
              <label>
                执行权限
                <select
                  value={permission}
                  onChange={(e) => setPermission(e.target.value)}
                >
                  <option value="read">只读 · 阅读和分析</option>
                  <option value="workspace">工作区 · 创建文件和图表</option>
                  <option value="full">完整 · 后端主机和服务器命令</option>
                </select>
              </label>
              <label>
                目标服务器
                <select
                  value={serverId}
                  onChange={(e) => setServerId(e.target.value)}
                >
                  <option value="">不选择远程服务器</option>
                  {servers.data?.map((server) => (
                    <option key={server.id} value={server.id}>
                      {server.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="dialog-actions">
              <button className="button primary">
                {editing ? "保存自动化" : "创建自动化"}{" "}
                <ArrowUpRight size={16} />
              </button>
            </div>
          </form>
        </Dialog>
      )}
    </div>
  );
}

type SettingsData = {
  model: string;
  model_url: string;
  model_configured: boolean;
  image_url: string;
  image_model: string;
  image_configured: boolean;
  zine_installed: boolean;
};
export function SettingsPage({
  theme,
  onTheme,
}: {
  theme: string;
  onTheme: (value: string) => void;
}) {
  const { data, error, reload } = useResource<SettingsData>("/settings"),
    [model, setModel] = useState(""),
    [modelUrl, setModelUrl] = useState(""),
    [key, setKey] = useState(""),
    [imageUrl, setImageUrl] = useState(""),
    [imageModel, setImageModel] = useState(""),
    [imageKey, setImageKey] = useState(""),
    [busy, setBusy] = useState(false),
    [password, setPassword] = useState({ current: "", password: "" }),
    toast = useToast();
  useEffect(() => {
    if (data) {
      setModel(data.model);
      setModelUrl(data.model_url);
      setImageUrl(data.image_url);
      setImageModel(data.image_model);
    }
  }, [data]);
  if (error) return <ErrorState message={error} retry={reload} />;
  if (!data) return <Loading />;
  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      await put("/settings", {
        model,
        model_url: modelUrl,
        model_api_key: key,
        image_url: imageUrl,
        image_model: imageModel,
        image_api_key: imageKey,
      });
      setKey("");
      setImageKey("");
      reload();
      toast("模型设置已保存");
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="page-enter settings-page">
      <PageHeader
        overline="MAKE IT YOURS"
        title="让空间，贴近自己。"
        description="外观、模型与连接，按你的习惯安排。"
      />
      <section className="settings-section">
        <div className="settings-intro">
          <Palette size={22} strokeWidth={1.3} />
          <h2>空间的颜色</h2>
          <p>
            暖白与深灰保持不变。
            <br />
            每次选择一种，让强调恰到好处。
          </p>
        </div>
        <div className="theme-options">
          {[
            ["teal", "深青", "沉静与专注"],
            ["clay", "陶红", "温暖与感性"],
            ["indigo", "靛蓝", "清晰与克制"],
            ["ink", "墨灰", "纯粹与秩序"],
          ].map(([value, label, description]) => (
            <button
              key={value}
              className={`theme-option ${theme === value ? "selected" : ""}`}
              onClick={() => onTheme(value)}
              aria-pressed={theme === value}
            >
              <span className={`theme-colour ${value}`} />
              <strong>{label}</strong>
              <small>{description}</small>
              {theme === value && <Check size={16} />}
            </button>
          ))}
        </div>
      </section>
      <label className="custom-accent">
        自定义强调色
        <input
          type="color"
          value={theme.startsWith("#") ? theme : "#376c62"}
          onChange={(e) => onTheme(e.target.value)}
        />
        <code>{theme.startsWith("#") ? theme : "自由选择色彩"}</code>
        <span>自动保持文字可读性</span>
      </label>
      <EmailSettings />
      <form onSubmit={save}>
        <section className="settings-section">
          <div className="settings-intro">
            <Sparkles size={22} strokeWidth={1.3} />
            <h2>对话模型</h2>
            <p>
              默认使用 DeepSeek V4.1 Flash。
              <br />
              密钥只发送到自己的后端，保存后不回显。
            </p>
            <span className="subtle-badge">
              {data.model_configured ? "密钥已配置" : "等待配置"}
            </span>
          </div>
          <div className="form-stack settings-fields">
            <label>
              模型 ID
              <input
                value={model}
                onChange={(e) => setModel(e.target.value)}
                required
                placeholder="deepseek-flash"
              />
            </label>
            <label>
              完整 API 地址
              <input
                type="url"
                value={modelUrl}
                onChange={(e) => setModelUrl(e.target.value)}
                required
                placeholder="https://api.deepseek.com/chat/completions"
              />
            </label>
            <label>
              API 密钥
              <input
                type="password"
                autoComplete="new-password"
                value={key}
                onChange={(e) => setKey(e.target.value)}
                placeholder={
                  data.model_configured
                    ? "已配置，留空保留现有密钥"
                    : "输入你的 DeepSeek API 密钥"
                }
              />
            </label>
          </div>
        </section>
        <section className="settings-section">
          <div className="settings-intro">
            <Image size={22} strokeWidth={1.3} />
            <h2>图像生成</h2>
            <p>
              拾景工具使用单独的图像服务。
              <br />
              DeepSeek 负责对话与工具调度。
            </p>
            <span className="subtle-badge">
              {data.image_configured ? "图像密钥已配置" : "可选配置"}
            </span>
          </div>
          <div className="form-stack settings-fields">
            <label>
              图片编辑接口地址
              <input
                type="url"
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
                placeholder="兼容 images/edits，返回 b64_json"
              />
            </label>
            <label>
              图像模型 ID
              <input
                value={imageModel}
                onChange={(e) => setImageModel(e.target.value)}
              />
            </label>
            <label>
              图像服务密钥
              <input
                type="password"
                autoComplete="new-password"
                value={imageKey}
                onChange={(e) => setImageKey(e.target.value)}
                placeholder={
                  data.image_configured
                    ? "已配置，留空保留"
                    : "输入图像服务密钥"
                }
              />
            </label>
            <p className="field-help">
              只向你配置的图像服务发送所选参考图与转换指令。拾景技能用于个人非商业创作。
            </p>
          </div>
        </section>
        <div className="settings-save">
          <button className="button primary" disabled={busy}>
            {busy ? "正在保存…" : "保存模型设置"}
            <Check size={16} />
          </button>
        </div>
      </form>
      <section className="settings-section">
        <div className="settings-intro">
          <LockKeyhole size={22} strokeWidth={1.3} />
          <h2>主人账号</h2>
          <p>
            关闭公开注册。
            <br />
            修改密码会让其他会话立即失效。
          </p>
        </div>
        <form
          className="form-stack settings-fields"
          onSubmit={async (event) => {
            event.preventDefault();
            try {
              const result = await put("/auth/password", password);
              await setSession(result.token);
              setPassword({ current: "", password: "" });
              toast("密码已更新，其他会话已退出");
            } catch (error) {
              toast((error as Error).message, true);
            }
          }}
        >
          <label>
            原密码
            <input
              type="password"
              autoComplete="current-password"
              value={password.current}
              onChange={(e) =>
                setPassword({ ...password, current: e.target.value })
              }
              required
            />
          </label>
          <label>
            新密码
            <input
              type="password"
              autoComplete="new-password"
              minLength={10}
              value={password.password}
              onChange={(e) =>
                setPassword({ ...password, password: e.target.value })
              }
              required
            />
          </label>
          <button className="button secondary">
            修改密码 <ArrowUpRight size={16} />
          </button>
        </form>
      </section>
    </div>
  );
}

export function ToolsPage() {
  const [tool, setTool] = useState<"plot" | "image" | null>(null),
    files = useResource<FileItem[]>("/files"),
    settings = useResource<SettingsData>("/settings"),
    [fileId, setFileId] = useState(""),
    [columns, setColumns] = useState<string[]>([]),
    [x, setX] = useState(""),
    [y, setY] = useState(""),
    [kind, setKind] = useState("line"),
    [title, setTitle] = useState("数据观察"),
    [palette, setPalette] = useState("teal"),
    [style, setStyle] = useState("collage"),
    [instruction, setInstruction] = useState(""),
    [busy, setBusy] = useState(false),
    toast = useToast(),
    navigate = useNavigate();
  useEffect(() => {
    let alive = true;
    setColumns([]);
    if (fileId && tool === "plot")
      api<{ columns: string[] }>(`/files/${fileId}/columns`)
        .then((value) => {
          if (!alive) return;
          setColumns(value.columns);
          setX(value.columns[0] || "");
          setY(value.columns[1] || value.columns[0] || "");
        })
        .catch((error) => toast(error.message, true));
    return () => {
      alive = false;
    };
  }, [fileId, tool]);
  async function create(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      const payload =
        tool === "plot"
          ? { file_id: fileId, x, y, kind, title, palette }
          : { file_id: fileId, style, instruction };
      const namespace = tool || "image";
      const run = await post<Run>(`/tools/${namespace}`, {
        ...payload,
        request_key: await stableRequestKey(namespace, payload),
      });
      acknowledgeRequest(namespace);
      setTool(null);
      navigate(`/tasks?run=${run.id}`);
      toast("任务已开始，可以在任务页查看产物");
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="page-enter">
      <PageHeader
        overline="SMALL TOOLS, GOOD WORK"
        title="创作工具"
        description="实用的小工具，也可以成为 Agent 完成任务的一部分。"
      />
      <div className="tool-grid">
        <button
          className="tool-card plot-tool"
          onClick={() => {
            setTool("plot");
            setFileId("");
          }}
        >
          <div className="tool-visual chart-visual" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
          </div>
          <div className="tool-card-body">
            <span className="eyebrow">01 / DATA & FIGURE</span>
            <h2>把数据，画得好看。</h2>
            <p>
              私人 CSV → 清晰图表。
              <br />
              交付 PNG、PDF 与可复现的脚本。
            </p>
            <span className="text-button">
              开始绘图 <ArrowUpRight size={17} />
            </span>
          </div>
        </button>
        <button
          className="tool-card zine-tool"
          onClick={() => {
            setTool("image");
            setFileId("");
          }}
        >
          <div className="tool-visual paper-visual" aria-hidden="true">
            <div className="paper-photo" />
            <div className="paper-shape" />
            <span>
              GATHERED
              <br />
              SCENES.
            </span>
          </div>
          <div className="tool-card-body">
            <span className="eyebrow">02 / IMAGE & EXPRESSION</span>
            <h2>拾景，让影像呼吸。</h2>
            <p>
              保留真实的实景拼贴，
              <br />
              或重新构成一幅影像蒸馏作品。
            </p>
            <span className="text-button">
              转换一张照片 <ArrowUpRight size={17} />
            </span>
          </div>
        </button>
      </div>
      <GalleryExplorer />
      {tool && (
        <Dialog
          title={tool === "plot" ? "创建一张数据图" : "拾景 · 图片风格转换"}
          onClose={() => setTool(null)}
        >
          <form className="form-stack" onSubmit={create}>
            <label>
              {tool === "plot" ? "选择 CSV" : "选择一张私人照片"}
              <select
                value={fileId}
                onChange={(e) => setFileId(e.target.value)}
                required
              >
                <option value="">从私人资料中选择</option>
                {files.data
                  ?.filter((file) =>
                    tool === "plot"
                      ? file.name.toLowerCase().endsWith(".csv")
                      : file.mime.startsWith("image/"),
                  )
                  .map((file) => (
                    <option key={file.id} value={file.id}>
                      {file.name}
                    </option>
                  ))}
              </select>
            </label>
            <label className="upload-inline">
              或上传新文件
              <input
                type="file"
                accept={
                  tool === "plot" ? ".csv" : "image/png,image/jpeg,image/webp"
                }
                onChange={async (event) => {
                  const file = event.target.files?.[0];
                  if (file) {
                    try {
                      const saved = await upload(file);
                      files.reload();
                      setFileId(saved.id);
                    } catch (error) {
                      toast((error as Error).message, true);
                    }
                  }
                }}
              />
            </label>
            {tool === "plot" ? (
              <>
                <label>
                  标题
                  <input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    required
                    maxLength={100}
                  />
                </label>
                <div className="form-columns">
                  <label>
                    X 列
                    <select
                      value={x}
                      onChange={(e) => setX(e.target.value)}
                      required
                    >
                      {columns.map((column) => (
                        <option key={column}>{column}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Y 列
                    <select
                      value={y}
                      onChange={(e) => setY(e.target.value)}
                      required
                    >
                      {columns.map((column) => (
                        <option key={column}>{column}</option>
                      ))}
                    </select>
                  </label>
                </div>
                <div className="form-columns">
                  <label>
                    画法
                    <select
                      value={kind}
                      onChange={(e) => setKind(e.target.value)}
                    >
                      <option value="line">折线 · 趋势</option>
                      <option value="bar">柱状 · 对比</option>
                      <option value="scatter">散点 · 关系</option>
                      <option value="hist">直方 · 分布</option>
                    </select>
                  </label>
                  <label>
                    配色
                    <select
                      value={palette}
                      onChange={(e) => setPalette(e.target.value)}
                    >
                      <option value="teal">深青</option>
                      <option value="clay">陶红</option>
                      <option value="indigo">靛蓝</option>
                      <option value="ink">墨灰</option>
                    </select>
                  </label>
                </div>
              </>
            ) : (
              <>
                <div className="style-choice">
                  {[
                    ["collage", "实景拼贴", "保留照片中的真实关系"],
                    ["distillation", "影像蒸馏", "提炼情绪，构成独立作品"],
                  ].map(([value, label, description]) => (
                    <button
                      type="button"
                      key={value}
                      className={style === value ? "selected" : ""}
                      onClick={() => setStyle(value)}
                      aria-pressed={style === value}
                    >
                      <strong>{label}</strong>
                      <small>{description}</small>
                    </button>
                  ))}
                </div>
                <label>
                  你想保留的感觉
                  <textarea
                    rows={4}
                    value={instruction}
                    onChange={(e) => setInstruction(e.target.value)}
                    placeholder="可以写情绪、色彩、文字语言，或最想保留的关系。"
                    maxLength={3000}
                  />
                </label>
                <p className="field-help">
                  所选照片和转换指令会发送给你在设置中配置的图像服务。原图留在私人资料中，由你随时删除。
                </p>
                {!settings.data?.image_configured && (
                  <div className="form-error">
                    图像服务还未配置。
                    <button
                      type="button"
                      className="text-button"
                      onClick={() => navigate("/settings")}
                    >
                      前往设置 <ArrowUpRight size={14} />
                    </button>
                  </div>
                )}
              </>
            )}
            <div className="dialog-actions">
              <button
                type="button"
                className="button secondary"
                onClick={() => setTool(null)}
              >
                取消
              </button>
              <button
                className="button primary"
                disabled={
                  busy ||
                  !fileId ||
                  (tool === "image" && !settings.data?.image_configured)
                }
              >
                {busy
                  ? "正在创建任务…"
                  : tool === "plot"
                    ? "生成图表"
                    : "开始转换"}
                <WandSparkles size={16} />
              </button>
            </div>
          </form>
        </Dialog>
      )}
    </div>
  );
}
