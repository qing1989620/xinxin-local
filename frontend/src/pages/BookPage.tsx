import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Check,
  ChevronRight,
  Circle,
  FileText,
  Loader2,
  Plus,
  RotateCcw,
  SlidersHorizontal,
  Pencil,
  Sparkles,
  Square,
  Trash2,
} from "lucide-react";
import {
  acknowledgeRequest,
  api,
  post,
  put,
  remove,
  stableRequestKey,
  watchRun,
} from "../api";
import {
  Dialog,
  Empty,
  ErrorState,
  Loading,
  useResource,
  useToast,
} from "../ui";
import { MathText } from "../components/MathText";
import { StudySource } from "../components/StudySource";
import { StudyPdfPages } from "../components/StudyPdfPages";
import {
  isGenerating,
  KIND_LABEL,
  wordCount,
  type Generation,
  type SourceText,
  type SourceUnit,
  type StudyBook,
  type SourceListing,
  type ImportJob,
} from "../learning";

type Question = {
  id: string;
  chapter_id: string;
  kind: keyof typeof KIND_LABEL;
  stem: string;
  tags: string[];
  difficulty: number;
  source_id?: string;
  source_quote?: string;
  source_pages?: number[];
  origin?: string;
};
const STATES: Record<string, string> = {
  queued: "等待开始",
  running: "正在出题",
  cancelling: "正在停止",
  cancelled: "已取消",
  interrupted: "服务中断",
  failed: "未能完成",
  partial: "部分完成",
  completed: "本次出题完成",
  analyzing: "分析材料",
  reading: "读取 PDF 原页",
  generating: "分批出题",
  reviewing: "复核答案",
};

function pageCount(scope: SourceUnit[]) {
  return scope.reduce(
    (sum, unit) =>
      sum +
      (unit.page_from && unit.page_to ? unit.page_to - unit.page_from + 1 : 0),
    0,
  );
}

function imageReadingIssue(
  scope: SourceUnit[],
  capability: SourceListing["image_reading"],
) {
  if (!capability?.available)
    return capability?.reason || "此资料暂不支持原页读取";
  if (
    scope.some(
      (unit) =>
        !unit.page_from || !unit.page_to || unit.page_to - unit.page_from >= 24,
    )
  )
    return "有片段缺少可靠页码或超过 24 页，请缩小选择范围。";
  return pageCount(scope) > capability.max_pages
    ? `一次最多读取 ${capability.max_pages} 个 PDF 原页，请减少选择范围。`
    : "";
}

export default function BookRoute() {
  const { id = "" } = useParams();
  return <BookPage key={id} />;
}

