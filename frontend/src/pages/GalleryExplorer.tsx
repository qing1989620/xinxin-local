import { useState } from "react";
import { useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import {
  ArrowUpRight,
  Search,
  Code2,
  Copy,
  Download,
  ChevronDown,
  Image,
} from "lucide-react";
import { api, saveBlob } from "../api";
import {
  Dialog,
  Empty,
  ErrorState,
  Loading,
  PrivateImage,
  useResource,
  useToast,
} from "../ui";

type Reference = {
  id: string;
  title: string;
  kind: string;
  purpose: string[];
  has_code: boolean;
  markdown?: string;
  code?: string;
  source?: string;
  license?: string;
};
export default function GalleryExplorer() {
  const { data, error, reload } = useResource<Reference[]>("/tools/gallery");
  const [query, setQuery] = useState(""),
    [kind, setKind] = useState("all"),
    [codeOnly, setCodeOnly] = useState(false),
    [limit, setLimit] = useState(12),
    [detail, setDetail] = useState<Reference | null>(null),
    [busy, setBusy] = useState(false);
  const toast = useToast(),
    navigate = useNavigate();
  if (error) return <ErrorState message={error} retry={reload} />;
  if (!data) return <Loading />;
  const visible = data.filter(
    (item) =>
      (!codeOnly || item.has_code) &&
      (kind === "all" || item.kind === kind) &&
      [item.title, item.kind, ...item.purpose]
        .join(" ")
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  async function open(item: Reference) {
    if (busy) return;
    setBusy(true);
    try {
      setDetail(await api(`/tools/gallery/${item.id}/reference`));
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      setBusy(false);
    }
  }
  function downloadCode() {
    if (!detail?.code) return;
    void saveBlob(
      new Blob([detail.code], { type: "text/x-python;charset=utf-8" }),
      `${detail.id}.py`,
    ).catch((error) => toast(error.message, true));
  }
  return (
    <section className="gallery-explorer" aria-label="绘图参考图库">
      <div className="section-heading">
        <div>
          <p className="eyebrow">A WELL-COMPOSED VIEW</p>
          <h2>让数据，有自己的表达。</h2>
          <p>
            {data.length} 个绘图参考。先选结构，再让 Agent 结合自己的数据实现。
          </p>
        </div>
      </div>
      <div className="gallery-toolbar">
        <label className="search-field">
          <Search size={16} />
          <input
            value={query}
            aria-label="搜索绘图参考"
            placeholder="搜索图表、用途、结构"
            onChange={(e) => {
              setQuery(e.target.value);
              setLimit(12);
            }}
          />
        </label>
        <select
          value={kind}
          aria-label="图表结构筛选"
          onChange={(e) => {
            setKind(e.target.value);
            setLimit(12);
          }}
        >
          <option value="all">全部结构</option>
          {[...new Set(data.map((item) => item.kind))]
            .filter(Boolean)
            .map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
        </select>
        <label className="gallery-code-filter">
          <input
            type="checkbox"
            checked={codeOnly}
            onChange={(e) => {
              setCodeOnly(e.target.checked);
              setLimit(12);
            }}
          />
          附参考代码
        </label>
        <span className="gallery-count">
          {visible.length} 个参考 {busy ? " · 正在读取…" : ""}
        </span>
      </div>
      <div className="reference-gallery">
        {visible.slice(0, limit).map((item) => (
          <button
            className="reference-card"
            key={item.id}
            onClick={() => void open(item)}
            aria-label={`查看绘图参考 ${item.title}`}
          >
            <PrivateImage
              path={`/tools/gallery/${item.id}`}
              alt={item.title}
              loading="lazy"
              retryable={false}
            />
            <div>
              <h3>{item.title}</h3>
              <p>{item.purpose.join(" · ") || item.kind}</p>
              <footer>
                <span>
                  {item.has_code ? <Code2 size={12} /> : <Image size={12} />}
                  {item.has_code ? "含 Python 参考" : "结构参考"}
                </span>
                <ArrowUpRight size={14} />
              </footer>
            </div>
          </button>
        ))}
      </div>
      {!visible.length && (
        <Empty
          title="换个关键词，再找找"
          description="可以按结构筛选，或关闭代码筛选查看全部参考。"
        />
      )}
      {visible.length > limit && (
        <div className="gallery-more">
          <button
            className="button secondary"
            onClick={() => setLimit((value) => value + 12)}
          >
            再看 12 个 <ChevronDown size={15} />
          </button>
          <span>
            已展示 {Math.min(limit, visible.length)} / {visible.length}
          </span>
        </div>
      )}
      {detail && (
        <Dialog title={detail.title} onClose={() => setDetail(null)} wide>
          <PrivateImage
            path={`/tools/gallery/${detail.id}`}
            alt={detail.title}
            className="gallery-detail-image"
          />
          <p className="gallery-provenance">
            来源：{detail.source} · {detail.license}
            。这是结构与风格参考；真实图表将使用你的数据重新生成。
          </p>
          <div className="markdown">
            <ReactMarkdown skipHtml>
              {(detail.markdown || "").replace(
                /^---\r?\n[\s\S]*?\r?\n---\r?\n/,
                "",
              )}
            </ReactMarkdown>
          </div>
          {detail.code && (
            <details>
              <summary>查看 Python 参考代码</summary>
              <div className="code-controls">
                <h3>参考代码</h3>
                <button
                  className="text-button"
                  onClick={() => {
                    void navigator.clipboard
                      .writeText(detail.code!)
                      .then(() => toast("代码已复制"))
                      .catch(() => toast("复制不可用，请下载代码", true));
                  }}
                >
                  <Copy size={14} />
                  复制
                </button>
                <button className="text-button" onClick={downloadCode}>
                  <Download size={14} />
                  下载
                </button>
              </div>
              <pre className="reference-code">{detail.code}</pre>
            </details>
          )}
          <div className="dialog-actions">
            <button
              className="button primary"
              onClick={() =>
                navigate("/agent", {
                  state: {
                    prompt: `请加载出版绘图技能，读取绘图参考 ${detail.id} 的说明${detail.has_code ? "和代码" : ""}，按这个结构帮我绘图。先让我选择私人数据文件，再生成真实图表及可复现代码。`,
                  },
                })
              }
            >
              按这个结构开始 <ArrowUpRight size={16} />
            </button>
          </div>
        </Dialog>
      )}
    </section>
  );
}
