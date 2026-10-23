import { describe, expect, it } from "vitest";
import { createStudyDrafts, fillDraftValues } from "../src/studyDrafts";
import {
  analyzedForMode,
  imageReadingIssue,
  scopePages,
  selectStudyBatch,
} from "../src/studyScope";
import type { SourceUnit } from "../src/learning";

function storage() {
  const values = new Map<string, string>();
  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => {
      values.set(key, value);
    },
    removeItem: (key: string) => {
      values.delete(key);
    },
    clear: () => values.clear(),
    key: (index: number) => [...values.keys()][index] ?? null,
    get length() {
      return values.size;
    },
  };
}
function unit(index: number, from = index + 1, to = from): SourceUnit {
  return {
    id: `source-${index}`,
    chapter_id: "chapter",
    idx: index,
    label: `PDF ${from}–${to}`,
    chars: 200,
    question_count: 0,
    page_from: from,
    page_to: to,
    eligible: true,
    text_eligible: true,
  };
}
const capability = { pdf: true, available: true, reason: "", max_pages: 60 };

describe("practice drafts", () => {
  it("restores a question after remount without mixing sessions or tutor modes", () => {
    const saved = storage();
    const first = createStudyDrafts("quiz-one", saved);
    first.write("answer:question-one", "我的未完成解题步骤");
    first.write("tutor:question-one:teacher", "为什么能换元？");
    first.write("tutor:question-one:xinxin", "我们换一种讲法");
    const restored = createStudyDrafts("quiz-one", saved);
    expect(restored.read("answer:question-one")).toBe("我的未完成解题步骤");
    expect(restored.read("tutor:question-one:teacher")).toBe("为什么能换元？");
    expect(restored.read("tutor:question-one:xinxin")).toBe("我们换一种讲法");
    expect(
      createStudyDrafts("quiz-two", saved).read("answer:question-one"),
    ).toBe("");
    restored.write("answer:question-one", "");
    expect(
      createStudyDrafts("quiz-one", saved).read("answer:question-one"),
    ).toBe("");
    expect(
      createStudyDrafts("quiz-one", saved).read("tutor:question-one:teacher"),
    ).toBe("为什么能换元？");
  });

  it("continues in memory when browser storage fails", () => {
    const blocked = {
      ...storage(),
      getItem() {
        throw new Error("blocked");
      },
      setItem() {
        throw new Error("quota");
      },
    };
    const drafts = createStudyDrafts("quiz", blocked);
    drafts.write("answer:q", "继续写下步骤");
    expect(drafts.read("answer:q")).toBe("继续写下步骤");
  });

  it("keeps commas, semicolons and empty positions inside distinct blanks", () => {
    expect(fillDraftValues('["(0,1)","A;B"]', 2)).toEqual(["(0,1)", "A;B"]);
    expect(fillDraftValues("(0,1)", 1)).toEqual(["(0,1)"]);
    expect(fillDraftValues('["first","","third"]', 3)).toEqual([
      "first",
      "",
      "third",
    ]);
    expect(fillDraftValues("", 2)).toEqual(["", ""]);
    const saved = storage();
    const values = Array.from({ length: 8 }, () => "x".repeat(500));
    createStudyDrafts("maximum-blanks", saved).write(
      "answer:q",
      JSON.stringify(values),
    );
    expect(
      fillDraftValues(
        createStudyDrafts("maximum-blanks", saved).read("answer:q"),
        8,
      ),
    ).toEqual(values);
  });
});

describe("bounded study selection", () => {
  it("chooses a usable batch when 40 sources at 24 questions would exceed 400", () => {
    const result = selectStudyBatch(
      Array.from({ length: 40 }, (_, index) => unit(index)),
      24,
      40,
      400,
      "text",
      capability,
      {},
    );
    expect(result).toHaveLength(16);
    expect(result.length * 24).toBeLessThanOrEqual(400);
  });

  it("stays within 60 unique PDF pages and counts overlap consistently", () => {
    const sources = Array.from({ length: 25 }, (_, index) =>
      unit(index, index * 4 + 1, index * 4 + 4),
    );
    const result = selectStudyBatch(sources, 1, 40, 400, "pdf", capability, {});
    expect(result).toHaveLength(15);
    expect(scopePages(result)).toBe(60);
    expect(scopePages([unit(1, 1, 4), unit(2, 3, 6)])).toBe(6);
    expect(
      imageReadingIssue([unit(1, 1, 30)], capability, { "source-1": [4, 6] }),
    ).toBe("");
    expect(
      imageReadingIssue([unit(1, 1, 30)], capability, { "source-1": [0, 6] }),
    ).toContain("精读");
  });

  it("does not confuse text analysis, another page range or partial reading with completed PDF analysis", () => {
    const source = unit(1, 1, 10);
    const analysis = {
      type: "exercises",
      type_label: "练习",
      eligible: true,
      reason: "",
      summary: "合成摘要",
      knowledge_points: [],
      exercises: [],
    };
    const ranges: Record<string, [number, number]> = { "source-1": [4, 6] };
    expect(analyzedForMode({ ...source, analysis }, "pdf", ranges)).toBe(false);
    expect(
      analyzedForMode(
        {
          ...source,
          analysis: {
            ...analysis,
            source_method: "pdf_images",
            page_scope: [4, 6],
            read_pages: [4, 6],
          },
        },
        "pdf",
        ranges,
      ),
    ).toBe(false);
    const complete = {
      ...source,
      analysis: {
        ...analysis,
        source_method: "pdf_images" as const,
        page_scope: [4, 6] as [number, number],
        read_pages: [4, 5, 6],
      },
    };
    expect(analyzedForMode(complete, "pdf", ranges)).toBe(true);
    expect(analyzedForMode(complete, "pdf", {})).toBe(false);
    expect(
      selectStudyBatch(
        [complete],
        12,
        40,
        400,
        "pdf",
        capability,
        ranges,
        true,
      ),
    ).toEqual([]);
  });
});
