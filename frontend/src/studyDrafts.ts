const PREFIX = "xinxin-study-draft:";
const MAX_DRAFT_LENGTH = 8192;
let logoutEpoch = 0;

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
  let storageAvailable = Boolean(storage);
  let epoch = logoutEpoch;
  function refresh() {
    if (epoch !== logoutEpoch) {
      values = {};
      epoch = logoutEpoch;
    }
    if (!storageAvailable) return;
    try {
      const saved: unknown = JSON.parse(storage?.getItem(key) ?? "{}");
      values =
        saved && typeof saved === "object" && !Array.isArray(saved)
          ? Object.fromEntries(
              Object.entries(saved)
                .filter(
                  ([name, value]) =>
                    name.length <= 160 &&
                    typeof value === "string" &&
                    value.length <= MAX_DRAFT_LENGTH,
                )
                .slice(0, 96),
            )
          : {};
    } catch {
      storageAvailable = false;
    }
  }
  function save() {
    try {
      if (Object.keys(values).length)
        storage?.setItem(key, JSON.stringify(values));
      else storage?.removeItem(key);
    } catch {
      storageAvailable = false;
      /* Keep this page's in-memory drafts when storage is unavailable. */
    }
  }
  return {
    read(name: string) {
      refresh();
      return values[name] ?? "";
    },
    write(name: string, value: string) {
      refresh();
      if (value && value.length <= MAX_DRAFT_LENGTH) values[name] = value;
      else delete values[name];
      save();
    },
    clearMatching(name: string, expected: string) {
      refresh();
      if (values[name] !== expected) return false;
      delete values[name];
      save();
      return true;
    },
    clear() {
      refresh();
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
    logoutEpoch += 1;
    const storage = sessionStore();
    try {
      for (const key of Object.keys(storage ?? {}))
        if (key.startsWith(PREFIX)) storage?.removeItem(key);
    } catch {
      /* Optional local draft storage. */
    }
  });
