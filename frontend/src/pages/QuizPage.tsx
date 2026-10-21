import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  GraduationCap,
  Loader2,
  RotateCcw,
  Send,
  X,
} from "lucide-react";
import { post } from "../api";
import { ErrorState, Loading, useResource, useToast } from "../ui";
import { MathText } from "../components/MathText";
import { FunctionPlot, extractPlotBlocks } from "../components/FunctionPlot";

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
};

type Session = {
  id: string;
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
      nodes.push(<FunctionPlot key={`p-${index}`} expressions={blocks[index]} height={220} />);
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
  const [tutor, setTutor] = useState<TutorMessage[]>([]);
  const [tutorDraft, setTutorDraft] = useState("");
  const [tutorBusy, setTutorBusy] = useState(false);

  useEffect(() => {
    if (!source.data) return;
    setSession(source.data.session);
    const next = source.data.session.questions.findIndex((item) => !item.status);
    setIndex(next >= 0 ? next : Math.max(0, source.data.session.questions.length - 1));
  }, [source.data]);

  const question = session?.questions[index];
  const finished = Boolean(session && session.answered >= session.total);
  const score = session ? Math.round((session.correct / Math.max(session.total, 1)) * 100) : 0;

  function pick(value: string) {
    if (feedback) return;
    setDraft(value);
  }

  function goNext() {
    if (!session) return;
    const next = session.questions.findIndex((item, position) => position > index && !item.status);
    setFeedback(null);
    setDraft("");
    if (next >= 0) setIndex(next);
    else if (session.answered < session.total) {
      const any = session.questions.findIndex((item) => !item.status);
      if (any >= 0) setIndex(any);
    }
  }

  async function submit() {
    if (!session || !question || feedback) return;
    if (!draft.trim()) {
      toast("先写点什么再交", true);
      return;
    }
    setSubmitting(true);
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
      setFeedback({
        status: result.status,
        reason: result.reason,
        answer: result.answer,
        explanation: result.explanation,
      });
      setSession(result.state);
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      setSubmitting(false);
    }
  }

  async function ask(message = "") {
    if (!question) return;
    const text = message.trim();
    setTutorBusy(true);
    if (text) setTutor((current) => [...current, { role: "user", content: text }]);
    try {
      const result = await post<{ reply: string; history: TutorMessage[] }>(
        `/learning/questions/${question.id}/explain`,
        { message: text },
      );
      setTutor(result.history);
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      setTutorBusy(false);
      setTutorDraft("");
    }
  }

  async function restart() {
    if (!session) return;
    try {
      const created = await post<{ session: { id: string } }>("/learning/quiz", {
        book_id: session.questions[0] ? undefined : undefined,
        count: 10,
      });
      navigate(`/learning/quiz/${created.session.id}`);
    } catch (error) {
      toast((error as Error).message, true);
    }
  }

  if (source.error) return <ErrorState message={source.error} retry={() => source.reload()} />;
  if (!session || !question) return <Loading />;

  const wrong = session.questions.filter((item) => item.status === "wrong" || item.status === "partial");

  if (finished && session.answered >= session.total) {
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
                      {item.kind === "single" ? "单选" : item.kind === "fill" ? "填空" : "简答"}
                    </span>
                    <div>
                      <MathText text={item.stem} />
                      <p className="muted">你的作答：{item.answered || "（空）"}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </>
          )}
          <div className="quiz-summary-actions">
            <button className="button secondary" onClick={() => void restart()}>
              <RotateCcw size={15} />
              再来一组
            </button>
            <button className="button primary" onClick={() => navigate("/learning")}>
              回到书架
            </button>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="page-enter quiz-page">
      <button className="back-link" onClick={() => navigate("/learning")}>
        <ArrowLeft size={15} />
        书架
      </button>

      <header className="quiz-head">
        <div>
          <p className="eyebrow">PRACTICE</p>
          <h1>{session.title}</h1>
        </div>
        <div className="quiz-progress">
          <span>
            {session.answered} / {session.total}
          </span>
          <div className="quiz-bar">
            <i style={{ width: `${(session.answered / Math.max(session.total, 1)) * 100}%` }} />
          </div>
          <span className="muted">对 {session.correct}</span>
        </div>
      </header>

      <article className="quiz-card">
        <div className="quiz-meta">
          <span className={`q-kind kind-${question.kind}`}>
            {question.kind === "single" ? "单选" : question.kind === "fill" ? "填空" : "简答"}
          </span>
          <span className="quiz-difficulty">{"★".repeat(question.difficulty)}</span>
          {question.tags.map((tag) => (
            <span key={tag} className="quiz-tag">
              {tag}
            </span>
          ))}
        </div>

        <div className="quiz-stem">
          <MathText text={question.stem} />
        </div>

        {question.kind === "single" ? (
          <div className="quiz-options">
            {question.options.map((option) => {
              const chosen = draft === option.key;
              const isRight = feedback && option.key === feedback.answer;
              const isWrong = feedback && chosen && feedback.status !== "correct";
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
              {feedback.status === "correct" ? <Check size={15} /> : <X size={15} />}
              {STATUS_TEXT[feedback.status] || "已提交"}
              {feedback.reason && <em>{feedback.reason}</em>}
            </p>
            {question.kind !== "single" && (
              <p className="quiz-reference">
                参考答案：{question.kind === "fill" ? formatFill(feedback.answer) : feedback.answer}
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
              下一题
              <ArrowRight size={15} />
            </button>
          ) : (
            <button className="button primary" onClick={() => void submit()} disabled={submitting}>
              {submitting ? <Loader2 className="spin" size={15} /> : null}
              提交
            </button>
          )}
          <button className="button secondary" onClick={() => void ask()} disabled={tutorBusy}>
            {tutorBusy ? <Loader2 className="spin" size={15} /> : <GraduationCap size={15} />}
            让老师讲这道
          </button>
        </div>
      </article>

      {(tutor.length > 0 || tutorBusy) && (
        <section className="tutor">
          <div className="section-heading">
            <h2>老师</h2>
            <span className="muted">讲思路，不直接背答案</span>
          </div>
          <ul className="tutor-log">
            {tutor.map((message, position) => (
              <li key={position} className={message.role}>
                <span>{message.role === "user" ? "你" : "老师"}</span>
                <div>{message.role === "assistant" ? <RichAnswer text={message.content} /> : message.content}</div>
              </li>
            ))}
            {tutorBusy && (
              <li className="assistant">
                <span>老师</span>
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
              onChange={(event) => setTutorDraft(event.target.value)}
              placeholder="还是不懂，问一句，比如「第二步为什么能这样代换」"
              aria-label="向老师提问"
            />
            <button className="button primary" disabled={tutorBusy || !tutorDraft.trim()}>
              <Send size={14} />
            </button>
          </form>
        </section>
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
