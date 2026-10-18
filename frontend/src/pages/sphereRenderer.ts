// Canvas 能力星球渲染器：端口自 skillnet-demo web/assets/sphere.js。
// 设计保持一致：
// - 节点坐标是视觉索引（等面积黄金角螺旋），不是学习到的能力度量；
// - 只画目录声明的关系边（depend_on / compose_with / similar_to），
//   远处的 similar_to 按 LOD 抑制，保持每个节点可被检索；
// - 标签在画布内绘制并做碰撞规避，最多 14 个，焦点邻域优先。
import { position, rotate, type Camera, type Point3 } from "./lunarGeometry";

export type SphereNode = {
  id: string;
  name?: string;
  domain: string;
  generation?: number;
  source?: string;
  pulls?: number;
  description?: string;
  tools?: number;
  relations?: [string, string][];
};
export type SphereEdge = { source: string; target: string; type: string };
export type NodeState = "running" | "done" | "failed";

const TAU = Math.PI * 2;
const PALETTE = [
  "#98e6cf",
  "#8bc9ee",
  "#dfc18c",
  "#b7a9e7",
  "#79d1d4",
  "#deab99",
  "#b8d494",
];
const EDGE_STYLE: Record<
  string,
  { stroke: string; width: number; dash: number[]; far: boolean }
> = {
  depend_on: { stroke: "#86d8bb", width: 0.9, dash: [], far: false },
  compose_with: { stroke: "#8bbce5", width: 0.7, dash: [4, 4], far: false },
  similar_to: { stroke: "#8bbce5", width: 0.55, dash: [1, 5], far: true },
};
const STATE_COLOR: Record<NodeState, string> = {
  running: "#ffe0a0",
  done: "#c8efd2",
  failed: "#ffab91",
};

const hash = (value: string) => {
  let h = 2166136261;
  for (const char of String(value)) h = Math.imul(h ^ char.charCodeAt(0), 16777619) >>> 0;
  return h;
};
export const domainColor = (domain: string) => PALETTE[hash(domain) % PALETTE.length];

const ARC_STEPS = 16;

function layout(nodes: SphereNode[]) {
  // 与 demo 相同：按 domain 字典序稳定排序后等面积铺点，
  // 相邻领域在球面上形成可读的连续带。
  const sorted = [...nodes].sort(
    (a, b) =>
      String(a.domain || "").localeCompare(String(b.domain || "")) ||
      String(a.id).localeCompare(String(b.id)),
  );
  return sorted.map((node, index) => {
    const point = position(index, sorted.length);
    return { ...node, point, color: domainColor(node.domain) };
  });
}

function arcPoints(a: Point3, b: Point3): Point3[] {
  const dot = Math.max(-1, Math.min(1, a.x * b.x + a.y * b.y + a.z * b.z));
  const theta = Math.acos(dot);
  const sine = Math.sin(theta);
  return Array.from({ length: ARC_STEPS + 1 }, (_, i) => {
    const t = i / ARC_STEPS;
    if (Math.abs(sine) < 1e-5) {
      return { x: a.x * (1 - t) + b.x * t, y: a.y * (1 - t) + b.y * t, z: a.z * (1 - t) + b.z * t };
    }
    const left = Math.sin((1 - t) * theta) / sine;
    const right = Math.sin(t * theta) / sine;
    return { x: a.x * left + b.x * right, y: a.y * left + b.y * right, z: a.z * left + b.z * right };
  });
}

type Positioned = ReturnType<typeof layout>[number] & { screen?: { x: number; y: number; z: number } };

