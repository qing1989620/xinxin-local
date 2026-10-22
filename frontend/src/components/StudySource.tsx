import { useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { api } from "../api";
import { Dialog, ErrorState, Loading } from "../ui";
import type { SourceText } from "../learning";
import { MathText } from "./MathText";

export function StudySource({
  id,
  quote = "",
  onClose,
}: {
  id: string;
  quote?: string;
  onClose: () => void;
}) {
  const [current, setCurrent] = useState(id);
  const [source, setSource] = useState<SourceText | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const navigationRequest = useRef<AbortController | null>(null);
  useEffect(() => () => navigationRequest.current?.abort(), []);
  useEffect(() => {
    const controller = new AbortController();
    setSource(null);
    setError("");
    void api<{ source: SourceText }>(`/learning/sources/${current}`, {
      signal: controller.signal,
    })
      .then((value) => {
        if (!controller.signal.aborted) setSource(value.source);
      })
      .catch((err: Error) => {
        if (!controller.signal.aborted) setError(err.message);
      });
    return () => controller.abort();
  }, [current, retry]);
  async function adjacent(offset: number) {
    if (!source) return;
    navigationRequest.current?.abort();
    const controller = new AbortController();
    navigationRequest.current = controller;
    try {
      const value = await api<{ source: SourceText }>(
        `/learning/sources/${source.id}?offset=${offset}`,
        { signal: controller.signal },
      );
      if (!controller.signal.aborted) setCurrent(value.source.id);
    } catch (err) {
      if (!controller.signal.aborted) setError((err as Error).message);
    } finally {
      if (navigationRequest.current === controller)
        navigationRequest.current = null;
    }
  }
  return (
    <Dialog title="回到原文" wide onClose={onClose}>
      {error ? (
        <ErrorState
          message={error}
          retry={() => setRetry((value) => value + 1)}
        />
      ) : !source ? (
        <Loading />
      ) : (
        <>
          <div className="study-source-nav">
            <span>{source.label}</span>
            <div>
              <button
                className="icon-button"
                aria-label="上一个片段"
                disabled={!source.has_previous}
                onClick={() => void adjacent(-1)}
              >
                <ChevronLeft size={18} />
              </button>
              <button
                className="icon-button"
                aria-label="下一个片段"
                disabled={!source.has_next}
                onClick={() => void adjacent(1)}
              >
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
          {current === id && quote && (
            <blockquote className="study-quote">
              <span>出题依据</span>
              {quote}
            </blockquote>
          )}
          <div className="study-source-text">
            <MathText text={source.content} />
          </div>
        </>
      )}
    </Dialog>
  );
}
