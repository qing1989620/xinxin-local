// LRC 歌词解析：时间戳行 → 按时间排序；翻译歌词按时间并回主歌词。
// 无时间戳的纯文本歌词原样按行返回（不同步高亮）。

export type LrcLine = {
  time: number;
  text: string;
  trans?: string;
};

const TIME_TAG = /\[(\d{1,2}):(\d{2})(?:[.:](\d{1,3}))?\]/g;

function tagTime(tag: RegExpMatchArray) {
  const fraction = tag[3] ? Number(`0.${tag[3]}`) : 0;
  return Number(tag[1]) * 60 + Number(tag[2]) + fraction;
}

export function parseLrc(raw: string): LrcLine[] {
  const timed: LrcLine[] = [];
  const plain: LrcLine[] = [];
  for (const line of (raw || "").split(/\r?\n/)) {
    const tags = [...line.matchAll(TIME_TAG)];
    const text = line.replace(TIME_TAG, "").trim();
    if (!tags.length) {
      // 元数据行（[ar:..]）没有时间戳，正文没有时间戳时才整行保留。
      if (text && !/^\[[a-z]{1,3}:/i.test(line.trim())) plain.push({ time: -1, text });
      continue;
    }
    if (!text) continue;
    for (const tag of tags) timed.push({ time: tagTime(tag), text });
  }
  if (timed.length) return timed.sort((a, b) => a.time - b.time);
  return plain;
}

/** 主歌词 + 翻译歌词按时间合并（0.6s 内视为同一句）。 */
export function mergeLrc(main: string, trans: string): LrcLine[] {
  const lines = parseLrc(main);
  const translations = parseLrc(trans);
  if (!lines.length) return translations;
  for (const item of translations) {
    const target = lines.find(
      (line) => line.time >= 0 && Math.abs(line.time - item.time) < 0.6,
    );
    if (target && item.text && item.text !== target.text) {
      target.trans = item.text;
    }
  }
  return lines;
}

/** 当前播放秒数对应的歌词行；无时间戳（或还没到）返回 -1。 */
export function activeLrcIndex(lines: LrcLine[], seconds: number): number {
  if (!lines.length || !(lines[0].time >= 0)) return -1;
  let active = -1;
  for (let index = 0; index < lines.length; index += 1) {
    if (lines[index].time <= seconds + 0.05) active = index;
    else break;
  }
  return active;
}
