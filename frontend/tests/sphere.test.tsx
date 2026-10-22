import { describe, expect, it } from "vitest";
import { createSphereRenderer } from "../src/pages/sphereRenderer";
import { focusCamera, INITIAL_CAMERA, rotate } from "../src/pages/lunarGeometry";

// 渲染器只在 resize 时读取 window.devicePixelRatio，node 环境下打桩即可。
(globalThis as unknown as { window: unknown }).window = { devicePixelRatio: 1 };
// SkillSphere 经 api 模块读取会话存储（token/base），node 环境下打桩。
function storage() {
  const values = new Map<string, string>();
  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
    removeItem: (key: string) => values.delete(key),
    clear: () => values.clear(),
  };
}
(globalThis as unknown as { sessionStorage: unknown }).sessionStorage = storage();
(globalThis as unknown as { localStorage: unknown }).localStorage = storage();

/** 记录调用的最小 2D 上下文，用于在无 canvas 的环境里驱动渲染器。 */
function mockContext() {
  const calls: string[] = [];
  const record = (name: string) =>
    (...args: unknown[]) => {
      calls.push(`${name}(${args.map((value) => String(value)).join(",")})`);
    };
  const gradient = { addColorStop: record("addColorStop") };
  return {
    calls,
    gradient,
    setTransform: record("setTransform"),
    clearRect: record("clearRect"),
    createRadialGradient: () => gradient,
    fillRect: record("fillRect"),
    beginPath: record("beginPath"),
    moveTo: record("moveTo"),
    lineTo: record("lineTo"),
    stroke: record("stroke"),
    arc: record("arc"),
    fill: record("fill"),
    setLineDash: record("setLineDash"),
    measureText: () => ({ width: 40 }),
    fillText: record("fillText"),
    fillStyle: "",
    strokeStyle: "",
    lineWidth: 1,
    globalAlpha: 1,
    shadowBlur: 0,
    shadowColor: "",
    font: "",
  };
}
function mockCanvas() {
  const context = mockContext();
  const canvas = {
    width: 0,
    height: 0,
    getContext: () => context,
    getBoundingClientRect: () => ({ width: 600, height: 500, left: 0, top: 0 }),
  };
  return { canvas: canvas as unknown as HTMLCanvasElement, context };
}

const nodes = [
  { id: "a-plot", name: "绘图", domain: "数据", generation: 0, source: "seed", description: "把测量画成图", tools: 2, relations: [["depend_on", "b-csv"]] as [string, string][] },
  { id: "b-csv", name: "表格", domain: "数据", generation: 0, source: "seed", description: "读取 CSV", tools: 1, relations: [] as [string, string][] },
  { id: "c-github", name: "社区技能", domain: "社区", generation: 0, source: "github", description: "只读资料", tools: 0, relations: [["similar_to", "a-plot"]] as [string, string][] },
  { id: "d-evolved", name: "演化技能", domain: "演化", generation: 3, source: "evolved", description: "带统计", tools: 0, relations: [] as [string, string][] },
];