function BookPage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const book = useResource<{ book: StudyBook }>(`/learning/books/${id}`);
  const questions = useResource<{ questions: Question[] }>(
    `/learning/questions?book_id=${encodeURIComponent(id)}`,
  );
  const units = useResource<SourceListing>(`/learning/books/${id}/sources`);
  const initialJob = useResource<{ job: Generation | null }>(
    `/learning/books/${id}/generation`,
  );
  const [job, setJob] = useState<Generation | null>(null);
  const [connection, setConnection] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [previewId, setPreviewId] = useState("");
  const [preview, setPreview] = useState<SourceText | null>(null);
  const [previewError, setPreviewError] = useState("");
  const [previewRetry, setPreviewRetry] = useState(0);
  const [count, setCount] = useState(12);
  const [readMode, setReadMode] = useState<"text" | "pdf">("text");
  const [showPdf, setShowPdf] = useState(false);
  const [generationMode, setGenerationMode] = useState<
    "auto" | "original" | "practice"
  >("auto");
  const [kinds, setKinds] = useState<Array<keyof typeof KIND_LABEL>>([
    "single",
    "fill",
    "short",
  ]);
  const [difficulty, setDifficulty] = useState(0);
  const [focus, setFocus] = useState("");
  const [busy, setBusy] = useState(false);
  const [quizBusy, setQuizBusy] = useState(false);
  const [pane, setPane] = useState("contents");
  const [filter, setFilter] = useState("");
  const [visible, setVisible] = useState(12);
  const [sourceDialog, setSourceDialog] = useState<Question | null>(null);
  const [correction, setCorrection] = useState<{
    id: string;
    text: string;
  } | null>(null);
  const [summaryShown, setSummaryShown] = useState(12);
  const [savingCorrection, setSavingCorrection] = useState(false);
  const correctionLock = useRef(false);
  const generationBusy = useRef(false);
  const currentBook = useRef(id);
  currentBook.current = id;
  const refresh = useRef(() => {});
  refresh.current = () => {
    book.reload();
    questions.reload();
    units.reload();
    setPreviewRetry((value) => value + 1);
  };
  const active = isGenerating(job);
  const limit = units.data?.max_sources ?? 40;
  const questionLimit = units.data?.max_questions ?? 400;

  useEffect(() => {
    setSelected([]);
    setPreviewId("");
    setJob(null);
    setPane("contents");
  }, [id]);
  useEffect(() => {
    if (initialJob.data) {
      const previous = initialJob.data.job;
      setJob(previous);
      // The other requests may have completed before the last source committed.
      // A terminal snapshot must reconcile the bank even without an SSE stream.
      if (previous && !isGenerating(previous)) refresh.current();
      if (previous?.options) {
        setCount(previous.options.count);
        setKinds(previous.options.kinds);
        setDifficulty(previous.options.difficulty);
        setFocus(previous.options.focus);
        setGenerationMode(previous.options.mode ?? "auto");
        setReadMode(previous.options.read_mode ?? "text");
        if (isGenerating(previous))
          setSelected(previous.items.map((item) => item.source_id));
      }
    }
  }, [initialJob.data]);
  useEffect(() => {
    if (!previewId && units.data?.sources.length)
      setPreviewId(units.data.sources[0].id);
  }, [units.data, previewId]);
  useEffect(() => {
    setPreview((current) => (current?.id === previewId ? current : null));
    setPreviewError("");
    if (!previewId) return;
    const controller = new AbortController();
    void api<{ source: SourceText }>(`/learning/sources/${previewId}`, {
      signal: controller.signal,
    })
      .then((value) => {
        if (!controller.signal.aborted) setPreview(value.source);
      })
      .catch((err: Error) => {
        if (!controller.signal.aborted) setPreviewError(err.message);
      });
    return () => controller.abort();
  }, [previewId, previewRetry]);
  useEffect(() => {
    if (!job?.run_id || !isGenerating(job)) return;
    const controller = new AbortController();
    let pending = false;
    async function sync() {
      if (pending || controller.signal.aborted) return;
      pending = true;
      try {
        const value = await api<{ job: Generation }>(
          `/learning/generations/${job!.id}`,
          { signal: controller.signal },
        );
        if (!controller.signal.aborted) {
          setJob(value.job);
          if (!isGenerating(value.job)) refresh.current();
        }
      } catch (err) {
        if (!controller.signal.aborted) setConnection((err as Error).message);
      } finally {
        pending = false;
      }
    }
    void watchRun(
      job.run_id,
      (event) => {
        void sync();
        if (
          event.kind === "learning.source.analyzed" ||
          event.kind === "learning.batch.saved"
        )
          refresh.current();
      },
      controller.signal,
      setConnection,
      () => void sync(),
    )
      .then(() => void sync())
      .catch((err: Error) => {
        if (!controller.signal.aborted) setConnection(err.message);
      });
    const recovery = setInterval(() => void sync(), 3000);
    return () => {
      controller.abort();
      clearInterval(recovery);
    };
  }, [job?.id, job?.run_id, active]);

  const byChapter = useMemo(() => {
    const map: Record<string, SourceUnit[]> = {};
    for (const unit of units.data?.sources ?? [])
      (map[unit.chapter_id] ||= []).push(unit);
    return map;
  }, [units.data]);
  const selectedScope = (units.data?.sources ?? []).filter((unit) =>
    selected.includes(unit.id),
  );
  const selectedPages = pageCount(selectedScope);
  const remainingItems =
    job?.items.filter((item) => item.target > item.created_count) ?? [];
  const resumeScope = (units.data?.sources ?? []).filter((unit) =>
    remainingItems.some((item) => item.source_id === unit.id),
  );
  const readingError =
    readMode === "pdf"
      ? imageReadingIssue(selectedScope, units.data?.image_reading)
      : "";
  const resumeReadingError =
    readMode === "pdf"
      ? resumeScope.length !== remainingItems.length
        ? "缺题来源尚未加载，请稍后重试。"
        : imageReadingIssue(resumeScope, units.data?.image_reading)
      : "";
  const bank = useMemo(
    () =>
      (questions.data?.questions ?? []).filter(
        (question) => !filter || question.kind === filter,
      ),
    [questions.data, filter],
  );

  function toggle(unit: {
    id: string;
    eligible?: boolean;
    text_eligible?: boolean;
  }) {
    if ((unit.text_eligible ?? unit.eligible) === false && readMode !== "pdf")
      return;
    if (selected.includes(unit.id))
      setSelected((value) => value.filter((ident) => ident !== unit.id));
    else if (selected.length < limit)
      setSelected((value) => [...value, unit.id]);
    else toast(`一次最多选择 ${limit} 个片段`, true);
  }
  async function generate(resume = false, analyzeOnly = false) {
    if (generationBusy.current) return;
    generationBusy.current = true;
    setBusy(true);
    const origin = id;
    const namespace = `study:${id}`;
    try {
      const payload = {
        source_ids: resume ? [] : selected,
        count,
        kinds,
        difficulty,
        focus: focus.trim(),
        resume_job_id: resume ? (job?.id ?? "") : "",
        mode: generationMode,
        analyze_only: analyzeOnly,
        read_mode: readMode,
      };
      const key = await stableRequestKey(namespace, payload);
      const value = await post<{ job: Generation }>(
        `/learning/books/${id}/generations`,
        { ...payload, request_key: key },
      );
      acknowledgeRequest(namespace);
      if (currentBook.current === origin) {
        setJob(value.job);
        setPane("settings");
      }
    } catch (err) {
      toast((err as Error).message, true);
    } finally {
      generationBusy.current = false;
      if (currentBook.current === origin) setBusy(false);
    }
  }
  function selectScope(onlyUnanalyzed = false) {
    const eligible = (units.data?.sources ?? []).filter(
      (unit) =>
        (readMode === "pdf"
          ? Boolean(
              unit.page_from &&
              unit.page_to &&
              unit.page_to - unit.page_from < 24,
            )
          : (unit.text_eligible ?? unit.eligible) !== false) &&
        (!onlyUnanalyzed || !unit.analysis),
    );
    setSelected(eligible.slice(0, limit).map((unit) => unit.id));
    if (eligible.length > limit)
      toast(`已选前 ${limit} 个片段，可分批覆盖其余内容`);
  }
  async function reread() {
    if (!data.file_id || generationBusy.current) return;
    generationBusy.current = true;
    setBusy(true);
    try {
      const payload = {
        file_id: data.file_id,
        title: data.title,
        subject: data.subject,
      };
      const requestKey = await stableRequestKey(`reread:${id}`, payload);
      await post<{ job: ImportJob }>("/learning/imports", {
        ...payload,
        request_key: requestKey,
      });
      acknowledgeRequest(`reread:${id}`);
      toast("已开始重新识别原资料，完成后生成一份新书本");
      navigate("/learning");
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      generationBusy.current = false;
      setBusy(false);
    }
  }
  async function saveCorrection(event: React.FormEvent) {
    event.preventDefault();
    if (!correction || correctionLock.current) return;
    correctionLock.current = true;
    setSavingCorrection(true);
    try {
      const value = await put<{ source: SourceText }>(
        `/learning/sources/${correction.id}`,
        { content: correction.text },
      );
      setPreview(value.source);
      setCorrection(null);
      refresh.current();
      toast("已保存校对，旧总结已清除，可重新分析这一片段");
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      correctionLock.current = false;
      setSavingCorrection(false);
    }
  }
  async function cancel() {
    if (!job || busy) return;
    setBusy(true);
    try {
      await post(`/runs/${job.run_id}/cancel`, {});
      const value = await api<{ job: Generation }>(
        `/learning/generations/${job.id}`,
      );
      setJob(value.job);
      refresh.current();
    } catch (err) {
      toast((err as Error).message, true);
    } finally {
      setBusy(false);
    }
  }
  async function practice(chapterId = "", mode = "all") {
    if (quizBusy) return;
    setQuizBusy(true);
    try {
      const value = await post<{ session: { id: string } }>("/learning/quiz", {
        book_id: id,
        chapter_id: chapterId,
        mode,
        count: 10,
      });
      navigate(`/learning/quiz/${value.session.id}`);
    } catch (err) {
      toast((err as Error).message, true);
      setQuizBusy(false);
    }
  }
  async function drop() {
    if (
      !book.data ||
      !window.confirm(`把《${book.data.book.title}》和它的题目一起删掉？`)
    )
      return;
    try {
      await remove(`/learning/books/${id}`);
      toast("已从书架移除");
      navigate("/learning");
    } catch (err) {
      toast((err as Error).message, true);
    }
  }
  if (book.error)
    return <ErrorState message={book.error} retry={book.reload} />;
  if (!book.data) return <Loading />;
  const data = book.data.book;
  const chapterTitle =
    data.chapters.find((chapter) => chapter.id === preview?.chapter_id)
      ?.title ?? "原文预览";
  const rejected =
    job?.items.reduce((total, item) => total + item.rejected, 0) ?? 0;
  const duplicates =
    job?.items.reduce((total, item) => total + item.duplicates, 0) ?? 0;
  const analysis = preview?.analysis;
  const coverage = units.data?.coverage;
  const analyzedUnits =
    units.data?.sources.filter((unit) => unit.analysis) ?? [];

  return (
    <div className="study-page study-book page-enter">
      <div className="study-breadcrumb">
        <button className="back-link" onClick={() => navigate("/learning")}>
          <ArrowLeft size={15} />
          学习
        </button>
        <span>/</span>
        <span>出题工作室</span>
      </div>
      <header className="study-book-header">
        <div>
          <p className="eyebrow">
            THE QUESTION STUDIO <span>01 / 学习资料</span>
          </p>
          <h1>{data.title}</h1>
          <p className="study-caption">
            {data.subject || "自选学科"}
            <i />
            {data.chapter_count} 章<i />
            {wordCount(data.char_count)}
            <i />
            {data.question_count} 道题
          </p>
        </div>
        <div className="study-header-actions">
          <button
            className="icon-button"
            aria-label="移除这本书"
            disabled={active}
            onClick={() => void drop()}
          >
            <Trash2 size={16} />
          </button>
          <button
            className="button secondary"
            disabled={quizBusy || !data.question_count}
            onClick={() => void practice("", "mistakes")}
          >
            <RotateCcw size={15} />
            错题复习
          </button>
          <button
            className="button primary"
            disabled={quizBusy || !data.question_count}
            onClick={() => void practice()}
          >
            全书练习
            <ArrowRight size={16} />
          </button>
        </div>
      </header>
      <section className="study-understanding" aria-label="资料理解与覆盖">
        <div className="study-understanding-heading">
          <div>
            <p className="eyebrow">UNDERSTAND BEFORE PRACTICE</p>
            <h2>先读懂，再出好题。</h2>
          </div>
          <div className="study-coverage">
            <span>
              <strong>
                {coverage?.analyzed ?? 0}
                <small> / {coverage?.total ?? "—"}</small>
              </strong>
              片段已分析
            </span>
            <span>
              <strong>{coverage?.knowledge_points ?? 0}</strong>知识点
            </span>
            <span>
              <strong>{coverage?.exercises ?? 0}</strong>识别原题
            </span>
          </div>
        </div>
        <p>
          先提炼原文知识与完整练习，再分批出题、复核答案。目录和纯答案表不参与出题；摘要仅覆盖已分析片段。
        </p>
        {data.extraction?.warning && (
          <p className="study-extraction-warning" role="status">
            识别提示：{data.extraction.warning}
          </p>
        )}
        {analyzedUnits.length > 0 && (
          <details className="study-summary-index">
            <summary>查看已分析材料的总结 · {analyzedUnits.length} 段</summary>
            <div>
              {analyzedUnits.slice(0, summaryShown).map((unit) => (
                <article key={unit.id}>
                  <button
                    className="text-button"
                    onClick={() => {
                      setPreviewId(unit.id);
                      setPane("reader");
                    }}
                  >
                    {unit.label} · {unit.analysis!.type_label}
                    <ArrowRight size={13} />
                  </button>
                  <p>{unit.analysis!.summary}</p>
                  <span>
                    {unit
                      .analysis!.knowledge_points.map((point) => point.name)
                      .join(" / ") || "原题条件与方法"}
                  </span>
                </article>
              ))}
            </div>
            {analyzedUnits.length > summaryShown && (
              <button
                className="text-button"
                onClick={() => setSummaryShown((value) => value + 12)}
              >
                继续阅读总结
              </button>
            )}
          </details>
        )}
        <div className="study-understanding-actions">
          <button
            className="text-button"
            disabled={
              active || busy || (readMode !== "pdf" && !coverage?.eligible)
            }
            onClick={() => selectScope(true)}
          >
            选择尚未分析的正文 <ArrowRight size={14} />
          </button>
          {data.file_id && (
            <button
              className="text-button"
              disabled={active || busy}
              onClick={() => void reread()}
            >
              <RotateCcw size={13} />
              重新识别原资料
            </button>
          )}
        </div>
      </section>
      <div className="study-process" aria-label="学习流程">
        <span className="current">
          <b>01</b> 选定资料
        </span>
        <ChevronRight size={14} />
        <span>
          <b>02</b> 定制出题
        </span>
        <ChevronRight size={14} />
        <a href="#question-bank">
          <b>03</b> 练习与理解
          <ArrowDown size={13} />
        </a>
      </div>
      <nav className="study-mobile-tabs" aria-label="工作室面板">
        {[
          ["contents", "目录"],
          ["reader", "原文"],
          ["settings", "出题"],
        ].map(([value, label]) => (
          <button
            key={value}
            aria-pressed={pane === value}
            onClick={() => setPane(value)}
          >
            {label}
          </button>
        ))}
      </nav>

      <div className="study-workspace" data-pane={pane}>
        <section className="study-contents" aria-label="选择出题范围">
          <div className="study-panel-title">
            <span>
              <BookOpen size={15} /> 资料目录
            </span>
            <small>
              {selected.length} / {limit}
            </small>
          </div>
          <p className="study-panel-hint">勾选正文或练习，点击标题读原文。</p>
          <button
            className="text-button study-select-scope"
            disabled={active || busy || !units.data}
            onClick={() => selectScope()}
          >
            选择可用正文（最多 {limit} 段）
          </button>
          {units.error ? (
            <ErrorState message={units.error} retry={units.reload} />
          ) : !units.data ? (
            <Loading />
          ) : units.data.sources.length === 0 ? (
            <Empty title="没有可用片段" />
          ) : (
            <div className="study-chapters">
              {data.chapters.map((chapter) => (
                <div className="study-chapter" key={chapter.id}>
                  <div className="study-chapter-title">
                    <span>{String(chapter.idx + 1).padStart(2, "0")}</span>
                    <h2>{chapter.title}</h2>
                  </div>
                  {(byChapter[chapter.id] ?? []).map((unit) => (
                    <div
                      key={unit.id}
                      className={`study-unit${previewId === unit.id ? " previewing" : ""}`}
                    >
                      <label className="study-unit-check">
                        <input
                          type="checkbox"
                          aria-label={`选择 ${chapter.title} ${unit.label}`}
                          checked={selected.includes(unit.id)}
                          disabled={
                            active ||
                            busy ||
                            (readMode === "pdf"
                              ? !unit.page_from ||
                                !unit.page_to ||
                                unit.page_to - unit.page_from >= 24
                              : (unit.text_eligible ?? unit.eligible) ===
                                false) ||
                            (!selected.includes(unit.id) &&
                              selected.length >= limit)
                          }
                          onChange={() => toggle(unit)}
                        />
                      </label>
                      <button
                        aria-current={
                          previewId === unit.id ? "true" : undefined
                        }
                        onClick={() => {
                          setPreviewId(unit.id);
                          setPane("reader");
                        }}
                      >
                        <span>{unit.label}</span>
                        <small>
                          {wordCount(unit.chars)} · {unit.question_count} 题
                          {unit.type_label ? ` · ${unit.type_label}` : ""}
                          {unit.eligible === false ? " · 已排除" : ""}
                        </small>
                      </button>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
          <button
            className="study-clear text-button"
            disabled={!selected.length || active || busy}
            onClick={() => setSelected([])}
          >
            清空选择
          </button>
          <button
            className="button primary study-scope-next"
            disabled={!selected.length}
            onClick={() => setPane("settings")}
          >
            已选 {selected.length} 个片段 · 下一步
            <ArrowRight size={15} />
          </button>
        </section>

        <section
          className="study-reader"
          id="study-source-reader"
          aria-label="教材原文"
        >
          <div className="study-panel-title">
            <span>
              <FileText size={15} /> 原文
            </span>
            <small>{preview?.label ?? "请选择片段"}</small>
          </div>
          {previewError ? (
            <ErrorState
              message={previewError}
              retry={() => setPreviewRetry((value) => value + 1)}
            />
          ) : !preview ? (
            previewId ? (
              <Loading />
            ) : (
              <Empty
                title="从一段原文开始"
                description="在目录中选择片段，读清楚，再出题。"
              />
            )
          ) : (
            <>
              <div className="study-paper" key={preview.id}>
                <p className="eyebrow">
                  SOURCE MATERIAL / {String(preview.idx + 1).padStart(2, "0")}
                </p>
                <h2>{chapterTitle}</h2>
                {units.data?.image_reading?.pdf &&
                  preview.page_from &&
                  preview.page_to &&
                  preview.page_to - preview.page_from < 24 && (
                    <div
                      className="study-reading-switch"
                      role="group"
                      aria-label="资料预览方式"
                    >
                      <button
                        className="text-button"
                        aria-pressed={!showPdf}
                        onClick={() => setShowPdf(false)}
                      >
                        识别文字
                      </button>
                      <button
                        className="text-button"
                        aria-pressed={showPdf}
                        onClick={() => setShowPdf(true)}
                      >
                        对照 PDF 原页
                      </button>
                    </div>
                  )}
                {showPdf &&
                preview.page_from &&
                preview.page_to &&
                preview.page_to - preview.page_from < 24 ? (
                  <StudyPdfPages
                    key={preview.id}
                    id={preview.id}
                    pages={Array.from(
                      { length: preview.page_to - preview.page_from + 1 },
                      (_, index) => preview.page_from! + index,
                    )}
                  />
                ) : (
                  <div className="study-paper-text">
                    <MathText text={analysis?.source_text ?? preview.content} />
                  </div>
                )}
                {analysis && (
                  <section
                    className="study-source-analysis"
                    aria-label="当前片段总结"
                  >
                    <p className="eyebrow">
                      READING NOTES / {analysis.type_label}
                    </p>
                    <h3>这段材料讲了什么</h3>
                    <p>{analysis.summary}</p>
                    {analysis.source_method === "pdf_images" && (
                      <p className="hint">
                        依据 PDF 原页读取；公式仍需对照原图核对。
                      </p>
                    )}
                    {Boolean(
                      analysis.warnings?.length ||
                      analysis.reading_warnings?.length,
                    ) && (
                      <details className="study-analysis-notes">
                        <summary>
                          已保留有效内容
                          {analysis.skipped_entries
                            ? ` · 跳过 ${analysis.skipped_entries} 条分析项`
                            : ""}
                          {" · 查看跳过与待核对项"}
                        </summary>
                        <ul>
                          {[
                            ...(analysis.warnings ?? []),
                            ...(analysis.reading_warnings ?? []),
                          ].map((warning, index) => (
                            <li key={index}>{warning}</li>
                          ))}
                        </ul>
                      </details>
                    )}
                    {analysis.knowledge_points.length > 0 && (
                      <ul>
                        {analysis.knowledge_points.map((point, index) => (
                          <li key={index}>
                            <strong>{point.name}</strong>
                            <details>
                              <summary>查看知识依据</summary>
                              <MathText text={point.quote} />
                            </details>
                          </li>
                        ))}
                      </ul>
                    )}
                    {analysis.exercises.length > 0 && (
                      <details>
                        <summary>
                          识别到 {analysis.exercises.length} 道原题
                        </summary>
                        {analysis.exercises.map((exercise, index) => (
                          <div className="study-original-exercise" key={index}>
                            <strong>
                              {exercise.label}
                              {exercise.solvable ? "" : " · 条件待核对"}
                            </strong>
                            <MathText text={exercise.quote} />
                          </div>
                        ))}
                      </details>
                    )}
                  </section>
                )}
                {preview.eligible === false && (
                  <p className="study-extraction-warning">{preview.reason}</p>
                )}
                <div className="study-paper-footer">
                  <span>
                    {preview.page_from
                      ? "页码为 PDF 文件实际页序"
                      : "文本片段 · 无可靠 PDF 页码"}
                    {preview.edited_at ? " · 已人工校对" : ""}
                  </span>
                  <span>{wordCount(preview.content.length)}</span>
                </div>
              </div>
              <div className="study-reader-actions">
                <button
                  className="text-button"
                  disabled={
                    active ||
                    busy ||
                    (units.data?.sources.find((unit) => unit.id === preview.id)
                      ?.question_count ?? 0) > 0
                  }
                  onClick={() =>
                    setCorrection({ id: preview.id, text: preview.content })
                  }
                >
                  <Pencil size={13} />
                  校对识别文字
                </button>
                <button
                  className="button secondary small"
                  disabled={
                    active ||
                    busy ||
                    (readMode !== "pdf" &&
                      (preview.text_eligible ?? preview.eligible) === false) ||
                    (!selected.includes(preview.id) && selected.length >= limit)
                  }
                  onClick={() => toggle(preview)}
                >
                  {selected.includes(preview.id) ? (
                    <Check size={14} />
                  ) : (
                    <Plus size={14} />
                  )}
                  {selected.includes(preview.id)
                    ? "已加入出题范围"
                    : "加入出题范围"}
                </button>
                <button
                  className="text-button"
                  disabled={
                    quizBusy ||
                    !questions.data?.questions.some(
                      (q) => q.chapter_id === preview.chapter_id,
                    )
                  }
                  onClick={() => void practice(preview.chapter_id)}
                >
                  练这一章
                  <ArrowRight size={14} />
                </button>
              </div>
            </>
          )}
        </section>

        <aside className="study-settings" aria-label="出题设置">
          <div className="study-panel-title">
            <span>
              <SlidersHorizontal size={15} /> 定制这一组题
            </span>
            <small>02</small>
          </div>
          <fieldset disabled={active || busy} className="study-config">
            <div>
              <label className="study-label" htmlFor="study-reading">
                材料读取方式
              </label>
              <select
                id="study-reading"
                value={readMode}
                onChange={(event) =>
                  setReadMode(event.target.value as "text" | "pdf")
                }
              >
                <option value="text">识别文字 · 适合清晰文本资料</option>
                <option
                  value="pdf"
                  disabled={!units.data?.image_reading?.available}
                >
                  PDF 原页 · 看清公式与上下标
                </option>
              </select>
              <p className="hint">
                {readMode === "pdf"
                  ? `将选中范围的 ${selectedPages} 个 PDF 原页图片发送给当前模型，另行核对原图；逐页缓存，提高模型用量。`
                  : "仅发送选中片段的识别文字。练习册若有分式或上下标缺失，请选择 PDF 原页。"}
              </p>
              {!units.data?.image_reading?.available && (
                <p className="hint">{units.data?.image_reading?.reason}</p>
              )}
            </div>
            <div className="study-config-row">
              <label htmlFor="study-count">每个片段</label>
              <select
                id="study-count"
                value={count}
                onChange={(event) => setCount(Number(event.target.value))}
              >
                {[1, 2, 3, 4, 5, 6, 8, 12, 16, 20, 24].map((value) => (
                  <option value={value} key={value}>
                    {value} 道题
                  </option>
                ))}
              </select>
            </div>
            <label className="study-label" htmlFor="study-mode">
              出题策略
            </label>
            <select
              id="study-mode"
              value={generationMode}
              onChange={(event) =>
                setGenerationMode(event.target.value as typeof generationMode)
              }
            >
              <option value="auto">自动 · 原题优先，补充知识变式</option>
              <option value="original">原题整理 · 保留条件与选项</option>
              <option value="practice">知识拓展 · 理解、应用与推理</option>
            </select>
            <div>
              <span className="study-label" id="study-kinds">
                题型组合
              </span>
              <div
                className="study-kinds"
                role="group"
                aria-labelledby="study-kinds"
              >
                {Object.entries(KIND_LABEL).map(([key, label]) => (
                  <label key={key}>
                    <input
                      type="checkbox"
                      checked={kinds.includes(key as keyof typeof KIND_LABEL)}
                      disabled={
                        active ||
                        busy ||
                        (kinds.length === 1 && kinds[0] === key)
                      }
                      onChange={() =>
                        setKinds((value) =>
                          value.includes(key as keyof typeof KIND_LABEL)
                            ? value.filter((kind) => kind !== key)
                            : [...value, key as keyof typeof KIND_LABEL],
                        )
                      }
                    />
                    <span>{label}</span>
                  </label>
                ))}
              </div>
            </div>
            <div>
              <label className="study-label" htmlFor="study-difficulty">
                难度
              </label>
              <select
                id="study-difficulty"
                value={difficulty}
                onChange={(event) => setDifficulty(Number(event.target.value))}
              >
                <option value={0}>循序渐进 · 混合难度</option>
                <option value={1}>基础 · 理解概念</option>
                <option value={2}>进阶 · 应用与推理</option>
                <option value={3}>挑战 · 综合分析</option>
              </select>
            </div>
            <div>
              <label className="study-label" htmlFor="study-focus">
                考查重点 <small>可选</small>
              </label>
              <textarea
                id="study-focus"
                rows={3}
                maxLength={240}
                value={focus}
                placeholder="例如：重点考查易混概念，用应用场景帮助理解。"
                onChange={(event) => setFocus(event.target.value)}
              />
              <span className="study-focus-count">{focus.length} / 240</span>
            </div>
          </fieldset>
          <div className="study-estimate">
            <span>本次计划</span>
            <strong>
              {selected.length * count}
              <small>道题</small>
            </strong>
            <p>
              {selected.length
                ? `${selected.length} 个片段 × ${count} 道 · 以实际通过校验数量为准`
                : "先在左侧勾选出题片段"}
            </p>
          </div>
          <button
            className="button primary study-generate"
            disabled={
              active ||
              busy ||
              !selected.length ||
              selected.length * count > questionLimit ||
              !initialJob.data ||
              Boolean(initialJob.error) ||
              Boolean(readingError)
            }
            onClick={() => void generate()}
          >
            {busy || active ? (
              <Loader2 className="spin" size={16} />
            ) : (
              <Sparkles size={16} />
            )}
            {active ? STATES[job!.status] : "生成这一组题"}
            <ArrowRight size={15} />
          </button>
          {selected.length * count > questionLimit && (
            <p className="study-extraction-warning" role="alert">
              单批最多 {questionLimit} 道题，请减少范围或每片段题量。
            </p>
          )}
          {readingError && (
            <p className="study-extraction-warning" role="alert">
              {readingError}
            </p>
          )}
          <button
            className="button secondary study-analyze"
            disabled={
              active ||
              busy ||
              !selected.length ||
              !initialJob.data ||
              Boolean(initialJob.error) ||
              Boolean(readingError)
            }
            onClick={() => void generate(false, true)}
          >
            <BookOpen size={15} />
            先总结选中材料
          </button>
          {initialJob.error && (
            <ErrorState message={initialJob.error} retry={initialJob.reload} />
          )}
          <p className="study-model-note">
            选中材料会发送给已配置的模型，按每批最多 3
            题生成并另行审题。提高题量会增加时间与模型用量；未通过复核的题不入库，AI
            结论仍需核对。
          </p>
        </aside>
      </div>

      {job && (
        <section
          className="study-generation"
          aria-label="出题进度"
          aria-busy={active}
        >
          <div className="study-generation-top">
            <div>
              <p className="eyebrow">GENERATION LOG</p>
              <h2 aria-live="polite">
                {job.options.analyze_only
                  ? active
                    ? "正在总结材料"
                    : job.status === "completed"
                      ? "材料分析完成"
                      : "材料分析未完成"
                  : (STATES[job.status] ?? job.status)}
              </h2>
            </div>
            <div className="study-generation-total">
              <strong>
                {job.options.analyze_only
                  ? job.finished_sources
                  : job.created_count}
                <span>
                  {" "}
                  / {job.options.analyze_only ? job.items.length : job.target}
                </span>
              </strong>
              <small>
                {job.options.analyze_only ? "片段已总结" : "道题已入库"}
              </small>
            </div>
            <div className="study-generation-actions">
              {active ? (
                <button
                  className="button secondary small"
                  disabled={busy || job.status === "cancelling"}
                  onClick={() => void cancel()}
                >
                  <Square size={12} />
                  停止出题
                </button>
              ) : job.options.analyze_only ? (
                <a
                  className="button secondary small"
                  href="#study-source-reader"
                  onClick={() => setPane("reader")}
                >
                  阅读材料总结 <ArrowRight size={14} />
                </a>
              ) : job.created_count < job.target ? (
                <button
                  className="button secondary small"
                  disabled={busy || Boolean(resumeReadingError)}
                  onClick={() => void generate(true)}
                >
                  <RotateCcw size={14} />
                  补出缺少的题
                  {readMode === "pdf"
                    ? ` · 原页 ${pageCount(resumeScope)} 页`
                    : ""}
                </button>
              ) : (
                <button
                  className="button secondary small"
                  disabled={quizBusy}
                  onClick={() => void practice()}
                >
                  开始练习
                  <ArrowRight size={14} />
                </button>
              )}
            </div>
          </div>
          {remainingItems.length > 0 && resumeReadingError && (
            <p className="study-extraction-warning" role="alert">
              {resumeReadingError}
            </p>
          )}
          <div
            className="study-generation-bar"
            role="progressbar"
            aria-label={
              job.options.analyze_only ? "材料分析进度" : "题目入库进度"
            }
            aria-valuenow={
              job.options.analyze_only
                ? job.finished_sources
                : job.created_count
            }
            aria-valuemin={0}
            aria-valuemax={
              job.options.analyze_only ? job.items.length : job.target
            }
          >
            <i
              style={{
                width: `${job.options.analyze_only ? (job.finished_sources / job.items.length) * 100 : job.target ? (job.created_count / job.target) * 100 : 0}%`,
              }}
            />
          </div>
          <ul className="study-job-items">
            {job.items.map((item) => (
              <li key={item.source_id}>
                {item.status === "completed" ? (
                  <Check size={14} />
                ) : [
                    "running",
                    "analyzing",
                    "reading",
                    "generating",
                    "reviewing",
                  ].includes(item.status) && active ? (
                  <Loader2 className="spin" size={14} />
                ) : (
                  <Circle size={12} />
                )}
                <span>
                  {item.chapter_title} · {item.label}
                </span>
                <small>
                  {active &&
                  ["reading", "analyzing", "generating", "reviewing"].includes(
                    item.status,
                  )
                    ? STATES[item.status]
                    : job.options.analyze_only
                      ? item.status === "completed"
                        ? "已总结"
                        : "待完成"
                      : `${item.created_count}/${item.target}`}
                </small>
                {item.error && <p>{item.error}</p>}
              </li>
            ))}
          </ul>
          <p className="study-job-note">
            {active
              ? connection === "reconnecting"
                ? "连接恢复中，已保存进度不会丢失。"
                : "可以离开此页，回来会恢复真实进度。停止后已入库的题会保留。"
              : job.options.analyze_only
                ? `${job.finished_sources} / ${job.items.length} 个片段完成总结，可在原文中查看知识点与原题。`
                : `${job.finished_sources} / ${job.items.length} 个片段达成计划 · 过滤 ${rejected} 个无效题、${duplicates} 个重复题`}
            {job.error && ` · ${job.error}`}
          </p>
        </section>
      )}

      <section className="study-bank" id="question-bank">
        <div className="study-section-heading">
          <div>
            <p className="eyebrow">YOUR QUESTION BANK</p>
            <h2>把知识，练成自己的。</h2>
          </div>
          <span>{questions.data?.questions.length ?? 0} 道题</span>
        </div>
        <div className="study-bank-toolbar" role="group" aria-label="筛选题型">
          {[["", "全部"], ...Object.entries(KIND_LABEL)].map(([key, label]) => (
            <button
              key={key}
              aria-pressed={filter === key}
              onClick={() => {
                setFilter(key);
                setVisible(12);
              }}
            >
              {label}
            </button>
          ))}
        </div>
        {questions.error ? (
          <ErrorState message={questions.error} retry={questions.reload} />
        ) : !questions.data ? (
          <Loading />
        ) : !bank.length ? (
          <Empty
            title={filter ? "这个题型还没有题" : "好题，从读懂原文开始"}
            description="选定片段和题型，生成后即可开始练习。"
          />
        ) : (
          <ol className="study-question-bank">
            {bank.slice(0, visible).map((question, index) => (
              <li key={question.id}>
                <span className="study-question-number">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div>
                  <div className="study-question-meta">
                    <span>{KIND_LABEL[question.kind]}</span>
                    {question.origin && question.origin !== "legacy" && (
                      <span>
                        {question.origin === "original"
                          ? "原题整理"
                          : "知识拓展"}
                      </span>
                    )}
                    <span>
                      {["", "基础", "进阶", "挑战"][question.difficulty]}
                    </span>
                    <span>{question.tags.join(" / ")}</span>
                  </div>
                  <div className="study-question-stem">
                    <MathText text={question.stem} />
                  </div>
                  {question.source_id ? (
                    <button
                      className="text-button"
                      onClick={() => setSourceDialog(question)}
                    >
                      <FileText size={13} />
                      核对原文依据
                      <ArrowRight size={13} />
                    </button>
                  ) : (
                    <small className="muted">早期题目 · 未记录来源</small>
                  )}
                </div>
              </li>
            ))}
          </ol>
        )}
        {visible < bank.length && (
          <button
            className="button secondary study-more"
            onClick={() => setVisible((value) => value + 12)}
          >
            再看 12 道题
            <span>
              {visible} / {bank.length}
            </span>
          </button>
        )}
      </section>
      {correction && (
        <Dialog
          title="校对识别文字"
          busy={savingCorrection}
          onClose={() => setCorrection(null)}
        >
          <form className="stack" onSubmit={saveCorrection}>
            <p className="hint">
              对照原文件校对公式、单位与完整题干。改动保存到学习副本，已有总结将重新分析；原文件保留。
            </p>
            <label className="field">
              <span>片段正文</span>
              <textarea
                aria-label="片段正文"
                rows={16}
                minLength={24}
                maxLength={8000}
                disabled={savingCorrection}
                value={correction.text}
                onChange={(event) =>
                  setCorrection((value) =>
                    value ? { ...value, text: event.target.value } : null,
                  )
                }
              />
            </label>
            <p className="hint">
              {correction.text.length} / 8000 字 ·
              已有题目的片段需重新识别原资料后再校对。
            </p>
            <div className="dialog-actions">
              <button
                type="button"
                className="button secondary"
                disabled={savingCorrection}
                onClick={() => setCorrection(null)}
              >
                取消
              </button>
              <button
                className="button primary"
                disabled={
                  savingCorrection || correction.text.trim().length < 24
                }
              >
                {savingCorrection ? "正在保存…" : "保存校对"}
              </button>
            </div>
          </form>
        </Dialog>
      )}
      {sourceDialog?.source_id && (
        <StudySource
          key={sourceDialog.source_id}
          id={sourceDialog.source_id}
          quote={sourceDialog.source_quote}
          pages={sourceDialog.source_pages}
          onClose={() => setSourceDialog(null)}
        />
      )}
    </div>
  );
}
