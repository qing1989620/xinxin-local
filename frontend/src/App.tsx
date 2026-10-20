import {
  lazy,
  Suspense,
  useEffect,
  useState,
  useRef,
  type FormEvent,
} from "react";
import {
  NavLink,
  Route,
  Routes,
  useNavigate,
  useLocation,
} from "react-router-dom";
import {
  LayoutDashboard,
  MessageSquare,
  ListTodo,
  FolderOpen,
  Server,
  Sparkles,
  BookOpen,
  WandSparkles,
  Bookmark,
  Clock3,
  Settings as SettingsIcon,
  Search,
  Plus,
  LogOut,
  Menu,
  X,
  ArrowUpRight,
  LockKeyhole,
  ChevronRight,
  Download,
  ShieldCheck,
  PanelLeftClose,
  PanelLeftOpen,
  SpellCheck,
  Music2,
} from "lucide-react";
import { registerSW } from "virtual:pwa-register";
import { Capacitor } from "@capacitor/core";

// 电脑软件端（desktop/Xinxin-Desktop.ps1）以 ?desktop=1 打开应用窗口：
// 窗口本身就是"安装好的软件"，不再展示安装提示与离线就绪提示。
// 标记写进 sessionStorage：同标签页内的整页跳转（重定向、刷新）不丢，
// 而新开标签页（网页端）不会继承。网页与手机端永远不带这个标记，行为不变。
function detectDesktopApp(): boolean {
  if (typeof window === "undefined") return false;
  try {
    if (new URLSearchParams(window.location.search).has("desktop")) {
      sessionStorage.setItem("xinxin-desktop", "1");
      return true;
    }
    return sessionStorage.getItem("xinxin-desktop") === "1";
  } catch {
    return false;
  }
}
const desktopApp = detectDesktopApp();
import {
  api,
  post,
  setSession,
  restoreSession,
  hasSession,
  setServer,
  getServer,
} from "./api";
import { Dialog, Loading, useToast } from "./ui";
import Dashboard from "./pages/Dashboard";
import AgentPage from "./pages/AgentPage";
import { configureConversationLocation } from "./conversationLocation";
import TasksPage from "./pages/TasksPage";
import FilesPage from "./pages/FilesPage";
import MusicPage from "./pages/MusicPage";
import { MiniPlayer, useMusicPlayer } from "./musicPlayer";
import ErrorBoundary from "./ErrorBoundary";
import {
  ServersPage,
  SkillsPage,
  MemoriesPage,
  SchedulesPage,
  SettingsPage,
  ToolsPage,
} from "./pages/WorkspacePages";

const ContentPage = lazy(() => import("./pages/ContentPage"));
const navigation = [
  { to: "/", label: "工作台", icon: LayoutDashboard, end: true },
  { to: "/agent", label: "Agent", icon: MessageSquare },
  { to: "/tasks", label: "任务", icon: ListTodo },
  { to: "/files", label: "私人资料", icon: FolderOpen },
  { to: "/servers", label: "服务器", icon: Server },
  { to: "/skills", label: "技能", icon: Sparkles },
  { to: "/content", label: "个人内容", icon: BookOpen },
  { to: "/tools", label: "工具", icon: WandSparkles },
  { to: "/music", label: "音乐", icon: Music2 },
  { to: "/memories", label: "记忆", icon: Bookmark },
  { to: "/schedules", label: "自动化", icon: Clock3 },
];

