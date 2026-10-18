import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { Check, FileUp, RotateCcw, X } from "lucide-react";
import { getServer, upload, type FileItem } from "./api";
import { size } from "./ui";
import "./uploads.css";

type Entry = {
  id: string;
  file: File;
  server: string;
  state: "queued" | "uploading" | "completed" | "failed" | "cancelled";
  sent: number;
  total: number;
  error?: string;
  result?: FileItem;
};
type Queue = {
  entries: Entry[];
  add: (files: File[]) => string[];
  cancel: (id: string) => void;
  retry: (id: string) => void;
  clear: () => void;
};
const Context = createContext<Queue | null>(null);

export function UploadProvider({ children }: { children: ReactNode }) {
  const [entries, setEntries] = useState<Entry[]>([]);
  const current = useRef(entries),
    running = useRef(new Map<string, AbortController>());
  function change(transform: (old: Entry[]) => Entry[]) {
    current.current = transform(current.current);
    setEntries(current.current);
  }
  function update(id: string, patch: Partial<Entry>) {
    change((old) =>
      old.map((entry) => (entry.id === id ? { ...entry, ...patch } : entry)),
    );
  }
  useEffect(() => {
    const reset = () => {
      running.current.forEach((controller) => controller.abort());
      change(() => []);
    };
    window.addEventListener("xinxin-unauthorized", reset);
    window.addEventListener("xinxin-session-cleared", reset);
    return () => {
      window.removeEventListener("xinxin-unauthorized", reset);
      window.removeEventListener("xinxin-session-cleared", reset);
      running.current.forEach((controller) => controller.abort());
    };
  }, []);
  useEffect(() => {
    const pending = current.current
      .filter((entry) => entry.state === "queued")
      .slice(0, Math.max(0, 2 - running.current.size));
    for (const entry of pending) {
      if (entry.server !== getServer()) {
        update(entry.id, {
          state: "cancelled",
          error: "后端地址已切换，请重新选择文件",
        });
        continue;
      }
      const controller = new AbortController();
      running.current.set(entry.id, controller);
      update(entry.id, { state: "uploading", error: "" });
      void upload(entry.file, {
        signal: controller.signal,
        requestId: entry.id,
        onProgress: (sent, total) => update(entry.id, { sent, total }),
      })
        .then((result) => {
          if (!controller.signal.aborted)
            update(entry.id, {
              state: "completed",
              result,
              sent: entry.file.size,
              total: entry.file.size,
            });
        })
        .catch((error: Error) => {
          update(entry.id, {
            state: controller.signal.aborted ? "cancelled" : "failed",
            error: controller.signal.aborted
              ? "已取消传输；若响应丢失，资源可能已保存，可查看资源库或重试"
              : error.message,
          });
        })
        .finally(() => {
          running.current.delete(entry.id);
          change((old) => [...old]);
        });
    }
  }, [entries]);
  const value: Queue = {
    entries,
    add(files) {
      const added = files
        .slice(0, Math.max(0, 50 - current.current.length))
        .map((file): Entry => ({
          id: crypto.randomUUID(),
          file,
          server: getServer(),
          state: "queued",
          sent: 0,
          total: file.size,
        }));
      change((old) => [...old, ...added]);
      return added.map((entry) => entry.id);
    },
    cancel(id) {
      running.current.get(id)?.abort();
      update(id, {
        state: "cancelled",
        error: "已取消传输；可重新上传，或先查看资源库",
      });
    },
    retry(id) {
      if (!running.current.has(id))
        update(id, { state: "queued", error: "", sent: 0 });
    },
    clear() {
      change((old) =>
        old.filter((entry) => ["queued", "uploading"].includes(entry.state)),
      );
    },
  };
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function useUploads() {
  const value = useContext(Context);
  if (!value) throw new Error("UploadProvider is missing");
  return value;
}
export function UploadQueue({ ids }: { ids?: string[] }) {
  const { entries, retry, cancel, clear } = useUploads();
  const visible = entries.filter((entry) => !ids || ids.includes(entry.id));
  if (!visible.length) return null;
  const labels = {
    queued: "等待上传",
    uploading: "正在上传",
    completed: "已保存",
    failed: "上传失败",
    cancelled: "已取消",
  };
  return (
    <section className="upload-queue" aria-label="资源上传队列">
      <header>
        <span>
          <FileUp size={16} />
          上传队列 ·{" "}
          {visible.filter((entry) => entry.state === "completed").length}/
          {visible.length}
        </span>
        {!ids && (
          <button className="text-button" onClick={clear}>
            清除已结束记录
          </button>
        )}
      </header>
      {visible.map((entry) => {
        const percent = entry.total
          ? Math.min(100, Math.round((entry.sent / entry.total) * 100))
          : 0;
        const pending = ["uploading", "queued"].includes(entry.state);
        return (
          <article className={`upload-entry ${entry.state}`} key={entry.id}>
            <div className="upload-entry-body">
              <strong>{entry.file.name}</strong>
              <small>
                {size(entry.file.size)} ·{" "}
                {entry.state === "uploading" && percent === 100
                  ? "传输完成，正在保存与提取正文…"
                  : labels[entry.state]}
                {entry.state === "uploading" && percent < 100
                  ? ` ${percent}%`
                  : ""}
              </small>
              {pending && (
                <progress
                  value={entry.sent}
                  max={entry.total || 1}
                  aria-label={`${entry.file.name} 上传进度`}
                />
              )}
              {entry.error && <p role="status">{entry.error}</p>}
              {entry.result?.parse_error && <p>{entry.result.parse_error}</p>}
            </div>
            {entry.state === "completed" ? (
              <Check size={17} aria-label="上传成功" />
            ) : pending ? (
              <button
                className="icon-button"
                aria-label={`取消上传 ${entry.file.name}`}
                onClick={() => cancel(entry.id)}
              >
                <X size={17} />
              </button>
            ) : (
              <button
                className="icon-button"
                aria-label={`重试上传 ${entry.file.name}`}
                onClick={() => retry(entry.id)}
              >
                <RotateCcw size={17} />
              </button>
            )}
          </article>
        );
      })}
      <p className="upload-note">
        上传到当前连接的后端，仅登录后可访问。应用内切换页面仍会继续，请保持应用打开直至完成。队列最多保留
        50 项。
      </p>
    </section>
  );
}
