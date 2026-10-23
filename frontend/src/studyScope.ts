import type { SourceListing, SourceUnit } from "./learning";

export type PageRanges = Record<string, [number, number]>;

export function pageRange(unit: SourceUnit, ranges: PageRanges = {}) {
  return ranges[unit.id] ?? [unit.page_from ?? 0, unit.page_to ?? 0];
}

export function rangeIssue(unit: SourceUnit, ranges: PageRanges = {}) {
  const [start, end] = pageRange(unit, ranges);
  if (!unit.page_from || !unit.page_to) return "此片段没有可靠的 PDF 页码";
  if (
    !Number.isInteger(start) ||
    !Number.isInteger(end) ||
    start < unit.page_from ||
    end > unit.page_to ||
    start > end
  )
    return `精读页段需在 ${unit.page_from}–${unit.page_to} 页内，起始页不能大于结束页`;
  return end - start >= 24 ? "每个精读页段最多 24 页，请缩小范围" : "";
}

export function scopePages(scope: SourceUnit[], ranges: PageRanges = {}) {
  const pages = new Set<number>();
  for (const unit of scope) {
    if (rangeIssue(unit, ranges)) continue;
    const [start, end] = pageRange(unit, ranges);
    for (let page = start; page <= end; page++) pages.add(page);
  }
  return pages.size;
}

export function imageReadingIssue(
  scope: SourceUnit[],
  capability: SourceListing["image_reading"],
  ranges: PageRanges = {},
) {
  if (!capability?.available)
    return capability?.reason || "此资料暂不支持原页读取";
  for (const unit of scope) {
    const issue = rangeIssue(unit, ranges);
    if (issue) return `${unit.label}：${issue}。`;
  }
  return scopePages(scope, ranges) > capability.max_pages
    ? `一次最多读取 ${capability.max_pages} 个 PDF 原页，请减少选择范围。`
    : "";
}

export function analyzedForMode(
  unit: SourceUnit,
  readMode: "text" | "pdf",
  ranges: PageRanges = {},
) {
  const analysis = unit.analysis;
  if (
    !analysis ||
    (analysis.source_method === "pdf_images") !== (readMode === "pdf")
  )
    return false;
  if (readMode === "text") return true;
  const [start, end] = pageRange(unit, ranges);
  const analyzedRange = analysis.page_scope ?? [unit.page_from, unit.page_to];
  return (
    !rangeIssue(unit, ranges) &&
    !analysis.reading_warnings?.length &&
    analyzedRange[0] === start &&
    analyzedRange[1] === end &&
    analysis.read_pages?.length === end - start + 1
  );
}

export function selectStudyBatch(
  units: SourceUnit[],
  count: number,
  maxSources: number,
  maxQuestions: number,
  readMode: "text" | "pdf",
  capability: SourceListing["image_reading"],
  ranges: PageRanges,
  onlyUnanalyzed = false,
) {
  const chosen: SourceUnit[] = [];
  const limit = Math.min(maxSources, Math.floor(maxQuestions / count));
  for (const unit of units) {
    if (chosen.length >= limit) break;
    if (onlyUnanalyzed && analyzedForMode(unit, readMode, ranges)) continue;
    if (readMode === "text" && (unit.text_eligible ?? unit.eligible) === false)
      continue;
    if (
      readMode === "pdf" &&
      imageReadingIssue([...chosen, unit], capability, ranges)
    )
      continue;
    chosen.push(unit);
  }
  return chosen;
}
