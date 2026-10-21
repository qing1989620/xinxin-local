import { useMemo } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

/** 把文本里的 $...$ / $$...$$ 渲染成公式，其余部分保持原样（含换行）。 */
export function MathText({ text, block = false }: { text: string; block?: boolean }) {
  const parts = useMemo(() => splitMath(text || ""), [text]);
  return (
    <span className={block ? "math-text math-text-block" : "math-text"}>
      {parts.map((part, index) => {
        if (part.kind === "text") {
          return (
            <span key={index} className="math-plain">
              {part.value}
            </span>
          );
        }
        let html = "";
        try {
          html = katex.renderToString(part.value, {
            displayMode: part.display,
            throwOnError: false,
            trust: false,
            strict: "ignore",
          });
        } catch {
          html = "";
        }
        if (!html) return <span key={index}>{part.raw}</span>;
        return (
          <span
            key={index}
            className="math-tex"
            dangerouslySetInnerHTML={{ __html: html }}
          />
        );
      })}
    </span>
  );
}

type Part =
  | { kind: "text"; value: string }
  | { kind: "tex"; value: string; display: boolean; raw: string };

/** 逐字符扫描，避免正则处理嵌套时出错。 */
function splitMath(source: string): Part[] {
  const parts: Part[] = [];
  let buffer = "";
  let index = 0;

  const flush = () => {
    if (buffer) {
      parts.push({ kind: "text", value: buffer });
      buffer = "";
    }
  };

  while (index < source.length) {
    const char = source[index];
    // 模型常把公式写成 \[ ... \] / \( ... \)，和 $...$ 等价处理
    if (char === "\\" && (source[index + 1] === "[" || source[index + 1] === "(")) {
      const display = source[index + 1] === "[";
      const close = display ? "\\]" : "\\)";
      const start = index + 2;
      const end = source.indexOf(close, start);
      if (end > start) {
        flush();
        parts.push({
          kind: "tex",
          value: source.slice(start, end),
          display,
          raw: source.slice(index, end + 2),
        });
        index = end + 2;
        continue;
      }
    }
    if (char !== "$") {
      buffer += char;
      index += 1;
      continue;
    }
    const display = source[index + 1] === "$";
    const marker = display ? "$$" : "$";
    const start = index + marker.length;
    let end = source.indexOf(marker, start);
    // 单个 $ 不能跨太多内容；避免把「价格 $5」这类误判成公式
    if (end < 0 || (!display && (end - start > 400 || source.slice(start, end).includes("\n")))) {
      buffer += char;
      index += 1;
      continue;
    }
    const value = source.slice(start, end);
    if (!value.trim()) {
      buffer += char;
      index += 1;
      continue;
    }
    flush();
    parts.push({ kind: "tex", value, display, raw: source.slice(index, end + marker.length) });
    index = end + marker.length;
  }
  flush();
  return parts.length ? parts : [{ kind: "text", value: source }];
}