describe("capability sphere renderer", () => {
  it(" lays out a stable sphere, keeps only declared edges and exposes points", () => {
    const { canvas, context } = mockCanvas();
    const renderer = createSphereRenderer(canvas)!;
    expect(renderer).not.toBeNull();
    renderer.setData(nodes, [
      { source: "a-plot", target: "b-csv", type: "depend_on" },
      { source: "c-github", target: "a-plot", type: "similar_to" },
      { source: "a-plot", target: "ghost", type: "depend_on" },
    ]);
    // 布局按 domain 稳定排序：点存在且落在单位球面上
    for (const node of nodes) {
      const point = renderer.point(node.id);
      expect(point).not.toBeNull();
      expect(Math.hypot(point!.x, point!.y, point!.z)).toBeCloseTo(1);
    }
    // 同一份数据两次布局一致（确定性）
    const fresh = createSphereRenderer(mockCanvas().canvas)!;
    fresh.setData(nodes, []);
    expect(renderer.point("a-plot")).toEqual(fresh.point("a-plot"));
    renderer.draw(INITIAL_CAMERA);
    expect(context.calls.some((call) => call.startsWith("arc("))).toBe(true);
    expect(context.calls.some((call) => call.startsWith("stroke("))).toBe(true);
    renderer.dispose();
  });

  it("hits the front-most node under the pointer and honours the filter", () => {
    const { canvas } = mockCanvas();
    const renderer = createSphereRenderer(canvas)!;
    renderer.setData(nodes, []);
    // 组件选中节点时会把镜头推向它；命中测试按同一相机取屏幕坐标
    const point = renderer.point("a-plot")!;
    const camera = focusCamera(point, INITIAL_CAMERA);
    renderer.setFocus("a-plot");
    renderer.draw(camera); // draw 负责按画布尺寸初始化投影
    const p = rotate(point, camera),
      k = 3.4 / (3.4 - p.z),
      x = 300 + p.x * 180 * k,
      y = 250 + p.y * 180 * k;
    expect(renderer.hit(x, y, camera)?.id).toBe("a-plot");
    // 过滤后不可见的节点不再参与命中
    renderer.setFilter((node) => node.id === "b-csv");
    expect(renderer.hit(x, y, camera)).toBeNull();
    renderer.dispose();
  });

  it("suppresses distant similarity strokes but keeps dependency edges", () => {
    const { canvas, context } = mockCanvas();
    const renderer = createSphereRenderer(canvas)!;
    renderer.setData(nodes, [
      { source: "a-plot", target: "b-csv", type: "depend_on" },
      { source: "c-github", target: "a-plot", type: "similar_to" },
    ]);
    renderer.draw(INITIAL_CAMERA);
    const dashed = context.calls.filter((call) =>
      call.startsWith("setLineDash(1,5)"),
    );
    // 无焦点时远处 similar_to 被 LOD 抑制；聚焦后邻域内的相似边恢复
    expect(dashed.length).toBe(0);
    renderer.setFocus("c-github");
    renderer.draw(INITIAL_CAMERA);
    expect(
      context.calls.filter((call) => call.startsWith("setLineDash(1,5)")).length,
    ).toBeGreaterThan(0);
    renderer.dispose();
  });
});

describe("skill sphere page", () => {
  it("renders the atlas with corpus summary, filters and relation legend", async () => {
    const { renderToStaticMarkup } = await import("react-dom/server");
    const SkillSphere = (await import("../src/pages/SkillSphere")).default;
    const html = renderToStaticMarkup(
      <SkillSphere
        graph={{
          nodes: nodes as never,
          edges: [
            { source: "a-plot", target: "b-csv", type: "depend_on" },
            { source: "c-github", target: "a-plot", type: "similar_to" },
          ],
          corpus: {
            available: true,
            skills: 1881,
            seed: 76,
            community: 1769,
            evolved: 36,
            domains: 57,
            edges: 2211,
          },
          skill_count: 4,
          edge_count: 2,
          relation_types: ["depend_on", "similar_to"],
        }}
        semantic={{ encoder: { kind: "dense-onnx" } }}
        onOpen={() => {}}
        onRun={() => {}}
      />,
    );
    expect(html).toContain("能力星图");
    expect(html).toContain("SkillNet 语料 1881 · 种子 76 · 社区 1769 · 演化 36");
    expect(html).toContain("4 个能力 · 2 项关系");
    // SSR has a usable directory even before the canvas renderer is mounted.
    expect(html).toContain("技能目录");
    expect(html).toContain('aria-label="筛选技能领域"');
    // 目录列出全部节点与领域筛选，含演化代际标记
    expect(html).toContain("演化 · G3");
    expect(html).toContain("<kbd>4</kbd>");
    // 目录默认截断提示只在超限时出现
    expect(html).not.toContain("仅显示前");
  });

  it("shows the truncation note when a filter leaves more than the cap", async () => {
    const { renderToStaticMarkup } = await import("react-dom/server");
    const SkillSphere = (await import("../src/pages/SkillSphere")).default;
    const many = Array.from({ length: 65 }, (_, index) => ({
      id: `skill-${index}`,
      name: `技能 ${index}`,
      domain: "数据",
      generation: 0,
      source: "seed",
      description: "说明",
      tools: 0,
      relations: [],
    }));
    const html = renderToStaticMarkup(
      <SkillSphere
        graph={{
          nodes: many as never,
          edges: [],
          skill_count: 65,
          edge_count: 0,
          relation_types: [],
        }}
        onOpen={() => {}}
        onRun={() => {}}
      />,
    );
    expect(html).toContain("仅显示前 60");
  });
});
