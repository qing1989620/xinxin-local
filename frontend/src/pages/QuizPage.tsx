import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  GraduationCap,
  FileText,
  Loader2,
  RotateCcw,
  Send,
  X,
} from "lucide-react";
import { api, post } from "../api";
import { Empty, ErrorState, Loading, useResource, useToast } from "../ui";
import { MathText } from "../components/MathText";
import { FunctionPlot, extractPlotBlocks } from "../components/FunctionPlot";
import { StudySource } from "../components/StudySource";

type Question = {
  id: string;
  kind: "single" | "fill" | "short";
  stem: string;
  options: Array<{ key: string; text: string }>;
  tags: string[];
  difficulty: number;
  answer: string | null;
  explanation: string;
  answered: string | null;
  status: string | null;
  ai_reason: string;
  position: number;
  source_id?: string;
  source_quote?: string;
  source_pages?: number[];
  origin?: string;
};

type Session = {
  id: string;
  book_id: string | null;
  chapter_id: string | null;
  mode?: "all" | "mistakes";
  title: string;
  total: number;
  answered: number;
  correct: number;
  status: string;
  questions: Question[];
};

type Feedback = {
  status: string;
  reason: string;
  answer: string;
  explanation: string;
};

type TutorMessage = { role: string; content: string };
type TutorMode = "teacher" | "xinxin";

const STATUS_TEXT: Record<string, string> = {
  correct: "答对了",
  partial: "部分正确",
  wrong: "答错了",
  unknown: "待核对",
};

function RichAnswer({ text }: { text: string }) {
  const { body, blocks } = useMemo(() => extractPlotBlocks(text), [text]);
  const chunks = body.split("[[PLOT]]");
  const nodes: React.ReactNode[] = [];
  chunks.forEach((chunk, index) => {
    if (chunk.trim()) {
      nodes.push(
        <p key={`t-${index}`} className="rich-text">
          {chunk
            .trim()
            .split(/(\*\*[^*]+\*\*)/g)
            .filter(Boolean)
            .map((part, position) =>
              part.startsWith("**") && part.endsWith("**") ? (
                <strong key={position}>
                  <MathText text={part.slice(2, -2)} />
                </strong>
              ) : (
                <MathText key={position} text={part} />
              ),
            )}
        </p>,
      );
    }
    if (blocks[index]) {
      nodes.push(
        <p key={`p-${index}`} className="plot-note">
          图已画在右侧画布
        </p>,
      );
    }
  });
  return <>{nodes}</>;
}

