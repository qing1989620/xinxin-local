import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Check,
  Clock3,
  FileUp,
  MoveUpRight,
  Plus,
  Trash2,
} from "lucide-react";
import {
  acknowledgeRequest,
  api,
  post,
  remove,
  stableRequestKey,
  upload,
  type FileItem,
} from "../api";
import {
  Dialog,
  Empty,
  ErrorState,
  Loading,
  useResource,
  useToast,
  date,
} from "../ui";
import { FunctionPlot } from "../components/FunctionPlot";
import { wordCount, type StudyBook, type ImportJob } from "../learning";

type Stats = {
  books: number;
  questions: number;
  answered: number;
  correct: number;
  accuracy: number;
  weak_tags: Array<{ tag: string; total: number; wrong: number }>;
  recent: Array<{
    id: string;
    title: string;
    total: number;
    status: string;
    created: number;
  }>;
};
const PRESETS = [
  ["y = sin(x)", "y = cos(x)"],
  ["y = x^2 - 2", "y = 2x + 1"],
  ["y = 1/x"],
  ["y = e^(-x^2)"],
];
const BOOK_EXT = [".pdf", ".docx", ".txt", ".md", ".markdown"];

export default function LearningPage() {
  const toast = useToast();
  const navigate = useNavigate();
  const books = useResource<{ books: StudyBook[] }>("/learning/books");
  const stats = useResource<Stats>("/learning/stats");
  const files = useResource<FileItem[]>("/files");
  const lastImport = useResource<{ job: ImportJob | null }>(
    "/learning/imports",
  );
  const [importJob, setImportJob] = useState<ImportJob | null>(null);
  const initiatedImport = useRef("");
  const [importError, setImportError] = useState("");
  const [uploadPercent, setUploadPercent] = useState(0);
  const [adding, setAdding] = useState(false);
  const [fileId, setFileId] = useState("");
  const [subject, setSubject] = useState("");
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState<FileItem | null>(null);
  const [expr, setExpr] = useState("y = sin(x)\ny = 0.5x + 1");
  const fileInput = useRef<HTMLInputElement>(null);
  const submitBusy = useRef(false);
  const preparing = Boolean(
    importJob && ["queued", "running", "cancelling"].includes(importJob.status),
  );
  useEffect(() => {
    if (lastImport.data) setImportJob(lastImport.data.job);
  }, [lastImport.data]);
  useEffect(() => {
    if (!importJob || !preparing) return;
    const controller = new AbortController();
    let pending = false;
    const sync = async () => {
      if (pending || controller.signal.aborted) return;
      pending = true;
      try {
        const value = await api<{ job: ImportJob }>(
          `/learning/imports/${importJob.id}`,
          { signal: controller.signal },
        );
        if (!controller.signal.aborted) {
          setImportJob(value.job);
          setImportError("");
        }
      } catch (error) {
        if (!controller.signal.aborted)
          setImportError((error as Error).message);
      } finally {
        pending = false;
      }
    };
    void sync();
    const timer = setInterval(() => void sync(), 1200);
    return () => {
      controller.abort();
      clearInterval(timer);
    };
  }, [importJob?.id, preparing]);
  useEffect(() => {
    if (
      importJob?.status === "completed" &&
      importJob.book_id &&
      initiatedImport.current === importJob.id
    ) {
      initiatedImport.current = "";
      navigate(`/learning/books/${importJob.book_id}`);
    }
  }, [importJob, navigate]);
  const candidates = useMemo(() => {
    const items = (files.data || []).filter((file) =>
      BOOK_EXT.some((ext) => file.name.toLowerCase().endsWith(ext)),
    );
    return uploaded && !items.some((file) => file.id === uploaded.id)
      ? [...items, uploaded]
      : items;
  }, [files.data, uploaded]);
  const expressions = useMemo(
    () =>
      expr
        .split(/[\n;；]+/)
        .map((line) => line.trim())
        .filter(Boolean)
        .slice(0, 4),
    [expr],
  );
  const summary = stats.data;
  const recent = summary?.recent.find((item) => item.status === "active");
  const firstBook = books.data?.books[0];
  const uniqueAnswered =
    books.data?.books.reduce(
      (count, book) =>
        count +
        (book.unique_answered ?? Math.min(book.answered, book.question_count)),
      0,
    ) ?? 0;

  async function addBook(event: React.FormEvent) {
    event.preventDefault();
    if (!fileId || submitBusy.current) return;
    submitBusy.current = true;
    setBusy(true);
    try {
      const payload = {
        file_id: fileId,
        title: "",
        subject,
      };
      const requestKey = await stableRequestKey("study-import", payload);
      const created = await post<{ job: ImportJob }>("/learning/imports", {
        ...payload,
        request_key: requestKey,
      });
      acknowledgeRequest("study-import");
      initiatedImport.current = created.job.id;
      setImportJob(created.job);
      setAdding(false);
      setFileId("");
      setSubject("");
      toast("资料识别已开始，可在下方查看逐页进度");
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      setBusy(false);
      submitBusy.current = false;
    }
  }
  async function uploadFile(file?: File) {
    if (!file || uploading) return;
    if (!BOOK_EXT.some((ext) => file.name.toLowerCase().endsWith(ext))) {
      toast("请选择 PDF、Word 或文本资料", true);
      return;
    }
    setUploading(true);
    setUploadPercent(0);
    try {
      const result = await upload(file, {
        onProgress: (sent, total) =>
          setUploadPercent(Math.round((sent / total) * 100)),
      });
      setUploaded(result);
      setFileId(result.id);
      files.reload();
      toast("资料已上传，确认学科后即可加入书架");
    } catch (err) {
      toast((err as Error).message, true);
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }
  async function dropBook(book: StudyBook) {
    if (!window.confirm(`把《${book.title}》和它的题目一起删掉？`)) return;
    try {
      await remove(`/learning/books/${book.id}`);
      toast("已从书架移除");
      books.reload();
      stats.reload();
    } catch (err) {
      toast((err as Error).message, true);
    }
  }
  function continueStudy() {
    if (recent) navigate(`/learning/quiz/${recent.id}`);
    else if (firstBook) navigate(`/learning/books/${firstBook.id}`);
    else setAdding(true);
  }

  return (
    <div className="study-page study-home page-enter">
      <header className="study-home-header">
        <span className="eyebrow">XINXIN / STUDY ROOM</span>
        <span className="study-room-label">
          <i />
          为理解，留一点时间
        </span>
      </header>
      <section className="study-hero">
        <div className="study-hero-copy">
          <p className="study-overline">学习 / 一间属于你的自习室</p>
          <h1>
            读过的，
            <br />
            成为<span>懂得的。</span>
          </h1>
          <p className="study-hero-description">
            从你的一份资料开始。让每一道题有据可循，
            <br className="study-desktop-break" />
            让每一次卡住，都有人陪你想明白。
          </p>
          <div className="study-hero-actions">
            <button className="button primary" onClick={continueStudy}>
              {recent
                ? "继续上次练习"
                : firstBook
                  ? "进入出题工作室"
                  : "开始我的学习"}
              <ArrowUpRight size={17} />
            </button>
            <a href="#study-shelf" className="study-quiet-link">
              浏览书架
              <ArrowDown size={14} />
            </a>
          </div>
        </div>
        <div className="study-hero-index" aria-hidden="true">
          <div className="study-index-top">
            <span>
              THE ART OF
              <br />
              UNDERSTANDING
            </span>
            <span>学 · 习</span>
          </div>
          <div className="study-index-number">
            Aa<span>知</span>
          </div>
          <div className="study-index-bottom">
            <span>阅读 / 练习 / 理解</span>
            <MoveUpRight size={25} strokeWidth={1} />
          </div>
          <i className="study-page-tab">XINXIN</i>
        </div>
      </section>
      <div className="study-ledger" aria-label="学习统计">
        {[
          ["01", "在架资料", summary?.books, "本"],
          ["02", "我的题库", summary?.questions, "道"],
          ["03", "已练题目", books.data ? uniqueAnswered : undefined, "道"],
          [
            "04",
            "作答正确率",
            summary && summary.answered
              ? Math.round(summary.accuracy * 100)
              : undefined,
            summary?.answered ? "%" : "待练习",
          ],
        ].map(([number, label, value, unit]) => (
          <div key={String(number)}>
            <span className="study-ledger-label">
              <small>{number}</small>
              {label}
            </span>
            <strong>
              {value ?? "—"}
              <i>{unit}</i>
            </strong>
          </div>
        ))}
      </div>
      {stats.error && <ErrorState message={stats.error} retry={stats.reload} />}
      {lastImport.error && (
        <ErrorState message={lastImport.error} retry={lastImport.reload} />
      )}
      {importJob && (
        <section
          className="study-import-progress"
          aria-label="资料识别进度"
          aria-busy={preparing}
        >
          <div>
            <p className="eyebrow">MATERIAL PREPARATION</p>
            <h2>
              {preparing
                ? "正在读懂这份资料。"
                : importJob.status === "completed"
                  ? "资料已准备好。"
                  : "资料识别尚未完成。"}
            </h2>
            <p role="status">
              {importJob.progress
                ? `已处理 ${importJob.progress.page} / ${importJob.progress.total} 页 · ${importJob.progress.method === "ocr" ? "本地 OCR" : "文字提取"}`
                : preparing
                  ? "正在检查正文与扫描页面…"
                  : "可重新选择资料开始识别"}
            </p>
            {(importError || importJob.error) && (
              <p className="study-import-error" role="alert">
                {importError || importJob.error}
              </p>
            )}
          </div>
          <div className="study-header-actions">
            {preparing && (
              <button
                className="button secondary"
                disabled={importJob.status === "cancelling"}
                onClick={() =>
                  void post(`/runs/${importJob.run_id}/cancel`, {})
                    .then(() =>
                      setImportJob((value) =>
                        value ? { ...value, status: "cancelling" } : null,
                      ),
                    )
                    .catch((error) => toast(error.message, true))
                }
              >
                停止识别
              </button>
            )}
            {importJob.book_id && (
              <Link
                className="button primary"
                to={`/learning/books/${importJob.book_id}`}
              >
                打开资料 <ArrowRight size={15} />
              </Link>
            )}
          </div>
        </section>
      )}

      <section className="study-shelf" id="study-shelf">
        <div className="study-section-heading">
          <div>
            <p className="eyebrow">MY MATERIALS</p>
            <h2>学习，从这里翻开。</h2>
          </div>
          <button className="button secondary" onClick={() => setAdding(true)}>
            <Plus size={16} />
            加入书架
          </button>
        </div>
        {books.error ? (
          <ErrorState message={books.error} retry={books.reload} />
        ) : !books.data ? (
          <Loading />
        ) : !books.data.books.length ? (
          <div className="study-empty-shelf">
            <BookOpen size={38} strokeWidth={1} />
            <h3>第一本书，会是关于什么？</h3>
            <p>
              上传 PDF、Word 或笔记。我们按原文分章，
              <br />
              你决定从哪里开始。
            </p>
            <button className="button primary" onClick={() => setAdding(true)}>
              <Plus size={15} />
              加入第一份资料
            </button>
          </div>
        ) : (
          <div className="study-book-grid">
            {books.data.books.map((book, index) => {
              const practiced =
                book.unique_answered ??
                Math.min(book.answered, book.question_count);
              const progress = book.question_count
                ? Math.min(
                    100,
                    Math.round((practiced / book.question_count) * 100),
                  )
                : 0;
              return (
                <article key={book.id} className="study-shelf-card">
                  <Link
                    to={`/learning/books/${book.id}`}
                    className="study-cover"
                    aria-label={`打开 ${book.title}`}
                  >
                    <div className="study-cover-top">
                      <span>{book.subject || "自主学习"}</span>
                      <ArrowUpRight size={17} />
                    </div>
                    <h3>{book.title}</h3>
                    <div className="study-cover-bottom">
                      <span>{book.question_count ? "继续深入" : "待出题"}</span>
                      <b>{String(index + 1).padStart(2, "0")}</b>
                    </div>
                    <i className="study-cover-spine" />
                  </Link>
                  <button
                    className="study-book-remove icon-button"
                    aria-label={`移除 ${book.title}`}
                    onClick={() => void dropBook(book)}
                  >
                    <Trash2 size={14} />
                  </button>
                  <div className="study-book-meta">
                    <p>
                      {book.chapter_count} 章 · {wordCount(book.char_count)}
                      <span>{book.question_count} 道题</span>
                    </p>
                    <div className="study-book-progress" aria-hidden="true">
                      <i style={{ width: `${progress}%` }} />
                    </div>
                    <p>
                      <span>
                        {practiced
                          ? `已练 ${practiced} 道不同的题`
                          : "准备好，翻开新的一章"}
                      </span>
                      <span>{progress}%</span>
                    </p>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      <section className="study-review-grid">
        <div>
          <div className="study-section-heading">
            <div>
              <p className="eyebrow">PICK UP WHERE YOU LEFT OFF</p>
              <h2>每一步，都算数。</h2>
            </div>
            <Clock3 size={20} strokeWidth={1.3} />
          </div>
          {summary?.recent.length ? (
            <ul className="study-recent">
              {summary.recent.map((item) => (
                <li key={item.id}>
                  <Link to={`/learning/quiz/${item.id}`}>
                    <span className={`study-session-icon ${item.status}`}>
                      {item.status === "completed" ? (
                        <Check size={15} />
                      ) : (
                        <BookOpen size={15} />
                      )}
                    </span>
                    <div>
                      <strong>{item.title}</strong>
                      <small>
                        {item.total} 道题 · {date(item.created)}
                      </small>
                    </div>
                    <span>{item.status === "completed" ? "回看" : "继续"}</span>
                    <ArrowUpRight size={16} />
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="study-calm-empty">
              还没有练习记录。读完一段，试着用一道题理解它。
            </p>
          )}
        </div>
        <aside className="study-weak">
          <p className="eyebrow">ROOM FOR GROWTH</p>
          <h2>留给下一次的灵光。</h2>
          <p>
            那些暂时卡住的地方，
            <br />
            正是下一步可以长进的地方。
          </p>
          {summary?.weak_tags.length ? (
            <ul>
              {summary.weak_tags.map((item) => (
                <li key={item.tag}>
                  <span>{item.tag}</span>
                  <small>
                    {item.wrong} / {item.total} 次需巩固
                  </small>
                </li>
              ))}
            </ul>
          ) : (
            <div className="study-weak-empty">
              <span>还没有薄弱知识点</span>
              <small>完成练习后，在这里找到复习方向。</small>
            </div>
          )}
          <span className="study-weak-foot">
            从资料详情进入「错题复习」
            <ArrowRight size={14} />
          </span>
        </aside>
      </section>

      <details className="study-canvas">
        <summary>
          <div>
            <span className="eyebrow">A LITTLE EXPLORATION</span>
            <h2>换一种方式，看见函数。</h2>
          </div>
          <Plus size={22} strokeWidth={1.2} />
        </summary>
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
            />
            <p className="plot-hint">
              支持 sin / cos / ln / sqrt 等函数，最多四条曲线。
            </p>
          </div>
          <FunctionPlot
            expressions={expressions}
            height={280}
            xMin={-8}
            xMax={8}
          />
        </div>
      </details>
      <footer className="study-footer">
        <span>XINXIN STUDY ROOM</span>
        <p>
          资料保存在本机。出题、主观题判分与辅导会将相关内容发送给你配置的模型。
        </p>
        <span>学，然后知不足。</span>
      </footer>

      {adding && (
        <Dialog
          title="加入书架"
          busy={busy || uploading}
          onClose={() => {
            if (!busy && !uploading) setAdding(false);
          }}
        >
          <form className="stack" onSubmit={addBook}>
            <div className="study-upload-intro">
              <BookOpen size={25} strokeWidth={1.2} />
              <p>
                一本教材，一份笔记。
                <br />
                <span>让你的资料，变成真正的理解。</span>
              </p>
            </div>
            <input
              ref={fileInput}
              type="file"
              accept={BOOK_EXT.join(",")}
              hidden
              aria-label="上传学习资料"
              onChange={(event) => void uploadFile(event.target.files?.[0])}
            />
            <button
              type="button"
              className="study-upload-button"
              disabled={busy || uploading}
              onClick={() => fileInput.current?.click()}
            >
              <FileUp size={19} />
              <span>
                {uploading
                  ? uploadPercent < 100
                    ? `正在上传 ${uploadPercent}%…`
                    : "上传完成，正在检查正文…"
                  : "上传新的学习资料"}
                <small>PDF / Word / 文本 · 单个最多 256 MB</small>
              </span>
              <Plus size={16} />
            </button>
            <label className="field">
              <span>或从私人资料中选择</span>
              <select
                disabled={busy || uploading}
                value={fileId}
                onChange={(event) => setFileId(event.target.value)}
              >
                <option value="">选择一份已有资料…</option>
                {candidates.map((file) => (
                  <option key={file.id} value={file.id}>
                    {file.name}
                  </option>
                ))}
              </select>
            </label>
            {files.error && (
              <ErrorState message={files.error} retry={files.reload} />
            )}
            <label className="field">
              <span>
                学科 <small>可选</small>
              </span>
              <input
                value={subject}
                disabled={busy || uploading}
                onChange={(event) => setSubject(event.target.value)}
                placeholder="数学 / 英语 / 专业课…"
                maxLength={40}
              />
            </label>
            <p className="hint">
              扫描页面会在本机进行
              OCR。识别过程可查看进度并停止；公式和图示仍需对照原文件核对。
            </p>
            <div className="dialog-actions">
              <button
                type="button"
                className="button ghost"
                disabled={busy || uploading}
                onClick={() => setAdding(false)}
              >
                取消
              </button>
              <button
                className="button primary"
                disabled={
                  busy || uploading || preparing || !fileId || !lastImport.data
                }
              >
                {busy
                  ? "正在开始识别…"
                  : preparing
                    ? "请等待当前资料识别"
                    : "加入并开始学习"}
                <ArrowRight size={15} />
              </button>
            </div>
          </form>
        </Dialog>
      )}
    </div>
  );
}
