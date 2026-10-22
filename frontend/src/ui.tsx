import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  X,
  Loader2,
  ArrowUpRight,
  FolderOpen,
  CircleAlert,
} from "lucide-react";
import { api } from "./api";
import { loadPrivateImage } from "./privateImages";

type Toast = (message: string, error?: boolean) => void;
type ToastMessage = { message: string; error: boolean };
const ToastStateContext = createContext<{
  toast: ToastMessage | null;
  close: () => void;
} | null>(null);
export const ToastContext = createContext<Toast>(() => {});
export const useToast = () => useContext(ToastContext);
export function useMedia(query: string) {
  const [matches, setMatches] = useState(() => matchMedia(query).matches);
  useEffect(() => {
    const media = matchMedia(query);
    const change = () => setMatches(media.matches);
    media.addEventListener("change", change);
    return () => media.removeEventListener("change", change);
  }, [query]);
  return matches;
}
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<ToastMessage | null>(null);
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [toast]);
  return (
    <ToastContext.Provider
      value={(message, error = false) => setToast({ message, error })}
    >
      <ToastStateContext.Provider
        value={{ toast, close: () => setToast(null) }}
      >
        {children}
        <ToastNotice />
      </ToastStateContext.Provider>
    </ToastContext.Provider>
  );
}
function ToastNotice({ modal = false }: { modal?: boolean }) {
  const state = useContext(ToastStateContext);
  if (!state) return null;
  const { toast, close } = state;
  return (
    <div
      className={`toast-host${modal ? " dialog-toast-host" : ""}`}
      aria-live="polite"
    >
      {toast && (
        <div
          className={`toast ${toast.error ? "error" : ""}`}
          role={toast.error ? "alert" : "status"}
        >
          {toast.message}
          <button
            className="icon-button"
            type="button"
            onClick={close}
            aria-label="关闭提示"
          >
            <X size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
export function Dialog({
  title,
  children,
  onClose,
  wide = false,
  busy = false,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  wide?: boolean;
  busy?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const pointerStartedOutside = useRef(false);
  useEffect(() => {
    const element = ref.current;
    const previous = document.activeElement as HTMLElement;
    element?.showModal();
    element
      ?.querySelector<HTMLElement>(
        "[data-autofocus], input:not([type=hidden]):not([disabled]), textarea:not([disabled]), select:not([disabled])",
      )
      ?.focus({ preventScroll: true });
    return () => {
      element?.close();
      if (previous?.isConnected) previous.focus({ preventScroll: true });
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className={wide ? "dialog wide" : "dialog"}
      aria-label={title}
      aria-busy={busy || undefined}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
      onPointerDown={(event) => {
        pointerStartedOutside.current = event.target === event.currentTarget;
      }}
      onClick={(event) => {
        if (
          !busy &&
          pointerStartedOutside.current &&
          event.target === event.currentTarget
        )
          onClose();
        pointerStartedOutside.current = false;
      }}
    >
      <div className="dialog-inner">
        <header className="dialog-header">
          <h2>{title}</h2>
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            className="icon-button"
            aria-label="关闭对话框"
          >
            <X size={20} />
          </button>
        </header>
        {children}
        <ToastNotice modal />
      </div>
    </dialog>
  );
}
export function Empty({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty">
      <span className="empty-icon">
        <FolderOpen size={24} strokeWidth={1.3} />
      </span>
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {action}
    </div>
  );
}
export function Loading({ label = "正在读取私人空间" }: { label?: string }) {
  return (
    <div className="loading" role="status">
      <Loader2 className="spin" size={22} />
      <span>{label}</span>
    </div>
  );
}
export function PageHeader({
  overline,
  title,
  description,
  action,
  meta,
}: {
  overline: string;
  title: string;
  description?: string;
  action?: ReactNode;
  meta?: ReactNode;
}) {
  return (
    <header className="page-heading">
      <div className="page-heading-copy">
        <p className="eyebrow">{overline}</p>
        <h1>{title}</h1>
        {description && <p className="lead">{description}</p>}
        {meta && <div className="page-heading-meta">{meta}</div>}
      </div>
      {action && <div className="page-heading-action">{action}</div>}
    </header>
  );
}
export function Status({ value }: { value: string }) {
  const labels: Record<string, string> = {
    queued: "等待执行",
    running: "执行中",
    cancelling: "正在停止",
    completed: "已完成",
    failed: "执行失败",
    cancelled: "已取消",
    interrupted: "已中断",
  };
  return (
    <span className={`status ${value}`}>
      <span />
      {labels[value] || value}
    </span>
  );
}
export function PrivateImage({
  path,
  alt = "",
  className = "",
  loading,
  retryable = true,
}: {
  path: string;
  alt?: string;
  className?: string;
  loading?: "eager" | "lazy";
  retryable?: boolean;
}) {
  const [source, setSource] = useState("");
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    let object = "";
    setSource("");
    setError("");
    loadPrivateImage(path, controller.signal)
      .then((blob) => {
        if (controller.signal.aborted) return;
        if (!blob.type.startsWith("image/"))
          throw new Error("返回的内容不是图片，请下载原文件检查");
        object = URL.createObjectURL(blob);
        setSource(object);
      })
      .catch((failure) => {
        if (!controller.signal.aborted)
          setError((failure as Error).message || "图片加载失败");
      });
    return () => {
      controller.abort();
      if (object) URL.revokeObjectURL(object);
    };
  }, [path, revision]);
  return source && !error ? (
    <img
      src={source}
      alt={alt}
      className={className}
      loading={loading}
      onError={() => setError("图片解码失败，请重试或下载原文件查看")}
    />
  ) : (
    <span
      className={`image-placeholder ${error ? "image-error" : ""} ${className}`}
      role={error ? "group" : "img"}
      aria-label={error ? `${alt || "图片"}加载失败` : `${alt || "图片"}加载中`}
      aria-busy={!error}
    >
      {error ? (
        <>
          <span>图片加载失败</span>
          <small>{error}</small>
          {retryable ? (
            <button
              type="button"
              className="text-button"
              onClick={() => setRevision((value) => value + 1)}
            >
              重新加载图片
            </button>
          ) : (
            <small>打开详情后可重试</small>
          )}
        </>
      ) : (
        <span className="muted">图片加载中…</span>
      )}
    </span>
  );
}
/** Markdown 正文里的图片：本机私有文件走鉴权加载，其余一律降级为文字说明。 */
export function MarkdownImage({ src, alt }: { src?: string; alt?: string }) {
  const path = typeof src === "string" ? src : "";
  if (/^\/files\/[^/?#]+/.test(path))
    return (
      <PrivateImage
        path={path}
        alt={alt || ""}
        className="markdown-image"
        loading="lazy"
      />
    );
  return <span className="muted">[图片：{alt || "参考图片"}]</span>;
}
export function useResource<T>(path: string) {
  const [resource, setResource] = useState<{ path: string; data: T } | null>(
      null,
    ),
    [failure, setFailure] = useState<{ path: string; message: string } | null>(
      null,
    ),
    [revision, setRevision] = useState(0);
  useEffect(() => {
    let alive = true;
    const controller = new AbortController();
    setFailure(null);
    api<T>(path, { signal: controller.signal })
      .then((value) => {
        if (alive) setResource({ path, data: value });
      })
      .catch((error) => {
        if (alive) setFailure({ path, message: error.message });
      });
    return () => {
      alive = false;
      controller.abort();
    };
  }, [path, revision]);
  return {
    data: resource?.path === path ? resource.data : null,
    error: failure?.path === path ? failure.message : "",
    reload: () => setRevision((value) => value + 1),
  };
}
export function ErrorState({
  message,
  retry,
}: {
  message: string;
  retry: () => void;
}) {
  return (
    <div className="error-state" role="alert">
      <CircleAlert size={25} strokeWidth={1.4} aria-hidden="true" />
      <h2>暂时没能读取</h2>
      <p>{message}</p>
      <button className="button secondary" onClick={retry}>
        重新读取 <ArrowUpRight size={16} />
      </button>
    </div>
  );
}
export const date = (value: number) =>
  new Intl.DateTimeFormat("zh-CN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Shanghai",
  }).format(value);
export const size = (bytes: number) =>
  bytes < 1024
    ? `${bytes} B`
    : bytes > 1048576
      ? `${(bytes / 1048576).toFixed(1)} MB`
      : `${Math.max(1, Math.round(bytes / 1024))} KB`;
