export type Chapter = { id: string; idx: number; title: string; chars: number };
export type StudyBook = {
  id: string;
  title: string;
  subject: string;
  chapter_count: number;
  char_count: number;
  question_count: number;
  answered: number;
  unique_answered?: number;
  correct: number;
  chapters: Chapter[];
  created: number;
  updated: number;
};
export type SourceUnit = {
  id: string;
  chapter_id: string;
  idx: number;
  label: string;
  chars: number;
  question_count: number;
  page_from: number | null;
  page_to: number | null;
};
export type SourceText = SourceUnit & {
  book_id: string;
  content: string;
  has_previous: boolean;
  has_next: boolean;
};
export type Generation = {
  id: string;
  book_id: string;
  run_id: string;
  status: string;
  error: string;
  created_count: number;
  target: number;
  finished_sources: number;
  options: {
    count: number;
    kinds: Array<"single" | "fill" | "short">;
    difficulty: number;
    focus: string;
  };
  items: Array<{
    source_id: string;
    label: string;
    chapter_title: string;
    target: number;
    created_count: number;
    status: string;
    rejected: number;
    duplicates: number;
    error: string;
  }>;
};
export const KIND_LABEL = {
  single: "单选",
  fill: "填空",
  short: "简答",
} as const;
export const isGenerating = (job: Generation | null) =>
  Boolean(job && ["queued", "running", "cancelling"].includes(job.status));
export const wordCount = (count: number) =>
  count >= 1000 ? `${(count / 1000).toFixed(1)}k 字` : `${count} 字`;