function AuthScreen({
  configured,
  onReady,
}: {
  configured: boolean;
  onReady: () => void;
}) {
  const toast = useToast();
  const [name, setName] = useState(""),
    [password, setPassword] = useState(""),
    [code, setCode] = useState(""),
    [server, setServerValue] = useState(getServer()),
    [busy, setBusy] = useState(false),
    [connection, setConnection] = useState(false),
    [method, setMethod] = useState("password"),
    [email, setEmail] = useState(""),
    [emailCode, setEmailCode] = useState(""),
    [cooldown, setCooldown] = useState(0),
    [sending, setSending] = useState(false),
    [notice, setNotice] = useState(""),
    [error, setError] = useState("");
  useEffect(() => {
    if (!cooldown) return;
    const timer = setInterval(
      () => setCooldown((value) => Math.max(0, value - 1)),
      1000,
    );
    return () => clearInterval(timer);
  }, [cooldown > 0]);
  async function sendCode() {
    setSending(true);
    setError("");
    setNotice("");
    try {
      const result = await post("/auth/email/code", {
        email,
        scene: method === "reset" ? "reset" : "login",
      });
      setCooldown(result.retry_after);
      setNotice(result.message);
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setSending(false);
    }
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const result = await post(
        !configured
          ? "/auth/setup"
          : method === "password"
            ? "/auth/login"
            : method === "reset"
              ? "/auth/email/reset"
              : "/auth/email/login",
        !configured
          ? { name, password, setup_code: code }
          : method === "password"
            ? { name, password }
            : method === "reset"
              ? { email, code: emailCode, password }
              : { email, code: emailCode },
      );
      await setSession(result.token);
      onReady();
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="auth-page">
      <div className="auth-editorial">
        <a className="wordmark" href="/" aria-label="Xinxin本地版 首页">
          <span className="brand-mark">x</span>Xinxin本地版
          <span className="wordmark-dot">.</span>
        </a>
        <div className="auth-story">
          <p className="eyebrow">A SPACE OF YOUR OWN</p>
          <h1>
            想法有了。
            <br />
            让它发生。
          </h1>
          <p>
            你的资料、项目与行动，
            <br />
            在一个安静的私人空间里，慢慢成形。
          </p>
          <div className="auth-seal">
            <ShieldCheck size={18} />
            <span>只属于主人 · 无公开注册</span>
          </div>
        </div>
        <footer>PERSONAL INTELLIGENCE, WITH INTENTION.</footer>
      </div>
      <section className="auth-panel">
        <div className="auth-form-wrap">
          <p className="eyebrow">WELCOME TO XINXIN</p>
          <h2>{configured ? "回到你的空间" : "建立你的私人空间"}</h2>
          <p className="muted">
            {configured
              ? "登录后继续与你的 Agent 一起工作。"
              : "只需创建一次主人账号。初始化码在后端 data/bootstrap.code 文件中。"}
          </p>
          {configured && (
            <div className="auth-methods" aria-label="登录方式">
              {[
                ["password", "账号密码"],
                ["code", "邮箱验证码"],
                ["reset", "找回密码"],
              ].map(([value, label]) => (
                <button
                  type="button"
                  key={value}
                  className={method === value ? "active" : ""}
                  aria-pressed={method === value}
                  disabled={busy || sending}
                  onClick={() => {
                    setMethod(value);
                    setError("");
                    setNotice("");
                    setEmailCode("");
                    setPassword("");
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
          )}
          <form onSubmit={submit} className="form-stack">
            {(method === "password" || !configured) && (
              <label>
                主人账号
                <input
                  autoComplete="username"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  maxLength={80}
                />
              </label>
            )}
            {configured && method !== "password" && (
              <>
                <label>
                  主人邮箱
                  <input
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    maxLength={254}
                    placeholder="输入你绑定的邮箱"
                  />
                </label>
                <label>
                  6 位验证码
                  <div className="email-code-row">
                    <input
                      type="text"
                      inputMode="numeric"
                      autoComplete="one-time-code"
                      pattern="[0-9]{6}"
                      maxLength={6}
                      value={emailCode}
                      onChange={(e) =>
                        setEmailCode(e.target.value.replace(/\D/g, ""))
                      }
                      required
                      placeholder="000000"
                    />
                    <button
                      type="button"
                      className="button secondary"
                      disabled={
                        busy || sending || cooldown > 0 || !email.includes("@")
                      }
                      onClick={() => void sendCode()}
                    >
                      {sending
                        ? "发送中…"
                        : cooldown > 0
                          ? `${cooldown} 秒后重发`
                          : "发送验证码"}
                    </button>
                  </div>
                </label>
              </>
            )}
            {(method === "password" || method === "reset" || !configured) && (
              <label>
                {method === "reset" ? "新密码" : "密码"}
                <input
                  type="password"
                  autoComplete={
                    configured && method === "password"
                      ? "current-password"
                      : "new-password"
                  }
                  minLength={configured && method === "password" ? 1 : 10}
                  maxLength={256}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder={
                    configured && method === "password"
                      ? "输入你的密码"
                      : "至少 10 个字符"
                  }
                />
              </label>
            )}
            {!configured && (
              <label>
                初始化码
                <input
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  autoComplete="off"
                  required
                  placeholder="从后端本地文件读取"
                />
              </label>
            )}
            {notice && (
              <p className="form-notice" role="status">
                {notice}
              </p>
            )}
            {error && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}
            <button className="button primary full-width" disabled={busy}>
              {busy
                ? "正在进入…"
                : configured
                  ? method === "reset"
                    ? "重置密码并进入"
                    : "进入工作空间"
                  : "创建主人账号"}
              <ArrowUpRight size={17} />
            </button>
          </form>
          <button
            className="text-button connection-toggle"
            onClick={() => setConnection(!connection)}
          >
            连接自己的后端 <ChevronRight size={14} />
          </button>
          {connection && (
            <div className="connection-form">
              <label>
                后端地址
                <input
                  value={server}
                  onChange={(e) => setServerValue(e.target.value)}
                  placeholder="留空使用当前地址；手机填写 https://…"
                />
              </label>
              <button
                className="button secondary small"
                onClick={async () => {
                  try {
                    await setSession("");
                    setServer(server);
                    window.location.reload();
                  } catch (error) {
                    toast((error as Error).message, true);
                  }
                }}
              >
                保存并重新连接
              </button>
            </div>
          )}
          <p className="auth-footnote">
            <LockKeyhole size={12} />
            模型和服务器密钥只保存在后端。
          </p>
        </div>
      </section>
    </main>
  );
}

export default function App() {
  const player = useMusicPlayer();
  const [state, setState] = useState<"loading" | "auth" | "ready" | "offline">(
      "loading",
    ),
    [configured, setConfigured] = useState(true),
    [name, setName] = useState("主人"),
    [drawer, setDrawer] = useState(false),
    [compact, setCompact] = useState(
      localStorage.getItem("xinxin-sidebar") === "compact",
    ),
    [search, setSearch] = useState(false),
    [searchText, setSearchText] = useState(""),
    [theme, setTheme] = useState(
      localStorage.getItem("xinxin-accent") || "teal",
    ),
    [background, setBackground] = useState(
      localStorage.getItem("xinxin-bg") || "paper",
    ),
    [install, setInstall] = useState<any>(null),
    [updateAvailable, setUpdateAvailable] = useState(false);
  const applyUpdate = useRef<((reloadPage?: boolean) => Promise<void>) | null>(
    null,
  );
  const navigate = useNavigate(),
    location = useLocation(),
    toast = useToast();
  async function boot() {
    setState("loading");
    let gotStatus = false;
    try {
      await restoreSession();
      const status = await api<{ configured: boolean }>("/auth/status");
      setConfigured(status.configured);
      gotStatus = true;
      if (hasSession()) {
        const me = await api<{ name: string }>("/auth/me");
        await configureConversationLocation(
          getServer() || window.location.origin,
          me.name,
        );
        setName(me.name);
        setState("ready");
      } else setState("auth");
    } catch {
      setState(gotStatus && !hasSession() ? "auth" : "offline");
    }
  }
  useEffect(() => {
    void boot();
    const unauthorized = () => setState("auth");
    window.addEventListener("xinxin-unauthorized", unauthorized);
    return () =>
      window.removeEventListener("xinxin-unauthorized", unauthorized);
  }, []);
  useEffect(() => {
    if (!drawer) return;
    const previous = document.activeElement as HTMLElement | null;
    const sidebar = document.querySelector<HTMLElement>(".sidebar");
    const focusable = () =>
      Array.from(
        sidebar?.querySelectorAll<HTMLElement>(
          "a[href],button:not([disabled])",
        ) || [],
      ).filter((el) => el.getClientRects().length > 0);
    focusable()[0]?.focus();
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setDrawer(false);
      }
      if (event.key === "Tab") {
        const items = focusable(),
          first = items[0],
          last = items[items.length - 1];
        if (
          event.shiftKey &&
          (document.activeElement === first ||
            !sidebar?.contains(document.activeElement))
        ) {
          event.preventDefault();
          last?.focus();
        } else if (
          !event.shiftKey &&
          (document.activeElement === last ||
            !sidebar?.contains(document.activeElement))
        ) {
          event.preventDefault();
          first?.focus();
        }
      }
    };
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", keydown);
    return () => {
      window.removeEventListener("keydown", keydown);
      document.body.style.overflow = overflow;
      previous?.focus();
    };
  }, [drawer]);
  useEffect(() => {
    const wide = matchMedia("(min-width: 761px)");
    const resize = () => {
      if (wide.matches) setDrawer(false);
    };
    wide.addEventListener("change", resize);
    return () => wide.removeEventListener("change", resize);
  }, []);
  useEffect(() => {
    const root = document.documentElement;
    const custom = /^#[a-f\d]{6}$/i.test(theme);
    root.dataset.accent = custom ? "custom" : theme;
    if (custom) {
      let rgb = [1, 3, 5].map((i) => parseInt(theme.slice(i, i + 2), 16));
      const luminance = () =>
        rgb
          .map((v) => v / 255)
          .map((v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4))
          .reduce((sum, v, i) => sum + v * [0.2126, 0.7152, 0.0722][i], 0);
      while (luminance() > 0.17) rgb = rgb.map((v) => Math.round(v * 0.92));
      root.style.setProperty("--accent", `rgb(${rgb.join(",")})`);
      root.style.setProperty(
        "--accent-soft",
        `rgb(${rgb.map((v) => Math.round(v * 0.09 + 247 * 0.91)).join(",")})`,
      );
    } else {
      root.style.removeProperty("--accent");
      root.style.removeProperty("--accent-soft");
    }
    localStorage.setItem("xinxin-accent", theme);
  }, [theme]);
  useEffect(() => {
    document.documentElement.dataset.bg = background;
    localStorage.setItem("xinxin-bg", background);
  }, [background]);
  useEffect(() => {
    localStorage.setItem("xinxin-sidebar", compact ? "compact" : "expanded");
  }, [compact]);
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key === "k") {
        event.preventDefault();
        setSearch(true);
      }
    };
    const installHandler = (event: Event) => {
      if (desktopApp) return; // 电脑端不需要"安装到手机"
      event.preventDefault();
      setInstall(event);
    };
    window.addEventListener("keydown", handler);
    window.addEventListener("beforeinstallprompt", installHandler);
    const updateSW = !Capacitor.isNativePlatform()
      ? registerSW({
          onNeedRefresh() {
            setUpdateAvailable(true);
            toast("新版本已准备好，保存当前编辑后可在顶栏更新应用。");
          },
          onOfflineReady() {
            if (!desktopApp) toast("Xinxin 已可安装，离线时可以打开界面。");
          },
        })
      : null;
    applyUpdate.current = updateSW;
    if (Capacitor.isNativePlatform() && "serviceWorker" in navigator) {
      void navigator.serviceWorker
        .getRegistrations()
        .then((registrations) =>
          Promise.all(
            registrations.map((registration) => registration.unregister()),
          ),
        )
        .catch(() => {});
    }
    const viewport = window.visualViewport;
    const keyboard = () =>
      document.body.classList.toggle(
        "keyboard-open",
        Boolean(viewport && window.innerHeight - viewport.height > 180),
      );
    viewport?.addEventListener("resize", keyboard);
    return () => {
      window.removeEventListener("keydown", handler);
      window.removeEventListener("beforeinstallprompt", installHandler);
      viewport?.removeEventListener("resize", keyboard);
      applyUpdate.current = null;
    };
  }, []);
  if (state === "loading")
    return (
      <div className="boot">
        <span className="brand-mark">x</span>
        <Loading />
      </div>
    );
  if (state === "offline")
    return (
      <main className="boot">
        <span className="brand-mark">x</span>
        <h1>还没连接到你的空间</h1>
        <p className="muted">启动本地后端，或填写你自己的服务器地址。</p>
        <label className="server-input">
          后端地址
          <input
            defaultValue={getServer()}
            placeholder="https://your-server"
            id="offline-server"
          />
        </label>
        <button
          className="button primary"
          onClick={() => {
            try {
              setServer(
                (document.getElementById("offline-server") as HTMLInputElement)
                  .value,
              );
              void boot();
            } catch (error) {
              toast((error as Error).message, true);
            }
          }}
        >
          重新连接 <ArrowUpRight size={16} />
        </button>
      </main>
    );
  if (state === "auth")
    return <AuthScreen configured={configured} onReady={() => void boot()} />;
  return (
    <div className={`app-shell ${compact ? "sidebar-compact" : ""}`}>
      <a className="skip-link" href="#main">
        跳到主要内容
      </a>
      {drawer && (
        <button
          className="sidebar-backdrop"
          onClick={() => setDrawer(false)}
          aria-label="关闭导航"
        />
      )}
      <aside
        className={`sidebar ${drawer ? "open" : ""}`}
        role={drawer ? "dialog" : undefined}
        aria-modal={drawer || undefined}
        aria-label="功能导航"
      >
        <div className="sidebar-brand">
          <a
            className="wordmark"
            href="/"
            onClick={(e) => {
              e.preventDefault();
              navigate("/");
              setDrawer(false);
            }}
          >
            <span className="brand-mark">x</span>Xinxin本地版
            <span className="wordmark-dot">.</span>
          </a>
          <button
            className="icon-button desktop-only sidebar-collapse"
            onClick={() => setCompact(!compact)}
            aria-label={compact ? "展开侧栏" : "收起侧栏"}
            aria-expanded={!compact}
          >
            {compact ? (
              <PanelLeftOpen size={17} />
            ) : (
              <PanelLeftClose size={17} />
            )}
          </button>
          <button
            className="icon-button mobile-only"
            onClick={() => setDrawer(false)}
            aria-label="关闭导航"
          >
            <X size={20} />
          </button>
        </div>
        <p className="sidebar-caption">私人工作空间</p>
        <button
          className="new-task"
          onClick={() => {
            navigate("/agent?new=1");
            setDrawer(false);
          }}
        >
          <Plus size={17} />
          开始一件事<span>↗</span>
        </button>
        <nav aria-label="主导航">
          {navigation.map((item, index) => (
            <div key={item.to}>
              {index === 3 && <p className="nav-section">我的资源</p>}
              {index === 9 && <p className="nav-section">长期协作</p>}
              <NavLink
                to={item.to}
                aria-label={item.label}
                title={item.label}
                end={item.end}
                onClick={() => setDrawer(false)}
                className={({ isActive }) =>
                  `nav-link ${isActive ? "active" : ""}`
                }
              >
                <item.icon size={18} strokeWidth={1.6} />
                <span>{item.label}</span>
                {item.to === "/agent" && <span className="nav-badge">AI</span>}
              </NavLink>
            </div>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="accent-selector" aria-label="强调色选择">
            {["teal", "clay", "indigo", "ink"].map((color) => (
              <button
                key={color}
                className={`accent-swatch ${color} ${theme === color ? "selected" : ""}`}
                onClick={() => setTheme(color)}
                aria-label={`切换${{ teal: "深青", clay: "陶红", indigo: "靛蓝", ink: "墨灰" }[color]}强调色`}
                aria-pressed={theme === color}
              />
            ))}
          </div>
          <NavLink
            to="/settings"
            className="nav-link"
            onClick={() => setDrawer(false)}
          >
            <SettingsIcon size={18} strokeWidth={1.6} />
            <span>设置</span>
          </NavLink>
          <div className="owner-chip">
            <span className="owner-avatar">{name.slice(0, 1)}</span>
            <div>
              <strong>{name}</strong>
              <small>OWNER · 私人空间</small>
            </div>
            <button
              className="icon-button"
              title="退出登录"
              aria-label="退出登录"
              onClick={async () => {
                player?.stop();
                try {
                  await post("/auth/logout", {});
                } finally {
                  await setSession("");
                  setState("auth");
                }
              }}
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>
      <div className="workspace" inert={drawer || undefined}>
        <header className="topbar">
          <button
            className="icon-button mobile-only"
            onClick={() => setDrawer(true)}
            aria-label="展开导航"
          >
            <Menu size={20} />
          </button>
          <span className="workspace-label">
            <span />
            Xinxin本地版 /{" "}
            <span>
              {navigation.find(
                (item) =>
                  item.to !== "/" && location.pathname.startsWith(item.to),
              )?.label ||
                (location.pathname.startsWith("/settings") ? "设置" : "工作台")}
            </span>
          </span>
          <div className="topbar-actions">
            {updateAvailable && (
              <button
                className="text-button"
                aria-label="更新应用"
                title="保存当前编辑后更新；后台任务会保留"
                onClick={() =>
                  void applyUpdate
                    .current?.(true)
                    .catch(() => toast("更新暂未完成，请稍后重试", true))
                }
              >
                <Download size={15} />
                <span>更新应用</span>
              </button>
            )}
            {install && (
              <button
                className="text-button"
                onClick={async () => {
                  await install.prompt();
                  setInstall(null);
                }}
              >
                <Download size={15} />
                <span>安装到手机</span>
              </button>
            )}
            <button
              className="search-trigger"
              onClick={() => setSearch(true)}
              aria-label="搜索页面"
            >
              <Search size={16} />
              <span>搜索页面</span>
              <kbd>Ctrl K</kbd>
            </button>
          </div>
        </header>
        <main id="main" className="main">
          <ErrorBoundary resetKey={location.pathname}>
            <Suspense fallback={<Loading />}>
              <Routes>
                <Route path="/" element={<Dashboard name={name} />} />
                <Route path="/agent" element={<AgentPage />} />
                <Route path="/tasks" element={<TasksPage />} />
                <Route path="/files" element={<FilesPage />} />
                <Route path="/servers" element={<ServersPage />} />
                <Route path="/skills" element={<SkillsPage />} />
                <Route path="/content/*" element={<ContentPage />} />
                <Route path="/tools" element={<ToolsPage />} />
                <Route path="/music" element={<MusicPage />} />
                <Route path="/memories" element={<MemoriesPage />} />
                <Route path="/schedules" element={<SchedulesPage />} />
                <Route
                  path="/settings"
                  element={
                    <SettingsPage
                      theme={theme}
                      onTheme={setTheme}
                      background={background}
                      onBackground={setBackground}
                    />
                  }
                />
                <Route
                  path="*"
                  element={
                    <div className="empty">
                      <h1>这里还没有内容</h1>
                      <button
                        className="button primary"
                        onClick={() => navigate("/")}
                      >
                        回到工作台
                      </button>
                    </div>
                  }
                />
              </Routes>
            </Suspense>
          </ErrorBoundary>
        </main>
        <footer className="workspace-footer">
          <span>XINXIN — A SPACE OF YOUR OWN</span>
          <span>专注于下一件值得完成的事。</span>
        </footer>
      </div>
      <MiniPlayer />
      <nav
        className="mobile-tabs"
        aria-label="手机导航"
        inert={drawer || undefined}
      >
        <NavLink to="/" end>
          <LayoutDashboard size={20} />
          <span>工作台</span>
        </NavLink>
        <NavLink to="/agent">
          <MessageSquare size={20} />
          <span>Agent</span>
        </NavLink>
        <NavLink to="/tasks">
          <ListTodo size={20} />
          <span>任务</span>
        </NavLink>
        <button onClick={() => setDrawer(true)}>
          <Menu size={20} />
          <span>更多</span>
        </button>
      </nav>
      {search && (
        <Dialog title="在空间里寻找" onClose={() => setSearch(false)}>
          <label className="search-field">
            <Search size={18} />
            <input
              autoFocus
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              placeholder="工作台、Agent、资料、服务器…"
            />
          </label>
          <div className="command-list">
            {navigation
              .filter((item) =>
                (item.label + " " + item.to)
                  .toLowerCase()
                  .includes(searchText.toLowerCase()),
              )
              .map((item) => (
                <button
                  key={item.to}
                  onClick={() => {
                    navigate(item.to);
                    setSearch(false);
                    setSearchText("");
                  }}
                >
                  <item.icon size={18} />
                  {item.label}
                  <ArrowUpRight size={15} />
                </button>
              ))}
          </div>
        </Dialog>
      )}
    </div>
  );
}
