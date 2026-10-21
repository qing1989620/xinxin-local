import { useEffect, useMemo, useRef, useState } from "react";
import { compileExpression, stripAssignment } from "../lib/mathExpr";

type Props = {
  expressions: string[];
  xMin?: number;
  xMax?: number;
  height?: number;
  caption?: string;
};

const COLORS = ["var(--accent)", "#a8553e", "#566096", "#7d857c"];
const PADDING = { left: 40, right: 14, top: 14, bottom: 24 };
const SAMPLES = 520;

function niceNumber(span: number, round: boolean): number {
  const exponent = Math.floor(Math.log10(Math.max(span, 1e-9)));
  const fraction = span / 10 ** exponent;
  let nice: number;
  if (round) {
    if (fraction < 1.5) nice = 1;
    else if (fraction < 3) nice = 2;
    else if (fraction < 7) nice = 5;
    else nice = 10;
  } else if (fraction <= 1) nice = 1;
  else if (fraction <= 2) nice = 2;
  else if (fraction <= 5) nice = 5;
  else nice = 10;
  return nice * 10 ** exponent;
}

function ticksFor(min: number, max: number, count: number): number[] {
  if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) return [];
  const step = niceNumber(niceNumber(max - min, false) / Math.max(count - 1, 1), true);
  const start = Math.ceil(min / step) * step;
  const values: number[] = [];
  for (let value = start; value <= max + step * 0.5 && values.length < 14; value += step) {
    values.push(Number(value.toPrecision(12)));
  }
  return values;
}

function formatTick(value: number): string {
  if (Math.abs(value) < 1e-9) return "0";
  const absolute = Math.abs(value);
  if (absolute >= 10000 || absolute < 0.01) return value.toExponential(1).replace(/\.0e/, "e");
  return String(Number(value.toPrecision(4)));
}

type Series = {
  label: string;
  color: string;
  points: Array<{ x: number; y: number } | null>;
};