export default function QuizPage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const source = useResource<{ session: Session }>(`/learning/quiz/${id}`);
  const [session, setSession] = useState<Session | null>(null);
  const [index, setIndex] = useState(0);
  const [draft, setDraft] = useState("");
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const submitBusy = useRef(false);
  const [reviewing, setReviewing] = useState(false);
  const restarting = useRef(false);
  const [restartBusy, setRestartBusy] = useState(false);
  const [tutor, setTutor] = useState<TutorMessage[]>([]);
  const [tutorMode, setTutorMode] = useState<TutorMode>(() => {
    try {
      return localStorage.getItem("xinxin-tutor-mode") === "xinxin"
        ? "xinxin"
        : "teacher";
    } catch {
      return "teacher";
    }
  });
  const [tutorDraft, setTutorDraft] = useState("");
  const [tutorBusy, setTutorBusy] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [historyRetry, setHistoryRetry] = useState(0);
  const tutorRequest = useRef(0);
  const tutorInFlight = useRef(false);
  const [canvasExpr, setCanvasExpr] = useState("");
  const [readingSource, setReadingSource] = useState(false);
  const logRef = useRef<HTMLUListElement | null>(null);
  const question = session?.questions[index];
  const questionId = question?.id || "";
  const tutorName = tutorMode === "xinxin" ? "Xinxin" : "老师";
  const contextKey = `${id}:${questionId}:${tutorMode}`;
  const currentContext = useRef(contextKey);
  currentContext.current = contextKey;
  const currentQuestion = useRef({ sessionId: id, questionId });
  currentQuestion.current = { sessionId: id, questionId };

  useEffect(() => {
    if (!source.data) return;
    setSession(source.data.session);
    setReviewing(false);
    const next = source.data.session.questions.findIndex(
      (item) => !item.status,
    );
    const position =
      next >= 0 ? next : Math.max(0, source.data.session.questions.length - 1);
    setIndex(position);
    const initial = source.data.session.questions[position];
    setDraft(initial?.answered || "");
    setFeedback(
      initial?.status
        ? {
            status: initial.status,
            reason: initial.ai_reason,
            answer: initial.answer || "",
            explanation: initial.explanation || "",
          }
        : null,
    );
  }, [source.data]);

  useEffect(() => {
    try {
      localStorage.setItem("xinxin-tutor-mode", tutorMode);
    } catch {
      /* 可选偏好 */
    }
  }, [tutorMode]);

  useEffect(() => {
    setCanvasExpr("");
    setReadingSource(false);
  }, [questionId]);

  // 讲解、追问里出现的表达式都收集起来，统一画在右侧画布
  const plotSets = useMemo(() => {
    const found: string[][] = [];
    const push = (source?: string) => {
      if (!source) return;
      const { blocks } = extractPlotBlocks(source);
      for (const block of blocks) {
        const key = block.join("|");
        if (!found.some((item) => item.join("|") === key)) found.push(block);
      }
    };
    push(feedback?.explanation);
    for (const message of tutor) {
      if (message.role === "assistant") push(message.content);
    }
    return found;
  }, [feedback, tutor]);

  // 换题时把这道题之前的讲解捞回来，离开页面也不丢
  useEffect(() => {
    if (!questionId) return;
    let alive = true;
    const request = ++tutorRequest.current;
    tutorInFlight.current = false;
    setTutorBusy(false);
    setTutor([]);
    setTutorDraft("");
    setHistoryLoading(true);
    setHistoryError("");
    void api<{ history: TutorMessage[] }>(
      `/learning/questions/${questionId}/tutor?mode=${tutorMode}`,
    )
      .then((value) => {
        if (alive && request === tutorRequest.current)
          setTutor(value.history || []);
      })
      .catch((error: Error) => {
        if (alive && request === tutorRequest.current)
          setHistoryError(error.message);
      })
      .finally(() => {
        if (alive && request === tutorRequest.current) setHistoryLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [id, questionId, tutorMode, historyRetry]);

  useEffect(() => {
    const node = logRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [tutor, tutorBusy]);

  const finished = Boolean(session && session.answered >= session.total);
  const score = session
    ? Math.round((session.correct / Math.max(session.total, 1)) * 100)
    : 0;

  function pick(value: string) {
    if (feedback) return;
    setDraft(value);
  }

  function goNext() {
    if (!session) return;
    if (finished) {
      if (index + 1 < session.questions.length) jump(index + 1);
      else setReviewing(false);
      return;
    }
    const next = session.questions.findIndex(
      (item, position) => position > index && !item.status,
    );
    setFeedback(null);
    setDraft("");
    if (next >= 0) setIndex(next);
    else if (session.answered < session.total) {
      const any = session.questions.findIndex((item) => !item.status);
      if (any >= 0) setIndex(any);
    }
  }

  function jump(position: number) {
    if (!session) return;
    const item = session.questions[position];
    if (!item) return;
    setIndex(position);
    setDraft(item.answered || "");
    setFeedback(
      item.status
        ? {
            status: item.status,
            reason: item.ai_reason,
            answer: item.answer || "",
            explanation: item.explanation,
          }
        : null,
    );
  }

  async function submit() {
    if (!session || !question || feedback || submitBusy.current) return;
    if (!draft.trim()) {
      toast("先写点什么再交", true);
      return;
    }
    submitBusy.current = true;
    setSubmitting(true);
    const targetSession = id;
    const targetQuestion = question.id;
    try {
      const result = await post<{
        status: string;
        reason: string;
        answer: string;
        explanation: string;
        state: Session;
      }>(`/learning/quiz/${session.id}/answer`, {
        question_id: question.id,
        answer: draft,
      });
      if (currentQuestion.current.sessionId === targetSession) {
        setSession(result.state);
        if (currentQuestion.current.questionId === targetQuestion) {
          setFeedback({
            status: result.status,
            reason: result.reason,
            answer: result.answer,
            explanation: result.explanation,
          });
        }
      }
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      submitBusy.current = false;
      setSubmitting(false);
    }
  }

  async function ask(message = "") {
    if (!question || tutorInFlight.current || historyLoading || historyError)
      return;
    const text = message.trim();
    const key = contextKey;
    const request = ++tutorRequest.current;
    tutorInFlight.current = true;
    setTutorBusy(true);
    try {
      const result = await post<{ reply: string; history: TutorMessage[] }>(
        `/learning/questions/${question.id}/explain`,
        { message: text, mode: tutorMode },
      );
      if (currentContext.current === key && request === tutorRequest.current) {
        setTutor(result.history);
        setTutorDraft("");
      }
    } catch (error) {
      if (currentContext.current === key && request === tutorRequest.current)
        toast((error as Error).message, true);
    } finally {
      if (currentContext.current === key && request === tutorRequest.current) {
        tutorInFlight.current = false;
        setTutorBusy(false);
      }
    }
  }

  async function restart() {
    if (!session || restarting.current) return;
    restarting.current = true;
    setRestartBusy(true);
    try {
      const created = await post<{ session: { id: string } }>(
        "/learning/quiz",
        {
          book_id: session.book_id || undefined,
          chapter_id: session.chapter_id || undefined,
          count: session.total,
          mode: session.mode ?? "all",
        },
      );
      navigate(`/learning/quiz/${created.session.id}`);
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      restarting.current = false;
      setRestartBusy(false);
    }
  }

  if (source.error)
    return <ErrorState message={source.error} retry={() => source.reload()} />;
  if (session && session.questions.length === 0) {
    return (
      <div className="page-enter quiz-page">
        <button className="back-link" onClick={() => navigate("/learning")}>
          <ArrowLeft size={15} />
          书架
        </button>
        <Empty
          title="这次练习的题目已经不在了"
          description="书本可能被删除了，回书架重新选一章开始练。"
          action={
            <button
              className="button primary"
              onClick={() => navigate("/learning")}
            >
              回到书架
            </button>
          }
        />
      </div>
    );
  }
  if (!session || session.id !== id || !question) return <Loading />;

  const wrong = session.questions.filter(
    (item) => item.status === "wrong" || item.status === "partial",
  );

  if (finished && !reviewing) {
    return (
      <div className="page-enter quiz-page">
        <button className="back-link" onClick={() => navigate("/learning")}>
          <ArrowLeft size={15} />
          书架
        </button>
        <section className="quiz-summary">
          <p className="eyebrow">SESSION COMPLETE</p>
          <h1>
            {session.correct}/{session.total}
            <span>{score}%</span>
          </h1>
          <p className="muted">{session.title}</p>
          {wrong.length > 0 && (
            <>
              <h2>值得再看一遍</h2>
              <ul className="quiz-wrong">
                {wrong.map((item) => (
                  <li key={item.id}>
                    <span className={`q-kind kind-${item.kind}`}>
                      {item.kind === "single"
                        ? "单选"
                        : item.kind === "fill"
                          ? "填空"
                          : "简答"}
                    </span>
                    <div>
                      <MathText text={item.stem} />
                      <p className="muted">
                        你的作答：{item.answered || "（空）"}
                      </p>
                    </div>
                    <button
                      className="button secondary small"
                      onClick={() => {
                        setReviewing(true);
                        jump(
                          session.questions.findIndex(
                            (question) => question.id === item.id,
                          ),
                        );
                      }}
                    >
                      查看讲解
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}
          <div className="quiz-summary-actions">
            <button
              className="button secondary"
              onClick={() => {
                setReviewing(true);
                jump(0);
              }}
            >
              回看题目与讲解
            </button>
            <button
              className="button secondary"
              onClick={() => void restart()}
              disabled={restartBusy}
            >
              <RotateCcw size={15} />
              再来一组
            </button>
            <button
              className="button primary"
              onClick={() => navigate("/learning")}
            >
              回到书架
            </button>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="page-enter quiz-shell">
      <header className="quiz-top">
        <div className="quiz-top-left">
          <button className="back-link" onClick={() => navigate("/learning")}>
            <ArrowLeft size={15} />
            书架
          </button>
          <div>
            <p className="eyebrow">PRACTICE</p>
            <h1>{session.title}</h1>
          </div>
        </div>
        <div className="quiz-progress">
          {finished && (
            <button
              className="button secondary small"
              onClick={() => setReviewing(false)}
            >
              查看总结
            </button>
          )}
          <span>
            {session.answered} / {session.total}
          </span>
          <div className="quiz-bar">
            <i
              style={{
                width: `${(session.answered / Math.max(session.total, 1)) * 100}%`,
              }}
            />
          </div>
          <span className="muted">对 {session.correct}</span>
        </div>
      </header>

      <div className="quiz-columns">
        <section className="quiz-main">
          <nav className="quiz-nav" aria-label="题号">
            {session.questions.map((item, position) => (
              <button
                key={item.id}
                className={`quiz-dot${position === index ? " current" : ""}${
                  item.status ? ` ${item.status}` : ""
                }`}
                onClick={() => jump(position)}
                aria-label={`第 ${position + 1} 题${item.status ? "，" + (STATUS_TEXT[item.status] || "") : ""}`}
                aria-current={position === index ? "true" : undefined}
              >
                {position + 1}
              </button>
            ))}
          </nav>

          <article className="quiz-card">
            <div className="quiz-meta">
              <span className={`q-kind kind-${question.kind}`}>
                {question.kind === "single"
                  ? "单选"
                  : question.kind === "fill"
                    ? "填空"
                    : "简答"}
              </span>
              {question.origin && question.origin !== "legacy" && (
                <span className="quiz-tag">
                  {question.origin === "original" ? "原题整理" : "知识拓展"}
                </span>
              )}
              <span className="quiz-difficulty">
                {"★".repeat(question.difficulty)}
              </span>
              {question.tags.map((tag) => (
                <span key={tag} className="quiz-tag">
                  {tag}
                </span>
              ))}
            </div>

            <div className="quiz-stem">
              <MathText text={question.stem} />
            </div>
            {question.source_id && (
              <button
                className="text-button quiz-source-link"
                onClick={() => setReadingSource(true)}
              >
                <FileText size={13} />
                回到原文，寻找线索
              </button>
            )}

            {question.kind === "single" ? (
              <div className="quiz-options">
                {question.options.map((option) => {
                  const chosen = draft === option.key;
                  const isRight = feedback && option.key === feedback.answer;
                  const isWrong =
                    feedback && chosen && feedback.status !== "correct";
                  return (
                    <button
                      key={option.key}
                      className={`quiz-option${chosen ? " chosen" : ""}${isRight ? " right" : ""}${isWrong ? " wrong" : ""}`}
                      onClick={() => pick(option.key)}
                      disabled={Boolean(feedback)}
                    >
                      <b>{option.key}</b>
                      <span>
                        <MathText text={option.text} />
                      </span>
                    </button>
                  );
                })}
              </div>
            ) : question.kind === "fill" ? (
              <div className="quiz-fill">
                <input
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  placeholder="多个空用分号或逗号隔开"
                  disabled={Boolean(feedback)}
                  aria-label="填空答案"
                />
                <p className="hint">例如：第一空；第二空</p>
              </div>
            ) : (
              <textarea
                className="quiz-short"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder="写清关键步骤，判分看的是意思，不是字面"
                rows={4}
                disabled={Boolean(feedback)}
                aria-label="简答"
              />
            )}

            {feedback ? (
              <div className={`quiz-feedback ${feedback.status}`}>
                <p className="quiz-verdict">
                  {feedback.status === "correct" ? (
                    <Check size={15} />
                  ) : (
                    <X size={15} />
                  )}
                  {STATUS_TEXT[feedback.status] || "已提交"}
                  {feedback.reason && <em>{feedback.reason}</em>}
                </p>
                {question.kind !== "single" && (
                  <p className="quiz-reference">
                    参考答案：
                    {question.kind === "fill"
                      ? formatFill(feedback.answer)
                      : feedback.answer}
                  </p>
                )}
                {feedback.explanation && (
                  <div className="quiz-explanation">
                    <RichAnswer text={feedback.explanation} />
                  </div>
                )}
              </div>
            ) : null}

            <div className="quiz-actions">
              {feedback ? (
                <button className="button primary" onClick={goNext}>
                  {finished && index + 1 >= session.questions.length
                    ? "查看总结"
                    : "下一题"}
                  <ArrowRight size={15} />
                </button>
              ) : (
                <button
                  className="button primary"
                  onClick={() => void submit()}
                  disabled={submitting}
                >
                  {submitting ? <Loader2 className="spin" size={15} /> : null}
                  提交
                </button>
              )}
              <button
                className="button secondary"
                onClick={() => void ask()}
                disabled={tutorBusy || historyLoading || Boolean(historyError)}
              >
                {tutorBusy ? (
                  <Loader2 className="spin" size={15} />
                ) : (
                  <GraduationCap size={15} />
                )}
                让{tutorName}讲这道
              </button>
            </div>
          </article>
        </section>

        <aside className="quiz-aside">
          <section className="canvas-block">
            <div className="canvas-head">
              <span className="plate-label">画布</span>
              <span className="muted">
                {plotSets.length ? "老师的图" : "函数图像"}
              </span>
            </div>
            {canvasExpr.trim() ? (
              <FunctionPlot
                expressions={canvasExpr
                  .split(/[\n;；]+/)
                  .map((line) => line.trim())
                  .filter(Boolean)}
                height={200}
              />
            ) : plotSets.length ? (
              plotSets
                .slice(-1)
                .map((expressions, position) => (
                  <FunctionPlot
                    key={position}
                    expressions={expressions}
                    height={200}
                  />
                ))
            ) : (
              <p className="canvas-empty">
                老师讲到函数、图像时，图会画在这里。也可以自己写一个表达式试试。
              </p>
            )}
            <form
              className="canvas-input"
              onSubmit={(event) => event.preventDefault()}
            >
              <textarea
                value={canvasExpr}
                onChange={(event) => setCanvasExpr(event.target.value)}
                placeholder={"自己画：y = sin(x)"}
                aria-label="画布表达式"
                rows={2}
                spellCheck={false}
              />
              {canvasExpr && (
                <button
                  type="button"
                  className="row-icon"
                  aria-label="清空"
                  onClick={() => setCanvasExpr("")}
                >
                  <X size={12} />
                </button>
              )}
            </form>
            <p className="canvas-hint">每行一个 y = …，最多四条曲线。</p>
          </section>

          <section className="tutor-block">
            <div className="tutor-head">
              <div
                className="tutor-modes"
                role="group"
                aria-label="AI 辅导模式"
              >
                <button
                  type="button"
                  aria-pressed={tutorMode === "teacher"}
                  onClick={() => setTutorMode("teacher")}
                >
                  普通老师
                </button>
                <button
                  type="button"
                  aria-pressed={tutorMode === "xinxin"}
                  onClick={() => setTutorMode("xinxin")}
                >
                  Xinxin 辅导
                </button>
              </div>
              <span className="muted">
                {tutorMode === "xinxin"
                  ? "陪你想，一起把题做懂"
                  : "讲思路，逐步引导"}
              </span>
            </div>
            <ul
              className="tutor-log"
              ref={logRef}
              aria-label={`${tutorName}的讲解`}
              aria-busy={tutorBusy || historyLoading}
            >
              {historyLoading && <li className="tutor-empty">正在读取讲解…</li>}
              {historyError && (
                <li className="tutor-empty" role="alert">
                  讲解读取失败：{historyError}{" "}
                  <button
                    className="button secondary small"
                    onClick={() => setHistoryRetry((value) => value + 1)}
                  >
                    重试
                  </button>
                </li>
              )}
              {tutor.length === 0 &&
                !tutorBusy &&
                !historyLoading &&
                !historyError && (
                  <li className="tutor-empty">
                    {tutorMode === "xinxin"
                      ? "卡住了就叫我呀。我们从切入点开始，一步步把它想清楚。"
                      : "卡住了就点左边的「让老师讲这道」，老师会在这里一步步讲。"}
                  </li>
                )}
              {tutor.map((message, position) => (
                <li key={position} className={message.role}>
                  <span>{message.role === "user" ? "你" : tutorName}</span>
                  <div>
                    {message.role === "assistant" ? (
                      <RichAnswer text={message.content} />
                    ) : (
                      message.content
                    )}
                  </div>
                </li>
              ))}
              {tutorBusy && (
                <li className="assistant">
                  <span>{tutorName}</span>
                  <div className="muted">正在想…</div>
                </li>
              )}
            </ul>
            <form
              className="tutor-input"
              onSubmit={(event) => {
                event.preventDefault();
                if (tutorDraft.trim()) void ask(tutorDraft);
              }}
            >
              <input
                value={tutorDraft}
                disabled={tutorBusy || historyLoading || Boolean(historyError)}
                onChange={(event) => setTutorDraft(event.target.value)}
                placeholder="还是不懂？问一句，比如「第二步为什么能这样代换」"
                aria-label={`向${tutorName}提问`}
              />
              <button
                className="button primary"
                aria-label="发送追问"
                disabled={
                  tutorBusy ||
                  historyLoading ||
                  Boolean(historyError) ||
                  !tutorDraft.trim()
                }
              >
                <Send size={14} />
              </button>
            </form>
          </section>
        </aside>
      </div>
      {readingSource && question.source_id && (
        <StudySource
          key={question.source_id}
          id={question.source_id}
          quote={question.source_quote}
          pages={question.source_pages}
          onClose={() => setReadingSource(false)}
        />
      )}
    </div>
  );
}

function formatFill(answer: string) {
  try {
    const list = JSON.parse(answer);
    return Array.isArray(list) ? list.join("；") : String(list);
  } catch {
    return answer;
  }
}
