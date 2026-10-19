import { Capacitor } from "@capacitor/core";
import { Preferences } from "@capacitor/preferences";

export type FileItem = {
  id: string;
  name: string;
  mime: string;
  size: number;
  indexed: boolean;
  created: number;
  run_id?: string;
  parse_error?: string;
};
export type Run = {
  id: string;
  conversation_id: string;
  task: string;
  status: string;
  permission: string;
  server_id?: string;
  result: string;
  error: string;
  created: number;
  updated: number;
  usage: string;
  files?: FileItem[];
  max_calls?: number;
  max_seconds?: number;
  max_total_tokens?: number;
  context_window_tokens?: number | null;
  allow_memory?: boolean | number;
  resume_of?: string | null;
};
export type RecordItem = {
  id: string;
  kind: string;
  payload: Record<string, any>;
  created: number;
  updated: number;
};
export type EventItem = {
  run_id: string;
  seq: number;
  kind: string;
  data: Record<string, any>;
  created: number;
};
export type ServerItem = {
  id: string;
  name: string;
  host: string;
  port: number;
  username: string;
  workdir: string;
  host_key: string;
  key_configured: boolean;
};

let token = sessionStorage.getItem("xinxin-session") || "";
let base =
  localStorage.getItem("xinxin-server") || import.meta.env.VITE_API_BASE || "";

export async function restoreSession() {
  if (Capacitor.isNativePlatform()) {
    const [session, origin] = await Promise.all([
      Preferences.get({ key: "session" }),
      Preferences.get({ key: "session-origin" }),
    ]);
    token = origin.value === base ? session.value || "" : "";
  }
}
export async function setSession(value: string) {
  token = value;
  if (value) sessionStorage.setItem("xinxin-session", value);
  else sessionStorage.removeItem("xinxin-session");
  if (!value) window.dispatchEvent(new Event("xinxin-session-cleared"));
  if (Capacitor.isNativePlatform())
    await Promise.all([
      Preferences.set({ key: "session", value }),
      Preferences.set({ key: "session-origin", value: base }),
    ]);
}
export const hasSession = () => Boolean(token);
export const getServer = () => base;
export function isPrivateIPv4(hostname: string) {
  if (!/^\d{1,3}(\.\d{1,3}){3}$/.test(hostname)) return false;
  const parts = hostname.split(".").map(Number);
  return (
    parts.length === 4 &&
    parts.every((part) => Number.isInteger(part) && part >= 0 && part <= 255) &&
    (parts[0] === 10 ||
      (parts[0] === 192 && parts[1] === 168) ||
      (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31))
  );
}
export function setServer(value: string) {
  const trimmed = value.trim().replace(/\/+$/, "");
  if (trimmed) {
    const url = new URL(trimmed);
    if (
      !["http:", "https:"].includes(url.protocol) ||
      url.username ||
      url.password ||
      url.search ||
      url.hash
    )
      throw new Error("请输入完整的 HTTP(S) 服务地址");
    if (
      url.protocol === "http:" &&
      !["localhost", "127.0.0.1", "[::1]"].includes(url.hostname) &&
      !(
        import.meta.env.VITE_LOCAL_PHONE_TEST === "1" &&
        Capacitor.isNativePlatform() &&
        isPrivateIPv4(url.hostname)
      )
    )
      throw new Error("远程连接请使用 HTTPS 地址");
  }
  void setSession("");
  base = trimmed;
  if (base) localStorage.setItem("xinxin-server", base);
  else localStorage.removeItem("xinxin-server");
}
export const url = (path: string) => `${base}/api/v1${path}`;

// Retain the request identity after an uncertain network response, including reloads.
export async function stableRequestKey(namespace: string, payload: unknown) {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(JSON.stringify(payload)),
  );
  const fingerprint = Array.from(new Uint8Array(digest), (value) =>
    value.toString(16).padStart(2, "0"),
  ).join("");
  const storageKey = `xinxin-request:${namespace}`;
  let previous: { fingerprint: string; key: string } | null = null;
  try {
    previous = JSON.parse(sessionStorage.getItem(storageKey) || "null");
  } catch {
    /* Discard malformed local state. */
  }
  if (previous?.fingerprint === fingerprint) return previous.key;
  const key = crypto.randomUUID();
  sessionStorage.setItem(storageKey, JSON.stringify({ fingerprint, key }));
  return key;
}
export function acknowledgeRequest(namespace: string) {
  sessionStorage.removeItem(`xinxin-request:${namespace}`);
}

