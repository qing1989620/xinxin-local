import { useEffect, useRef } from "react";
import {
  EditorContent,
  NodeViewWrapper,
  ReactNodeViewRenderer,
  useEditor,
  type NodeViewProps,
} from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import ImageExtension from "@tiptap/extension-image";
import Placeholder from "@tiptap/extension-placeholder";
import {
  Bold,
  Italic,
  Heading2,
  List,
  Code2,
  Quote,
  Link2,
  ImagePlus,
} from "lucide-react";
import { upload } from "./api";
import { PrivateImage, useToast } from "./ui";

function ImageNode({ node }: NodeViewProps) {
  return (
    <NodeViewWrapper className="editor-image" contentEditable={false}>
      {node.attrs.file_id ? (
        <PrivateImage
          path={`/files/${node.attrs.file_id}/download?inline=true`}
          alt={node.attrs.alt || "文章配图"}
        />
      ) : (
        <span className="muted">
          历史配图：{node.attrs.alt || "未迁移的图片"}
        </span>
      )}
    </NodeViewWrapper>
  );
}
const PrivateImageExtension = ImageExtension.extend({
  addAttributes() {
    return { ...this.parent?.(), file_id: { default: null } };
  },
  addNodeView() {
    return ReactNodeViewRenderer(ImageNode);
  },
});
function parse(value: string) {
  try {
    const doc = JSON.parse(value);
    if (doc.type === "doc") return doc;
  } catch {}
  return {
    type: "doc",
    content: [
      {
        type: "paragraph",
        content: value ? [{ type: "text", text: value }] : [],
      },
    ],
  };
}
export default function RichEditor({
  value,
  onChange,
  readOnly = false,
  disabled = false,
  onUploadingChange,
}: {
  value: string;
  onChange?: (value: string) => void;
  readOnly?: boolean;
  disabled?: boolean;
  onUploadingChange?: (busy: boolean) => void;
}) {
  const picker = useRef<HTMLInputElement>(null),
    toast = useToast();
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        link: {
          openOnClick: readOnly,
          HTMLAttributes: { rel: "noopener noreferrer", target: "_blank" },
        },
      }),
      PrivateImageExtension,
      Placeholder.configure({ placeholder: "写下想留住的内容…" }),
    ],
    content: parse(value),
    editable: !readOnly && !disabled,
    editorProps: {
      attributes: readOnly
        ? { role: "document", "aria-label": "文章正文" }
        : {
            role: "textbox",
            "aria-label": "文章正文编辑器",
            "aria-multiline": "true",
          },
    },
    onUpdate: ({ editor }) => onChange?.(JSON.stringify(editor.getJSON())),
  });
  useEffect(() => {
    editor?.setEditable(!readOnly && !disabled);
  }, [editor, readOnly, disabled]);
  return (
    <div className={`rich-editor ${readOnly ? "read-only" : ""}`}>
      {!readOnly && (
        <div className="editor-toolbar" role="toolbar" aria-label="文章格式">
          {[
            {
              label: "加粗",
              icon: Bold,
              active: editor?.isActive("bold"),
              action: () => editor?.chain().focus().toggleBold().run(),
            },
            {
              label: "斜体",
              icon: Italic,
              active: editor?.isActive("italic"),
              action: () => editor?.chain().focus().toggleItalic().run(),
            },
            {
              label: "二级标题",
              icon: Heading2,
              active: editor?.isActive("heading", { level: 2 }),
              action: () =>
                editor?.chain().focus().toggleHeading({ level: 2 }).run(),
            },
            {
              label: "项目列表",
              icon: List,
              active: editor?.isActive("bulletList"),
              action: () => editor?.chain().focus().toggleBulletList().run(),
            },
            {
              label: "代码块",
              icon: Code2,
              active: editor?.isActive("codeBlock"),
              action: () => editor?.chain().focus().toggleCodeBlock().run(),
            },
            {
              label: "引用",
              icon: Quote,
              active: editor?.isActive("blockquote"),
              action: () => editor?.chain().focus().toggleBlockquote().run(),
            },
          ].map((item) => (
            <button
              key={item.label}
              type="button"
              className={`icon-button ${item.active ? "selected" : ""}`}
              title={item.label}
              aria-label={item.label}
              aria-pressed={Boolean(item.active)}
              onClick={item.action}
            >
              <item.icon size={17} />
            </button>
          ))}
          <button
            type="button"
            className="icon-button"
            aria-label="添加链接"
            title="添加链接"
            onClick={() => {
              const link = prompt(
                "链接地址（https:// 或 mailto:）",
                editor?.getAttributes("link").href || "",
              );
              if (link === null) return;
              if (!link) {
                editor?.chain().focus().unsetLink().run();
                return;
              }
              if (!/^(https?:\/\/|mailto:)/i.test(link)) {
                toast("链接必须使用 HTTP(S) 或 mailto", true);
                return;
              }
              editor?.chain().focus().setLink({ href: link }).run();
            }}
          >
            <Link2 size={17} />
          </button>
          <button
            type="button"
            className="icon-button"
            aria-label="插入私人图片"
            title="插入私人图片"
            onClick={() => picker.current?.click()}
          >
            <ImagePlus size={17} />
          </button>
        </div>
      )}
      <EditorContent editor={editor} />
      <input
        ref={picker}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        hidden
        onChange={async (event) => {
          const file = event.target.files?.[0];
          if (file) {
            onUploadingChange?.(true);
            try {
              const saved = await upload(file);
              if (!editor || editor.isDestroyed) return;
              editor
                ?.chain()
                .focus()
                .setImage({
                  src: "xinxin:" + saved.id,
                  file_id: saved.id,
                } as any)
                .run();
            } catch (error) {
              toast((error as Error).message, true);
            } finally {
              onUploadingChange?.(false);
            }
          }
          event.target.value = "";
        }}
      />
    </div>
  );
}
