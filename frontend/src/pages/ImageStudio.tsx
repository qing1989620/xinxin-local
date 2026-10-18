import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowUpRight,
  Download,
  ImagePlus,
  Loader2,
  X,
} from "lucide-react";
import { api, getBlob, saveBlob } from "../api";
import { useToast } from "../ui";

type ImageResult = {
  id?: string;
  file_id?: string;
  name: string;
  mime?: string;
  size?: number;
  bytes?: number;
  image?: {
    prompt: string;
    provider: string;
    model: string;
    width: number;
    height: number;
    seed?: number | null;
    note?: string;
  };
};
type RecentImage = {
  file_id: string;
  name: string;
  mime: string;
  bytes: number;
  created: number;
};
type ProviderInfo = {
  default: string;
  pollinations: { available: boolean; label: string; model: string };
  openrouter: { available: boolean; label: string; model: string; reason?: string };
};

const SIZES: { key: string; label: string; width: number; height: number }[] = [
  { key: "square", label: "方形 1024", width: 1024, height: 1024 },
  { key: "portrait", label: "竖版 768×1344", width: 768, height: 1344 },
  { key: "landscape", label: "横版 1344×768", width: 1344, height: 768 },
];

/** 通过带鉴权的下载接口取图片字节，转成可本地渲染的对象 URL。 */
function ImageThumb({
  fileId,
  alt,
  className,
}: {
  fileId: string;
  alt: string;
  className?: string;
}) {
  const [source, setSource] = useState("");
  useEffect(() => {
    let url = "";
    let alive = true;
    getBlob(`/files/${fileId}/download`)
      .then((blob) => {
        if (!alive) return;
        url = URL.createObjectURL(blob);
        setSource(url);
      })
      .catch(() => {
        if (alive) setSource("");
      });
    return () => {
      alive = false;
      if (url) URL.revokeObjectURL(url);
    };
  }, [fileId]);
  if (!source)
    return <span className={`image-thumb loading ${className || ""}`}>…</span>;
  return <img className={`image-thumb ${className || ""}`} src={source} alt={alt} />;
}

export default function ImageStudio({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [prompt, setPrompt] = useState(""),
    [sizeKey, setSizeKey] = useState("square"),
    [provider, setProvider] = useState(""),
    [busy, setBusy] = useState(false),
    [providers, setProviders] = useState<ProviderInfo | null>(null),
    [recent, setRecent] = useState<RecentImage[]>([]),
    [latest, setLatest] = useState<ImageResult | null>(null),
    panel = useRef<HTMLDivElement>(null),
    navigate = useNavigate(),
    toast = useToast();
  const refreshRecent = useCallback(async () => {
    try {
      setRecent(await api<RecentImage[]>("/images?limit=8"));
    } catch {
      /* 最近列表是附属信息，失败不影响主流程 */
    }
  }, []);
  useEffect(() => {
    if (!open) return;
    let alive = true;
    api<ProviderInfo>("/images/providers")
      .then((value) => {
        if (!alive) return;
        setProviders(value);
        setProvider(value.default || "pollinations");
      })
      .catch(() => {
        if (alive) setProviders(null);
      });
    void refreshRecent();
    return () => {
      alive = false;
    };
  }, [open, refreshRecent]);
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);
  if (!open) return null;
  const size = SIZES.find((item) => item.key === sizeKey) || SIZES[0];
  async function generate() {
    if (!prompt.trim() || busy) return;
    setBusy(true);
    try {
      const result = await api<ImageResult>("/images", {
        method: "POST",
        body: JSON.stringify({
          prompt: prompt.trim(),
          width: size.width,
          height: size.height,
          provider: provider || undefined,
        }),
      });
      setLatest(result);
      setPrompt("");
      void refreshRecent();
      toast("图画好了，已存进文件库");
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      setBusy(false);
    }
  }
  const latestId = latest?.id || latest?.file_id;
  return (
    <div className="image-studio" ref={panel} role="dialog" aria-label="生图工作台">
      <header>
        <ImagePlus size={15} />
        <strong>画一张图</strong>
        <span>
          {providers
            ? providers[provider as "pollinations"]?.label ||
              providers.pollinations.label
            : "读取档位…"}
        </span>
        <button className="icon-button" aria-label="收起生图面板" onClick={onClose}>
          <X size={14} />
        </button>
      </header>
      <textarea
        rows={2}
        maxLength={2000}
        value={prompt}
        onChange={(event) => setPrompt(event.target.value)}
        placeholder="描述你想要的画面，比如：夜色中的城市天台，霓虹灯，一只白猫"
        aria-label="生图描述"
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            void generate();
          }
        }}
      />
      <div className="image-studio-row">
        <div className="image-studio-sizes" aria-label="尺寸">
          {SIZES.map((item) => (
            <button
              key={item.key}
              aria-pressed={sizeKey === item.key}
              className={sizeKey === item.key ? "selected" : ""}
              onClick={() => setSizeKey(item.key)}
            >
              {item.label}
            </button>
          ))}
        </div>
        {providers && providers.openrouter.available && (
          <select
            aria-label="生图档位"
            value={provider}
            onChange={(event) => setProvider(event.target.value)}
          >
            <option value="pollinations">{providers.pollinations.label}</option>
            <option value="openrouter">{providers.openrouter.label}</option>
          </select>
        )}
        <button
          className="button primary"
          disabled={busy || !prompt.trim()}
          onClick={() => void generate()}
        >
          {busy ? <Loader2 size={15} className="spin" /> : <ImagePlus size={15} />}
          {busy ? "生成中…" : "生成"}
        </button>
      </div>
      {latest && latestId && (
        <div className="image-studio-result">
          <ImageThumb fileId={latestId} alt={latest.image?.prompt || latest.name} />
          <div>
            <strong>{latest.name}</strong>
            <small>
              {latest.image
                ? `${latest.image.provider} · ${latest.image.model} · ${latest.image.width}×${latest.image.height}`
                : latest.mime}
              {latest.image?.note ? ` · ${latest.image.note}` : ""}
            </small>
            <div className="image-studio-actions">
              <button
                className="text-button"
                onClick={() => {
                  void (async () => {
                    try {
                      const blob = await getBlob(`/files/${latestId}/download`);
                      await saveBlob(blob, latest.name, latestId);
                    } catch {
                      toast("保存失败，请从文件库下载", true);
                    }
                  })();
                }}
              >
                <Download size={13} />
                保存到本地
              </button>
              <button
                className="text-button"
                onClick={() => {
                  onClose();
                  navigate("/files");
                }}
              >
                去文件库看看
                <ArrowUpRight size={13} />
              </button>
            </div>
          </div>
        </div>
      )}
      {recent.length > 0 && (
        <div className="image-studio-recent" aria-label="最近生成的图">
          {recent.map((item) => (
            <ImageThumb key={item.file_id} fileId={item.file_id} alt={item.name} />
          ))}
        </div>
      )}
    </div>
  );
}
