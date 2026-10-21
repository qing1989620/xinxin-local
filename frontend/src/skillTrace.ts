import type { EventItem } from "./api";

export type SkillCard = {
  id: string;
  name: string;
  description: string;
  domain?: string;
  note?: string;
};
export type SkillEvidence = {
  id: string;
  kind: "reference" | "tool";
  ok: boolean;
  seq: number;
};
export type SkillTrace = {
  selection_seq: number;
  skills: SkillCard[];
  dependencies: SkillCard[];
  method: string;
  evidence: SkillEvidence[];
};

/** Merge SSE replay with the compact, event-derived historical view. */
export function skillTrace(
  events: EventItem[],
  saved?: SkillTrace | null,
): SkillTrace | null {
  const selection = [...events]
    .reverse()
    .find((event) => event.kind === "skills");
  const trace =
    selection && selection.seq >= (saved?.selection_seq || 0)
      ? {
          selection_seq: selection.seq,
          skills: (selection.data.skills || []) as SkillCard[],
          dependencies: (selection.data.dependencies || []) as SkillCard[],
          method: selection.data.selection?.method || "retrieval_order",
          evidence: [],
        }
      : saved;
  if (!trace) return null;
  const evidence = new Map<string, SkillEvidence>();
  const add = (item: SkillEvidence) => {
    if (
      item.seq <= trace.selection_seq ||
      !item.id ||
      !["reference", "tool"].includes(item.kind) ||
      typeof item.ok !== "boolean"
    )
      return;
    evidence.set(`${item.seq}:${item.id}:${item.kind}`, item);
  };
  if (saved?.selection_seq === trace.selection_seq) saved.evidence.forEach(add);
  for (const event of events) {
    if (
      event.kind === "tool.completed" &&
      Array.isArray(event.data.skill_evidence)
    ) {
      event.data.skill_evidence.forEach((item: Omit<SkillEvidence, "seq">) =>
        add({ ...item, seq: event.seq }),
      );
    }
  }
  return {
    ...trace,
    evidence: [...evidence.values()].sort((a, b) => a.seq - b.seq),
  };
}

export function tracedSkills(trace: SkillTrace) {
  const cards = new Map<
    string,
    SkillCard & { dependency?: boolean; onDemand?: boolean }
  >();
  trace.skills.forEach((card) => cards.set(card.id, card));
  trace.dependencies.forEach((card) => {
    if (!cards.has(card.id)) cards.set(card.id, { ...card, dependency: true });
  });
  for (const item of trace.evidence) {
    if (item.kind === "reference" && item.ok && !cards.has(item.id)) {
      cards.set(item.id, {
        id: item.id,
        name: item.id,
        description: "执行时按需补充的参考方法。",
        onDemand: true,
      });
    }
  }
  return [...cards.values()].map((card) => ({
    ...card,
    references: trace.evidence.filter(
      (item) => item.id === card.id && item.kind === "reference" && item.ok,
    ).length,
    tools: trace.evidence.filter(
      (item) => item.id === card.id && item.kind === "tool" && item.ok,
    ).length,
    failures: trace.evidence.filter((item) => item.id === card.id && !item.ok)
      .length,
  }));
}
