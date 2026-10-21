import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { MathText } from "../src/components/MathText";

describe("learning formula rendering", () => {
  it.each(["导数是 $2x$", "曲线 $$y=x^2$$", "切线 \\(y=2x-1\\)"])(
    "renders supported math syntax: %s",
    (text) => {
      const html = renderToStaticMarkup(<MathText text={text} />);
      expect(html).toContain('class="katex"');
      expect(html).not.toContain("katex-error");
    },
  );

  it("escapes ordinary HTML while preserving Chinese text", () => {
    const html = renderToStaticMarkup(
      <MathText text={'题目 <img src=x onerror="alert(1)">'} />,
    );
    expect(html).toContain("题目");
    expect(html).not.toContain("<img");
    expect(html).toContain("&lt;img");
  });

  it("does not create trusted links or HTML attributes from untrusted math", () => {
    for (const text of [
      String.raw`$\href{javascript:alert(1)}{x}$`,
      String.raw`$\htmlData{onclick=alert(1)}{x}$`,
    ]) {
      const html = renderToStaticMarkup(<MathText text={text} />);
      expect(html).not.toMatch(/<a\b|<img\b|<span[^>]+\sonclick=/);
    }
  });
});