async function timedFetch<T>(
  input: string,
  options: RequestInit,
  read: (response: Response) => Promise<T>,
) {
  // Older Android WebViews support AbortController but not AbortSignal.any.
  const controller = new AbortController();
  let expired = false;
  const cancel = () => controller.abort();
  const timer = setTimeout(() => {
    expired = true;
    controller.abort();
  }, 30000);
  if (options.signal?.aborted) cancel();
  else options.signal?.addEventListener("abort", cancel, { once: true });
  try {
    const response = await fetch(input, {
      ...options,
      signal: controller.signal,
    });
    return await read(response);
  } catch (error) {
    if (expired) throw new Error("连接超时，请检查后端地址和网络后重试");
    throw error;
  } finally {
    clearTimeout(timer);
    options.signal?.removeEventListener("abort", cancel);
  }
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
async function responseError(response: Response): Promise<never> {
  if (response.status === 401) {
    await setSession("");
    window.dispatchEvent(new Event("xinxin-unauthorized"));
  }
  const data = await response.json().catch(() => null);
  const detail = data?.detail;
  throw new ApiError(
    typeof detail === "string"
      ? detail
      : response.status === 422
        ? validationMessage(detail)
        : `请求失败 (${response.status})`,
    response.status,
  );
}

function validationMessage(detail: unknown): string {
  if (!Array.isArray(detail))
    return "提交内容未通过校验，请检查任务和执行参数。";
  const fields: Record<string, string> = {
    task: "任务内容",
    max_calls: "模型调用次数",
    max_seconds: "执行时间",
    max_total_tokens: "累计令牌预算",
    context_window_tokens: "上下文档位",
    file_ids: "附件",
    request_key: "请求标识",
    server_id: "目标服务器",
    conversation_id: "对话",
    permission: "权限等级",
    allow_memory: "记忆授权",
    name: "名称",
    password: "密码",
    email: "邮箱",
    host: "服务器地址",
    port: "端口",
    username: "登录名",
    model: "模型名称",
    model_url: "模型地址",
    model_api_key: "模型密钥",
  };
  return (
    detail
      .slice(0, 4)
      .map((issue) => {
        const field = Array.isArray(issue?.loc)
          ? issue.loc.find(
              (part: unknown) =>
                typeof part === "string" &&
                Object.prototype.hasOwnProperty.call(fields, part),
            )
          : undefined;
        const label = field ? fields[field] : "提交内容";
        return issue?.type === "extra_forbidden"
          ? `${label}：当前后端不支持该字段，请确认前后端版本一致。`
          : `${label}：格式、长度或范围不符合要求。`;
      })
      .join("\n") || "提交内容未通过校验，请检查任务和执行参数。"
  );
}

export async function api<T = any>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  return timedFetch<T>(url(path), { ...options, headers }, async (response) => {
    if (!response.ok) return responseError(response);
    return response.json();
  });
}
export const post = <T = any>(path: string, data: any) =>
  api<T>(path, { method: "POST", body: JSON.stringify(data) });
export const put = <T = any>(path: string, data: any) =>
  api<T>(path, { method: "PUT", body: JSON.stringify(data) });
