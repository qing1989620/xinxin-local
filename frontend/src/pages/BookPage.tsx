import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Dumbbell, Loader2, Sparkles, Trash2 } from "lucide-react";
import { post, remove } from "../api";
import { Empty, ErrorState, Loading, PageHeader, useResource, useToast } from "../ui";
import { MathText } from "../components/MathText";

type Chapter = {
  id: string;
  idx: number;
  title: string;
  chars: number;
};

type Book = {
  id: string;
  title: string;
  subject: string;
  chapter_count: number;
  char_count: number;
  question_count: number;
  answered: number;
  correct: number;
  chapters: Chapter[];
};

type Question = {
  id: string;
  chapter_id: string;
  kind: "single" | "fill" | "short";
  stem: string;
  tags: string[];
  difficulty: number;
};

const KIND_LABEL = { single: "单选", fill: "填空", short: "简答" } as const;

function words(count: number) {
  return count >= 1000 ? `${(count / 1000).toFixed(1)}k 字` : `${count} 字`;
}

export default function BookPage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const book = useResource<{ book: Book }>(`/learning/books/${id}`);
  const questions = useResource<{ questions: Question[] }>(
    `/learning/questions?book_id=${encodeURIComponent(id)}`,
  );
  const [generating, setGenerating] = useState("");
  const [busyChapter, setBusyChapter] = useState("");
  const [count, setCount] = useState(5);

  const byChapter = useMemo(() => {
    const map: Record<string, Question[]> = {};
    for (const question of questions.data?.questions || []) {
      if (!question.chapter_id) continue;
      (map[question.chapter_id] ||= []).push(question);
    }
    return map;
  }, [questions.data]);

  async function generate(chapter: Chapter) {
    setGenerating(chapter.id);
    try {
      const result = await post<{ created: Question[]; skipped: number }>(
        `/learning/books/${id}/questions`,
        { chapter_id: chapter.id, count },
      );
      toast(
        result.created.length
          ? `这一章出了 ${result.created.length} 道题`
          : "没有新题可出：内容太少或已经出过",
      );
      questions.reload();
      book.reload();
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      setGenerating("");
    }
  }

  async function startQuiz(chapterId = "") {
    setBusyChapter(chapterId || "all");
    try {
      const result = await post<{ session: { id: string } }>("/learning/quiz", {
        book_id: id,
        chapter_id: chapterId,
        count: 10,
      });
      navigate(`/learning/quiz/${result.session.id}`);
    } catch (error) {
      toast((error as Error).message, true);
      setBusyChapter("");
    }
  }

  async function drop() {
    if (!book.data) return;
    if (!window.confirm(`把《${book.data.book.title}》和它的题目一起删掉？`)) return;
    try {
      await remove(`/learning/books/${id}`);
      toast("已从书架移除");
      navigate("/learning");
    } catch (error) {
      toast((error as Error).message, true);
    }
  }

  if (book.error) return <ErrorState message={book.error} retry={() => book.reload()} />;
  if (!book.data) return <Loading />;
  const data = book.data.book;

  return (
    <div className="page-enter">
      <button className="back-link" onClick={() => navigate("/learning")}>
        <ArrowLeft size={15} />
        书架
      </button>
      <PageHeader
        overline={data.subject ? data.subject.toUpperCase() : "BOOK"}
        title={data.title}
        description={`${data.chapter_count} 章 · ${words(data.char_count)} · ${data.question_count} 道题`}
        action={
          <div className="header-actions">
            <button className="button ghost" onClick={() => void drop()}>
              <Trash2 size={15} />
              移除
            </button>
            <button
              className="button primary"
              disabled={!data.question_count || busyChapter === "all"}
              onClick={() => void startQuiz("")}
            >
              {busyChapter === "all" ? <Loader2 className="spin" size={15} /> : <Dumbbell size={15} />}
              全书练习
            </button>
          </div>
        }
      />

      <ol className="chapter-list">
        {data.chapters.map((chapter) => {
          const items = byChapter[chapter.id] || [];
          const working = generating === chapter.id;
          return (
            <li key={chapter.id}>
              <div className="chapter-main">
                <span className="chapter-index">{String(chapter.idx + 1).padStart(2, "0")}</span>
                <div>
                  <h3>{chapter.title}</h3>
                  <p className="muted">
                    {words(chapter.chars)} · {items.length} 题
                  </p>
                </div>
              </div>
              <div className="chapter-actions">
                <button
                  className="button secondary small"
                  disabled={working}
                  onClick={() => void generate(chapter)}
                >
                  {working ? (
                    <>
                      <Loader2 className="spin" size={13} /> 出题中
                    </>
                  ) : (
                    <>
                      <Sparkles size={13} /> 出题
                    </>
                  )}
                </button>
                <button
                  className="button primary small"
                  disabled={!items.length || busyChapter === chapter.id}
                  onClick={() => void startQuiz(chapter.id)}
                >
                  {busyChapter === chapter.id ? "准备中…" : "练这一章"}
                </button>
              </div>
            </li>
          );
        })}
      </ol>

      <div className="chapter-count">
        <span>每章出几道</span>
        {[3, 5, 8].map((value) => (
          <button
            key={value}
            className={`chip${count === value ? " active" : ""}`}
            onClick={() => setCount(value)}
          >
            {value}
          </button>
        ))}
      </div>

      <section className="learn-section">
        <div className="section-heading">
          <h2>已有题目</h2>
          <span className="muted">{data.question_count} 道</span>
        </div>
        {questions.data === null ? (
          <Loading />
        ) : (questions.data.questions.length === 0 ? (
          <Empty
            title="还没有题"
            description="在上面的章节里点「出题」，模型会按该章内容出选择题、填空题和简答题。"
          />
        ) : (
          <ul className="question-list">
            {questions.data.questions.slice(0, 40).map((question) => (
              <li key={question.id}>
                <span className={`q-kind kind-${question.kind}`}>{KIND_LABEL[question.kind]}</span>
                <div className="q-stem">
                  <MathText text={question.stem} />
                  <p className="muted">
                    {"★".repeat(question.difficulty)} · {question.tags.join(" · ") || "未打标签"}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        ))}
      </section>
    </div>
  );
}
