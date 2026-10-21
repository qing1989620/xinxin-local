import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowUpRight, BookOpen, FlaskConical, Plus, Trash2 } from "lucide-react";
import { api, post, remove, type FileItem } from "../api";
import { Dialog, Empty, ErrorState, Loading, PageHeader, useResource, useToast, date } from "../ui";
import { FunctionPlot } from "../components/FunctionPlot";

type Book = {
  id: string;
  title: string;
  subject: string;
  chapter_count: number;
  question_count: number;
  answered: number;
  correct: number;
  char_count: number;
  created: number;
  updated: number;
};

type Stats = {
  books: number;
  questions: number;
  answered: number;
  correct: number;
  accuracy: number;
  weak_tags: Array<{ tag: string; total: number; wrong: number }>;
  recent: Array<{ id: string; title: string; total: number; status: string; created: number }>;
};

const PRESETS = [
  ["y = sin(x)", "y = cos(x)"],
  ["y = x^2 - 2", "y = 2x + 1"],
  ["y = 1/x"],
  ["y = e^(-x^2)"],
];

const BOOK_EXT = [".pdf", ".docx", ".txt", ".md", ".markdown"];

function words(count: number) {
  return count >= 1000 ? `${(count / 1000).toFixed(1)}k 字` : `${count} 字`;
}

