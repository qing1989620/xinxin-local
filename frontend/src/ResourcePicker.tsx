import { useEffect, useRef, useState } from "react";
import { FileUp, Search } from "lucide-react";
import { type FileItem } from "./api";
import {
  Dialog,
  Empty,
  ErrorState,
  Loading,
  size,
  useResource,
  useToast,
} from "./ui";
import { UploadQueue, useUploads } from "./Uploads";

export default function ResourcePicker({
  existing,
  onAttach,
  onClose,
}: {
  existing: FileItem[];
  onAttach: (files: FileItem[]) => void;
  onClose: () => void;
}) {
  const { data, error, reload } = useResource<FileItem[]>("/files");
  const { entries, add } = useUploads();
  const [query, setQuery] = useState(""),
    [selected, setSelected] = useState(new Set<string>()),
    [owned, setOwned] = useState<string[]>([]);
  const picker = useRef<HTMLInputElement>(null),
    processed = useRef(new Set<string>()),
    toast = useToast();
  const uploaded = entries.filter(
    (entry) => owned.includes(entry.id) && entry.state === "completed",
  );
  const finished = uploaded.length;
  const pending = entries.some(
    (entry) =>
      owned.includes(entry.id) && ["queued", "uploading"].includes(entry.state),
  );
  const available = new Map((data || []).map((file) => [file.id, file]));
  uploaded.forEach((entry) => {
    if (entry.result) available.set(entry.result.id, entry.result);
  });
  const existingIds = new Set(existing.map((file) => file.id));
  useEffect(() => {
    const completed = uploaded.filter(
      (entry) => !processed.current.has(entry.id),
    );
    if (!completed.length) return;
    completed.forEach((entry) => processed.current.add(entry.id));
    setSelected(
      (old) =>
        new Set(
          [...old, ...completed.map((entry) => entry.result!.id)].slice(
            0,
            10 - existing.length,
          ),
        ),
    );
    reload();
  }, [finished]);
  const receive = (files: File[]) => {
    const ids = add(files);
    setOwned((old) => [...old, ...ids]);
    if (ids.length < files.length)
      toast("上传队列已满，请先清除已结束记录", true);
  };
  return (
    <Dialog title="给 Xinxin 添加资源" onClose={onClose} wide>
      <div
        className="resource-picker-upload"
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          receive(Array.from(event.dataTransfer.files));
        }}
      >
        <div>
          <strong>从手机或电脑上传</strong>
          <p>
            照片、文档、表格、压缩包都可保存，单个最多 256
            MB。上传后留在资源库，后续对话也能使用。
          </p>
        </div>
        <button
          className="button secondary"
          onClick={() => picker.current?.click()}
        >
          <FileUp size={17} />
          上传新资源
        </button>
      </div>
      <input
        ref={picker}
        type="file"
        multiple
        hidden
        onChange={(event) => {
          receive(Array.from(event.target.files || []));
          event.target.value = "";
        }}
      />
      <UploadQueue ids={owned} />
      <label className="search-field wide">
        <Search size={16} />
        <input
          aria-label="搜索可用资源"
          placeholder="从资源库选择，不必重复上传"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </label>
      {error ? (
        <ErrorState message={error} retry={reload} />
      ) : !data ? (
        <Loading />
      ) : (
        <div className="resource-picker-list">
          {[...available.values()]
            .filter((file) =>
              file.name.toLowerCase().includes(query.toLowerCase()),
            )
            .map((file) => (
              <label className="resource-picker-row" key={file.id}>
                <input
                  type="checkbox"
                  aria-label={`选择资源 ${file.name}`}
                  checked={selected.has(file.id) || existingIds.has(file.id)}
                  disabled={
                    existingIds.has(file.id) ||
                    (!selected.has(file.id) &&
                      selected.size + existing.length >= 10)
                  }
                  onChange={(event) =>
                    setSelected((old) => {
                      const next = new Set(old);
                      if (event.target.checked) next.add(file.id);
                      else next.delete(file.id);
                      return next;
                    })
                  }
                />
                <span>
                  <strong>{file.name}</strong>
                  <small>
                    {size(file.size)} ·{" "}
                    {existingIds.has(file.id)
                      ? "已在本轮附件中"
                      : file.indexed
                        ? "可读取正文"
                        : "原文件"}
                  </small>
                </span>
              </label>
            ))}
          {!available.size && (
            <Empty
              title="资源库还是空的"
              description="先上传一些文件，Xinxin 就能接着帮你处理。"
            />
          )}
          {available.size > 0 &&
            ![...available.values()].some((file) =>
              file.name.toLowerCase().includes(query.toLowerCase()),
            ) && (
              <Empty title="没有找到这个文件" description="换个文件名试试。" />
            )}
        </div>
      )}
      <div className="dialog-actions">
        <span className="muted small-text">
          本轮 {existing.length + selected.size} / 10 个附件
        </span>
        <button
          className="button primary"
          disabled={!selected.size || pending}
          onClick={() => {
            onAttach(
              [...selected]
                .map((id) => available.get(id))
                .filter((file): file is FileItem => Boolean(file)),
            );
            onClose();
          }}
        >
          加入本轮对话
        </button>
      </div>
      <p className="upload-note">
        仅选择的资源加入本轮；上传本身不会启动
        Agent。关闭此窗口后上传继续，可稍后从资源库选择。
      </p>
    </Dialog>
  );
}
