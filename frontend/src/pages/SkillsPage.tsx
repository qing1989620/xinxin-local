import { useEffect, useRef, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import SkillSphere, { type SphereGraph } from "./SkillSphere";
import { originKind, type OriginKind } from "./skillOrigin";
import {
  ArrowUpRight,
  ArrowRight,
  Search,
  Sparkles,
  Network,
  LayoutGrid,
  List,
  ShieldCheck,
  Check,
  ChevronRight,
  FlaskConical,
  BookOpen,
  FileText,
  Layers,
} from "lucide-react";
import { api } from "../api";
import {
  PageHeader,
  Dialog,
  Empty,
  Loading,
  ErrorState,
  useResource,
  useToast,
} from "../ui";
type Skill = {
  id: string;
  name: string;
  description: string;
  domain: string;
  tools: string[];
  relations: [string, string][];
  corpus_source?: string;
  generation?: number;
  capability?: string;
  tags?: string[];
  stats?: { pulls: number; best: number; mean_reward: number | null };
  score?: number;
  channels?: Record<string, number>;
};
type SkillStatus = {
  encoder: {
    kind: string;
    degraded?: boolean;
    reason?: string;
    model?: string;
  };
  weights: number[];
  skill_count: number;
};
type Selection = SkillStatus & {
  query: string;
  skills: Skill[];
  dependencies: Skill[];
  order: string[];
  algorithm: string;
  learning_updates: number;
};
type Detail = {
  name: string;
  skill?: Skill;
  passport?: {
    capability: string;
    use_when: string[];
    inputs: string[];
    outputs: string[];
    pitfalls: string[];
    verification: string[];
    steps: string[];
    boundary: string;
    environment: string;
  };
  markdown: string;
  resources?: { path: string; bytes: number; sha256: string }[];
  provenance?: Record<string, string>;
  corpus_source?: string;
  generation?: number;
  relations?: { type: string; target: string }[];
};
const LIBRARY_CAP = 60;
const GENERATIONS: { key: string; label: string }[] = [
  { key: "all", label: "全部" },
  { key: "platform", label: "平台可执行" },
  { key: "community", label: "社区导入" },
  { key: "evolved", label: "演化" },
];
function generationOf(skill: Skill): OriginKind {
  return originKind(skill);
}
export default function SkillsPage() {
  const detailRequest = useRef<AbortController | null>(null);
  const resourceRequest = useRef<AbortController | null>(null);
  useEffect(
    () => () => {
      detailRequest.current?.abort();
      resourceRequest.current?.abort();
    },
    [],
  );
  function closeDetail() {
    detailRequest.current?.abort();
    resourceRequest.current?.abort();
    setDetail(null);
  }
  const request = useRef(0);
  const { data, error, reload } = useResource<Skill[]>("/skills"),
    { data: status, error: statusError } =
      useResource<SkillStatus>("/skills/status"),
    { data: graph } = useResource<SphereGraph>("/skills/graph"),
    [tab, setTab] = useState("sphere"),
    [filter, setFilter] = useState("all"),
    [generation, setGeneration] = useState("all"),
    [shown, setShown] = useState(LIBRARY_CAP),
    [query, setQuery] = useState(""),
    [layout, setLayout] = useState("grid"),
    [detail, setDetail] = useState<Detail | null>(null),
    [resourceText, setResourceText] = useState<string>(""),
    [goal, setGoal] = useState(""),
    [selection, setSelection] = useState<Selection | null>(null),
    [busy, setBusy] = useState(false),
    toast = useToast(),
    navigate = useNavigate();
  async function open(skill: Pick<Skill, "id">) {
    if (!skill) return;
    detailRequest.current?.abort();
    resourceRequest.current?.abort();
    const controller = new AbortController();
    detailRequest.current = controller;
    try {
      const result = await api<Detail>(`/skills/${skill.id}`, {
        signal: controller.signal,
      });
      if (controller.signal.aborted) return;
      setDetail({
        ...result,
        name: result.name || skill.id,
        skill: {
          ...(data?.find((item) => item.id === skill.id) || {}),
          ...(result.skill || {}),
          id: skill.id,
        } as Skill,
      });
      setResourceText("");
    } catch (error) {
      if (!controller.signal.aborted) toast((error as Error).message, true);
    }
  }
  async function readResource(path: string) {
    if (!detail) return;
    resourceRequest.current?.abort();
    const controller = new AbortController();
    resourceRequest.current = controller;
    try {
      const result = await api<{ text: string; bytes: number; sha256: string }>(
        `/skills/${detail.name}/resource?path=${encodeURIComponent(path)}`,
        { signal: controller.signal },
      );
      if (controller.signal.aborted) return;
      setResourceText(
        `# ${path}（${result.bytes} 字节 · sha256 ${result.sha256.slice(0, 12)}）\n\n${result.text}`,
      );
    } catch (error) {
      if (!controller.signal.aborted) toast((error as Error).message, true);
    }
  }
  async function find(value: string) {
    if (!value.trim()) return;
    const revision = ++request.current;
    setBusy(true);
    try {
      const result = await api<Selection>(
        "/skills?q=" + encodeURIComponent(value),
      );
      if (request.current === revision) setSelection(result);
    } catch (error) {
      if (request.current === revision) toast((error as Error).message, true);
    } finally {
      if (request.current === revision) setBusy(false);
    }
  }
  if (error) return <ErrorState message={error} retry={reload} />;
  if (!data) return <Loading />;
  const domains = ["all", ...new Set(data.map((skill) => skill.domain))],
    visible = data.filter(
      (skill) =>
        (filter === "all" || skill.domain === filter) &&
        (generation === "all" || generationOf(skill) === generation) &&
        [skill.name, skill.description, ...skill.tools, skill.capability || ""]
          .join(" ")
          .toLowerCase()
          .includes(query.toLowerCase()),
    );
  const byId = new Map(
    [...(selection?.dependencies || []), ...(selection?.skills || [])].map(
      (skill) => [skill.id, skill],
    ),
  );
  const method = selection || status;
  const resetShown = () => setShown(LIBRARY_CAP);
  return (
    <div className="page-enter skills-v2">
      <PageHeader
        overline="CAPABILITIES, WITH INTENTION"
        title="技能中心"
        description="让合适的能力，在合适的时候参与工作。"
        meta={
          <>
            <span>
              <strong>{data.length}</strong>项能力
            </span>
            <span>SkillNet · 从目标找到方法</span>
          </>
        }
        action={
          <button
            className="button secondary"
            onClick={() => setTab(tab === "library" ? "lab" : "library")}
          >
            <FlaskConical size={16} />
            {tab === "library" ? "试一试技能选择" : "返回技能库"}
          </button>
        }
      />
      <div className="workspace-page-tabs">
        <button
          className={tab === "sphere" ? "active" : ""}
          aria-pressed={tab === "sphere"}
          onClick={() => setTab("sphere")}
        >
          <Sparkles size={15} />
          能力星图
        </button>
        <button
          className={tab === "library" ? "active" : ""}
          aria-pressed={tab === "library"}
          onClick={() => setTab("library")}
        >
          <BookOpen size={15} />
          能力库 <span>{data.length}</span>
        </button>
        <button
          className={tab === "lab" ? "active" : ""}
          aria-pressed={tab === "lab"}
          onClick={() => setTab("lab")}
        >
          <Network size={15} />
          选择预览
        </button>
      </div>
      {tab === "sphere" ? (
        <SkillSphere
          graph={graph || undefined}
          semantic={status || undefined}
          statusError={Boolean(statusError)}
          onOpen={(node) => void open(node)}
          onRun={(node) =>
            navigate("/agent", {
              state: {
                prompt: `Xinxin，请先加载 ${node.id}（${node.name}）技能，帮我处理一个相关任务。先结合我的目标确认必要输入与本轮权限。`,
              },
            })
          }
        />
      ) : tab === "library" ? (
        <>
          <div className="skill-library-toolbar">
            <label className="search-field">
              <Search size={16} />
              <input
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  resetShown();
                }}
                placeholder="搜索技能、用途或工具"
                aria-label="搜索技能库"
              />
            </label>
            <div className="view-toggle">
              <button
                aria-label="网格视图"
                aria-pressed={layout === "grid"}
                className={layout === "grid" ? "selected" : ""}
                onClick={() => setLayout("grid")}
              >
                <LayoutGrid size={16} />
              </button>
              <button
                aria-label="列表视图"
                aria-pressed={layout === "list"}
                className={layout === "list" ? "selected" : ""}
                onClick={() => setLayout("list")}
              >
                <List size={17} />
              </button>
            </div>
          </div>
          <div className="skill-domains" aria-label="技能领域">
            {domains.map((domain) => (
              <button
                key={domain}
                className={filter === domain ? "selected" : ""}
                aria-pressed={filter === domain}
                onClick={() => {
                  setFilter(domain);
                  resetShown();
                }}
              >
                {domain === "all" ? "全部能力" : domain}
                <span>
                  {domain === "all"
                    ? data.length
                    : data.filter((skill) => skill.domain === domain).length}
                </span>
              </button>
            ))}
          </div>
          <div className="skill-generations" aria-label="按来源筛选">
            <Layers size={14} />
            {GENERATIONS.map((item) => (
              <button
                key={item.key}
                className={generation === item.key ? "selected" : ""}
                aria-pressed={generation === item.key}
                onClick={() => {
                  setGeneration(item.key);
                  resetShown();
                }}
              >
                {item.label}
                <span>
                  {item.key === "all"
                    ? data.length
                    : data.filter((skill) => generationOf(skill) === item.key)
                        .length}
                </span>
              </button>
            ))}
          </div>
          <div
            className={`capability-grid ${layout === "list" ? "list-view" : ""}`}
          >
            {visible.slice(0, shown).map((skill) => (
              <button
                className="capability-card"
                key={skill.id}
                onClick={() => void open(skill)}
              >
                <div className="capability-top">
                  <span className="capability-symbol">
                    <Sparkles size={22} strokeWidth={1.2} />
                  </span>
                  <span className="eyebrow">{skill.domain}</span>
                  <ArrowUpRight size={16} />
                </div>
                <h2>{skill.name}</h2>
                <p>{skill.description}</p>
                <div className="capability-bottom">
                  <span>
                    <span className="connection-dot ready" />
                    {generationOf(skill) === "platform"
                      ? "可执行"
                      : generationOf(skill) === "community"
                        ? "社区资料"
                        : generationOf(skill) === "evolved"
                          ? `演化 G${skill.generation}`
                          : "已登记"}
                  </span>
                  <span>
                    {skill.tools.length} 个工具
                    {skill.relations.length > 0 &&
                      ` · ${skill.relations.length} 项依赖`}
                    {skill.stats?.pulls ? ` · ${skill.stats.pulls} 次调用` : ""}
                  </span>
                </div>
              </button>
            ))}
          </div>
          {visible.length > shown && (
            <div className="library-more">
              <button
                className="button secondary"
                onClick={() => setShown((value) => value + LIBRARY_CAP)}
              >
                显示更多（还有 {visible.length - shown} 项）
                <ChevronRight size={15} />
              </button>
            </div>
          )}
          {!visible.length && (
            <Empty
              title="还没找到合适的能力"
              description="试试不同的用途或领域关键词。"
            />
          )}
          <div className="context-note">
            <ShieldCheck size={19} />
            <p>
              能力通过平台注册工具完成工作。社区与语料技能是只读资料，执行范围由本轮任务权限决定。
            </p>
          </div>
        </>
      ) : (
        <div className="routing-lab">
          <section className="routing-input desk-panel">
            <div className="lab-intro">
              <span className="resource-icon">
                <FlaskConical size={25} strokeWidth={1.2} />
              </span>
              <p className="eyebrow">FROM INTENT TO CAPABILITY</p>
              <h2>先看看，这件事需要什么。</h2>
              <p>
                写下一个目标，预览候选能力与依赖顺序，再带着上下文进入对话。
              </p>
            </div>
            <form
              onSubmit={(e: FormEvent) => {
                e.preventDefault();
                void find(goal);
              }}
            >
              <label>
                你想完成的目标
                <textarea
                  rows={4}
                  maxLength={2000}
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  placeholder="例如：从 GitHub 部署一个网站，并验证它能正常访问。"
                  required
                />
              </label>
              <button
                className="button primary"
                disabled={busy || !goal.trim()}
              >
                {busy ? "正在选择…" : "预览技能选择"}
                <ArrowRight size={16} />
              </button>
            </form>
            <div className="lab-examples">
              {[
                "部署 GitHub 网站",
                "阅读私人 PDF 并总结",
                "用 CSV 绘制趋势图",
                "把照片转换为实景拼贴",
              ].map((example) => (
                <button
                  key={example}
                  onClick={() => {
                    setGoal(example);
                    void find(example);
                  }}
                >
                  {example}
                  <ArrowUpRight size={12} />
                </button>
              ))}
            </div>
            <div className="routing-method">
              <span className="eyebrow">本地检索 + 反馈学习</span>
              <div>
                <span>
                  关键词
                  <strong>
                    {method ? `${Math.round(method.weights[0] * 100)}%` : "…"}
                  </strong>
                </span>
                <span>
                  {method?.encoder.kind === "dense-onnx"
                    ? "E5 语义"
                    : "词法向量"}
                  <strong>
                    {method ? `${Math.round(method.weights[1] * 100)}%` : "…"}
                  </strong>
                </span>
                <span>
                  领域标签
                  <strong>
                    {method ? `${Math.round(method.weights[2] * 100)}%` : "…"}
                  </strong>
                </span>
                <span>
                  LinUCB<strong>反馈后参与</strong>
                </span>
              </div>
              <p>
                {method?.encoder.degraded &&
                  "语义模型未就绪，当前已回退词法检索。"}
                评分表示候选的相对排序。Xinxin
                会按任务需要选择，不会自动调用全部候选；执行权限由你在对话中设置。
              </p>
            </div>
          </section>
          <section className="routing-results desk-panel">
            <header className="desk-panel-header">
              <div>
                <span className="eyebrow">SELECTION & ORDER</span>
                <h2>{selection ? "选择结果" : "等待一个目标"}</h2>
              </div>
              {selection && (
                <span className="subtle-badge">
                  {selection.skills.length} 项候选
                </span>
              )}
            </header>
            {selection ? (
              <>
                <div className="routing-goal">{selection.query}</div>
                <div className="ranked-skills">
                  {selection.skills.map((skill, index) => (
                    <button key={skill.id} onClick={() => void open(skill)}>
                      <span className="rank-index">
                        {String(index + 1).padStart(2, "0")}
                      </span>
                      <span>
                        <strong>{skill.name}</strong>
                        <small>{skill.description}</small>
                        {skill.channels && (
                          <span className="routing-channel-tags">
                            {Object.keys(skill.channels)
                              .map(
                                (channel) =>
                                  ({
                                    bm25: "关键词",
                                    vector:
                                      selection.encoder.kind === "dense-onnx"
                                        ? "语义"
                                        : "词法向量",
                                    structural: "领域标签",
                                  })[channel],
                              )
                              .filter(Boolean)
                              .join(" · ")}
                          </span>
                        )}
                        <span className="rank-meter">
                          <i
                            style={{
                              width: `${Math.max(2, (Number(skill.score) / Math.max(...selection.skills.map((item) => Number(item.score)), 0.01)) * 100)}%`,
                            }}
                          />
                        </span>
                      </span>
                      <span className="rank-score">
                        {Number(skill.score).toFixed(2)}
                        <ArrowUpRight size={13} />
                      </span>
                    </button>
                  ))}
                </div>
                <div className="routing-order">
                  <p className="eyebrow">候选能力的依赖顺序 · 执行时按需选择</p>
                  <div>
                    {selection.order.map((id, index) => (
                      <button key={id} onClick={() => void open(byId.get(id)!)}>
                        <span>{index + 1}</span>
                        {byId.get(id)?.name || id}
                        {index < selection.order.length - 1 && (
                          <ChevronRight size={13} />
                        )}
                      </button>
                    ))}
                  </div>
                </div>
                <footer className="routing-result-footer">
                  <span>{selection.learning_updates} 次有证据的反馈学习</span>
                  <button
                    className="button secondary"
                    onClick={() =>
                      navigate("/agent", { state: { prompt: selection.query } })
                    }
                  >
                    带着目标开始对话
                    <ArrowUpRight size={15} />
                  </button>
                </footer>
              </>
            ) : (
              <Empty
                title="让选择有依据"
                description="结果会展示相关能力、评分与依赖顺序。"
              />
            )}
          </section>
        </div>
      )}
      {detail && (
        <Dialog title={detail.name} onClose={closeDetail} wide>
          <div className="skill-detail-meta">
            <span className="subtle-badge">{detail.skill?.domain}</span>
            <span>{detail.skill?.tools?.length || 0} 个注册工具</span>
            {detail.generation ? <span>演化 G{detail.generation}</span> : null}
            {detail.corpus_source === "github" ? (
              <span>社区导入 · 只读资料</span>
            ) : null}
            {detail.skill?.stats?.pulls ? (
              <span>{detail.skill.stats.pulls} 次调用</span>
            ) : null}
            <button
              className="text-button"
              onClick={() =>
                navigate("/agent", {
                  state: {
                    prompt: `请先加载 ${detail.name} 技能，帮我处理一个与它相关的任务，先明确输入与权限。`,
                  },
                })
              }
            >
              交给 Agent
              <ArrowUpRight size={14} />
            </button>
          </div>
          {detail.passport && (
            <div className="skill-passport">
              {detail.passport.use_when?.length > 0 && (
                <div>
                  <h4>适用场景</h4>
                  <ul>
                    {detail.passport.use_when.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
              {detail.passport.inputs?.length > 0 && (
                <div>
                  <h4>输入</h4>
                  <p>{detail.passport.inputs.join("；")}</p>
                </div>
              )}
              {detail.passport.outputs?.length > 0 && (
                <div>
                  <h4>输出</h4>
                  <p>{detail.passport.outputs.join("；")}</p>
                </div>
              )}
              {detail.passport.pitfalls?.length > 0 && (
                <div>
                  <h4>失效边界</h4>
                  <ul>
                    {detail.passport.pitfalls.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
              {detail.passport.environment && (
                <div>
                  <h4>环境要求</h4>
                  <p>{detail.passport.environment}</p>
                </div>
              )}
              <p className="skill-passport-boundary">
                <ShieldCheck size={13} />
                {detail.passport.boundary}
              </p>
            </div>
          )}
          <div className="markdown skill-markdown">
            {detail.provenance && (
              <p className="skill-provenance">
                来源：
                <a
                  href={detail.provenance.source_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  {detail.provenance.repository}
                </a>{" "}
                · {detail.provenance.license}
                <br />
                固定版本{" "}
                {String(
                  detail.provenance.revision || detail.provenance.commit || "",
                ).slice(0, 12)}
                ，保留原始参考包。方法说明已接入；脚本与外部依赖须按任务检查，未经自动执行认证。
              </p>
            )}
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              skipHtml
              components={{ img: ({ alt }) => <span>[参考图片：{alt}]</span> }}
            >
              {resourceText ||
                String(detail.markdown || "").replace(
                  /^---\r?\n[\s\S]*?\r?\n---\r?\n/,
                  "",
                )}
            </ReactMarkdown>
          </div>
          {detail.resources && detail.resources.length > 0 && (
            <div className="skill-resource-list">
              <h4>
                <FileText size={13} />
                参考资源（{detail.resources.length}）
              </h4>
              {detail.resources.slice(0, 24).map((item) => (
                <button
                  key={item.path}
                  className="text-button"
                  onClick={() => void readResource(item.path)}
                >
                  {item.path}
                  <small>{item.bytes} B</small>
                  <ArrowUpRight size={12} />
                </button>
              ))}
              {detail.resources.length > 24 && (
                <p className="atlas-cap-note">
                  共 {detail.resources.length} 个资源，仅显示前 24 个。
                </p>
              )}
            </div>
          )}
          {detail.skill?.tools && detail.skill.tools.length > 0 && (
            <div className="skill-tool-tags">
              {detail.skill.tools.map((tool: string) => (
                <code key={tool}>{tool}</code>
              ))}
            </div>
          )}
        </Dialog>
      )}
    </div>
  );
}
