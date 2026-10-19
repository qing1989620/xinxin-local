// 安全解析 JSON 文本：空值或脏数据（旧记录、截断的 SSE 事件）一律返回兜底值，
// 不向上抛异常，避免单个坏字段拖垮整页渲染。
export function parseJson<T>(text: string | null | undefined, fallback: T): T {
  if (!text) return fallback;
  try {
    const value = JSON.parse(text) as T;
    return value ?? fallback;
  } catch {
    return fallback;
  }
}
