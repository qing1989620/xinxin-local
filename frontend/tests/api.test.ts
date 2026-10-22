import { beforeEach, describe, expect, it, vi } from "vitest";
vi.mock("@capacitor/core", () => ({
  Capacitor: { isNativePlatform: () => false },
}));
vi.mock("@capacitor/preferences", () => ({
  Preferences: { get: vi.fn(), set: vi.fn() },
}));

function storage() {
  const values = new Map<string, string>();
  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
    removeItem: (key: string) => values.delete(key),
    clear: () => values.clear(),
  };
}
beforeEach(() => {
  vi.restoreAllMocks();
  vi.resetModules();
  vi.unstubAllGlobals();
  vi.stubGlobal("sessionStorage", storage());
  vi.stubGlobal("localStorage", storage());
  vi.stubGlobal("window", new EventTarget());
});

class UploadRequest {
  static instances: UploadRequest[] = [];
  upload: { onprogress?: (event: object) => void } = {};
  headers: Record<string, string> = {};
  timeout = 0;
  status = 200;
  responseText = '{"id":"saved-resource","name":"phone.txt"}';
  onload?: () => void;
  onerror?: () => void;
  onabort?: () => void;
  ontimeout?: () => void;
  open = vi.fn();
  send = vi.fn();
  constructor() {
    UploadRequest.instances.push(this);
  }
  setRequestHeader(key: string, value: string) {
    this.headers[key] = value;
  }
  abort() {
    this.onabort?.();
  }
}

describe("resource uploads", () => {
  it("reports actual transfer progress and preserves the retry identity", async () => {
    vi.stubGlobal("XMLHttpRequest", UploadRequest);
    const { upload, setSession } = await import("../src/api");
    await setSession("private-local-session");
    const progress = vi.fn();
    const pending = upload(new File(["file content"], "phone.txt"), {
      onProgress: progress,
      requestId: "same-retry-id",
    });
    const request = UploadRequest.instances.at(-1)!;
    expect(request.headers["Authorization"]).toBe(
      "Bearer private-local-session",
    );
    expect(request.headers["X-Upload-ID"]).toBe("same-retry-id");
    request.upload.onprogress?.({
      lengthComputable: true,
      loaded: 40,
      total: 100,
    });
    expect(progress).toHaveBeenCalledWith(40, 100);
    request.onload?.();
    expect((await pending).id).toBe("saved-resource");
  });
  it("distinguishes cancellation from server rejection and revokes expired sessions", async () => {
    vi.stubGlobal("XMLHttpRequest", UploadRequest);
    const { upload, setSession, hasSession } = await import("../src/api");
    const controller = new AbortController();
    const pending = upload(new File(["data"], "a.txt"), {
      signal: controller.signal,
    });
    const rejected = expect(pending).rejects.toMatchObject({
      name: "AbortError",
    });
    controller.abort();
    await rejected;
    await setSession("expired");
    const expired = upload(new File(["data"], "a.txt"));
    const expiredCheck = expect(expired).rejects.toMatchObject({
      status: 401,
      message: "请重新登录",
    });
    const request = UploadRequest.instances.at(-1)!;
    request.status = 401;
    request.responseText = '{"detail":"请重新登录"}';
    request.onload?.();
    await expiredCheck;
    expect(hasSession()).toBe(false);
  });
  it("rejects empty and oversized resources before sending", async () => {
    vi.stubGlobal("XMLHttpRequest", UploadRequest);
    const { upload } = await import("../src/api");
    const count = UploadRequest.instances.length;
    await expect(upload(new File([], "empty.txt"))).rejects.toThrow("为空");
    await expect(
      upload({ size: 256 * 1024 * 1024 + 1 } as File),
    ).rejects.toThrow("256 MB");
    expect(UploadRequest.instances.length).toBe(count);
  });
  it("allows HTTP LAN only in the native local-test build", async () => {
    vi.stubEnv("VITE_LOCAL_PHONE_TEST", "1");
    const { Capacitor } = await import("@capacitor/core");
    const native = vi
      .spyOn(Capacitor, "isNativePlatform")
      .mockReturnValue(true);
    const { setServer, isPrivateIPv4 } = await import("../src/api");
    expect(() => setServer("http://192.168.1.12:8000")).not.toThrow();
    expect(() => setServer("http://8.8.8.8:8000")).toThrow("HTTPS");
    native.mockReturnValue(false);
    expect(() => setServer("http://192.168.1.12:8000")).toThrow("HTTPS");
    expect(isPrivateIPv4("10..0.2")).toBe(false);
    expect(isPrivateIPv4("172.32.0.1")).toBe(false);
    expect(isPrivateIPv4("172.16.0.1")).toBe(true);
    vi.unstubAllEnvs();
  });
});