export default function LearningPage() {
  const toast = useToast();
  const navigate = useNavigate();
  const books = useResource<{ books: Book[] }>("/learning/books");
  const stats = useResource<Stats>("/learning/stats");
  const files = useResource<FileItem[]>("/files");
  const [adding, setAdding] = useState(false);
  const [fileId, setFileId] = useState("");
  const [subject, setSubject] = useState("");
  const [busy, setBusy] = useState(false);
  const [expr, setExpr] = useState("y = sin(x)\ny = 0.5x + 1");

  const candidates = useMemo(
    () =>
      (files.data || []).filter((file) =>
        BOOK_EXT.some((extension) => file.name.toLowerCase().endsWith(extension)),
      ),
    [files.data],
  );
  const expressions = useMemo(
    () => expr.split(/[\n;；]+/).map((line) => line.trim()).filter(Boolean).slice(0, 4),
    [expr],
  );
  const summary = stats.data;

  async function addBook(event: React.FormEvent) {
    event.preventDefault();
    if (!fileId) {
      toast("先选一份文件", true);
      return;
    }
    setBusy(true);
    try {
      const created = await post<{ book: Book }>("/learning/books", {
        file_id: fileId,
        subject,
      });
      toast(`《${created.book.title}》已上架，共 ${created.book.chapter_count} 章`);
      setAdding(false);
      setFileId("");
      setSubject("");
      books.reload();
      stats.reload();
      navigate(`/learning/books/${created.book.id}`);
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      setBusy(false);
    }
  }

  async function dropBook(book: Book) {
    if (!window.confirm(`把《${book.title}》和它的题目一起删掉？`)) return;
    try {
      await remove(`/learning/books/${book.id}`);
      toast("已从书架移除");
      books.reload();
      stats.reload();
    } catch (error) {
      toast((error as Error).message, true);
    }
  }

  return (
    <div className="page-enter">
      <PageHeader
        overline="STUDY ROOM"
        title="学习"
        description="把书架里的资料变成可以练的题：先出题，再判分，做错了让老师讲清楚。"
        action={
          <button className="button primary" onClick={() => setAdding(true)}>
            <Plus size={16} />
            加入书架
          </button>
        }
      />

      {summary && (
        <div className="learn-stats">
          {[
            ["在架书本", summary.books, "本"],
            ["题库", summary.questions, "道"],
            ["已练", summary.answered, "次"],
            ["正确率", Math.round((summary.accuracy || 0) * 100), "%"],
          ].map(([label, value, unit]) => (
            <div key={String(label)} className="learn-stat">
              <span>{label}</span>
              <strong>
                {value}
                <i>{unit}</i>
              </strong>
            </div>
          ))}
        </div>
      )}

      <section className="learn-section">
        <div className="section-heading">
          <h2>书架</h2>
          <span className="muted">{books.data?.books.length ?? 0} 本</span>
        </div>
        {books.error ? (
          <ErrorState message={books.error} retry={() => books.reload()} />
        ) : books.data === null ? (
          <Loading />
        ) : books.data.books.length === 0 ? (
          <Empty
            title="书架还是空的"
            description="先在「私人资料」里上传 PDF / Word / 文本，再加入书架；会自动切章，之后就能出题和练习。"
            action={
              <button className="button primary" onClick={() => setAdding(true)}>
                <Plus size={16} />
                加入书架
              </button>
            }
          />
        ) : (
          <div className="book-grid">
            {books.data.books.map((book) => {
              const progress =
                book.question_count > 0
                  ? Math.min(100, Math.round((book.answered / book.question_count) * 100))
                  : 0;
              return (
                <article
                  key={book.id}
                  className="book-card"
                  onClick={() => navigate(`/learning/books/${book.id}`)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") navigate(`/learning/books/${book.id}`);
                  }}
                >
                  <div className="book-spine" aria-hidden="true">
                    {book.title.slice(0, 1)}
                  </div>
                  <div className="book-body">
                    <p className="book-subject">{book.subject || "未分学科"}</p>
                    <h3>{book.title}</h3>
                    <p className="muted">
                      {book.chapter_count} 章 · {words(book.char_count)} ·{" "}
                      {book.question_count} 题
                    </p>
                    <div className="book-progress" aria-hidden="true">
                      <i style={{ width: `${progress}%` }} />
                    </div>
                    <p className="book-foot">
                      <span>
                        {book.answered > 0
                          ? `练过 ${book.answered} 题 · 对 ${book.correct}`
                          : "还没开始练"}
                      </span>
                      <span className="book-open">
                        打开 <ArrowUpRight size={12} />
                      </span>
                    </p>
                  </div>
                  <button
                    className="icon-button book-remove"
                    aria-label="从书架移除"
                    onClick={(event) => {
                      event.stopPropagation();
                      void dropBook(book);
                    }}
                  >
                    <Trash2 size={14} />
                  </button>
                </article>
              );
            })}
          </div>
        )}
      </section>

      <section className="learn-section">
        <div className="section-heading">
          <h2>函数画布</h2>
          <span className="muted">写表达式，直接出图</span>
        </div>
        <div className="plot-tool">
          <div className="plot-input">
            <div className="plot-presets">
              {PRESETS.map((preset) => (
                <button
                  key={preset.join("|")}
                  className="chip"
                  onClick={() => setExpr(preset.join("\n"))}
                >
                  {preset[0]}
                </button>
              ))}
            </div>
            <textarea
              value={expr}
              onChange={(event) => setExpr(event.target.value)}
              rows={4}
              spellCheck={false}
              aria-label="函数表达式，每行一个"
              placeholder={"每行一个表达式，例如：\ny = sin(x)\ny = x^2 - 2"}
            />
            <p className="plot-hint">
              支持 + − × ÷ ^、括号、sin/cos/tan/ln/log/sqrt/abs、pi 与 e；最多四条曲线。
            </p>
          </div>
          <div className="plot-stage">
            <FunctionPlot expressions={expressions} height={280} xMin={-8} xMax={8} />
          </div>
        </div>
      </section>

      {summary && (summary.recent.length > 0 || summary.weak_tags.length > 0) && (
        <section className="learn-section learn-meta">
          <div>
            <div className="section-heading">
              <h2>最近的练习</h2>
            </div>
            {summary.recent.length === 0 ? (
              <p className="muted">还没有练习记录。</p>
            ) : (
              <ul className="recent-list">
                {summary.recent.map((item) => (
                  <li key={item.id}>
                    <button onClick={() => navigate(`/learning/quiz/${item.id}`)}>
                      <BookOpen size={14} />
                      <span>{item.title}</span>
                      <small>
                        {item.total} 题 · {date(item.created)}
                      </small>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div>
            <div className="section-heading">
              <h2>该补的标签</h2>
            </div>
            {summary.weak_tags.length === 0 ? (
              <p className="muted">还没有错题，继续。</p>
            ) : (
              <ul className="weak-list">
                {summary.weak_tags.map((item) => (
                  <li key={item.tag}>
                    <span>{item.tag}</span>
                    <small>
                      错 {item.wrong} / {item.total}
                    </small>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      )}

      {adding && (
        <Dialog title="加入书架" onClose={() => setAdding(false)}>
          <form className="stack" onSubmit={addBook}>
            <label className="field">
              <span>选一份资料</span>
              <select value={fileId} onChange={(event) => setFileId(event.target.value)}>
                <option value="">从私人资料里选…</option>
                {candidates.map((file) => (
                  <option key={file.id} value={file.id}>
                    {file.name}
                  </option>
                ))}
              </select>
            </label>
            {candidates.length === 0 && (
              <p className="hint">
                还没有可用的文件。先到「私人资料」上传 PDF、Word 或文本，再回来。
              </p>
            )}
            <label className="field">
              <span>学科（可选）</span>
              <input
                value={subject}
                onChange={(event) => setSubject(event.target.value)}
                placeholder="数学 / 英语 / 专业课…"
                maxLength={20}
              />
            </label>
            <div className="dialog-actions">
              <button type="button" className="button ghost" onClick={() => setAdding(false)}>
                取消
              </button>
              <button className="button primary" disabled={busy || !fileId}>
                {busy ? "解析中…" : "上架"}
              </button>
            </div>
          </form>
        </Dialog>
      )}

      <p className="learn-note">
        <FlaskConical size={13} />
        书本正文来自你上传的文件，只留在本机；出题、判分与讲题需要模型，没配模型时仍可看书和章节。
      </p>
    </div>
  );
}
