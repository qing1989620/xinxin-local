import { useEffect, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import {
  ArrowUpRight,
  BookOpen,
  Camera,
  ChevronRight,
  Download,
  FileText,
  ImagePlus,
  Plus,
  Quote,
  Trash2,
  X,
} from "lucide-react";
import {
  api,
  post,
  put,
  remove,
  upload,
  download,
  type RecordItem,
  type FileItem,
} from "../api";
import {
  Dialog,
  Empty,
  ErrorState,
  Loading,
  PageHeader,
  PrivateImage,
  date,
  useResource,
  useToast,
} from "../ui";
import RichEditor from "../editor";

const kinds = [
  ["article", "文章"],
  ["collection", "合集"],
  ["photo", "相册"],
  ["poem", "诗词"],
  ["resume", "简历"],
];
export default function ContentPage() {
  const [params, setParams] = useSearchParams(),
    kind = kinds.some(([id]) => id === params.get("kind"))
      ? params.get("kind")!
      : "article";
  const { data, error, reload } = useResource<RecordItem[]>(
      `/records?kind=${kind}`,
    ),
    collections = useResource<RecordItem[]>("/records?kind=collection"),
    [edit, setEdit] = useState<
      | RecordItem
      | { id?: string; kind: string; payload: Record<string, any> }
      | null
    >(null),
    [preview, setPreview] = useState<RecordItem | null>(null),
    [form, setForm] = useState<Record<string, any>>({}),
    [dirty, setDirty] = useState(false),
    [busy, setBusy] = useState(false),
    [query, setQuery] = useState(""),
    toast = useToast();
  useEffect(() => {
    setPreview(null);
    setQuery("");
  }, [kind]);
  useEffect(() => {
    if (!dirty) return;
    const handler = (event: BeforeUnloadEvent) => {
      event.preventDefault();
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [dirty]);
  function change(key: string, value: any) {
    setForm((old) => ({ ...old, [key]: value }));
    setDirty(true);
  }
  function begin(record?: RecordItem) {
    const value = record || {
      kind,
      payload:
        kind === "resume"
          ? {
              name: "",
              title: "",
              skills: [],
              experiences: [],
              education: [],
              certificates: [],
            }
          : kind === "article"
            ? {
                title: "",
                content: "",
                summary: "",
                published: false,
                collection_id: "",
              }
            : { title: "", content: "", description: "" },
    };
    setEdit(value);
    setForm({ ...value.payload });
    setDirty(false);
  }
  function close() {
    if (dirty && !confirm("有尚未保存的修改，确认关闭？")) return;
    setEdit(null);
    setDirty(false);
  }
  async function save(event: FormEvent) {
    event.preventDefault();
    if (!edit) return;
    setBusy(true);
    try {
      const payload = { ...form };
      await (edit.id
        ? put(`/records/${edit.id}`, { kind: edit.kind, payload })
        : post("/records", { kind: edit.kind, payload }));
      setEdit(null);
      setDirty(false);
      reload();
      collections.reload();
      toast("已保存到私人内容");
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      setBusy(false);
    }
  }
  async function destroy(record: RecordItem) {
    if (!confirm("删除这项内容？上传的原文件会保留在私人资料中。")) return;
    try {
      await remove(`/records/${record.id}`);
      reload();
      setPreview(null);
    } catch (error) {
      toast((error as Error).message, true);
    }
  }
  async function image(file: File, key = "file_id") {
    try {
      const result = await upload(file);
      change(key, result.id);
    } catch (error) {
      toast((error as Error).message, true);
    }
  }
  if (error) return <ErrorState message={error} retry={reload} />;
  if (!data) return <Loading />;
  const visible = data.filter((item) =>
    JSON.stringify(item.payload).toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <div className="page-enter">
      <PageHeader
        overline="THE PERSONAL SIDE"
        title="记录，属于自己的片段。"
        description="文章、相册、诗词与经历，都在自己的私人空间里妥善安放。"
        action={
          <button className="button primary" onClick={() => begin()}>
            <Plus size={17} />
            新建{kinds.find(([id]) => id === kind)?.[1]}
          </button>
        }
      />
      <div className="toolbar">
        <div className="segmented content-tabs">
          {kinds.map(([value, label]) => (
            <button
              key={value}
              className={kind === value ? "selected" : ""}
              onClick={() => setParams({ kind: value })}
            >
              {label}
            </button>
          ))}
        </div>
        <input
          className="content-search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="寻找一段记录"
          aria-label="搜索个人内容"
        />
      </div>
      {kind === "resume" ? (
        <>
          {data.length ? (
            data.map((record) => (
              <div key={record.id} className="resume-wrapper">
                <div className="resume-actions">
                  <button
                    className="button secondary"
                    onClick={() => begin(record)}
                  >
                    编辑简历 <ArrowUpRight size={15} />
                  </button>
                  <button
                    className="button secondary"
                    onClick={() => window.print()}
                  >
                    <Download size={15} />
                    打印 / PDF
                  </button>
                  {record.payload.pdf_file_id && (
                    <button
                      className="button secondary"
                      onClick={async () => {
                        try {
                          await download(
                            await api<FileItem>(
                              `/files/${record.payload.pdf_file_id}/metadata`,
                            ),
                          );
                        } catch (error) {
                          toast((error as Error).message, true);
                        }
                      }}
                    >
                      原版 PDF <Download size={15} />
                    </button>
                  )}
                </div>
                <ResumeDocument payload={record.payload} />
              </div>
            ))
          ) : (
            <Empty
              title="让你的经历，清晰地被看见"
              description="添加基本资料、专业技能、教育与项目经历。支持打印或保存为 PDF。"
              action={
                <button className="button secondary" onClick={() => begin()}>
                  开始整理简历 <ArrowUpRight size={16} />
                </button>
              }
            />
          )}
        </>
      ) : visible.length ? (
        <div className={`content-grid ${kind === "photo" ? "photo-grid" : ""}`}>
          {visible.map((record) => (
            <article key={record.id} className={`content-card ${kind}`}>
              <button
                className="content-card-open"
                onClick={() => setPreview(record)}
              >
                {(record.payload.file_id || record.payload.cover_file_id) && (
                  <PrivateImage
                    path={`/files/${record.payload.file_id || record.payload.cover_file_id}/download?inline=true`}
                    alt={record.payload.title || "个人照片"}
                    retryable={false}
                  />
                )}
                <div className="content-card-copy">
                  <span className="eyebrow">
                    {kind === "article"
                      ? record.payload.published
                        ? "已发布 · 私人"
                        : "草稿"
                      : kind === "poem"
                        ? record.payload.author || "拾章"
                        : record.payload.category ||
                          kinds.find(([id]) => id === kind)?.[1]}
                  </span>
                  {kind === "poem" ? (
                    <p className="poem-excerpt">{record.payload.content}</p>
                  ) : (
                    <>
                      <h2>{record.payload.title || record.payload.name}</h2>
                      <p>
                        {record.payload.summary ||
                          record.payload.description ||
                          "留下一段自己的记录。"}
                      </p>
                    </>
                  )}
                  <small>{date(record.updated)}</small>
                </div>
              </button>
              <div className="content-card-actions">
                <button className="text-button" onClick={() => begin(record)}>
                  编辑 <ArrowUpRight size={14} />
                </button>
                <button
                  className="icon-button"
                  aria-label="删除这项内容"
                  onClick={() => void destroy(record)}
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <Empty
          title={
            query
              ? "还没有找到这段记录"
              : {
                  article: "留下一篇属于自己的文章",
                  collection: "把相关的记录归到一起",
                  photo: "留住一帧值得记住的日常",
                  poem: "拾起偶然打动你的句子",
                }[kind] || "从一条记录开始"
          }
          description="这里保留个人内容的完整位置，内容由你自己决定。"
          action={
            <button className="button secondary" onClick={() => begin()}>
              <Plus size={15} />
              添加第一条记录
            </button>
          }
        />
      )}
      <div className="content-footnote">
        <LockKeyholeIcon />
        所有内容当前均为私人可见，发布状态用于整理，不会公开你的空间。
      </div>
      {edit && (
        <Dialog
          title={`${edit.id ? "编辑" : "新建"}${kinds.find(([id]) => id === edit.kind)?.[1]}`}
          onClose={close}
          wide={["article", "resume"].includes(edit.kind)}
        >
          <form onSubmit={save} className="form-stack">
            {edit.kind === "resume" ? (
              <ResumeForm form={form} change={change} />
            ) : edit.kind === "poem" ? (
              <>
                <label>
                  内容
                  <textarea
                    rows={8}
                    value={form.content || ""}
                    onChange={(e) => change("content", e.target.value)}
                    required
                  />
                </label>
                <div className="form-columns">
                  <label>
                    作者
                    <input
                      value={form.author || ""}
                      onChange={(e) => change("author", e.target.value)}
                    />
                  </label>
                  <label>
                    出处
                    <input
                      value={form.source || ""}
                      onChange={(e) => change("source", e.target.value)}
                    />
                  </label>
                </div>
              </>
            ) : (
              <>
                <label>
                  标题
                  <input
                    value={form.title || form.name || ""}
                    onChange={(e) => change("title", e.target.value)}
                    required
                    maxLength={200}
                  />
                </label>
                {edit.kind === "article" ? (
                  <>
                    <div className="form-columns">
                      <label>
                        合集
                        <select
                          value={form.collection_id || ""}
                          onChange={(e) =>
                            change("collection_id", e.target.value)
                          }
                        >
                          <option value="">未归入合集</option>
                          {collections.data?.map((collection) => (
                            <option key={collection.id} value={collection.id}>
                              {collection.payload.title ||
                                collection.payload.name}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label>
                        状态
                        <select
                          value={form.published ? "published" : "draft"}
                          onChange={(e) =>
                            change("published", e.target.value === "published")
                          }
                        >
                          <option value="draft">草稿</option>
                          <option value="published">已发布 · 私人</option>
                        </select>
                      </label>
                    </div>
                    <label>
                      摘要
                      <textarea
                        rows={2}
                        value={form.summary || ""}
                        onChange={(e) => change("summary", e.target.value)}
                        maxLength={2000}
                      />
                    </label>
                    <div className="editor-field">
                      <span className="field-label">正文</span>
                      <RichEditor
                        key={edit.id || "new"}
                        value={form.content || ""}
                        onChange={(value) => change("content", value)}
                      />
                    </div>
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={Boolean(form.pinned)}
                        onChange={(e) => change("pinned", e.target.checked)}
                      />
                      置顶这篇文章
                    </label>
                  </>
                ) : (
                  <>
                    <label>
                      描述
                      <textarea
                        rows={3}
                        value={form.description || ""}
                        onChange={(e) => change("description", e.target.value)}
                      />
                    </label>
                    {edit.kind === "photo" && (
                      <label>
                        分类
                        <input
                          value={form.category || ""}
                          onChange={(e) => change("category", e.target.value)}
                          placeholder="例如：日常、旅行、项目"
                        />
                      </label>
                    )}
                    <label>
                      图片
                      <input
                        type="file"
                        accept="image/png,image/jpeg,image/webp"
                        onChange={(e) => {
                          if (e.target.files?.[0])
                            void image(e.target.files[0]);
                        }}
                      />
                    </label>
                    {form.file_id && (
                      <PrivateImage
                        path={`/files/${form.file_id}/download?inline=true`}
                        alt="所选图片"
                        className="form-image-preview"
                      />
                    )}
                  </>
                )}
              </>
            )}
            <div className="dialog-actions">
              <button
                type="button"
                className="button secondary"
                onClick={close}
              >
                取消
              </button>
              <button className="button primary" disabled={busy}>
                {busy ? "正在保存…" : "保存记录"}
                <ArrowUpRight size={16} />
              </button>
            </div>
          </form>
        </Dialog>
      )}
      {preview && (
        <Dialog
          title={preview.payload.title || preview.payload.author || "私人记录"}
          onClose={() => setPreview(null)}
          wide
        >
          {(preview.payload.file_id || preview.payload.cover_file_id) && (
            <PrivateImage
              path={`/files/${preview.payload.file_id || preview.payload.cover_file_id}/download?inline=true`}
              alt={preview.payload.title || "图片"}
              className="document-image"
            />
          )}
          {preview.kind === "article" ? (
            <RichEditor
              key={preview.id}
              value={preview.payload.content || ""}
              readOnly
            />
          ) : preview.kind === "poem" ? (
            <div className="poem-document">
              <p>{preview.payload.content}</p>
              <small>
                {preview.payload.author} {preview.payload.source}
              </small>
            </div>
          ) : (
            <p className="lead">{preview.payload.description}</p>
          )}
          {preview.kind === "collection" && (
            <CollectionArticles ident={preview.id} />
          )}
          <div className="dialog-actions">
            <button
              className="button secondary"
              onClick={() => {
                begin(preview);
                setPreview(null);
              }}
            >
              编辑记录 <ArrowUpRight size={15} />
            </button>
          </div>
        </Dialog>
      )}
    </div>
  );
}

function LockKeyholeIcon() {
  return <span aria-hidden="true">◇</span>;
}
function CollectionArticles({ ident }: { ident: string }) {
  const { data } = useResource<RecordItem[]>("/records?kind=article");
  return (
    <div className="collection-articles">
      <h3>合集中的文章</h3>
      {data
        ?.filter((item) => item.payload.collection_id === ident)
        .map((item) => (
          <details key={item.id}>
            <summary>{item.payload.title}</summary>
            <RichEditor value={item.payload.content || ""} readOnly />
          </details>
        ))}
    </div>
  );
}
function ResumeForm({
  form,
  change,
}: {
  form: Record<string, any>;
  change: (key: string, value: any) => void;
}) {
  const toast = useToast();
  const fields = [
    ["name", "姓名"],
    ["title", "职位 / 方向"],
    ["email", "邮箱"],
    ["phone", "电话"],
    ["location", "所在地"],
    ["jobTarget", "求职意向"],
  ];
  return (
    <>
      <div className="form-columns">
        {fields.map(([key, label]) => (
          <label key={key}>
            {label}
            <input
              value={form[key] || ""}
              onChange={(e) => change(key, e.target.value)}
              required={key === "name"}
            />
          </label>
        ))}
      </div>
      <label className="upload-inline">
        简历头像
        <input
          type="file"
          accept="image/png,image/jpeg,image/webp"
          onChange={async (e) => {
            const file = e.target.files?.[0];
            if (file)
              try {
                const saved = await upload(file);
                change("avatar_file_id", saved.id);
              } catch (error) {
                toast((error as Error).message, true);
              }
          }}
        />
      </label>
      <label>
        个人介绍
        <textarea
          rows={3}
          value={form.bio || form.selfEvaluation || ""}
          onChange={(e) => change("bio", e.target.value)}
        />
      </label>
      <details className="advanced-settings">
        <summary>
          其他基本资料 <ChevronRight size={16} />
        </summary>
        <div className="form-columns">
          {[
            ["birthDate", "出生日期"],
            ["birthplace", "籍贯"],
            ["degree", "学历"],
            ["political", "政治面貌"],
            ["hobbies", "兴趣爱好"],
          ].map(([key, label]) => (
            <label key={key}>
              {label}
              <input
                value={form[key] || ""}
                onChange={(e) => change(key, e.target.value)}
              />
            </label>
          ))}
        </div>
      </details>
      {[
        ["skills", "专业技能"],
        ["education", "教育经历"],
        ["experiences", "项目与实践经历"],
        ["certificates", "证书与奖项"],
      ].map(([key, label]) => (
        <section className="resume-form-section" key={key}>
          <div className="section-heading">
            <h3>{label}</h3>
            <button
              type="button"
              className="text-button"
              onClick={() =>
                change(key, [
                  ...(form[key] || []),
                  { title: "", name: "", description: "" },
                ])
              }
            >
              <Plus size={15} />
              添加
            </button>
          </div>
          {(form[key] || []).map((item: any, index: number) => (
            <div className="resume-entry" key={index}>
              <div className="form-columns">
                <label>
                  {key === "skills" ? "技能名称" : "名称"}
                  <input
                    value={item.title || item.name || ""}
                    onChange={(e) =>
                      change(
                        key,
                        form[key].map((entry: any, i: number) =>
                          i === index
                            ? {
                                ...entry,
                                title: e.target.value,
                                name: e.target.value,
                              }
                            : entry,
                        ),
                      )
                    }
                  />
                </label>
                {key === "skills" ? (
                  <label>
                    熟练度
                    <input
                      type="number"
                      min={0}
                      max={100}
                      value={item.level || 0}
                      onChange={(e) =>
                        change(
                          key,
                          form[key].map((entry: any, i: number) =>
                            i === index
                              ? { ...entry, level: Number(e.target.value) }
                              : entry,
                          ),
                        )
                      }
                    />
                  </label>
                ) : (
                  <label>
                    角色 / 学校 / 机构
                    <input
                      value={item.subtitle || ""}
                      onChange={(e) =>
                        change(
                          key,
                          form[key].map((entry: any, i: number) =>
                            i === index
                              ? { ...entry, subtitle: e.target.value }
                              : entry,
                          ),
                        )
                      }
                    />
                  </label>
                )}
              </div>
              {key !== "skills" && (
                <>
                  <div className="form-columns">
                    <label>
                      开始时间
                      <input
                        value={item.startDate || ""}
                        onChange={(e) =>
                          change(
                            key,
                            form[key].map((entry: any, i: number) =>
                              i === index
                                ? { ...entry, startDate: e.target.value }
                                : entry,
                            ),
                          )
                        }
                      />
                    </label>
                    <label>
                      结束时间
                      <input
                        value={item.endDate || ""}
                        onChange={(e) =>
                          change(
                            key,
                            form[key].map((entry: any, i: number) =>
                              i === index
                                ? { ...entry, endDate: e.target.value }
                                : entry,
                            ),
                          )
                        }
                      />
                    </label>
                  </div>
                  <label>
                    说明
                    <textarea
                      rows={3}
                      value={item.description || ""}
                      onChange={(e) =>
                        change(
                          key,
                          form[key].map((entry: any, i: number) =>
                            i === index
                              ? { ...entry, description: e.target.value }
                              : entry,
                          ),
                        )
                      }
                    />
                  </label>
                  <label className="upload-inline">
                    证明材料配图
                    <input
                      type="file"
                      accept="image/png,image/jpeg,image/webp"
                      onChange={async (e) => {
                        const file = e.target.files?.[0];
                        if (file)
                          try {
                            const saved = await upload(file);
                            change(
                              key,
                              form[key].map((entry: any, i: number) =>
                                i === index
                                  ? { ...entry, image_file_id: saved.id }
                                  : entry,
                              ),
                            );
                          } catch (error) {
                            toast((error as Error).message, true);
                          }
                      }}
                    />
                  </label>
                  {item.image_file_id && (
                    <div>
                      <PrivateImage
                        path={`/files/${item.image_file_id}/download?inline=true`}
                        alt="证明材料预览"
                      />
                      <button
                        type="button"
                        className="text-button"
                        onClick={() =>
                          change(
                            key,
                            form[key].map((entry: any, i: number) =>
                              i === index
                                ? { ...entry, image_file_id: null }
                                : entry,
                            ),
                          )
                        }
                      >
                        移除此配图
                      </button>
                    </div>
                  )}
                </>
              )}
              <button
                type="button"
                className="text-button danger"
                onClick={() =>
                  change(
                    key,
                    form[key].filter((_: any, i: number) => i !== index),
                  )
                }
              >
                <Trash2 size={14} />
                移除此项
              </button>
            </div>
          ))}
        </section>
      ))}
    </>
  );
}
function ResumeDocument({ payload: p }: { payload: Record<string, any> }) {
  return (
    <article className="resume-document">
      <header>
        {p.avatar_file_id && (
          <PrivateImage
            className="resume-avatar"
            path={`/files/${p.avatar_file_id}/download?inline=true`}
            alt="简历头像"
          />
        )}
        <p className="eyebrow">CURRICULUM VITAE</p>
        <h1>{p.name || "我的简历"}</h1>
        <h2>{p.title}</h2>
        <p>{[p.email, p.phone, p.location].filter(Boolean).join(" · ")}</p>
      </header>
      {(p.bio || p.selfEvaluation) && (
        <section>
          <h3>关于我</h3>
          <p>{p.bio || p.selfEvaluation}</p>
        </section>
      )}
      {p.jobTarget && (
        <section>
          <h3>求职意向</h3>
          <p>{p.jobTarget}</p>
        </section>
      )}
      {p.skills?.length > 0 && (
        <section>
          <h3>专业技能</h3>
          <div className="resume-skills">
            {p.skills.map((skill: any, index: number) => (
              <span key={index}>{skill.name || skill.title}</span>
            ))}
          </div>
        </section>
      )}
      {[
        ["education", "教育经历"],
        ["experiences", "项目与实践经历"],
        ["certificates", "证书与奖项"],
      ].map(
        ([key, label]) =>
          p[key]?.length > 0 && (
            <section key={key}>
              <h3>{label}</h3>
              {p[key].map((item: any, index: number) => (
                <div className="resume-document-entry" key={index}>
                  <header>
                    <strong>{item.title || item.name}</strong>
                    <span>
                      {item.startDate} {item.endDate && "— " + item.endDate}
                    </span>
                  </header>
                  <p className="muted">{item.subtitle}</p>
                  <p>{item.description}</p>
                  {item.image_file_id && (
                    <PrivateImage
                      path={`/files/${item.image_file_id}/download?inline=true`}
                      alt={item.title || "经历配图"}
                    />
                  )}
                </div>
              ))}
            </section>
          ),
      )}
    </article>
  );
}