describe("private transport boundaries", () => {
  it("loads authenticated images on WebViews without AbortSignal.any or timeout", async () => {
    vi.spyOn(AbortSignal, "any").mockImplementation(() => {
      throw new Error("unsupported");
    });
    vi.spyOn(AbortSignal, "timeout").mockImplementation(() => {
      throw new Error("unsupported");
    });
    const { getBlob, setSession } = await import("../src/api");
    await setSession("synthetic-image-session");
    vi.stubGlobal(
      "fetch",
      vi.fn(async (_input, options) => {
        expect(options.headers.Authorization).toBe(
          "Bearer synthetic-image-session",
        );
        return new Response("synthetic image bytes", {
          headers: { "Content-Type": "image/png" },
        });
      }),
    );
    const image = await getBlob(
      "/files/image/preview",
      new AbortController().signal,
    );
    expect(image.type).toBe("image/png");
  });
  it("keeps cancellation and timeout active while image response bytes are being read", async () => {
    vi.useFakeTimers();
    try {
      const { getBlob } = await import("../src/api");
      vi.stubGlobal(
        "fetch",
        vi.fn(async (_input, options) => ({
          ok: true,
          blob: () =>
            new Promise((_resolve, reject) => {
              options.signal.addEventListener(
                "abort",
                () => reject(new DOMException("Aborted", "AbortError")),
                { once: true },
              );
            }),
        })),
      );
      const controller = new AbortController();
      const pending = getBlob("/files/image/preview", controller.signal);
      const rejected = expect(pending).rejects.toMatchObject({
        name: "AbortError",
      });
      await Promise.resolve();
      controller.abort();
      await rejected;
      const timeout = getBlob("/files/image/preview");
      const expired = expect(timeout).rejects.toThrow("连接超时");
      await vi.advanceTimersByTimeAsync(30001);
      await expired;
    } finally {
      vi.useRealTimers();
    }
  });
  it("uses bounded previews and falls back only when the preview route is absent", async () => {
    const { loadPrivateImage } = await import("../src/privateImages");
    const path = `/files/${"a".repeat(32)}/download?inline=true`;
    const request = vi.fn(async (input: string) =>
      input.endsWith("/preview")
        ? new Response('{"detail":"Not Found"}', { status: 404 })
        : new Response("image", { headers: { "Content-Type": "image/png" } }),
    );
    vi.stubGlobal("fetch", request);
    expect(
      (await loadPrivateImage(path, new AbortController().signal)).type,
    ).toBe("image/png");
    expect(request.mock.calls.map(([input]) => input)).toEqual([
      `/api/v1/files/${"a".repeat(32)}/preview`,
      `/api/v1${path}`,
    ]);
  });
  it("continues the selected run with a fresh budget and a stable retry identity", async () => {
    const { submitAgentRun } = await import("../src/runSubmission");
    const bodies: any[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string, options?: RequestInit) => {
        if (input.endsWith("/settings"))
          return new Response(
            JSON.stringify({
              model_configured: true,
              capabilities: { run_continuation: true, run_token_budget: true },
              execution_limits: {
                max_calls: 128,
                max_seconds: 7200,
                max_total_tokens: 100000000,
              },
            }),
          );
        expect(input).toContain("/runs/parent/continue");
        bodies.push(JSON.parse(String(options?.body)));
        return new Response('{"id":"continued-run"}');
      }),
    );
    const payload = {
      task: "only finish remaining work",
      conversation_id: "same-conversation",
      resume_run_id: "parent",
      permission: "read",
      server_id: null,
      max_calls: 64,
      max_seconds: 3600,
      max_total_tokens: 8000000,
      allow_memory: false,
      file_ids: [],
    };
    await submitAgentRun(payload);
    await submitAgentRun(payload);
    expect(bodies[0]).toEqual(bodies[1]);
    expect(bodies[0].instruction).toBe(payload.task);
    expect(bodies[0].permission).toBe("read");
    expect(bodies[0].max_calls).toBe(64);
    expect(bodies[0]).not.toHaveProperty("conversation_id");
    expect(bodies[0]).not.toHaveProperty("task");
    expect(bodies[0]).not.toHaveProperty("resume_run_id");
  });
  it("does not replace continuation with an unrelated new task on an old backend", async () => {
    const { submitAgentRun } = await import("../src/runSubmission");
    const request = vi.fn(
      async () => new Response('{"model_configured":true}'),
    );
    vi.stubGlobal("fetch", request);
    await expect(
      submitAgentRun({
        task: "",
        conversation_id: "conversation",
        resume_run_id: "parent",
        permission: "read",
        server_id: null,
        max_calls: 8,
        max_seconds: 300,
        allow_memory: false,
        file_ids: [],
      }),
    ).rejects.toThrow("不支持一键续接");
    expect(request).toHaveBeenCalledTimes(1);
  });
  it.each([80000, 300000, 1048576])(
    "sends the selected %i context independently from the cumulative token budget",
    async (tier) => {
      const { setSession } = await import("../src/api");
      const { submitAgentRun } = await import("../src/runSubmission");
      await setSession("local-test");
      vi.stubGlobal(
        "fetch",
        vi.fn(async (input: string, options?: RequestInit) => {
          if (input.endsWith("/settings"))
            return new Response(
              JSON.stringify({
                model_configured: true,
                capabilities: { context_tiers: true, run_token_budget: true },
                execution_limits: {
                  max_calls: 128,
                  max_seconds: 7200,
                  max_total_tokens: 100000000,
                },
              }),
            );
          const sent = JSON.parse(String(options?.body));
          expect(sent.context_window_tokens).toBe(tier);
          expect(sent.max_total_tokens).toBe(8000000);
          return new Response('{"id":"tier-accepted"}');
        }),
      );
      expect(
        (
          await submitAgentRun({
            task: "synthetic",
            conversation_id: null,
            server_id: null,
            permission: "read",
            max_calls: 64,
            max_seconds: 3600,
            max_total_tokens: 8000000,
            context_window_tokens: tier,
            allow_memory: false,
            file_ids: [],
          })
        ).id,
      ).toBe("tier-accepted");
    },
  );
  it("does not silently omit a context choice when connected to an old server", async () => {
    const { submitAgentRun } = await import("../src/runSubmission");
    const request = vi.fn(
      async () => new Response('{"model_configured":true}'),
    );
    vi.stubGlobal("fetch", request);
    await expect(
      submitAgentRun({
        task: "synthetic",
        conversation_id: null,
        server_id: null,
        permission: "read",
        max_calls: 8,
        max_seconds: 300,
        context_window_tokens: 80000,
        allow_memory: false,
        file_ids: [],
      }),
    ).rejects.toThrow("不支持会话上下文档位");
    expect(request).toHaveBeenCalledTimes(1);
  });
  it("recovers the terminal state when the event stream ends before finished", async () => {
    const { watchRun, setSession } = await import("../src/api");
    await setSession("local-test");
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async (input: string) =>
          new Response(
            input.includes("/events")
              ? "event: end\ndata: {}\n\n"
              : '{"id":"task","status":"cancelled"}',
          ),
      ),
    );
    const snapshot = vi.fn();
    await watchRun(
      "task",
      () => {},
      new AbortController().signal,
      undefined,
      snapshot,
    );
    expect(snapshot).toHaveBeenCalledWith({ id: "task", status: "cancelled" });
  });
  it("reports validation fields without echoing inputs or unknown field names", async () => {
    const { post, setSession } = await import("../src/api");
    await setSession("local-test");
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              detail: [
                {
                  loc: ["body", "max_total_tokens"],
                  type: "extra_forbidden",
                  input: "private-input",
                  msg: "private-input",
                },
                {
                  loc: ["body", "private-field-name"],
                  type: "value_error",
                  ctx: { private: "private-input" },
                },
              ],
            }),
            { status: 422 },
          ),
      ),
    );
    const error = await post("/runs", {}).catch((error: Error) => error);
    expect(error.message).toContain("累计令牌预算");
    expect(error.message).toContain("前后端版本");
    expect(error.message).not.toContain("private-input");
    expect(error.message).not.toContain("private-field-name");
  });
  it("submits the supported legacy fields to an older backend", async () => {
    const { setSession } = await import("../src/api");
    const { submitAgentRun } = await import("../src/runSubmission");
    await setSession("local-test");
    const request = vi.fn(async (input: string, options?: RequestInit) => {
      if (input.endsWith("/settings"))
        return new Response('{"model":"offline","model_configured":true}');
      expect(JSON.parse(String(options?.body))).not.toHaveProperty(
        "max_total_tokens",
      );
      return new Response('{"id":"legacy-accepted"}');
    });
    vi.stubGlobal("fetch", request);
    const result = await submitAgentRun({
      task: "synthetic",
      conversation_id: null,
      server_id: null,
      permission: "read",
      max_calls: 8,
      max_seconds: 300,
      allow_memory: false,
      file_ids: [],
    });
    expect(result.id).toBe("legacy-accepted");
    expect(request).toHaveBeenCalledTimes(2);
  });
  it("honors explicit token budgets when the backend advertises support", async () => {
    const { setSession } = await import("../src/api");
    const { submitAgentRun } = await import("../src/runSubmission");
    await setSession("local-test");
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string, options?: RequestInit) => {
        if (input.endsWith("/settings"))
          return new Response(
            '{"model":"offline","model_configured":true,"capabilities":{"run_token_budget":true}}',
          );
        expect(JSON.parse(String(options?.body)).max_total_tokens).toBe(80000);
        return new Response('{"id":"new-accepted"}');
      }),
    );
    const result = await submitAgentRun({
      task: "synthetic",
      conversation_id: null,
      server_id: null,
      permission: "read",
      max_calls: 4,
      max_seconds: 120,
      max_total_tokens: 80000,
      allow_memory: false,
      file_ids: [],
    });
    expect(result.id).toBe("new-accepted");
  });
  it("does not silently drop an explicit budget if the backend was rolled back", async () => {
    const { setSession } = await import("../src/api");
    const { submitAgentRun } = await import("../src/runSubmission");
    await setSession("local-test");
    const request = vi.fn(
      async () => new Response('{"model":"offline","model_configured":true}'),
    );
    vi.stubGlobal("fetch", request);
    await expect(
      submitAgentRun({
        task: "synthetic",
        conversation_id: null,
        server_id: null,
        permission: "read",
        max_calls: 4,
        max_seconds: 120,
        max_total_tokens: 5000,
        allow_memory: false,
        file_ids: [],
      }),
    ).rejects.toThrow("不支持自定义令牌预算");
    expect(request).toHaveBeenCalledTimes(1);
  });
  it("replays progress separately and preserves final Markdown across reconnects", async () => {
    const { setSession, watchRun } = await import("../src/api");
    const { nextAssistantText } = await import("../src/runText");
    await setSession("local-test");
    const final = "检查完成。\n\n```text\n/demo\n```\n\n- 已核对";
    const frame = (seq: number, kind: string, text: string) =>
      `id: ${seq}\ndata: ${JSON.stringify({ seq, kind, data: { text } })}\n\n`;
    const progress: string[] = [];
    let draft = "",
      streams = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string) => {
        if (!input.includes("/events"))
          return new Response('{"status":"running"}');
        streams++;
        if (streams === 2) expect(input).toContain("after=2");
        const content =
          streams === 1
            ? frame(1, "delta", "我先看看。") +
              frame(2, "assistant.progress", "我先看看。")
            : frame(3, "delta", final.slice(0, 8)) +
              frame(2, "assistant.progress", "我先看看。") +
              frame(4, "delta", final.slice(8)) +
              "event: end\ndata: {}\n\n";
        return new Response(content);
      }),
    );
    await watchRun(
      "task",
      (event) => {
        draft = nextAssistantText(draft, event);
        if (event.kind === "assistant.progress") progress.push(event.data.text);
      },
      new AbortController().signal,
    );
    expect(progress).toEqual(["我先看看。"]);
    expect(draft).toBe(final);
    expect(streams).toBe(2);
  });
  it("does not restore a native credential from a different backend even if preference clearing is unfinished", async () => {
    const { Capacitor } = await import("@capacitor/core");
    vi.spyOn(Capacitor, "isNativePlatform").mockReturnValue(true);
    const { Preferences } = await import("@capacitor/preferences");
    vi.mocked(Preferences.get).mockImplementation(async ({ key }) => ({
      value:
        key === "session"
          ? "previous-server-token"
          : "https://previous.example",
    }));
    const { setServer, restoreSession, hasSession } =
      await import("../src/api");
    setServer("https://new.example");
    await restoreSession();
    expect(hasSession()).toBe(false);
  });
  it("removes the previous server token before contacting a different server", async () => {
    const { setSession, setServer, api } = await import("../src/api");
    await setSession("old-server-secret");
    setServer("https://another.example");
    const fetch = vi
      .fn()
      .mockResolvedValue(
        new Response("{}", { headers: { "content-type": "application/json" } }),
      );
    vi.stubGlobal("fetch", fetch);
    await api("/auth/status");
    expect(
      new Headers(fetch.mock.calls[0][1].headers).has("Authorization"),
    ).toBe(false);
    expect(() => setServer("http://remote.example")).toThrow("HTTPS");
    expect(() => setServer("https://owner:password@example.com")).toThrow();
  });
  it("reuses an uncertain submission identity across a page reload and distinguishes changed work", async () => {
    const first = await import("../src/api");
    const key = await first.stableRequestKey("agent", {
      task: "部署",
      permission: "read",
    });
    vi.resetModules();
    const restored = await import("../src/api");
    expect(
      await restored.stableRequestKey("agent", {
        task: "部署",
        permission: "read",
      }),
    ).toBe(key);
    expect(
      await restored.stableRequestKey("agent", {
        task: "部署",
        permission: "full",
      }),
    ).not.toBe(key);
    restored.acknowledgeRequest("agent");
    expect(sessionStorage.getItem("xinxin-request:agent")).toBe(null);
  });
  it("decodes fragmented UTF-8 events and reconnects from the last accepted cursor without duplication", async () => {
    const { setSession, watchRun } = await import("../src/api");
    await setSession("local-test");
    const encoder = new TextEncoder(),
      seen: string[] = [];
    const event = (seq: number, text: string) =>
      `id: ${seq}\ndata: ${JSON.stringify({ seq, kind: "delta", data: { text } })}\n\n`;
    let streams = 0;
    const fetch = vi.fn(async (input: string) => {
      if (!input.includes("/events"))
        return new Response('{"status":"running"}');
      streams++;
      if (streams === 2) expect(input).toContain("after=1");
      const bytes = encoder.encode(
        streams === 1
          ? event(1, "你好")
          : event(1, "你好") + event(2, "完成") + "event: end\ndata: {}\n\n",
      );
      return new Response(
        new ReadableStream({
          start(controller) {
            for (let i = 0; i < bytes.length; i += 3)
              controller.enqueue(bytes.slice(i, i + 3));
            controller.close();
          },
        }),
      );
    });
    vi.stubGlobal("fetch", fetch);
    await watchRun(
      "task",
      (item) => seen.push(item.data.text),
      new AbortController().signal,
    );
    expect(seen).toEqual(["你好", "完成"]);
    expect(streams).toBe(2);
  });
  it("skips a malformed event and keeps the rest of the stream flowing", async () => {
    const { setSession, watchRun } = await import("../src/api");
    await setSession("local-test");
    const seen: string[] = [];
    const event = (seq: number, text: string) =>
      `id: ${seq}\ndata: ${JSON.stringify({ seq, kind: "delta", data: { text } })}\n\n`;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string) =>
        new Response(
          input.includes("/events")
            ? event(1, "开始") +
                'id: 2\ndata: {"seq":2,"kind":"delta","data":{"text":"截断\n\n' +
                event(3, "继续") +
                "event: end\ndata: {}\n\n"
            : '{"status":"running"}',
        ),
      ),
    );
    await watchRun(
      "task",
      (item) => seen.push(item.data.text),
      new AbortController().signal,
    );
    expect(seen).toEqual(["开始", "继续"]);
  });
});
