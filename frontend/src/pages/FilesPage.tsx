import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  ArrowUpRight,
  Download,
  FileText,
  Image,
  Plus,
  Search,
  Trash2,
  UploadCloud,
} from "lucide-react";
import { api, remove, download, type FileItem } from "../api";
import { UploadQueue, useUploads } from "../Uploads";
import {
  Dialog,
  Empty,
  ErrorState,
  Loading,
  PageHeader,
  PrivateImage,
  date,
  size,
  useResource,
  useToast,
} from "../ui";

export default function FilesPage() {
  const { data, error, reload } = useResource<FileItem[]>("/files"),
    [query, setQuery] = useState(""),
    [preview, setPreview] = useState<FileItem | null>(null),
    [text, setText] = useState(""),
    [textBusy, setTextBusy] = useState(false),
    [textError, setTextError] = useState(""),
    [searchBusy, setSearchBusy] = useState(false),
    [nextOffset, setNextOffset] = useState<number | null>(null),
    [totalChars, setTotalChars] = useState(0),
    [results, setResults] = useState<any[] | null>(null);
  const picker = useRef<HTMLInputElement>(null),
    previewId = useRef(""),
    searchController = useRef<AbortController | null>(null),
    toast = useToast(),
    navigate = useNavigate(),
    [params, setParams] = useSearchParams();
  const uploads = useUploads();
  useEffect(() => () => searchController.current?.abort(), []);
  function clearSearch() {
    searchController.current?.abort();
    searchController.current = null;
    setSearchBusy(false);
    setResults(null);
  }
  async function searchText() {
    if (!query.trim()) return;
    searchController.current?.abort();
    const controller = new AbortController();
    searchController.current = controller;
    setSearchBusy(true);
    try {
      const result = await api<any[]>(
        `/files/search?q=${encodeURIComponent(query.trim())}`,
        { signal: controller.signal },
      );
      if (!controller.signal.aborted) setResults(result);
    } catch (error) {
      if (!controller.signal.aborted) toast((error as Error).message, true);
    } finally {
      if (searchController.current === controller) setSearchBusy(false);
    }
  }
  const completed = uploads.entries.filter(
    (entry) => entry.state === "completed",
  ).length;
  useEffect(() => {
    reload();
  }, [completed]);
  // 支持 /files?file=<id> 直达：Agent 交付物、聊天里的文件链接可以直接打开预览。
  useEffect(() => {
    const wanted = params.get("file");
    if (!wanted || !data) return;
    const target = data.find((file) => file.id === wanted);
    if (target && previewId.current !== target.id) void open(target);
    if (!target) toast("这份资料不存在，可能已被删除", true);
    setParams(
      (previous) => {
        const next = new URLSearchParams(previous);
        next.delete("file");
        return next;
      },
      { replace: true },
    );
  }, [data, params]);
  function receive(files: FileList | File[]) {
    const list = Array.from(files);
    if (uploads.add(list).length < list.length)
      toast("上传队列已满，请先清除已结束记录", true);
  }
  async function open(file: FileItem) {
    previewId.current = file.id;
    setPreview(file);
    setText("");
    setTextError("");
    setNextOffset(null);
    setTotalChars(0);
    setTextBusy(file.indexed);
    if (file.indexed) {
      try {
        const value = await api(`/files/${file.id}/text`);
        if (previewId.current !== file.id) return;
        setText(value.text);
        setNextOffset(value.next_offset);
        setTotalChars(value.total_chars);
      } catch (error) {
        if (previewId.current === file.id)
          setTextError((error as Error).message);
      } finally {
        if (previewId.current === file.id) setTextBusy(false);
      }
    }
  }
  if (error) return <ErrorState message={error} retry={reload} />;
  if (!data) return <Loading />;
  return (
    <div className="page-enter">
      <PageHeader
        overline="YOUR RESOURCE LIBRARY"
        title="私人资源库"
        description="从手机上传，交给 Xinxin 处理，再把结果带走。你的文件，随时接着用。"
        meta={
          <>
            <span>
              <strong>{data.length}</strong>份资料
            </span>
            <span>
              <strong>{data.filter((file) => file.indexed).length}</strong>
              份可检索
            </span>
          </>
        }
        action={
          <button
            className="button primary"
            onClick={() => picker.current?.click()}
          >
            <Plus size={17} />
            上传资源
          </button>
        }
      />
      <input
        ref={picker}
        type="file"
        multiple
        hidden
        onChange={(event) => {
          if (event.target.files) void receive(event.target.files);
          event.target.value = "";
        }}
      />
      <div
        className="file-drop"
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          void receive(event.dataTransfer.files);
        }}
      >
        <UploadCloud size={24} strokeWidth={1.3} />
        <div>
          <strong>把文件放在这里</strong>
          <p>支持文档、图片、表格、压缩包等原文件 · 单个最多 256 MB</p>
        </div>
        <button className="text-button" onClick={() => picker.current?.click()}>
          选择文件 <ArrowUpRight size={16} />
        </button>
      </div>
      <UploadQueue />
      <div className="toolbar">
        <label className="search-field wide">
          <Search size={17} />
          <input
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              clearSearch();
            }}
            placeholder="搜索文件名，或查找资料中的内容"
            aria-label="搜索私人资料"
          />
        </label>
        <button
          className="button secondary"
          disabled={!query.trim() || searchBusy}
          onClick={() => void searchText()}
        >
          {searchBusy ? "正在检索…" : "检索正文"} <ArrowUpRight size={15} />
        </button>
        <span className="muted small-text">{data.length} 份资料</span>
        <button className="text-button" onClick={reload}>
          刷新资源
        </button>
      </div>
      {results ? (
        <section className="search-results">
          {results.length ? (
            results.map((item, index) => (
              <article key={index} className="citation-result">
                <p className="eyebrow">SOURCE {index + 1}</p>
                <h3>{item.filename}</h3>
                <p>{item.text}</p>
                <button
                  className="text-button"
                  onClick={() => {
                    const file = data.find((file) => file.id === item.file_id);
                    if (file) void open(file);
                  }}
                >
                  回到来源 <ArrowUpRight size={15} />
                </button>
              </article>
            ))
          ) : (
            <Empty
              title="资料中暂未找到相关片段"
              description="试试更具体的关键词，或先上传对应资料。"
            />
          )}
        </section>
      ) : (
        <section className="list-panel">
          {data.filter((file) =>
            file.name.toLowerCase().includes(query.toLowerCase()),
          ).length ? (
            data
              .filter((file) =>
                file.name.toLowerCase().includes(query.toLowerCase()),
              )
              .map((file) => (
                <article className="library-file-row" key={file.id}>
                  <button className="file-open" onClick={() => void open(file)}>
                    <span className="file-type-icon">
                      {file.mime.startsWith("image/") ? (
                        <Image size={22} strokeWidth={1.3} />
                      ) : (
                        <FileText size={22} strokeWidth={1.3} />
                      )}
                    </span>
                    <div>
                      <strong>{file.name}</strong>
                      <small>
                        {size(file.size)} · {date(file.created)}
                      </small>
                    </div>
                  </button>
                  <span
                    className={`index-badge ${file.indexed ? "indexed" : ""}`}
                  >
                    {file.indexed ? "可检索" : "原文件"}
                  </span>
                  <button
                    className="icon-button"
                    aria-label={`下载 ${file.name}`}
                    onClick={() =>
                      void download(file).catch((error) =>
                        toast(error.message, true),
                      )
                    }
                  >
                    <Download size={17} />
                  </button>
                  <button
                    className="icon-button"
                    aria-label={`删除 ${file.name}`}
                    onClick={async () => {
                      if (
                        !window.confirm(
                          `删除「${file.name}」？引用它的内容将无法再读取原文件。`,
                        )
                      )
                        return;
                      try {
                        await remove(`/files/${file.id}`);
                        reload();
                      } catch (error) {
                        toast((error as Error).message, true);
                      }
                    }}
                  >
                    <Trash2 size={16} />
                  </button>
                </article>
              ))
          ) : (
            <Empty
              title={query ? "没有找到这份资料" : "留一份资料，开始建立上下文"}
              description={
                query
                  ? "试试其他文件名，或检索资料正文中的片段。"
                  : "上传后，Agent 可以检索其中的文字，并给出文件来源。"
              }
            />
          )}
        </section>
      )}
      {preview && (
        <Dialog
          title={preview.name}
          onClose={() => {
            previewId.current = "";
            setPreview(null);
          }}
          wide
        >
          {preview.mime.startsWith("image/") ? (
            <PrivateImage
              path={`/files/${preview.id}/download?inline=true`}
              alt={preview.name}
              className="document-image"
            />
          ) : textError ? (
            <ErrorState message={textError} retry={() => void open(preview)} />
          ) : text ? (
            <>
              <pre className="document-text">{text}</pre>
              {nextOffset != null && (
                <div className="gallery-more">
                  <button
                    className="button secondary"
                    disabled={textBusy}
                    onClick={async () => {
                      const id = preview.id;
                      setTextBusy(true);
                      try {
                        const result = await api(
                          `/files/${id}/text?offset=${nextOffset}`,
                        );
                        if (previewId.current !== id) return;
                        setText((value) => value + result.text);
                        setNextOffset(result.next_offset);
                      } catch (error) {
                        if (previewId.current === id)
                          toast((error as Error).message, true);
                      } finally {
                        if (previewId.current === id) setTextBusy(false);
                      }
                    }}
                  >
                    {textBusy ? "正在读取…" : "继续读取正文"}
                  </button>
                  <span>
                    {text.length.toLocaleString()} /{" "}
                    {totalChars.toLocaleString()} 字符
                  </span>
                </div>
              )}
            </>
          ) : textBusy ? (
            <Loading />
          ) : (
            <Empty
              title="原文件已妥善保存"
              description="这个格式暂不提供文字预览，可以下载查看。"
            />
          )}
          <div className="dialog-actions">
            <button
              className="button secondary"
              onClick={() =>
                void download(preview).catch((error) =>
                  toast(error.message, true),
                )
              }
            >
              <Download size={16} />
              下载文件
            </button>
            <button
              className="button primary"
              onClick={() =>
                navigate("/agent", {
                  state: {
                    files: [preview],
                    prompt: `帮我分析私人文件「${preview.name}」，文件 ID 是 ${preview.id}。请引用原文，先读取文件再回答。`,
                  },
                })
              }
            >
              和 Agent 一起阅读 <ArrowUpRight size={16} />
            </button>
          </div>
        </Dialog>
      )}
    </div>
  );
}
