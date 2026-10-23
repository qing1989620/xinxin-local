import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { getBlob } from "../api";
import { ErrorState, Loading } from "../ui";

export function StudyPdfPages({ id, pages }: { id: string; pages: number[] }) {
  const [index, setIndex] = useState(0);
  const [image, setImage] = useState("");
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const page = pages[Math.min(index, pages.length - 1)];
  useEffect(() => {
    const controller = new AbortController();
    let object = "";
    setImage("");
    setError("");
    if (page)
      void getBlob(`/learning/sources/${id}/pages/${page}`, controller.signal)
        .then((blob) => {
          if (!controller.signal.aborted) {
            object = URL.createObjectURL(blob);
            setImage(object);
          }
        })
        .catch((err: Error) => {
          if (!controller.signal.aborted) setError(err.message);
        });
    return () => {
      controller.abort();
      if (object) URL.revokeObjectURL(object);
    };
  }, [id, page, retry]);
  if (!page) return null;
  return (
    <div className="study-pdf-pages">
      <div className="study-source-nav">
        <span>PDF 原页 · 第 {page} 页</span>
        <div>
          <button
            className="icon-button"
            aria-label="上一原页"
            disabled={index === 0}
            onClick={() => setIndex((value) => value - 1)}
          >
            <ChevronLeft size={17} />
          </button>
          <small>
            {Math.min(index + 1, pages.length)} / {pages.length}
          </small>
          <button
            className="icon-button"
            aria-label="下一原页"
            disabled={index >= pages.length - 1}
            onClick={() => setIndex((value) => value + 1)}
          >
            <ChevronRight size={17} />
          </button>
        </div>
      </div>
      {error ? (
        <ErrorState
          message={error}
          retry={() => setRetry((value) => value + 1)}
        />
      ) : image ? (
        <img src={image} alt={`教材 PDF 物理第 ${page} 页原图`} />
      ) : (
        <Loading />
      )}
    </div>
  );
}
