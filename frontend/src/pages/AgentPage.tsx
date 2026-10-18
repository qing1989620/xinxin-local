import { Fragment, useEffect, useRef, useState, type FormEvent } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  ArrowUp,
  Plus,
  Paperclip,
  Square,
  Sparkles,
  MessageSquare,
  X,
  Shield,
  PanelRightOpen,
  ArrowUpRight,
  Search,
  MoreHorizontal,
  Pencil,
  Archive,
  Copy,
  SlidersHorizontal,
  FolderOpen,
  Code2,
  Server,
  Check,
  Bookmark,
  Trash2,
  ImagePlus,
} from "lucide-react";
import {
  api,
  ApiError,
  post,
  put,
  remove,
  watchRun,
  acknowledgeRequest,
  type EventItem,
  type FileItem,
  type Run,
  type ServerItem,
} from "../api";
import { nextAssistantText } from "../runText";
import {
  Empty,
  Status,
  date,
  size,
  Dialog,
  useResource,
  useToast,
  useMedia,
} from "../ui";
import AgentInspector from "./AgentInspector";
import ImageStudio from "./ImageStudio";
import ResourcePicker from "../ResourcePicker";
import RunFailureNotice from "./RunFailureNotice";
import AgentActivity from "./AgentActivity";
import HistoricalActivity from "./HistoricalActivity";
import MemoryGrant from "./MemoryGrant";
import { submitAgentRun, type AgentSettings } from "../runSubmission";
import {
  rememberConversation,
  rememberedConversation,
  forgetConversation,
} from "../conversationLocation";
type Conversation = {
  id: string;
  title: string;
  updated: number;
  archived?: number;
};
type Detail = {
  id: string;
  title: string;
  archived: number;
  context_window_tokens?: number;
  messages: {
    id: string;
    role: string;
    content: string;
    created?: number;
    run_id?: string;
  }[];
  runs: Run[];
};
const presets = [
  {
    icon: Server,
    title: "部署一个网站",
    description: "从 GitHub 到可用的服务",
    prompt:
      "帮我部署一个 GitHub 项目。先了解仓库和服务器，再提出部署与验证步骤。",
  },
  {
    icon: FolderOpen,
    title: "整理私人资料",
    description: "检索、阅读、归纳与处理",
    prompt: "帮我整理私人文件，先检索可用资料，再给出整理方案。",
  },
  {
    icon: Code2,
    title: "把想法写成代码",
    description: "实现、运行测试并交付",
    prompt: "帮我编写代码。先明确需求，在工作区实现并验证结果。",
  },
  {
    icon: ImagePlus,
    title: "画一张图",
    description: "描述画面，免费模型生成",
    prompt:
      "帮我画一张图。先确认我想要的画面、尺寸和用途，再用生图工具生成，画完告诉我文件在哪里、要不要调整。",
  },
];
export default function AgentPage() {
  const location = useLocation(),
    navigate = useNavigate(),
    [params] = useSearchParams(),
    toast = useToast(),
    cid = params.get("conversation") || "",
    explicitNew =
      params.get("new") === "1" ||
      Boolean(
        (location.state as any)?.prompt ||
        (location.state as any)?.serverId ||
        (location.state as any)?.files?.length,
      );
  const [conversations, setConversations] = useState<Conversation[]>([]),
    [messages, setMessages] = useState<Detail["messages"]>([]),
    [runs, setRuns] = useState<Run[]>([]),
    [draft, setDraft] = useState((location.state as any)?.prompt || ""),
    [permission, setPermission] = useState("read"),
    [server, setServer] = useState((location.state as any)?.serverId || ""),
    [files, setFiles] = useState<FileItem[]>(
      (location.state as any)?.files || [],
    ),
    [resourcesOpen, setResourcesOpen] = useState(false),
    [imageStudio, setImageStudio] = useState(false),
    [active, setActive] = useState<Run | null>(null),
    [watched, setWatched] = useState<Run | null>(null),
    [events, setEvents] = useState<EventItem[]>([]),
    [stream, setStream] = useState(""),
    [busy, setBusy] = useState(false),
    [cancelPending, setCancelPending] = useState(false),
    [contextWindow, setContextWindow] = useState(1048576),
    [contextSaving, setContextSaving] = useState(false),
    [trace, setTrace] = useState(
      () => matchMedia("(min-width: 1280px)").matches,
    ),
    [connection, setConnection] = useState("connected"),
    [mobileHistory, setMobileHistory] = useState(false),
    [historyQuery, setHistoryQuery] = useState(""),
    [showArchived, setShowArchived] = useState(false),
    [selectingConversations, setSelectingConversations] = useState(false),
    [selectedConversations, setSelectedConversations] = useState<string[]>([]),
    [archived, setArchived] = useState(false),
    [title, setTitle] = useState("新对话"),
    [editing, setEditing] = useState<Conversation | null>(null),
    [rename, setRename] = useState(""),
    [deleting, setDeleting] = useState<Conversation[] | null>(null),
    [deletionPreview, setDeletionPreview] = useState<{
      messages: number;
      runs: number;
      events: number;
      workspace_bytes: number;
      generated_bytes: number;
    } | null>(null),
    [deletionConfirmed, setDeletionConfirmed] = useState(false),
    [deletionBusy, setDeletionBusy] = useState(false),
    [options, setOptions] = useState(false),
    [maxCalls, setMaxCalls] = useState(16),
    [maxSeconds, setMaxSeconds] = useState(900),
    [maxTotalTokens, setMaxTotalTokens] = useState(320000),
    [allowMemory, setAllowMemory] = useState(false),
    [artifacts, setArtifacts] = useState<FileItem[]>([]),
    [follow, setFollow] = useState(true);
  const [streamEpoch, setStreamEpoch] = useState(0);
  const servers = useResource<ServerItem[]>("/servers"),
    settings = useResource<AgentSettings>("/settings"),
    bottom = useRef<HTMLDivElement>(null),
    draftRef = useRef<HTMLTextAreaElement>(null),
    currentCid = useRef(cid),
    executionDefaultsApplied = useRef(false),
    contextRevision = useRef(0),
    executionRevision = useRef(0),
    executionLoadedCid = useRef(""),
    deletionRevision = useRef(0),
    archiveMode = useRef(showArchived);
  const mounted = useRef(true);
  currentCid.current = cid;
  archiveMode.current = showArchived;
  const compactContext = useMedia("(max-width: 1280px)");
  const limits = settings.data?.execution_limits || {
    max_calls: 20,
    max_seconds: 1800,
    max_total_tokens: 1000000,
  };
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  useEffect(() => {
    if (cid) return;
    if (explicitNew) rememberConversation(null);
    else {
      const previous = rememberedConversation();
      if (previous)
        navigate(`/agent?conversation=${previous}`, { replace: true });
    }
  }, [cid, explicitNew]);
  useEffect(() => {
    const reconnect = () => {
      if (document.visibilityState !== "hidden")
        setStreamEpoch((value) => value + 1);
    };
    window.addEventListener("online", reconnect);
    window.addEventListener("focus", reconnect);
    document.addEventListener("visibilitychange", reconnect);
    return () => {
      window.removeEventListener("online", reconnect);
      window.removeEventListener("focus", reconnect);
      document.removeEventListener("visibilitychange", reconnect);
    };
  }, []);
  useEffect(() => {
    if (!settings.data || executionDefaultsApplied.current) return;
    executionDefaultsApplied.current = true;
    const defaults = settings.data.execution_defaults;
    if (defaults && !active) {
      setMaxCalls(defaults.max_calls);
      setMaxSeconds(defaults.max_seconds);
      setMaxTotalTokens(defaults.max_total_tokens);
    }
  }, [settings.data, active]);
  useEffect(() => {
    if (compactContext) setTrace(false);
  }, [compactContext]);
  async function refreshHistory() {
    const mode = archiveMode.current;
    const result = await api<Conversation[]>(`/conversations?archived=${mode}`);
    if (archiveMode.current === mode) setConversations(result);
  }
  async function loadConversation(id: string) {
    const revision = contextRevision.current;
    const executionVersion = executionRevision.current;
    if (!/^[a-f0-9]{32}$/i.test(id)) throw new ApiError("对话链接无效", 404);
    const detail = await api<Detail>(`/conversations/${id}`);
    if (!mounted.current || currentCid.current !== id) return;
    rememberConversation(id);
    setMessages(detail.messages);
    setRuns(detail.runs);
    if (revision === contextRevision.current)
      setContextWindow(detail.context_window_tokens || 1048576);
    setTitle(detail.title);
    setArchived(Boolean(detail.archived));
    const latest = detail.runs[0] || null;
    const ongoing =
      detail.runs.find((run) =>
        ["queued", "running", "cancelling"].includes(run.status),
      ) || null;
    setActive(ongoing);
    if (ongoing) {
      setPermission(ongoing.permission);
      setServer(ongoing.server_id || "");
      setMaxCalls(ongoing.max_calls ?? 16);
      setMaxSeconds(ongoing.max_seconds ?? 900);
      setMaxTotalTokens(ongoing.max_total_tokens ?? 320000);
      setAllowMemory(Boolean(ongoing.allow_memory));
      if (ongoing.context_window_tokens)
        setContextWindow(ongoing.context_window_tokens);
    } else {
      setAllowMemory(false);
      if (
        executionLoadedCid.current !== id &&
        executionVersion === executionRevision.current &&
        latest &&
        ["failed", "cancelled", "interrupted"].includes(latest.status)
      ) {
        setPermission(latest.permission);
        setServer(latest.server_id || "");
      }
    }
    executionLoadedCid.current = id;
    setWatched(latest);
    if (latest) {
      const full = await api<Run>(`/runs/${latest.id}`);
      if (currentCid.current === id) {
        setWatched(full);
        setArtifacts(full.files || []);
      }
    }
  }
  useEffect(() => {
    void refreshHistory().catch((error) => toast(error.message, true));
    setSelectedConversations([]);
  }, [showArchived]);
  useEffect(() => {
    executionLoadedCid.current = "";
    setMessages([]);
    setRuns([]);
    setFollow(true);
    setEvents([]);
    setStream("");
    setActive(null);
    setWatched(null);
    setArtifacts([]);
    setArchived(false);
    setTitle("新对话");
    setAllowMemory(false);
    if (/^[a-f\d]{32}$/i.test(cid)) rememberConversation(cid);
    if (cid)
      void loadConversation(cid).catch((error) => {
        if (!mounted.current || currentCid.current !== cid) return;
        if (error instanceof ApiError && error.status === 404) {
          forgetConversation(cid);
          navigate("/agent?new=1", { replace: true });
          toast("这段对话在当前后端不可用，已回到新对话", true);
        } else toast(error.message, true);
      });
  }, [cid]);
  useEffect(() => {
    if (!watched) return;
    const controller = new AbortController();
    setEvents([]);
    setStream("");
    watchRun(
      watched.id,
      (event) => {
        if (
          controller.signal.aborted ||
          !mounted.current ||
          currentCid.current !== watched.conversation_id
        )
          return;
        if (event.kind !== "delta")
          setEvents((old) =>
            old.some((item) => item.seq === event.seq)
              ? old
              : [
                  ...old.filter(
                    (item) =>
                      event.kind !== "command.progress" ||
                      item.kind !== "command.progress" ||
                      item.data.command_id !== event.data.command_id,
                  ),
                  event,
                ],
          );
        if (
          ["delta", "assistant.progress"].includes(event.kind) &&
          ["queued", "running", "cancelling"].includes(watched.status)
        )
          setStream((old) => nextAssistantText(old, event));
        if (event.kind === "started")
          setActive((old) => (old ? { ...old, status: "running" } : old));
        if (event.kind === "cancelling")
          setActive((old) => (old ? { ...old, status: "cancelling" } : old));
        if (event.kind === "finished") {
          setActive(null);
          setStream("");
          void loadConversation(watched.conversation_id).catch((error) =>
            toast(error.message, true),
          );
          void refreshHistory().catch((error) => toast(error.message, true));
          if (event.data.error) toast(event.data.error, true);
        }
      },
      controller.signal,
      setConnection,
      (snapshot) => {
        if (
          controller.signal.aborted ||
          !mounted.current ||
          currentCid.current !== watched.conversation_id
        )
          return;
        if (["queued", "running", "cancelling"].includes(snapshot.status)) {
          setActive(snapshot);
          return;
        }
        setActive(null);
        setStream("");
        setWatched(snapshot);
        void loadConversation(snapshot.conversation_id).catch((error) =>
          toast(error.message, true),
        );
        if (settings.data?.capabilities?.command_progress)
          void api<EventItem[]>(`/runs/${snapshot.id}/activity`)
            .then(setEvents)
            .catch(() => {});
      },
    ).catch((error) => toast(error.message, true));
    return () => controller.abort();
  }, [watched?.id, streamEpoch]);
  useEffect(() => {
    if (!follow || (!messages.length && !active)) return;
    bottom.current?.scrollIntoView({
      block: "end",
      behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "instant"
        : "smooth",
    });
  }, [messages.length, stream, follow, events.at(-1)?.seq]);
  async function send() {
    await submit();
  }
  async function submit(resumeRun?: Run) {
    if (
      (!draft.trim() && !resumeRun) ||
      busy ||
      active ||
      archived ||
      contextSaving
    )
      return;
    if (!settings.data) {
      toast("正在读取后端能力，请稍候再提交。", true);
      return;
    }
    setBusy(true);
    setFollow(true);
    const text = draft;
    const submittedCid = cid;
    try {
      const payload = {
        task: text,
        conversation_id: cid || null,
        permission,
        server_id: server || null,
        max_calls: maxCalls,
        max_seconds: maxSeconds,
        ...(settings.data.capabilities?.context_tiers
          ? { context_window_tokens: contextWindow }
          : {}),
        ...(settings.data.capabilities?.run_token_budget
          ? { max_total_tokens: maxTotalTokens }
          : {}),
        allow_memory: allowMemory,
        file_ids: files.map((file) => file.id),
        ...(resumeRun ? { resume_run_id: resumeRun.id } : {}),
      };
      const result = await submitAgentRun(payload);
      acknowledgeRequest("agent");
      if ((rememberedConversation() || "") === submittedCid)
        rememberConversation(result.conversation_id);
      if (!mounted.current || currentCid.current !== submittedCid) {
        void refreshHistory();
        toast("任务已在原对话提交，可以返回查看进度。");
        return;
      }
      setDraft("");
      setFiles([]);
      if (!cid)
        navigate(`/agent?conversation=${result.conversation_id}`, {
          replace: true,
        });
      else {
        setMessages((old) => [
          ...old,
          {
            id: crypto.randomUUID(),
            role: "user",
            content: resumeRun
              ? "继续原任务。" + (text ? "\n补充：" + text : "")
              : text,
            created: result.created,
            run_id: result.id,
          },
        ]);
        setRuns((old) => [result, ...old]);
        setActive(result);
        setWatched(result);
        setArtifacts([]);
      }
      void refreshHistory().catch((error) => toast(error.message, true));
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      setBusy(false);
    }
  }
  function closeDeletion() {
    if (deletionBusy) return;
    deletionRevision.current++;
    setDeleting(null);
  }
  async function openDeletion(items: Conversation[]) {
    if (!items.length) return;
    const revision = ++deletionRevision.current;
    setDeleting(items);
    setDeletionConfirmed(false);
    setDeletionPreview(null);
    setEditing(null);
    setMobileHistory(false);
    try {
      const preview =
        items.length === 1
          ? await api(`/conversations/${items[0].id}/deletion-preview`)
          : await post("/conversations/batch/deletion-preview", {
              ids: items.map((item) => item.id),
            });
      if (revision === deletionRevision.current) setDeletionPreview(preview);
    } catch (error) {
      if (revision === deletionRevision.current) {
        toast((error as Error).message, true);
        closeDeletion();
      }
    }
  }
  function newConversation() {
    rememberConversation(null);
    navigate("/agent?new=1");
    setDraft("");
    setFiles([]);
    setMobileHistory(false);
    setArchived(false);
    contextRevision.current++;
    setContextWindow(1048576);
    draftRef.current?.focus();
  }
  const filteredConversations = conversations.filter((item) =>
    item.title.toLowerCase().includes(historyQuery.toLowerCase()),
  );
  function toggleConversation(id: string) {
    setSelectedConversations((old) =>
      old.includes(id)
        ? old.filter((item) => item !== id)
        : old.length < 100
          ? [...old, id]
          : old,
    );
  }
  const history = (
    <>
      <header>
        <div>
          <span className="eyebrow">YOUR CONVERSATIONS</span>
          <h2>对话</h2>
        </div>
        <button
          className="icon-button"
          aria-label="新建对话"
          onClick={newConversation}
        >
          <Plus size={18} />
        </button>
      </header>
      <button className="button secondary full-width" onClick={newConversation}>
        <Plus size={16} />
        新对话<span className="shortcut-hint">＋</span>
      </button>
      <label className="history-search">
        <Search size={14} />
        <input
          value={historyQuery}
          onChange={(e) => setHistoryQuery(e.target.value)}
          placeholder="搜索对话"
          aria-label="搜索对话"
        />
      </label>
      <div className="history-tabs">
        <button
          aria-pressed={!showArchived}
          className={!showArchived ? "active" : ""}
          onClick={() => setShowArchived(false)}
        >
          最近
        </button>
        <button
          aria-pressed={showArchived}
          className={showArchived ? "active" : ""}
          onClick={() => setShowArchived(true)}
        >
          已归档
        </button>
      </div>
      {settings.data?.capabilities?.conversation_batch_delete && (
        <div className="history-batch">
          <button
            className="text-button"
            onClick={() => {
              setSelectingConversations(!selectingConversations);
              setSelectedConversations([]);
            }}
          >
            {selectingConversations ? "退出选择" : "批量管理"}
          </button>
          {selectingConversations && (
            <>
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  aria-label="全选当前筛选的对话"
                  checked={
                    filteredConversations.length > 0 &&
                    filteredConversations
                      .slice(0, 100)
                      .every((item) => selectedConversations.includes(item.id))
                  }
                  onChange={(event) =>
                    setSelectedConversations(
                      event.target.checked
                        ? filteredConversations
                            .slice(0, 100)
                            .map((item) => item.id)
                        : [],
                    )
                  }
                />
                全选当前列表（最多100段）
              </label>
              <button
                className="text-button destructive"
                disabled={
                  !selectedConversations.length || busy || Boolean(active)
                }
                onClick={() =>
                  void openDeletion(
                    conversations.filter((item) =>
                      selectedConversations.includes(item.id),
                    ),
                  )
                }
              >
                <Trash2 size={14} />
                删除所选 {selectedConversations.length} 段…
              </button>
            </>
          )}
        </div>
      )}
      <div className="conversation-list">
        {filteredConversations.map((item) => (
          <div
            className={`conversation-item ${cid === item.id ? "selected" : ""}`}
            key={item.id}
          >
            {selectingConversations && (
              <input
                type="checkbox"
                className="conversation-select"
                aria-label={`选择对话 ${item.title}`}
                checked={selectedConversations.includes(item.id)}
                disabled={
                  !selectedConversations.includes(item.id) &&
                  selectedConversations.length >= 100
                }
                onChange={() => toggleConversation(item.id)}
              />
            )}
            <button
              onClick={() => {
                if (selectingConversations) {
                  toggleConversation(item.id);
                  return;
                }
                navigate(`/agent?conversation=${item.id}`);
                setMobileHistory(false);
              }}
            >
              <MessageSquare size={15} />
              <span>
                <strong>{item.title}</strong>
                <small>{date(item.updated)}</small>
              </span>
            </button>
            <button
              className="conversation-menu icon-button"
              aria-label={`管理对话 ${item.title}`}
              onClick={() => {
                setEditing(item);
                setRename(item.title);
              }}
            >
              <MoreHorizontal size={16} />
            </button>
          </div>
        ))}
        {!conversations.length && (
          <div className="history-empty">
            <MessageSquare size={24} strokeWidth={1} />
            <p>{showArchived ? "还没有归档对话" : "从一件想完成的事开始"}</p>
          </div>
        )}
      </div>
      <div className="conversation-note">
        <Shield size={15} />
        <p>
          你的资料，留在私人空间。
          <br />
          每次行动，遵守本轮授权。
        </p>
      </div>
    </>
  );
  return (
    <div
      className={`agent-layout agent-v2 page-enter ${trace ? "inspector-open" : ""}`}
    >
      <aside className="conversation-sidebar">{history}</aside>
      <section className="chat-panel">
        <header className="chat-header">
          <div>
            <button
              className="icon-button history-toggle"
              aria-label="查看历史对话"
              onClick={() => setMobileHistory(true)}
            >
              <MessageSquare size={18} />
            </button>
            <div>
              <h1>
                Xinxin <span>{cid ? title : "你的私人 Agent"}</span>
              </h1>
              <p className="agent-model-line">
                <span
                  className={`connection-dot ${settings.data?.model_configured ? "ready" : ""}`}
                />
                <span className="agent-model-name">
                  {!settings.data
                    ? "正在读取模型配置"
                    : settings.data.model_configured
                      ? settings.data.model === "deepseek-flash"
                        ? "DeepSeek Flash"
                        : settings.data.model
                      : "等待配置模型"}
                </span>
                {settings.data?.context_window_tokens && (
                  <span
                    className="context-capacity"
                    title={`${contextWindow.toLocaleString()} tokens`}
                  >
                    {contextWindow === 80000
                      ? "80K"
                      : contextWindow === 300000
                        ? "300K"
                        : "1000K"}{" "}
                    上下文
                  </span>
                )}
                <span className="agent-model-divider" aria-hidden="true">
                  ·
                </span>
                <span>{active ? "任务正在执行" : "准备好，与你一起工作"}</span>
              </p>
            </div>
          </div>
          <div className="chat-header-actions">
            {cid && (
              <button
                className="icon-button"
                aria-label="管理当前对话"
                onClick={() => {
                  setEditing({
                    id: cid,
                    title,
                    updated: Date.now(),
                    archived: archived ? 1 : 0,
                  });
                  setRename(title);
                }}
              >
                <MoreHorizontal size={18} />
              </button>
            )}
            <button
              className={`icon-button ${trace ? "selected" : ""}`}
              onClick={() => setTrace(!trace)}
              aria-label="展开任务上下文"
              aria-pressed={trace}
            >
              <PanelRightOpen size={19} />
            </button>
          </div>
        </header>
        <div
          className="chat-messages"
          onScroll={(e) => {
            const target = e.currentTarget;
            setFollow(
              target.scrollHeight - target.scrollTop - target.clientHeight <
                100,
            );
          }}
        >
          {!messages.length && !active ? (
            <div className="chat-welcome">
              <div className="welcome-agent-mark">
                <span className="brand-mark">x</span>
                <span>Xinxin Agent</span>
              </div>
              <h2>在这呀，今天想折腾点什么？</h2>
              <p>
                文件也可以一起给我。
                <br />
                我先看看，弄好给你。
              </p>
              <div className="welcome-preset-grid">
                {presets.map((item) => (
                  <button
                    key={item.title}
                    onClick={() => {
                      setDraft(item.prompt);
                      draftRef.current?.focus();
                    }}
                  >
                    <item.icon size={20} strokeWidth={1.4} />
                    <strong>{item.title}</strong>
                    <p>{item.description}</p>
                    <ArrowUpRight size={15} />
                  </button>
                ))}
              </div>
              <button
                className="welcome-tools-link text-button"
                onClick={() => navigate("/skills")}
              >
                <Sparkles size={14} />
                看看 Agent 有哪些能力
                <ArrowUpRight size={13} />
              </button>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <Fragment key={message.id}>
                  <article className={`message ${message.role}`}>
                    <div className="message-label">
                      <span
                        className={
                          message.role === "user"
                            ? "message-owner"
                            : "message-agent"
                        }
                      >
                        {message.role === "user" ? "我" : "x"}
                      </span>
                      {message.role === "user" ? "你" : "Xinxin"}
                    </div>
                    <div className="message-body">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        skipHtml
                        components={{
                          img: ({ alt }) => (
                            <span className="muted">
                              [图片：{alt || "参考图片"}]
                            </span>
                          ),
                        }}
                      >
                        {message.role === "user"
                          ? message.content.split(
                              "\n\n本轮附件（使用文件工具读取）：",
                            )[0]
                          : message.content}
                      </ReactMarkdown>
                    </div>
                    {message.role === "assistant" && (
                      <div className="message-actions">
                        <button
                          onClick={async () => {
                            try {
                              await navigator.clipboard.writeText(
                                message.content,
                              );
                              toast("答复已复制");
                            } catch {
                              toast("浏览器未允许复制，请选择文本复制", true);
                            }
                          }}
                        >
                          <Copy size={13} />
                          复制
                        </button>
                        {watched && (
                          <button onClick={() => setTrace(true)}>
                            <PanelRightOpen size={13} />
                            查看过程
                          </button>
                        )}
                      </div>
                    )}
                  </article>
                  {message.role === "user" &&
                    (() => {
                      const run =
                        runs.find((item) => item.id === message.run_id) ||
                        runs
                          .filter((item) => item.task === message.content)
                          .sort(
                            (a, b) =>
                              Math.abs(a.created - (message.created || 0)) -
                              Math.abs(b.created - (message.created || 0)),
                          )[0];
                      if (!run) return null;
                      return run.id === watched?.id ? (
                        <AgentActivity
                          run={active || watched}
                          events={events}
                        />
                      ) : (
                        <HistoricalActivity run={run} />
                      );
                    })()}
                </Fragment>
              ))}
              {active && (
                <article className="message assistant">
                  <div className="message-label">
                    <span className="message-agent">x</span>Xinxin
                    <Status value={active.status} />
                  </div>
                  {stream ? (
                    <div className="message-body">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        skipHtml
                        components={{
                          img: ({ alt }) => <span>[图片：{alt}]</span>,
                        }}
                      >
                        {stream}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <div className="working-label">
                      <span />
                      <span />
                      <span />
                      {events.some((event) => event.kind === "tool.started")
                        ? "正在执行并验证工具结果"
                        : "正在理解目标与选择能力"}
                    </div>
                  )}
                </article>
              )}
              {!active &&
                watched &&
                ["failed", "cancelled", "interrupted"].includes(
                  watched.status,
                ) && (
                  <RunFailureNotice
                    run={watched}
                    onTrace={() => setTrace(true)}
                    onOptions={() => setOptions(true)}
                    continuing={busy}
                    disabled={archived || contextSaving}
                    onContinue={() => void submit(watched)}
                  />
                )}
            </>
          )}
          <div ref={bottom} />
        </div>
        <div className="composer-area">
          {!follow && messages.length > 0 && (
            <button
              className="text-button follow-latest"
              onClick={() => {
                setFollow(true);
                bottom.current?.scrollIntoView({ block: "end" });
              }}
            >
              回到最新进展 ↓
            </button>
          )}
          {connection === "reconnecting" && active && (
            <p className="connection-notice">
              正在恢复连接，任务继续执行；恢复后补回进度。
            </p>
          )}
          {archived && (
            <div className="archived-notice">
              <Archive size={15} />
              <span>此对话已归档，历史和产物仍然保留。</span>
              <button
                className="text-button"
                onClick={async () => {
                  try {
                    await post(`/conversations/${cid}/restore`, {});
                    setArchived(false);
                    void refreshHistory();
                    toast("对话已恢复");
                  } catch (error) {
                    toast((error as Error).message, true);
                  }
                }}
              >
                恢复对话
              </button>
            </div>
          )}
          {files.length > 0 && (
            <div className="attachment-list">
              {files.map((file) => (
                <span key={file.id}>
                  <Paperclip size={12} />
                  {file.name}
                  <button
                    className="icon-button"
                    aria-label={`移除附件 ${file.name}`}
                    onClick={() =>
                      setFiles((old) =>
                        old.filter((item) => item.id !== file.id),
                      )
                    }
                  >
                    <X size={13} />
                  </button>
                </span>
              ))}
            </div>
          )}
          <ImageStudio
            open={imageStudio}
            onClose={() => setImageStudio(false)}
          />
          <div className="composer">
            <textarea
              ref={draftRef}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder={
                archived ? "先恢复对话，再继续工作" : "说说你想完成什么…"
              }
              aria-label="给 Agent 的任务"
              rows={3}
              maxLength={12000}
              disabled={archived}
              onKeyDown={(e) => {
                if (
                  e.key === "Enter" &&
                  !e.shiftKey &&
                  !e.nativeEvent.isComposing
                ) {
                  e.preventDefault();
                  void send();
                }
              }}
            />
            <div className="composer-toolbar">
              <div>
                <button
                  className="icon-button"
                  aria-label="上传或选择资源"
                  title="上传文件，或从资源库选择"
                  disabled={active !== null || archived}
                  onClick={() => setResourcesOpen(true)}
                >
                  <Paperclip size={18} />
                </button>
                <button
                  className={`icon-button ${imageStudio ? "selected" : ""}`}
                  aria-label="生图工作台"
                  title="直接生成一张图（免费模型）"
                  disabled={active !== null || archived}
                  onClick={() => setImageStudio((value) => !value)}
                >
                  <ImagePlus size={18} />
                </button>
                <select
                  className="permission-select"
                  aria-label="本次任务权限"
                  value={permission}
                  disabled={active !== null || archived}
                  onChange={(e) => {
                    executionRevision.current++;
                    setPermission(e.target.value);
                    if (e.target.value === "read") setAllowMemory(false);
                  }}
                >
                  <option value="read">只读</option>
                  <option value="workspace">工作区</option>
                  <option value="full">完整权限</option>
                </select>
                <select
                  className="server-select"
                  aria-label="本次目标服务器"
                  value={server}
                  disabled={active !== null || archived}
                  onChange={(e) => {
                    executionRevision.current++;
                    if (e.target.value === "add") navigate("/servers");
                    else setServer(e.target.value);
                  }}
                >
                  <option value="">无远程服务器</option>
                  {servers.data?.map((item) => (
                    <option value={item.id} key={item.id}>
                      {item.name}
                    </option>
                  ))}
                  <option value="add">＋登记服务器</option>
                </select>
                <button
                  className={`icon-button ${allowMemory ? "selected" : ""}`}
                  aria-label="本轮参数与记忆授权"
                  disabled={active !== null}
                  onClick={() => setOptions(true)}
                >
                  <SlidersHorizontal size={17} />
                </button>
                {allowMemory && (
                  <span className="memory-grant">
                    <Bookmark size={12} />
                    可保存记忆
                  </span>
                )}
                {settings.data?.capabilities?.context_tiers && (
                  <select
                    className="context-select"
                    aria-label="会话上下文档位"
                    value={contextWindow}
                    disabled={active !== null || contextSaving}
                    onChange={async (event) => {
                      const choice = Number(event.target.value);
                      contextRevision.current++;
                      if (!cid) {
                        setContextWindow(choice);
                        return;
                      }
                      const target = cid;
                      setContextSaving(true);
                      try {
                        await put(`/conversations/${target}/context`, {
                          context_window_tokens: choice,
                        });
                        if (currentCid.current === target)
                          setContextWindow(choice);
                      } catch (error) {
                        toast((error as Error).message, true);
                      } finally {
                        setContextSaving(false);
                      }
                    }}
                  >
                    {settings.data.context_tiers?.map((tier) => (
                      <option key={tier.tokens} value={tier.tokens}>
                        {tier.label} 上下文
                      </option>
                    ))}
                  </select>
                )}
              </div>
              {active ? (
                <button
                  className="send-button stop"
                  aria-label={
                    active.status === "cancelling" || cancelPending
                      ? "正在停止当前任务"
                      : "停止当前任务"
                  }
                  disabled={active.status === "cancelling" || cancelPending}
                  onClick={async () => {
                    setCancelPending(true);
                    try {
                      const result = await post<Run>(
                        `/runs/${active.id}/cancel`,
                        {},
                      );
                      if (
                        ["queued", "running", "cancelling"].includes(
                          result.status,
                        )
                      )
                        setActive(result);
                      else {
                        setActive(null);
                        void loadConversation(result.conversation_id).catch(
                          (error) => toast(error.message, true),
                        );
                      }
                    } catch (error) {
                      toast((error as Error).message, true);
                    } finally {
                      setCancelPending(false);
                    }
                  }}
                >
                  <Square size={15} fill="currentColor" />
                </button>
              ) : (
                <button
                  className="send-button"
                  aria-label="发送任务"
                  disabled={!draft.trim() || busy || archived || contextSaving}
                  onClick={() => void send()}
                >
                  <ArrowUp size={20} />
                </button>
              )}
            </div>
          </div>
          <p className="composer-hint">
            <span>
              <Shield size={11} />
              {permission === "full"
                ? "完整权限：后端主机与所选服务器命令。"
                : permission === "workspace"
                  ? "工作区：创建文件、图表与私人草稿。"
                  : "只读：检索、阅读与分析。"}
            </span>
            <span>Enter 发送 · Shift Enter 换行</span>
          </p>
        </div>
      </section>
      {resourcesOpen && (
        <ResourcePicker
          existing={files}
          onClose={() => setResourcesOpen(false)}
          onAttach={(selected) =>
            setFiles((old) =>
              [
                ...new Map(
                  [...old, ...selected].map((file) => [file.id, file]),
                ).values(),
              ].slice(0, 10),
            )
          }
        />
      )}
      {trace && !compactContext && (
        <AgentInspector
          run={watched}
          events={events}
          files={artifacts}
          onClose={() => setTrace(false)}
        />
      )}
      {trace && compactContext && (
        <Dialog title="任务上下文" onClose={() => setTrace(false)}>
          <AgentInspector
            run={watched}
            events={events}
            files={artifacts}
            onClose={() => setTrace(false)}
          />
        </Dialog>
      )}
      {mobileHistory && (
        <Dialog title="历史对话" onClose={() => setMobileHistory(false)}>
          <div className="mobile-history-content">{history}</div>
        </Dialog>
      )}
      {editing && (
        <Dialog title="管理对话" onClose={() => setEditing(null)}>
          <form
            className="form-stack"
            onSubmit={async (e: FormEvent) => {
              e.preventDefault();
              try {
                await put(`/conversations/${editing.id}`, { title: rename });
                if (cid === editing.id) setTitle(rename);
                setEditing(null);
                void refreshHistory();
                toast("对话名称已更新");
              } catch (error) {
                toast((error as Error).message, true);
              }
            }}
          >
            <label>
              对话名称
              <input
                value={rename}
                maxLength={80}
                required
                onChange={(e) => setRename(e.target.value)}
              />
            </label>
            <div className="dialog-actions">
              <button
                type="button"
                className="text-button"
                onClick={async () => {
                  try {
                    if (editing.archived)
                      await post(`/conversations/${editing.id}/restore`, {});
                    else await remove(`/conversations/${editing.id}`);
                    if (cid === editing.id) newConversation();
                    setEditing(null);
                    void refreshHistory();
                    toast(
                      editing.archived
                        ? "对话已恢复"
                        : "对话已归档，记录和产物已保留",
                    );
                  } catch (error) {
                    toast((error as Error).message, true);
                  }
                }}
              >
                <Archive size={15} />
                {editing.archived ? "恢复对话" : "归档对话"}
              </button>
              <button className="button primary">
                <Pencil size={15} />
                保存名称
              </button>
            </div>
            {settings.data?.capabilities?.conversation_delete && (
              <button
                type="button"
                className="text-button destructive"
                onClick={() => void openDeletion([editing])}
              >
                <Trash2 size={15} />
                永久删除并清理空间…
              </button>
            )}
          </form>
        </Dialog>
      )}
      {deleting && (
        <Dialog
          title={
            deleting.length > 1
              ? `永久删除 ${deleting.length} 段对话`
              : "永久删除对话"
          }
          onClose={closeDeletion}
        >
          <div className="form-stack">
            <p>
              将永久删除所选 {deleting.length}{" "}
              段对话的消息、执行日志、上下文检查点、工作区和专属生成文件。此操作无法在应用中撤销。
            </p>
            <ul className="deletion-titles">
              {deleting.map((item) => (
                <li key={item.id}>{item.title}</li>
              ))}
            </ul>
            {deletionPreview ? (
              <p className="field-help">
                {deletionPreview.messages} 条消息 · {deletionPreview.runs}{" "}
                轮任务 · {deletionPreview.events} 条执行事件。工作区{" "}
                {size(deletionPreview.workspace_bytes)}，生成文件最多{" "}
                {size(deletionPreview.generated_bytes)}
                ；被未选对话或内容引用的文件会保留。
              </p>
            ) : (
              <p role="status">正在计算清理范围…</p>
            )}
            <p className="field-help">
              独立资料库上传、服务器部署目录与服务保留。已有备份按原保留周期到期。
            </p>
            <label className="checkbox-row">
              <input
                type="checkbox"
                checked={deletionConfirmed}
                disabled={deletionBusy}
                onChange={(event) => setDeletionConfirmed(event.target.checked)}
              />
              我确认永久删除所选 {deleting.length} 段对话及其专属数据
            </label>
            <div className="dialog-actions">
              <button
                className="button secondary"
                disabled={deletionBusy}
                onClick={closeDeletion}
              >
                保留对话
              </button>
              <button
                className="button destructive"
                disabled={
                  !deletionConfirmed || !deletionPreview || deletionBusy
                }
                onClick={async () => {
                  setDeletionBusy(true);
                  try {
                    const ids = deleting.map((item) => item.id);
                    const result =
                      ids.length === 1
                        ? await remove(`/conversations/${ids[0]}/permanent`)
                        : await post("/conversations/batch/permanent", { ids });
                    if (ids.includes(cid)) newConversation();
                    deletionRevision.current++;
                    setDeleting(null);
                    setSelectedConversations([]);
                    setSelectingConversations(false);
                    void refreshHistory();
                    toast(
                      result.cleanup_pending
                        ? "对话已删除，部分暂存文件仍待清理，请查看存储状态。"
                        : `对话已永久删除，清理文件空间 ${size(result.removed_file_bytes)}。`,
                    );
                  } catch (error) {
                    toast((error as Error).message, true);
                  } finally {
                    setDeletionBusy(false);
                  }
                }}
              >
                {deletionBusy ? "正在清理空间…" : "永久删除"}
              </button>
            </div>
          </div>
        </Dialog>
      )}
      {options && (
        <Dialog title="本轮执行参数" onClose={() => setOptions(false)}>
          <div className="form-stack">
            <p className="field-help">
              仅用于下一次提交。任务开始后，权限、目标和预算保持固定。
            </p>
            <div className="budget-presets">
              {(settings.data?.execution_limits
                ? [
                    ["轻量", 16, 600, 1000000],
                    ["常规", 64, 3600, 8000000],
                    ["深入", 128, 7200, 32000000],
                  ]
                : [
                    ["轻量", 4, 120, 80000],
                    ["常规", 16, 900, 320000],
                    ["深入", 20, 1800, 400000],
                  ]
              ).map(([label, calls, seconds, tokens]) => (
                <button
                  key={label}
                  className={
                    maxCalls === calls &&
                    maxSeconds === seconds &&
                    maxTotalTokens === tokens
                      ? "selected"
                      : ""
                  }
                  onClick={() => {
                    setMaxCalls(Number(calls));
                    setMaxSeconds(Number(seconds));
                    setMaxTotalTokens(Number(tokens));
                  }}
                >
                  {label}
                  <small>{Number(seconds) / 60} 分钟</small>
                </button>
              ))}
            </div>
            <div className="form-columns">
              <label>
                最多模型调用
                <input
                  type="number"
                  min={1}
                  max={limits.max_calls}
                  value={maxCalls}
                  onChange={(e) =>
                    setMaxCalls(
                      Math.max(
                        1,
                        Math.min(limits.max_calls, Number(e.target.value)),
                      ),
                    )
                  }
                />
              </label>
              <label>
                时间预算（秒）
                <input
                  type="number"
                  min={10}
                  max={limits.max_seconds}
                  value={maxSeconds}
                  onChange={(e) =>
                    setMaxSeconds(
                      Math.max(
                        10,
                        Math.min(limits.max_seconds, Number(e.target.value)),
                      ),
                    )
                  }
                />
              </label>
            </div>
            <label>
              本轮累计用量上限（多次请求的输入＋输出）
              <input
                type="number"
                min={5000}
                max={limits.max_total_tokens}
                step={5000}
                disabled={!settings.data?.capabilities?.run_token_budget}
                placeholder="由服务端决定"
                value={
                  settings.data?.capabilities?.run_token_budget
                    ? maxTotalTokens
                    : ""
                }
                onChange={(e) =>
                  setMaxTotalTokens(
                    Math.max(
                      5000,
                      Math.min(limits.max_total_tokens, Number(e.target.value)),
                    ),
                  )
                }
              />
            </label>
            {settings.data?.context_window_tokens && (
              <p className="field-help">
                模型上下文窗口：
                {settings.data.context_window_tokens.toLocaleString()}{" "}
                tokens（模型上限）。此对话选择{" "}
                {contextWindow === 1048576
                  ? "1000K"
                  : `${contextWindow / 1000}K`}{" "}
                档位，并预留工具协议和输出空间。上面的累计用量统计多次调用，与上下文长度分别计算；只有接近所选窗口才回收旧交换，持久历史仍保留。
              </p>
            )}
            <p className="field-help">
              {settings.data?.capabilities?.run_token_budget
                ? "按模型服务返回的用量累计，下一次调用前检查；单次响应可能超过剩余预算。完整权限决定能做什么，预算决定本轮能执行多久。"
                : "当前后端未提供自定义令牌预算；本轮仅发送调用次数和时间设置。更新后端并刷新连接后可调整令牌预算。"}
            </p>
            <MemoryGrant
              permission={permission}
              checked={allowMemory}
              disabled={Boolean(active) || busy}
              onChange={(checked, nextPermission) => {
                executionRevision.current++;
                setPermission(nextPermission);
                setAllowMemory(checked);
              }}
            />
            <div className="dialog-actions">
              <button
                className="button primary"
                onClick={() => setOptions(false)}
              >
                <Check size={16} />
                应用到下一轮
              </button>
            </div>
          </div>
        </Dialog>
      )}
    </div>
  );
}