export const remove = (path: string) => api(path, { method: "DELETE" });
export const MAX_UPLOAD_BYTES = 64 * 1024 * 1024;
export async function upload(
  file: File,
  options: {
    signal?: AbortSignal;
    onProgress?: (sent: number, total: number) => void;
    requestId?: string;
  } = {},
): Promise<FileItem> {
  if (!file.size) throw new Error("文件为空");
  if (file.size > MAX_UPLOAD_BYTES) throw new Error("单个文件最多 64 MB");
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    const abort = () => request.abort();
    const cleanup = () => options.signal?.removeEventListener("abort", abort);
    request.open("POST", url("/files"));
    request.timeout = 180000;
    if (token) request.setRequestHeader("Authorization", `Bearer ${token}`);
    request.setRequestHeader(
      "X-Upload-ID",
      options.requestId || crypto.randomUUID(),
    );
    request.upload.onprogress = (event) => {
      if (event.lengthComputable)
        options.onProgress?.(event.loaded, event.total);
    };
    request.onerror = () => {
      cleanup();
      reject(new Error("上传连接中断，请检查网络后重试"));
    };
    request.ontimeout = () => {
      cleanup();
      reject(new Error("上传超时，可在当前队列中重试"));
    };
    request.onabort = () => {
      cleanup();
      reject(new DOMException("上传已取消", "AbortError"));
    };
    request.onload = async () => {
      cleanup();
      try {
        const response = new Response(request.responseText, {
          status: request.status,
        });
        if (request.status < 200 || request.status >= 300)
          await responseError(response);
        resolve(await response.json());
      } catch (error) {
        reject(error);
      }
    };
    if (options.signal?.aborted) {
      reject(new DOMException("上传已取消", "AbortError"));
      return;
    }
    options.signal?.addEventListener("abort", abort, { once: true });
    const body = new FormData();
    body.append("file", file);
    request.send(body);
  });
}
export async function getBlob(path: string, signal?: AbortSignal) {
  return timedFetch(
    url(path),
    {
      headers: { Authorization: `Bearer ${token}` },
      signal,
    },
    async (response) => {
      if (!response.ok) return responseError(response);
      return response.blob();
    },
  );
}
export async function download(file: FileItem) {
  const blob = await getBlob(`/files/${file.id}/download`);
  return saveBlob(blob, file.name, file.id);
}
export async function saveBlob(
  blob: Blob,
  filename: string,
  id: string = crypto.randomUUID(),
) {
  if (Capacitor.isNativePlatform()) {
    const [{ Filesystem, Directory }, { Share }] = await Promise.all([
      import("@capacitor/filesystem"),
      import("@capacitor/share"),
    ]);
    const encoded = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onerror = () => reject(new Error("无法读取下载文件"));
      reader.onload = () => resolve(String(reader.result).split(",")[1]);
      reader.readAsDataURL(blob);
    });
    const name = filename.replace(/[^\p{L}\p{N}_.-]/gu, "_");
    const saved = await Filesystem.writeFile({
      path: `exports/${id}-${name}`,
      data: encoded,
      directory: Directory.Cache,
      recursive: true,
    });
    await Share.share({
      title: filename,
      files: [saved.uri],
      dialogTitle: "保存或打开文件",
    });
    return;
  }
  const object = URL.createObjectURL(blob),
    link = document.createElement("a");
  link.href = object;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(object), 1000);
}

export async function watchRun(
  id: string,
  onEvent: (event: EventItem) => void,
  signal: AbortSignal,
  onConnection?: (state: string) => void,
  onSnapshot?: (run: Run) => void,
) {
  let cursor = 0,
    delay = 500,
    sawFinished = false;
  while (!signal.aborted) {
    try {
      const response = await fetch(url(`/runs/${id}/events?after=${cursor}`), {
        headers: { Authorization: `Bearer ${token}` },
        signal,
      });
      if (!response.ok) await responseError(response);
      if (!response.body) throw new Error("浏览器不支持事件流");
      onConnection?.("connected");
      delay = 500;
      const reader = response.body!.getReader(),
        decoder = new TextDecoder();
      let buffer = "";
      while (!signal.aborted) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true }).replace(/\r/g, "");
        let boundary;
        while ((boundary = buffer.indexOf("\n\n")) >= 0) {
          const block = buffer.slice(0, boundary);
          buffer = buffer.slice(boundary + 2);
          if (block.includes("event: end")) {
            if (!sawFinished && onSnapshot)
              onSnapshot(await api<Run>(`/runs/${id}`));
            return;
          }
          const text = block
            .split("\n")
            .filter((line) => line.startsWith("data:"))
            .map((line) => line.slice(5).trimStart())
            .join("\n");
          if (!text) continue;
          let event: EventItem;
          try {
            event = JSON.parse(text) as EventItem;
            if (!event || typeof event !== "object") continue;
          } catch {
            // 单条脏事件（截断的 JSON、网关注入的杂项）不应中断整个任务流：
            // 跳过即可，游标不前进，断线重连后后端会按游标补发完整事件。
            continue;
          }
          if (event.seq > cursor) {
            cursor = event.seq;
            if (event.kind === "finished") sawFinished = true;
            onEvent(event);
          }
        }
      }
      const run = await api<Run>(`/runs/${id}`);
      onSnapshot?.(run);
      if (!["queued", "running", "cancelling"].includes(run.status)) return;
    } catch (error) {
      if (signal.aborted) return;
      if (!hasSession()) throw error;
    }
    onConnection?.("reconnecting");
    await new Promise<void>((resolve) => {
      const finish = () => {
        clearTimeout(timer);
        signal.removeEventListener("abort", finish);
        resolve();
      };
      const timer = setTimeout(finish, delay);
      signal.addEventListener("abort", finish, { once: true });
    });
    delay = Math.min(delay * 2, 10000);
  }
}
