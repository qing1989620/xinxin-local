import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import ErrorBoundary from "../src/ErrorBoundary";

describe("ErrorBoundary", () => {
  it("renders children untouched when nothing has failed", () => {
    const html = renderToStaticMarkup(
      <ErrorBoundary>
        <p>正常内容</p>
      </ErrorBoundary>,
    );
    expect(html).toContain("正常内容");
    expect(html).not.toContain("界面出了一点问题");
  });
  it("derives the error state for React", () => {
    expect(ErrorBoundary.getDerivedStateFromError(new Error("boom"))).toEqual({
      error: expect.any(Error),
    });
  });
  it("shows a recoverable screen instead of a blank page when rendering fails", () => {
    const boundary = new ErrorBoundary({ children: null });
    boundary.state = { error: new Error("boom") };
    const html = renderToStaticMarkup(boundary.render());
    expect(html).toContain("界面出了一点问题");
    expect(html).toContain("重新加载页面");
    expect(html).toContain("回到工作台");
    expect(html).toContain("boom");
  });
});
