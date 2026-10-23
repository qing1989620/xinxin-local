const PREFIX = "xinxin-study-draft:";
const MAX_DRAFT_LENGTH = 8192;

function sessionStore(): Storage | null {
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

export function createStudyDrafts(sessionId: string, storage = sessionStore()) {
  const key = PREFIX + sessionId;
  let values: Record<string, string> = {};
  try {
    const saved: unknown = JSON.parse(storage?.getItem(key) ?? "{}");
    if (saved && typeof saved === "object" && !Array.isArray(saved))
      values = Object.fromEntries(
        Object.entries(saved)
          .filter(
            ([name, value]) =>
              name.length <= 160 &&
              typeof value === "string" &&
              value.length <= MAX_DRAFT_LENGTH,
          )
          .slice(0, 96),
      );
  } catch {
    /* A damaged or unavailable browser cache must not block practice. */
  }
  function save() {
    try {
      if (Object.keys(values).length)
        storage?.setItem(key, JSON.stringify(values));
      else storage?.removeItem(key);
    } catch {
      /* Keep this page's in-memory drafts when storage is unavailable. */
    }
  }
  return {
    read(name: string) {
      return values[name] ?? "";
    },
    write(name: string, value: string) {
      if (value && value.length <= MAX_DRAFT_LENGTH) values[name] = value;
      else delete values[name];
      save();
    },
    clear() {
      values = {};
      save();
    },
  };
}

export function fillDraftValues(draft: string, count: number) {
  let parts: string[] = [];
  try {
    const parsed: unknown = JSON.parse(draft);
    if (
      Array.isArray(parsed) &&
      parsed.every((value) => typeof value === "string")
    )
      parts = parsed;
  } catch {
    /* Legacy drafts are unstructured text. */
  }
  if (!parts.length && draft)
    parts = count === 1 ? [draft] : draft.split(/[;；|,，、]/);
  return Array.from({ length: count }, (_, index) => parts[index] ?? "");
}

if (typeof window !== "undefined")
  window.addEventListener("xinxin-session-cleared", () => {
    const storage = sessionStore();
    try {
      for (const key of Object.keys(storage ?? {}))
        if (key.startsWith(PREFIX)) storage?.removeItem(key);
    } catch {
      /* Optional local draft storage. */
    }
  });
