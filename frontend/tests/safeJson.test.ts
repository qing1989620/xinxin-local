import { describe, expect, it } from "vitest";
import { parseJson } from "../src/safeJson";

describe("parseJson", () => {
  it("parses valid JSON", () => {
    expect(
      parseJson('{"total_tokens":55701}', {} as { total_tokens?: number }),
    ).toEqual({ total_tokens: 55701 });
    expect(parseJson("[1,2]", [] as number[])).toEqual([1, 2]);
  });
  it("falls back for empty, absent and malformed input", () => {
    expect(parseJson("", { a: 1 })).toEqual({ a: 1 });
    expect(parseJson(null, { a: 1 })).toEqual({ a: 1 });
    expect(parseJson(undefined, "x")).toBe("x");
    expect(parseJson("{坏", 0)).toBe(0);
    // JSON.parse("null") 得到 null：同样视为无效，返回兜底值。
    expect(parseJson("null", 7)).toBe(7);
  });
});