export function createSphereRenderer(canvas: HTMLCanvasElement) {
  const ctx2d = canvas.getContext("2d", { alpha: true });
  if (!ctx2d) return null;
  // 赋成非空类型的常量，闭包内不再需要重复判空
  const context: CanvasRenderingContext2D = ctx2d;
  let disposed = false;
  let nodes: Positioned[] = [];
  const byId = new Map<string, Positioned>();
  let edges: { source: string; target: string; type: string; path: Point3[] }[] = [];
  let filter: (node: SphereNode) => boolean = () => true;
  let focusId: string | null = null;
  let states = new Map<string, NodeState>();
  let showLabels = true;
  let showRelations = true;
  let width = 0;
  let height = 0;

  const project = (point: Point3, camera: Camera) => {
    const p = rotate(point, camera);
    const radius = Math.min(width, height) * 0.36 * camera.zoom;
    const k = 3.4 / (3.4 - p.z);
    return { x: width / 2 + p.x * radius * k, y: height / 2 + p.y * radius * k, z: p.z, k };
  };

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const rect = canvas.getBoundingClientRect();
    width = rect.width;
    height = rect.height;
    if (!width || !height) return;
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
  }

  function draw(camera: Camera) {
    if (disposed) return;
    resize();
    if (!width || !height) return;
    const scale = canvas.width / width;
    context.setTransform(scale, 0, 0, scale, 0, 0);
    context.clearRect(0, 0, width, height);
    const radius = Math.min(width, height) * 0.36 * camera.zoom;
    const cx = width / 2;
    const cy = height / 2;

    // 球体辉光
    const glow = context.createRadialGradient(cx, cy, radius * 0.55, cx, cy, radius * 1.5);
    glow.addColorStop(0, "rgba(103,203,181,0.05)");
    glow.addColorStop(0.65, "rgba(126,213,206,0.09)");
    glow.addColorStop(1, "rgba(103,203,181,0)");
    context.fillStyle = glow;
    context.fillRect(0, 0, width, height);

    // 经纬线：4 条纬线 + 3 条经线，稀疏视图下也提供深度
    context.lineWidth = 0.7;
    for (let ring = 0; ring < 7; ring++) {
      context.beginPath();
      for (let i = 0; i <= 100; i++) {
        const a = (i / 100) * TAU;
        let p: Point3;
        if (ring < 4) {
          const lat = (ring - 1.5) * 0.43;
          const r = Math.sqrt(Math.max(0, 1 - lat * lat));
          p = { x: r * Math.cos(a), y: lat, z: r * Math.sin(a) };
        } else {
          const b = ((ring - 4) * Math.PI) / 3;
          p = { x: Math.cos(a) * Math.cos(b), y: Math.sin(a), z: Math.cos(a) * Math.sin(b) };
        }
        const q = project(p, camera);
        if (i) context.lineTo(q.x, q.y);
        else context.moveTo(q.x, q.y);
      }
      context.strokeStyle = "rgba(136,201,197,0.11)";
      context.stroke();
    }

    // 焦点邻域
    const focus = focusId ? byId.get(focusId) : undefined;
    const neighbors = new Set<string>();
    if (focus) {
      neighbors.add(focus.id);
      for (const edge of edges) {
        if (edge.source === focus.id) neighbors.add(edge.target);
        if (edge.target === focus.id) neighbors.add(edge.source);
      }
    }
    const active = (node: Positioned) =>
      neighbors.has(node.id) || states.has(node.id);

    // 关系边（LOD：远处 similar_to 抑制）
    if (showRelations) {
      const visible = nodes.filter((node) => filter(node));
      const visibleIds = new Set(visible.map((node) => node.id));
      for (const edge of edges) {
        const style = EDGE_STYLE[edge.type];
        if (!style) continue;
        if (!visibleIds.has(edge.source) || !visibleIds.has(edge.target)) continue;
        const hot = neighbors.has(edge.source) && neighbors.has(edge.target);
        if (style.far && !hot) continue;
        context.beginPath();
        let previous: { x: number; y: number } | null = null;
        for (const point of edge.path) {
          const p = project(point, camera);
          if (p.z < -0.25) {
            previous = null;
            continue;
          }
          if (previous) context.lineTo(p.x, p.y);
          else context.moveTo(p.x, p.y);
          previous = p;
        }
        context.setLineDash(style.dash);
        context.lineWidth = hot ? style.width + 0.6 : style.width;
        context.strokeStyle = hot
          ? "rgba(185,239,205,0.68)"
          : edge.type === "depend_on"
            ? "rgba(134,216,187,0.16)"
            : "rgba(139,188,229,0.12)";
        context.stroke();
        context.setLineDash([]);
      }
    }

    // 节点（按深度排序绘制）
    const points = nodes
      .filter((node) => filter(node))
      .map((node) => ({ node, screen: project(node.point, camera) }))
      .sort((a, b) => a.screen.z - b.screen.z);
    const dimming = focusId !== null || states.size > 0;
    for (const { node, screen } of points) {
      const hot = active(node);
      const dim = dimming && !hot;
      const state = states.get(node.id);
      const color = state ? STATE_COLOR[state] : node.color;
      const depth = (screen.z + 1) / 2;
      context.globalAlpha = (0.16 + 0.84 * depth) * (dim ? 0.16 : 1);
      const r = (hot ? 4.2 : 1.65) * screen.k;
      if (hot) {
        context.shadowBlur = 15;
        context.shadowColor = color;
      }
      context.fillStyle = color;
      context.beginPath();
      context.arc(screen.x, screen.y, Math.max(0.6, r), 0, TAU);
      context.fill();
      context.shadowBlur = 0;
      if (node.generation || state || node.id === focusId) {
        context.lineWidth = node.id === focusId ? 1.5 : 1;
        context.strokeStyle = state ? color : "#ddbc87";
        context.beginPath();
        context.arc(screen.x, screen.y, r + 3, 0, TAU);
        context.stroke();
      }
    }
    context.globalAlpha = 1;

    // 标签：焦点/邻域优先，其余按可见深度补齐，碰撞规避
    if (showLabels) {
      const occupied: { x: number; y: number; w: number; h: number }[] = [];
      let count = 0;
      const candidates = points
        .filter((p) => p.screen.z > 0 && (active(p.node) || camera.zoom > 1.5))
        .sort(
          (a, b) =>
            Number(active(b.node)) - Number(active(a.node)) || b.screen.z - a.screen.z,
        );
      if (!focusId && !states.size && camera.zoom < 1.5) {
        const domains = new Map<string, (typeof points)[number]>();
        for (const p of points) {
          if (p.screen.z > 0.2 && (!domains.has(p.node.domain) || p.screen.z > domains.get(p.node.domain)!.screen.z)) {
            domains.set(p.node.domain, p);
          }
        }
        for (const p of domains.values()) candidates.push({ ...p, domainLabel: true } as never);
      }
      for (const entry of candidates) {
        if (count >= 14) break;
        const p = entry as (typeof points)[number] & { domainLabel?: boolean };
        const label = p.domainLabel
          ? p.node.domain
          : String(p.node.name || p.node.id).replace(/^gh-/, "").slice(0, 38);
        const x = p.screen.x + 8;
        const y = p.screen.y - 8;
        context.font = "11px 'Microsoft YaHei', sans-serif";
        const w = context.measureText(label).width + 8;
        const rect = { x: x - 3, y: y - 13, w, h: 19 };
        if (
          x + w > width - 8 ||
          x < 8 ||
          y < 20 ||
          y > height - 28 ||
          occupied.some(
            (other) =>
              rect.x < other.x + other.w &&
              rect.x + rect.w > other.x &&
              rect.y < other.y + other.h &&
              rect.y + rect.h > other.y,
          )
        ) {
          continue;
        }
        occupied.push(rect);
        count++;
        context.fillStyle = "rgba(9,35,48,0.87)";
        context.fillRect(rect.x, rect.y, rect.w, rect.h);
        context.fillStyle = p.domainLabel ? "#a4c7c5" : "#e0f5e8";
        context.fillText(label, x, y);
      }
    }
  }

  return {
    setData(nextNodes: SphereNode[], nextEdges: SphereEdge[]) {
      nodes = layout(nextNodes);
      byId.clear();
      for (const node of nodes) byId.set(node.id, node);
      edges = nextEdges
        .filter((edge) => byId.has(edge.source) && byId.has(edge.target))
        .map((edge) => ({
          ...edge,
          path: arcPoints(byId.get(edge.source)!.point, byId.get(edge.target)!.point),
        }));
    },
    setFilter(next: (node: SphereNode) => boolean) {
      filter = next;
    },
    setFocus(id: string | null) {
      focusId = id;
    },
    setStates(next: Map<string, NodeState>) {
      states = next;
    },
    setLabels(value: boolean) {
      showLabels = value;
    },
    setRelations(value: boolean) {
      showRelations = value;
    },
    draw,
    point(id: string): Point3 | null {
      return byId.get(id)?.point ?? null;
    },
    hit(x: number, y: number, camera: Camera): SphereNode | null {
      const hits: { node: Positioned; z: number; d: number }[] = [];
      for (const node of nodes) {
        if (!filter(node)) continue;
        const p = project(node.point, camera);
        if (p.z < -0.15) continue;
        const d = Math.hypot(p.x - x, p.y - y);
        const radius = (focusId === node.id || neighborsOf(node.id).has(node.id) ? 4.2 : 1.65) * p.k;
        if (d < Math.max(9, radius + 4)) hits.push({ node, z: p.z, d });
      }
      if (!hits.length) return null;
      hits.sort((a, b) => b.z - a.z || a.d - b.d);
      const { node, ...rest } = hits[0];
      return node as SphereNode;
    },
    dispose() {
      disposed = true;
    },
  };

  function neighborsOf(id: string) {
    const set = new Set<string>([id]);
    for (const edge of edges) {
      if (edge.source === id) set.add(edge.target);
      if (edge.target === id) set.add(edge.source);
    }
    return set;
  }
}

export type SphereRenderer = ReturnType<typeof createSphereRenderer>;