export function FunctionPlot({ expressions, xMin = -8, xMax = 8, height = 250, caption }: Props) {
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const [width, setWidth] = useState(640);
  const [hover, setHover] = useState<{ x: number; y: number } | null>(null);

  useEffect(() => {
    const node = wrapRef.current;
    if (!node) return;
    const observer = new ResizeObserver((entries) => {
      const next = entries[0]?.contentRect.width ?? 640;
      setWidth(Math.max(260, Math.round(next)));
    });
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  const compiled = useMemo(
    () => expressions.map((expr) => ({ expr: stripAssignment(expr), result: compileExpression(expr) })),
    [expressions],
  );

  const innerWidth = Math.max(120, width - PADDING.left - PADDING.right);
  const innerHeight = Math.max(80, height - PADDING.top - PADDING.bottom);

  const series = useMemo<Series[]>(() => {
    return compiled.map((item, index) => {
      const points: Series["points"] = [];
      if (item.result.ok) {
        const step = (xMax - xMin) / SAMPLES;
        for (let i = 0; i <= SAMPLES; i += 1) {
          const x = xMin + step * i;
          const y = item.result.evaluate(x);
          points.push(Number.isFinite(y) ? { x, y } : null);
        }
      }
      return { label: item.expr, color: COLORS[index % COLORS.length], points };
    });
  }, [compiled, xMax, xMin]);

  const yRange = useMemo(() => {
    const values: number[] = [];
    for (const item of series) {
      for (const point of item.points) {
        if (point && Number.isFinite(point.y)) values.push(point.y);
      }
    }
    if (!values.length) return { min: -1, max: 1 };
    values.sort((a, b) => a - b);
    const low = values[Math.floor((values.length - 1) * 0.02)];
    const high = values[Math.floor((values.length - 1) * 0.98)];
    let min = Math.min(low, 0);
    let max = Math.max(high, 0);
    if (max - min < 1e-6) {
      min -= 1;
      max += 1;
    }
    const padding = (max - min) * 0.12;
    return { min: min - padding, max: max + padding };
  }, [series]);

  const xScale = (x: number) => PADDING.left + ((x - xMin) / (xMax - xMin || 1)) * innerWidth;
  const yScale = (y: number) =>
    PADDING.top + innerHeight - ((y - yRange.min) / (yRange.max - yRange.min || 1)) * innerHeight;

  const xTicks = ticksFor(xMin, xMax, 7);
  const yTicks = ticksFor(yRange.min, yRange.max, 5);
  const jumpLimit = (yRange.max - yRange.min) * 0.8;

  const paths = series.map((item) => {
    let path = "";
    let previous: { x: number; y: number } | null = null;
    for (const point of item.points) {
      if (!point) {
        previous = null;
        continue;
      }
      const command = previous && Math.abs(point.y - previous.y) < jumpLimit ? "L" : "M";
      path += `${command}${xScale(point.x).toFixed(2)},${yScale(point.y).toFixed(2)} `;
      previous = point;
    }
    return path.trim();
  });

  const failed = compiled.filter((item) => !item.result.ok);

  function handleMove(event: React.MouseEvent<SVGSVGElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    const ratio = (event.clientX - rect.left) / rect.width;
    const x = xMin + ratio * (xMax - xMin);
    setHover({ x: Number(x.toFixed(4)), y: 0 });
  }

  const hoverValues = hover
    ? series
        .map((item) => {
          const point = item.points.reduce<{ x: number; y: number } | null>((best, current) => {
            if (!current) return best;
            if (!best) return current;
            return Math.abs(current.x - hover.x) < Math.abs(best.x - hover.x) ? current : best;
          }, null);
          return point ? { label: item.label, color: item.color, y: point.y } : null;
        })
        .filter(Boolean)
    : [];

  return (
    <figure className="plot-figure">
      <div className="plot-canvas" ref={wrapRef}>
        <svg
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-label={caption || `函数图像：${expressions.join("；")}`}
          onMouseMove={handleMove}
          onMouseLeave={() => setHover(null)}
        >
          <rect x={0} y={0} width={width} height={height} fill="var(--paper)" rx={2} />
          {yTicks.map((value) => (
            <g key={`y-${value}`}>
              <line
                x1={PADDING.left}
                x2={width - PADDING.right}
                y1={yScale(value)}
                y2={yScale(value)}
                stroke="var(--line)"
                strokeWidth={0.6}
                opacity={Math.abs(value) < 1e-9 ? 0 : 0.7}
              />
              <text
                x={PADDING.left - 7}
                y={yScale(value) + 3}
                textAnchor="end"
                className="plot-tick"
              >
                {formatTick(value)}
              </text>
            </g>
          ))}
          {xTicks.map((value) => (
            <g key={`x-${value}`}>
              <line
                x1={xScale(value)}
                x2={xScale(value)}
                y1={PADDING.top}
                y2={height - PADDING.bottom}
                stroke="var(--line)"
                strokeWidth={0.6}
                opacity={Math.abs(value) < 1e-9 ? 0 : 0.7}
              />
              <text x={xScale(value)} y={height - PADDING.bottom + 14} textAnchor="middle" className="plot-tick">
                {formatTick(value)}
              </text>
            </g>
          ))}
          {/* 坐标轴 */}
          {yRange.min <= 0 && yRange.max >= 0 && (
            <line
              x1={PADDING.left}
              x2={width - PADDING.right}
              y1={yScale(0)}
              y2={yScale(0)}
              stroke="var(--ink)"
              strokeWidth={1}
              opacity={0.55}
            />
          )}
          {xMin <= 0 && xMax >= 0 && (
            <line
              x1={xScale(0)}
              x2={xScale(0)}
              y1={PADDING.top}
              y2={height - PADDING.bottom}
              stroke="var(--ink)"
              strokeWidth={1}
              opacity={0.55}
            />
          )}
          {paths.map((path, index) =>
            path ? (
              <path
                key={index}
                d={path}
                fill="none"
                stroke={series[index].color}
                strokeWidth={1.6}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            ) : null,
          )}
          {hover && (
            <line
              x1={xScale(hover.x)}
              x2={xScale(hover.x)}
              y1={PADDING.top}
              y2={height - PADDING.bottom}
              stroke="var(--accent)"
              strokeWidth={0.8}
              strokeDasharray="3 3"
              opacity={0.7}
            />
          )}
          {hover &&
            hoverValues.map((item) =>
              item ? (
                <circle
                  key={item.label}
                  cx={xScale(hover.x)}
                  cy={yScale(item.y)}
                  r={2.8}
                  fill={item.color}
                />
              ) : null,
            )}
        </svg>
        {hover && hoverValues.length > 0 && (
          <div className="plot-readout">
            <span>x = {hover.x}</span>
            {hoverValues.map((item) =>
              item ? (
                <span key={item.label} style={{ color: item.color }}>
                  {item.label} = {Number(item.y.toFixed(4))}
                </span>
              ) : null,
            )}
          </div>
        )}
      </div>
      <figcaption className="plot-caption">
        {caption || (
          <span className="plot-legend">
            {series.map((item) => (
              <span key={item.label}>
                <i style={{ background: item.color }} />
                {item.label}
              </span>
            ))}
          </span>
        )}
        {failed.length > 0 && <em>画不出来：{failed.map((item) => `${item.expr}（${(item.result as { error: string }).error}）`).join("；")}</em>}
      </figcaption>
    </figure>
  );
}

/** 从 Markdown 文本里拆出 ```plot 代码块，交给 FunctionPlot 渲染。 */
export function extractPlotBlocks(text: string): {
  body: string;
  blocks: string[][];
} {
  const blocks: string[][] = [];
  const body = (text || "").replace(/```plot\s*\n([\s\S]*?)```/gi, (_match, raw: string) => {
    const expressions = raw
      .split(/[\n;；]+/)
      .map((line) => line.trim())
      .filter(Boolean)
      .slice(0, 4);
    if (expressions.length) blocks.push(expressions);
    return "\n\n[[PLOT]]\n\n";
  });
  return { body, blocks };
}
