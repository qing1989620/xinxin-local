import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { skillTrace, tracedSkills, type SkillTrace } from "../src/skillTrace";
import SkillNetTrace from "../src/pages/SkillNetTrace";
import type { EventItem, Run } from "../src/api";

vi.mock("../src/api", () => ({ api: vi.fn() }));
const route: SkillTrace = {
  selection_seq: 2,
  skills: [
    {
      id: "one",
      name: "示例方法",
      description: "整理文件",
      note: "与目标有关",
    },
  ],
  dependencies: [],
  method: "task_utility",
  evidence: [],
};
const event = (
  seq: number,
  data: Record<string, any>,
  kind = "tool.completed",
) => ({ seq, kind, data }) as EventItem;

describe("SkillNet evidence in conversations", () => {
  it("never turns selection, candidate scores or a tool name into execution", () => {
    const selected = event(
      2,
      { ...route, candidates: [{ id: "other", score: 99 }] },
      "skills",
    );
    const trace = skillTrace([
      selected,
      event(3, { name: "write_file", ok: true }),
    ]);
    expect(tracedSkills(trace!)[0]).toMatchObject({ references: 0, tools: 0 });
    expect(tracedSkills(trace!)).toHaveLength(1);
  });
  it("merges persisted and replayed evidence without duplicate counts", () => {
    const proof = { id: "one", kind: "reference" as const, ok: true, seq: 3 };
    const saved = { ...route, evidence: [proof] };
    const merged = skillTrace(
      [
        event(3, { skill_evidence: [proof] }),
        event(4, { skill_evidence: [{ id: "one", kind: "tool", ok: false }] }),
      ],
      saved,
    )!;
    expect(merged.evidence).toHaveLength(2);
    expect(tracedSkills(merged)[0]).toMatchObject({
      references: 1,
      tools: 0,
      failures: 1,
    });
  });
  it("does not carry evidence across a newer routing decision or accept string success flags", () => {
    const saved = {
      ...route,
      evidence: [{ id: "one", kind: "tool" as const, ok: true, seq: 3 }],
    };
    const trace = skillTrace(
      [
        event(5, { skills: [] }, "skills"),
        event(6, { skill_evidence: [{ id: "one", kind: "tool", ok: "true" }] }),
      ],
      saved,
    )!;
    expect(trace.evidence).toEqual([]);
    expect(tracedSkills(trace)).toEqual([]);
  });
  it("adds successful on-demand reference reads without presenting them as initial selections", () => {
    const trace = skillTrace(
      [
        event(3, {
          skill_evidence: [{ id: "additional", kind: "reference", ok: true }],
        }),
      ],
      route,
    )!;
    expect(
      tracedSkills(trace).find((card) => card.id === "additional"),
    ).toMatchObject({ references: 1, tools: 0 });
    expect(trace.skills).toHaveLength(1);
  });
  it("restores an honest inline route and escapes model-provided reasons", () => {
    const run = {
      id: "run",
      status: "completed",
      skillnet: {
        ...route,
        skills: [{ ...route.skills[0], note: "<script>unsafe()</script>" }],
      },
    } as Run;
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <SkillNetTrace run={run} />
      </MemoryRouter>,
    );
    expect(html).toContain("SkillNet");
    expect(html).toContain("尚无读取或工具结果记录");
    expect(html).toContain("模型建议");
    expect(html).not.toContain("<script>");
    expect(html).toContain("/tasks?run=run");
  });
  it("keeps direct answers compact and hides missing legacy routing records", () => {
    const run = {
      id: "direct",
      status: "completed",
      skillnet: { ...route, skills: [] },
    } as Run;
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <SkillNetTrace run={run} />
      </MemoryRouter>,
    );
    expect(html).toContain("本轮未选额外技能");
    expect(html).not.toContain("匹配 1 项");
    expect(
      renderToStaticMarkup(<SkillNetTrace run={{ ...run, skillnet: null }} />),
    ).toBe("");
  });
});
