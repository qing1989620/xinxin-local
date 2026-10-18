// 按服务地址和主人记住"最近打开的对话"。
// 重新打开应用、刷新页面或从手机壳冷启动时，继续回到那段对话。
// 记忆只写本机 localStorage，不随任何请求发送，也不包含对话内容。

const STORAGE_KEY = "xinxin-conversation-location";

type Remembered = {
  origin: string;
  name: string;
  conversation_id: string | null;
};

function read(): Remembered | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const value = JSON.parse(raw) as Partial<Remembered> | null;
    if (typeof value?.origin !== "string" || typeof value?.name !== "string")
      return null;
    return {
      origin: value.origin,
      name: value.name,
      conversation_id:
        typeof value.conversation_id === "string"
          ? value.conversation_id
          : null,
    };
  } catch {
    return null;
  }
}

function write(value: Remembered): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
  } catch {
    // 隐私模式或存储被禁用时静默降级：仅失去"继续上次对话"的便利。
  }
}

// 登录后调用：服务地址或主人发生变化时，丢弃属于其他后端的记忆。
export async function configureConversationLocation(
  origin: string,
  name: string,
): Promise<void> {
  const current = read();
  if (current && current.origin === origin && current.name === name) return;
  write({ origin, name, conversation_id: null });
}

// 记录当前对话；传入 null 表示新对话。
export function rememberConversation(id: string | null): void {
  const current = read();
  if (!current || current.conversation_id === id) return;
  write({ ...current, conversation_id: id });
}

export function rememberedConversation(): string | null {
  return read()?.conversation_id ?? null;
}

// 对话被永久删除或对当前后端不可用时，清除对应记忆。
export function forgetConversation(id: string): void {
  const current = read();
  if (!current || current.conversation_id !== id) return;
  write({ ...current, conversation_id: null });
}
