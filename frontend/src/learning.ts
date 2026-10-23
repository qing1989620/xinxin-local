export type Chapter = { id: string; idx: number; title: string; chars: number };
export type StudyBook = {
  id: string;
  file_id?: string;
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
  extraction?: {
    complete?: boolean;
    pages?: number;
    ocr_pages?: number;
    missing_pages?: number[];
    uncertain_pages?: number[];
    warning?: string;
  };
};
export type MaterialAnalysis = {
  type: string;
  type_label: string;
  eligible: boolean;
  reason: string;
  summary: string;
  warnings?: string[];
  reading_warnings?: string[];
  skipped_entries?: number;
  source_method?: "text" | "pdf_images";
  source_text?: string;
  read_pages?: number[];
  page_scope?: [number, number];
  knowledge_points: Array<{ name: string; quote: string }>;
  exercises: Array<{ label: string; quote: string; solvable: boolean }>;
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
  eligible?: boolean;
  text_eligible?: boolean;
  type_label?: string;
  reason?: string;
  analysis?:
    | (Omit<MaterialAnalysis, "knowledge_points" | "exercises"> & {
        knowledge_points: Array<{ name: string }>;
        exercises: Array<{ label: string; solvable: boolean }>;
      })
    | null;
};
export type SourceListing = {
  sources: SourceUnit[];
  max_sources: number;
  max_questions: number;
  image_reading?: {
    pdf: boolean;
    available: boolean;
    max_pages: number;
    reason: string;
  };
  coverage: {
    analyzed: number;
    total: number;
    eligible: number;
    knowledge_points: number;
    exercises: number;
    partial_sources?: number;
  };
};
export type ImportJob = {
  id: string;
  run_id: string;
  file_id: string;
  book_id: string | null;
  status: string;
  error: string;
  progress: { page: number; total: number; method: string } | null;
};
export type SourceText = Omit<SourceUnit, "analysis"> & {
  book_id: string;
  content: string;
  has_previous: boolean;
  has_next: boolean;
  edited_at?: number | null;
  analysis?: MaterialAnalysis | null;
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
    mode?: "auto" | "original" | "practice";
    analyze_only?: boolean;
    read_mode?: "text" | "pdf";
    page_ranges?: Record<string, [number, number]>;
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
