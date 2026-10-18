/** 技能来源分类：能力球体与能力库共用同一套口径，避免两处逻辑漂移。
 *
 * 判定顺序（与后端 corpus_source/generation/tools 语义对齐）：
 * 1. 演化代际 > 0        → evolved（演化资产）
 * 2. 来源为 github       → community（社区导入）
 * 3. 注册了平台工具      → platform（平台可执行技能）
 * 4. 其余               → seed（种子资产）
 */

export type OriginKind = "evolved" | "community" | "platform" | "seed";

type OriginInput = {
  generation?: number;
  corpus_source?: string;
  source?: string;
  /** 球体图节点传工具计数（number），能力库传工具名列表（string[]）。 */
  tools?: unknown[] | number;
};

export function originKind(input: OriginInput): OriginKind {
  if ((input.generation || 0) > 0) return "evolved";
  const source = input.corpus_source ?? input.source;
  if (source === "github") return "community";
  const tools = input.tools;
  const count = Array.isArray(tools)
    ? tools.length
    : typeof tools === "number"
      ? tools
      : 0;
  if (count > 0) return "platform";
  return "seed";
}

const ORIGIN_LABEL: Record<OriginKind, string> = {
  evolved: "演化",
  community: "社区导入",
  platform: "平台技能",
  seed: "种子资产",
};

/** 中文标签；evolved 且 withGeneration 时附上代际号（如「演化 G3」）。 */
export function originLabel(input: OriginInput, withGeneration = false): string {
  const kind = originKind(input);
  if (kind === "evolved" && withGeneration) {
    return `演化 G${input.generation}`;
  }
  return ORIGIN_LABEL[kind];
}
