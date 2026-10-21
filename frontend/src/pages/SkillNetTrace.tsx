import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { api, type EventItem, type Run } from "../api";
import { Dialog } from "../ui";
import { skillTrace, tracedSkills } from "../skillTrace";

export default function SkillNetTrace({
  run,
  events = [],
}: {
  run: Run;
  events?: EventItem[];
}) {
  const trace = skillTrace(events, run.skillnet);
  const [openId, setOpenId] = useState("");
  const [detail, setDetail] = useState<{
    name: string;
    markdown: string;
  } | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!openId) return;
    const controller = new AbortController();
    setDetail(null);
    setError("");
    void api<{ name: string; markdown: string }>(
      `/skills/${encodeURIComponent(openId)}`,
      { signal: controller.signal },
    )
      .then((value) => {
        if (!controller.signal.aborted) setDetail(value);
      })
      .catch((issue) => {
        if (!controller.signal.aborted) setError((issue as Error).message);
      });
    return () => controller.abort();
  }, [openId]);
  useEffect(() => setOpenId(""), [run.id]);
  if (!trace)
    return ["queued", "running"].includes(run.status) ? (
      <p className="skillnet-pending">SkillNet · 正在根据目标匹配能力…</p>
    ) : null;
  const cards = tracedSkills(trace);
  const used = cards.filter((card) => card.references || card.tools).length;
  return (
    <section className="skillnet-trace" aria-label="SkillNet 本轮能力路线">
      <details>
        <summary>
          <span className="skillnet-brand">SkillNet</span>
          <strong>
            {trace.skills.length
              ? `匹配 ${trace.skills.length} 项能力${trace.dependencies.length ? ` · ${trace.dependencies.length} 项配合能力` : ""}`
              : cards.length
                ? `按需读取 ${cards.length} 项参考`
                : "本轮未选额外技能"}
          </strong>
          {cards.length > 0 && (
            <span className="skillnet-preview">
              {cards
                .slice(0, 3)
                .map((card) => card.name)
                .join(" / ")}
              {cards.length > 3 ? ` 等 ${cards.length} 项` : ""}
            </span>
          )}
          {used > 0 && (
            <span className="skillnet-evidence-count">
              {used} 项有读取或工具记录
            </span>
          )}
          <span className="skillnet-expand">展开路线</span>
        </summary>
        {cards.length ? (
          <>
            <p className="skillnet-explanation">
              先按目标选择方法，再按需要读取参考、调用工具；结果见这轮答复与交付。
            </p>
            <ol className="skillnet-cards">
              {cards.map((card) => (
                <li key={card.id}>
                  <button
                    className="text-button"
                    onClick={() => setOpenId(card.id)}
                  >
                    {card.name}
                    <span>查看方法 ↗</span>
                  </button>
                  {card.dependency && <small>配合能力</small>}
                  <p>
                    {card.note ? (
                      <>
                        <span>选择理由（模型建议）：</span>
                        {card.note}
                      </>
                    ) : card.onDemand ? (
                      card.description
                    ) : (
                      <>按目标相关度匹配。{card.description}</>
                    )}
                  </p>
                  <div className="skillnet-evidence">
                    {card.references > 0 && (
                      <span>参考读取 {card.references} 次</span>
                    )}
                    {card.tools > 0 && (
                      <span>关联工具成功返回 {card.tools} 次</span>
                    )}
                    {card.failures > 0 && (
                      <span className="skillnet-failure">
                        有 {card.failures} 次未成功返回
                      </span>
                    )}
                    {!card.references && !card.tools && !card.failures && (
                      <span>已匹配，尚无读取或工具结果记录</span>
                    )}
                  </div>
                </li>
              ))}
            </ol>
            <p className="skillnet-explanation">
              工具返回记录用于核对过程，不代表这项方法或最终成果已通过验收。
            </p>
          </>
        ) : (
          <p className="skillnet-explanation">
            这轮没有选中额外技能，按当前上下文继续回答。
          </p>
        )}
        <nav className="skillnet-links" aria-label="技能路线相关入口">
          <Link to="/skills">浏览 SkillNet 技能库</Link>
          {!["queued", "running", "cancelling"].includes(run.status) && (
            <Link to={`/tasks?run=${run.id}`}>查看本轮结果与交付</Link>
          )}
        </nav>
      </details>
      {openId && (
        <Dialog
          title={detail?.name || openId}
          onClose={() => setOpenId("")}
          wide
        >
          {error ? (
            <p role="alert">{error}</p>
          ) : detail ? (
            <div className="markdown skill-markdown">
              <ReactMarkdown skipHtml>{detail.markdown}</ReactMarkdown>
            </div>
          ) : (
            <p role="status">正在读取方法…</p>
          )}
        </Dialog>
      )}
    </section>
  );
}
