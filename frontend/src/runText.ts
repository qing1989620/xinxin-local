import type { EventItem } from "./api";

export function nextAssistantText(current: string, event: EventItem): string {
  if (event.kind === "assistant.progress") return "";
  if (event.kind === "delta") return current + String(event.data.text ?? "");
  return current;
}
