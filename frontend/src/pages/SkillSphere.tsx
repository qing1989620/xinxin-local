import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowUpRight,
  ArrowRight,
  RotateCcw,
  Move,
  Pause,
  Play,
  Plus,
  Minus,
  Search,
  Network,
  ScanLine,
  ChevronLeft,
  ChevronRight,
  Zap,
} from "lucide-react";
import { clamp, focusCamera, INITIAL_CAMERA, type Camera } from "./lunarGeometry";
import {
  createSphereRenderer,
  type SphereNode,
  type NodeState,
} from "./sphereRenderer";
import { originLabel as sharedOriginLabel } from "./skillOrigin";
import { api } from "../api";
import "../lunar.css";

export type SphereGraphNode = {
  id: string;
  name: string;
  domain: string;
  generation: number;
  source: string;
  pulls?: number;
  mean_reward?: number | null;
  description: string;
  tools: number;
  relations: [string, string][];
};
export type SphereGraphEdge = { source: string; target: string; type: string };
export type SphereGraph = {
  nodes: SphereGraphNode[];
  edges: SphereGraphEdge[];
  corpus?: {
    available?: boolean;
    skills?: number;
    seed?: number;
    community?: number;
    evolved?: number;
    domains?: number;
    edges?: number;
  };
  skill_count: number;
  edge_count: number;
  relation_types: string[];
};

type Motion = { from: Camera; to: Camera; started: number };

type SkillActivity = {
  running: string[];
  finished: { id: string; state: NodeState; run_id: string }[];
};
const ACTIVITY_INTERVAL = 6000;

const DIRECTORY_CAP = 60;
const DOMAIN_CHIPS = 12;
const ZOOM_MIN = 0.7;
const ZOOM_MAX = 2.6;
const RELATION_LABEL: Record<string, string> = {
  depend_on: "依赖",
  compose_with: "组合",
  similar_to: "相似",
};

function originLabel(node: SphereGraphNode): string {
  return sharedOriginLabel(node, true);
}

