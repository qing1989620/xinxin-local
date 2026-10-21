import { describe, expect, it } from "vitest";
import { activeLrcIndex, mergeLrc, parseLrc } from "../src/lib/lrc";

describe("parseLrc", () => {
  it("解析时间戳并按时间排序", () => {
    const lines = parseLrc(
      "[00:12.50]第二句\n[00:03.00]第一句\n[00:20]第三句",
    );
    expect(lines.map((line) => line.text)).toEqual([
      "第一句",
      "第二句",
      "第三句",
    ]);
    expect(lines[0].time).toBeCloseTo(3);
    expect(lines[1].time).toBeCloseTo(12.5);
    expect(lines[2].time).toBeCloseTo(20);
  });

  it("同一行多个时间戳拆成多条", () => {
    const lines = parseLrc("[00:05.00][01:10.00]重复句");
    expect(lines).toHaveLength(2);
    expect(lines.map((line) => line.time)).toEqual([5, 70]);
  });

  it("没有时间戳时保留纯文本行并丢掉元数据行", () => {
    const lines = parseLrc("[ar:某歌手]\n第一行\n\n第二行");
    expect(lines.map((line) => line.text)).toEqual(["第一行", "第二行"]);
    expect(lines.every((line) => line.time === -1)).toBe(true);
  });

  it("空输入返回空数组", () => {
    expect(parseLrc("")).toEqual([]);
  });
});

describe("mergeLrc", () => {
  it("翻译按时间并入主歌词", () => {
    const lines = mergeLrc(
      "[00:03.00]hello\n[00:10.00]world",
      "[00:03.10]你好\n[00:10.05]世界",
    );
    expect(lines).toHaveLength(2);
    expect(lines[0]).toMatchObject({ text: "hello", trans: "你好" });
    expect(lines[1]).toMatchObject({ text: "world", trans: "世界" });
  });

  it("只有翻译时直接返回翻译", () => {
    const lines = mergeLrc("", "[00:03.00]你好");
    expect(lines.map((line) => line.text)).toEqual(["你好"]);
  });
});

describe("activeLrcIndex", () => {
  const lines = mergeLrc("[00:03.00]a\n[00:10.00]b\n[00:20.00]c", "");

  it("跟随播放进度", () => {
    expect(activeLrcIndex(lines, 0)).toBe(-1);
    expect(activeLrcIndex(lines, 3)).toBe(0);
    expect(activeLrcIndex(lines, 15)).toBe(1);
    expect(activeLrcIndex(lines, 99)).toBe(2);
  });

  it("无时间戳不高亮", () => {
    expect(activeLrcIndex(parseLrc("纯文本"), 5)).toBe(-1);
  });
});