export default function SkillSphere({
  graph,
  onOpen,
  onRun,
  semantic,
  statusError,
}: {
  graph?: SphereGraph;
  onOpen: (node: SphereGraphNode) => void;
  onRun: (node: SphereGraphNode) => void;
  semantic?: { encoder: { kind: string; degraded?: boolean } };
  statusError?: boolean;
}) {
  const nodes = useMemo(() => graph?.nodes || [], [graph]);
  const edges = useMemo(() => graph?.edges || [], [graph]);
  const [camera, setCamera] = useState(INITIAL_CAMERA),
    [selected, setSelected] = useState(""),
    [hover, setHover] = useState(""),
    [query, setQuery] = useState(""),
    [domain, setDomain] = useState("全部"),
    [auto, setAuto] = useState(false),
    [relations, setRelations] = useState(true),
    [labels, setLabels] = useState(true),
    [executableOnly, setExecutableOnly] = useState(false),
    [active, setActive] = useState(true),
    [reduced, setReduced] = useState(false),
    [surface, setSurface] = useState(false);
  const stage = useRef<HTMLDivElement>(null),
    viewport = useRef<HTMLDivElement>(null),
    canvas = useRef<HTMLCanvasElement>(null),
    currentCamera = useRef(camera),
    renderer = useRef<ReturnType<typeof createSphereRenderer>>(null),
    animation = useRef<Motion | null>(null),
    velocity = useRef({ x: 0, y: 0 }),
    frame = useRef(0),
    lastPaint = useRef(0),
    drag = useRef<{
      id: number;
      x: number;
      y: number;
      moved: number;
    } | null>(null),
    options = useRef({ auto, active, reduced, hover });
  options.current = { auto, active, reduced, hover };
  const byId = useMemo(
    () => new Map(nodes.map((node) => [node.id, node])),
    [nodes],
  );
  const matches = useCallback(
    (node: SphereNode) =>
      (domain === "全部" || node.domain === domain) &&
      (!executableOnly || (node.tools || 0) > 0) &&
      [node.name, node.description, node.domain, node.id]
        .join(" ")
        .toLowerCase()
        .includes(query.trim().toLowerCase()),
    [domain, executableOnly, query],
  );
  const domains = useMemo(() => {
    const counts = new Map<string, number>();
    for (const node of nodes)
      counts.set(node.domain, (counts.get(node.domain) || 0) + 1);
    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .slice(0, DOMAIN_CHIPS)
      .map(([name, count]) => ({ name, count }));
  }, [nodes]);
  const filtered = useMemo(() => nodes.filter(matches), [nodes, matches]);
  const tick = useRef<(now: number) => void>(() => {});
  const schedule = useCallback(() => {
    if (!frame.current && options.current.active && !document.hidden)
      frame.current = requestAnimationFrame((now) => tick.current(now));
  }, []);
  const commit = useCallback((next: Camera) => {
    currentCamera.current = next;
    setCamera(next);
  }, []);
  tick.current = (now) => {
    frame.current = 0;
    if (!options.current.active || document.hidden) return;
    if (now - lastPaint.current < 32) {
      schedule();
      return;
    }
    lastPaint.current = now;
    const motion = animation.current;
    if (motion) {
      const progress = clamp((now - motion.started) / 520, 0, 1),
        eased = 1 - Math.pow(1 - progress, 3);
      commit({
        yaw: motion.from.yaw + (motion.to.yaw - motion.from.yaw) * eased,
        pitch:
          motion.from.pitch + (motion.to.pitch - motion.from.pitch) * eased,
        zoom: motion.from.zoom + (motion.to.zoom - motion.from.zoom) * eased,
      });
      if (progress === 1) animation.current = null;
    } else if (!drag.current) {
      const v = velocity.current;
      if (!options.current.reduced && Math.abs(v.x) + Math.abs(v.y) > 0.0004) {
        commit({
          ...currentCamera.current,
          yaw: currentCamera.current.yaw + v.x,
          pitch: clamp(currentCamera.current.pitch + v.y, -1.55, 1.55),
        });
        v.x *= 0.87;
        v.y *= 0.87;
      } else if (
        options.current.auto &&
        !options.current.reduced &&
        !options.current.hover
      ) {
        commit({
          ...currentCamera.current,
          yaw: currentCamera.current.yaw + 0.003,
        });
      } else return;
    }
    if (!drag.current) schedule();
  };
  const moveTo = useCallback(
    (to: Camera) => {
      velocity.current = { x: 0, y: 0 };
      if (options.current.reduced) {
        animation.current = null;
        commit(to);
      } else {
        animation.current = {
          from: currentCamera.current,
          to,
          started: performance.now(),
        };
        schedule();
      }
    },
    [commit, schedule],
  );
  // 球面坐标由渲染器按 domain 稳定排序后计算，这里只负责镜头动画
  const chooseNode = useCallback(
    (node: SphereGraphNode) => {
      setSelected(node.id);
      setAuto(false);
      setHover("");
      const point = renderer.current?.point(node.id);
      if (point) moveTo(focusCamera(point, currentCamera.current));
    },
    [moveTo],
  );
  useEffect(() => {
    const media = matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => {
      setReduced(media.matches);
      if (media.matches) {
        setAuto(false);
        velocity.current = { x: 0, y: 0 };
        if (animation.current) {
          commit(animation.current.to);
          animation.current = null;
        }
      }
    };
    update();
    media.addEventListener("change", update);
    const observer = new IntersectionObserver((entries) =>
      setActive(entries[0].isIntersecting),
    );
    if (stage.current) observer.observe(stage.current);
    const visibility = () => {
      if (document.hidden) {
        if (frame.current) cancelAnimationFrame(frame.current);
        frame.current = 0;
      } else schedule();
    };
    document.addEventListener("visibilitychange", visibility);
    return () => {
      media.removeEventListener("change", update);
      observer.disconnect();
      document.removeEventListener("visibilitychange", visibility);
      if (frame.current) cancelAnimationFrame(frame.current);
    };
  }, [commit, schedule]);
  useEffect(() => {
    if (
      (auto && !reduced) ||
      animation.current ||
      Math.abs(velocity.current.x) + Math.abs(velocity.current.y) > 0.0004
    )
      schedule();
  }, [auto, active, reduced, hover, schedule]);
  // 画布渲染器：一次创建，数据/筛选/焦点变化时增量更新
  useEffect(() => {
    const element = canvas.current;
    if (!element) return;
    renderer.current = createSphereRenderer(element);
    setSurface(Boolean(renderer.current));
    const resize = new ResizeObserver(() =>
      renderer.current?.draw(currentCamera.current),
    );
    resize.observe(element);
    renderer.current?.draw(currentCamera.current);
    return () => {
      resize.disconnect();
      renderer.current?.dispose();
      renderer.current = null;
    };
  }, []);
  useEffect(() => {
    renderer.current?.setData(nodes, edges);
    renderer.current?.draw(currentCamera.current);
  }, [nodes, edges]);
  useEffect(() => {
    renderer.current?.setFilter(matches);
    renderer.current?.draw(currentCamera.current);
  }, [matches]);
  useEffect(() => {
    renderer.current?.setLabels(labels);
    renderer.current?.setRelations(relations);
    renderer.current?.draw(currentCamera.current);
  }, [labels, relations]);
  useEffect(() => {
    renderer.current?.setFocus(selected || hover || null);
    renderer.current?.draw(camera);
  }, [camera, hover, selected]);
  // 滚轮缩放（原生监听，避免被动事件无法阻止默认滚动）
  useEffect(() => {
    const element = viewport.current;
    if (!element) return;
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      setAuto(false);
      moveTo({
        ...currentCamera.current,
        zoom: clamp(
          currentCamera.current.zoom * Math.exp(-event.deltaY * 0.0012),
          ZOOM_MIN,
          ZOOM_MAX,
        ),
      });
    };
    element.addEventListener("wheel", onWheel, { passive: false });
    return () => element.removeEventListener("wheel", onWheel);
  }, [moveTo]);
  useEffect(() => {
    if (selected && !byId.has(selected)) setSelected(nodes[0]?.id || "");
  }, [nodes, selected, byId]);
  // 运行态：轮询 /skills/activity（聚合既有 runs/events），
  // 把进行中与最近结束的技能状态喂给渲染器做高亮/变暗。
  const [activity, setActivity] = useState<SkillActivity>({
    running: [],
    finished: [],
  });
  useEffect(() => {
    let alive = true;
    const load = () => {
      api<SkillActivity>("/skills/activity")
        .then((value) => {
          if (alive) setActivity(value);
        })
        .catch(() => {
          /* 运行态是增强信息，失败时保持上一次快照 */
        });
    };
    load();
    const timer = window.setInterval(() => {
      if (!document.hidden) load();
    }, ACTIVITY_INTERVAL);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, []);
  const runStates = useMemo(() => {
    const map = new Map<string, NodeState>();
    // finished 按时间倒序返回，先写入者更新；running 覆盖一切历史状态
    for (const item of activity.finished) {
      if (item.state === "done" || item.state === "failed" || item.state === "running")
        map.set(item.id, item.state);
    }
    for (const id of activity.running) map.set(id, "running");
    return map;
  }, [activity]);
  useEffect(() => {
    renderer.current?.setStates(runStates);
    renderer.current?.draw(currentCamera.current);
  }, [runStates]);
  const runningCount = activity.running.length;
  const current = selected ? byId.get(selected) : undefined,
    index = nodes.findIndex((node) => node.id === selected);
  const relationSummary = useMemo(() => {
    const counts = new Map<string, number>();
    for (const [type] of current?.relations || [])
      counts.set(type, (counts.get(type) || 0) + 1);
    return counts;
  }, [current]);
  function zoom(delta: number) {
    setAuto(false);
    moveTo({
      ...currentCamera.current,
      zoom: clamp(
        (animation.current?.to.zoom ?? currentCamera.current.zoom) + delta,
        ZOOM_MIN,
        ZOOM_MAX,
      ),
    });
  }
  function locate(event: { clientX: number; clientY: number }) {
    const element = canvas.current;
    if (!element || !renderer.current) return null;
    const rect = element.getBoundingClientRect();
    return renderer.current.hit(
      event.clientX - rect.left,
      event.clientY - rect.top,
      currentCamera.current,
    );
  }
  function release(event: React.PointerEvent<HTMLDivElement>) {
    const dragging = drag.current;
    if (!dragging || event.pointerId !== dragging.id) return;
    drag.current = null;
    if (event.currentTarget.hasPointerCapture(event.pointerId))
      event.currentTarget.releasePointerCapture(event.pointerId);
    if (event.type === "pointerup" && dragging.moved < 6) {
      const hit = locate(event);
      if (hit) chooseNode(hit as SphereGraphNode);
    } else if (event.type === "pointerup" && !reduced) schedule();
    else velocity.current = { x: 0, y: 0 };
  }
  const corpus = graph?.corpus;
  return (
    <section className="lunar-explorer" aria-label="Xinxin 的交互能力星图">
      <div className="atlas-stage" ref={stage}>
        <header className="atlas-stage-heading">
          <div>
            <span className="atlas-kicker">XINXIN / CAPABILITY ATLAS</span>
            <h2>小小星球，大有可为。</h2>
          </div>
          <span className="atlas-live">
            <i />
            {graph?.skill_count ?? nodes.length} 个能力
            {graph?.edge_count ? ` · ${graph.edge_count} 项关系` : ""}
            {runningCount > 0 && (
              <em className="atlas-running" role="status">
                {runningCount} 个进行中
              </em>
            )}
          </span>
        </header>
        <div
          className="atlas-viewport"
          ref={viewport}
          data-renderer={surface ? "sphere-canvas" : "node-map"}
          tabIndex={0}
          role="group"
          aria-label="技能星球，拖动旋转，滚轮缩放，方向键调整，Home 复位，空格切换旋转"
          aria-describedby="atlas-help"
          onKeyDown={(event) => {
            if (event.target !== event.currentTarget) return;
            if (
              ![
                "ArrowLeft",
                "ArrowRight",
                "ArrowUp",
                "ArrowDown",
                "Home",
                "+",
                "=",
                "-",
                " ",
              ].includes(event.key)
            )
              return;
            event.preventDefault();
            if (event.key === " ") {
              setAuto((value) => !value && !reduced);
              return;
            }
            setAuto(false);
            if (event.key === "Home") moveTo(INITIAL_CAMERA);
            else if (event.key === "+" || event.key === "=") zoom(0.12);
            else if (event.key === "-") zoom(-0.12);
            else
              moveTo({
                ...currentCamera.current,
                yaw:
                  currentCamera.current.yaw +
                  (event.key === "ArrowLeft"
                    ? -0.25
                    : event.key === "ArrowRight"
                      ? 0.25
                      : 0),
                pitch: clamp(
                  currentCamera.current.pitch +
                    (event.key === "ArrowUp"
                      ? -0.2
                      : event.key === "ArrowDown"
                        ? 0.2
                        : 0),
                  -1.55,
                  1.55,
                ),
              });
          }}
          onPointerDown={(event) => {
            if (event.button !== 0 || drag.current) return;
            animation.current = null;
            velocity.current = { x: 0, y: 0 };
            setAuto(false);
            drag.current = {
              id: event.pointerId,
              x: event.clientX,
              y: event.clientY,
              moved: 0,
            };
            event.currentTarget.setPointerCapture(event.pointerId);
          }}
          onPointerMove={(event) => {
            const d = drag.current;
            if (d && event.pointerId === d.id) {
              const dx = event.clientX - d.x,
                dy = event.clientY - d.y;
              d.moved += Math.abs(dx) + Math.abs(dy);
              d.x = event.clientX;
              d.y = event.clientY;
              velocity.current = { x: dx * 0.005, y: dy * 0.005 };
              commit({
                ...currentCamera.current,
                yaw: currentCamera.current.yaw + dx * 0.006,
                pitch: clamp(
                  currentCamera.current.pitch + dy * 0.006,
                  -1.55,
                  1.55,
                ),
              });
              return;
            }
            if (event.pointerType === "touch") return;
            const hit = locate(event);
            const id = (hit as SphereGraphNode | null)?.id || "";
            if (id !== hover) {
              setHover(id);
              if (viewport.current)
                viewport.current.style.cursor = id ? "pointer" : "grab";
            }
          }}
          onPointerUp={release}
          onPointerCancel={release}
          onLostPointerCapture={release}
          onPointerLeave={() => {
            if (hover) setHover("");
          }}
        >
          <div className="atlas-stars" aria-hidden="true" />
          <canvas className="atlas-particles" ref={canvas} aria-hidden="true" />
          <div className="atlas-scale" aria-hidden="true">
            <i />
            <span>{Math.round(camera.zoom * 100)}%</span>
          </div>
          <p className="atlas-coordinate" aria-hidden="true">
            {(((camera.yaw * 180) / Math.PI) % 360).toFixed(1)}° /{" "}
            {((camera.pitch * 180) / Math.PI).toFixed(1)}°
          </p>
        </div>
        <div className="atlas-controls" aria-label="星图显示控制">
          <div>
            <button
              title={
                auto
                  ? "暂停旋转"
                  : reduced
                    ? "系统已开启减少动态效果"
                    : "缓慢旋转"
              }
              aria-label={auto ? "暂停旋转" : "缓慢旋转"}
              aria-pressed={auto}
              disabled={reduced}
              onClick={() => setAuto((value) => !value)}
            >
              {auto ? <Pause size={16} /> : <Play size={16} />}
            </button>
            <span className="atlas-control-divider" />
            <button
              aria-label="缩小星球"
              disabled={camera.zoom <= ZOOM_MIN + 0.001}
              onClick={() => zoom(-0.12)}
            >
              <Minus size={16} />
            </button>
            <button
              aria-label="放大星球"
              disabled={camera.zoom >= ZOOM_MAX - 0.001}
              onClick={() => zoom(0.12)}
            >
              <Plus size={16} />
            </button>
            <button
              aria-label="复位星图"
              onClick={() => {
                setAuto(false);
                moveTo(INITIAL_CAMERA);
              }}
            >
              <RotateCcw size={15} />
            </button>
          </div>
          <div>
            <button
              className={executableOnly ? "active" : ""}
              aria-label="只看可执行能力"
              aria-pressed={executableOnly}
              title="只看注册了平台工具的技能"
              onClick={() => setExecutableOnly((value) => !value)}
            >
              <Zap size={16} />
            </button>
            <button
              className={relations ? "active" : ""}
              aria-label="显示关系连线"
              aria-pressed={relations}
              onClick={() => setRelations((value) => !value)}
            >
              <Network size={16} />
            </button>
            <button
              className={labels ? "active" : ""}
              aria-label="显示技能标签"
              aria-pressed={labels}
              onClick={() => setLabels((value) => !value)}
            >
              <ScanLine size={16} />
            </button>
          </div>
        </div>
        <footer className="atlas-stage-footer">
          <span id="atlas-help">
            <Move size={12} />
            拖动探索 · 点选聚焦 · 滚轮缩放
          </span>
          <span>
            {surface ? "CAPABILITY SPHERE" : "技能节点视图"} /{" "}
            {graph?.edge_count || edges.length} 项关系
            {graph?.relation_types?.length
              ? `（${graph.relation_types.map((type) => RELATION_LABEL[type] || type).join(" · ")}）`
              : ""}
          </span>
        </footer>
      </div>
      <aside className="atlas-directory">
        <header>
          <span className="eyebrow">A LITTLE HELP, A LOT DONE.</span>
          <h2>有事，尽管交给我。</h2>
          <p>选一个能力，看看 Xinxin 能怎么帮你。</p>
        </header>
        <label className="atlas-search">
          <Search size={15} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="寻找一种能力"
            aria-label="搜索星图技能"
            onKeyDown={(event) => {
              if (event.key === "Enter" && filtered.length)
                chooseNode(filtered[0]);
            }}
          />
          <kbd>{filtered.length}</kbd>
        </label>
        <div className="atlas-filters" aria-label="筛选技能领域">
          {[{ name: "全部", count: nodes.length }, ...domains].map((item) => (
            <button
              key={item.name}
              aria-pressed={domain === item.name}
              onClick={() => setDomain(item.name)}
            >
              {item.name === "全部" ? "全部" : item.name}
              <span>{item.count}</span>
            </button>
          ))}
        </div>
        <div className="atlas-directory-list" aria-label="技能列表">
          {filtered.slice(0, DIRECTORY_CAP).map((node) => (
            <button
              key={node.id}
              aria-pressed={node.id === selected}
              className={node.id === selected ? "selected" : ""}
              onClick={() => chooseNode(node)}
            >
              <span className="atlas-list-dot" />
              <strong>{node.name}</strong>
              <small>
                {node.domain}
                {node.generation > 0 ? ` · G${node.generation}` : ""}
              </small>
              <ArrowUpRight size={13} />
            </button>
          ))}
          {filtered.length > DIRECTORY_CAP && (
            <p className="atlas-cap-note" role="status">
              共 {filtered.length} 项，仅显示前 {DIRECTORY_CAP}
              项；用搜索或领域缩小范围。
            </p>
          )}
          {!filtered.length && (
            <p className="atlas-no-results" role="status">
              还没找到，换个关键词试试呀。
            </p>
          )}
        </div>
        {current ? (
          <section
            className="atlas-inspector"
            aria-label="当前技能"
            aria-live="polite"
          >
            <div className="atlas-selection-count">
              <span>
                {String(index + 1).padStart(2, "0")}{" "}
                <i>/ {String(nodes.length).padStart(2, "0")}</i>
              </span>
              <div>
                <button
                  aria-label="上一个技能"
                  onClick={() =>
                    chooseNode(nodes[(index - 1 + nodes.length) % nodes.length])
                  }
                >
                  <ChevronLeft size={16} />
                </button>
                <button
                  aria-label="下一个技能"
                  onClick={() => chooseNode(nodes[(index + 1) % nodes.length])}
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
            <span className="atlas-domain">
              {current.domain} · {current.tools || 0} 个工具 ·{" "}
              <em className="atlas-gen">{originLabel(current)}</em>
            </span>
            <h3>{current.name}</h3>
            <p>{current.description}</p>
            {relationSummary.size > 0 && (
              <div className="atlas-relation-row" aria-label="登记关系">
                {[...relationSummary.entries()].map(([type, count]) => (
                  <span key={type} className={`atlas-relation-chip ${type}`}>
                    {RELATION_LABEL[type] || type} {count}
                  </span>
                ))}
              </div>
            )}
            {(current.relations || []).slice(0, 6).map(([type, target]) => (
              <button
                className="atlas-dependency"
                key={type + target}
                onClick={() => {
                  const node = byId.get(target);
                  if (node) chooseNode(node);
                }}
              >
                <Network size={13} />
                {RELATION_LABEL[type] || type} {byId.get(target)?.name || target}
                <ArrowUpRight size={12} />
              </button>
            ))}
            <div className="atlas-inspector-actions">
              <button className="button primary" onClick={() => onRun(current)}>
                和 Xinxin 开始
                <ArrowRight size={15} />
              </button>
              <button className="text-button" onClick={() => onOpen(current)}>
                了解能力
                <ArrowUpRight size={14} />
              </button>
            </div>
          </section>
        ) : (
          <p>选择一个能力后，在这里查看用途与工具。</p>
        )}
        <footer className="atlas-model-status">
          <i />
          {semantic
            ? semantic.encoder.kind === "dense-onnx"
              ? "语义模型已连接"
              : semantic.encoder.degraded
                ? "语义模型未就绪 · 当前使用词法检索"
                : "轻量词法检索"
            : statusError
              ? "检索状态暂不可用，稍后重试"
              : "正在读取检索状态…"}
          {corpus?.available ? (
            <span>
              SkillNet 语料 {corpus.skills} · 种子 {corpus.seed} · 社区{" "}
              {corpus.community} · 演化 {corpus.evolved}
            </span>
          ) : (
            <span>SkillNet</span>
          )}
        </footer>
      </aside>
    </section>
  );
}
