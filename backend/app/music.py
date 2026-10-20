"""GD 音乐台代理与情绪模型。

三条边界：
1. 只代理 JSON（搜索 / 取链 / 歌词），音频由客户端直连 CDN，不经过本机；
2. 官方限流 5 分钟 50 次，这里做进程内配额 + 结果缓存，避免把限流打穿；
3. 情绪是**本地启发式**：从标题/歌手/专辑的词表推断 valence（悲伤↔愉快）
   与 energy（安静↔激昂），不是音频分析，也不假装是事实。

播放记录按 90 分钟半衰期聚合成本轮"氛围"，注入人格提示——这是语气倾向，
不改变事实、权限与安全约束。
"""

from __future__ import annotations

import math
import re
import threading
import time
from collections import deque

import httpx

from .store import uid

BASE = "https://music-api.gdstudio.xyz/api.php"
SOURCES = ("netease", "kuwo", "joox", "tencent", "bilibili")
BITRATES = (128, 192, 320, 740, 999)
CALL_LIMIT, CALL_WINDOW = 45, 300  # 官方 50/5min，留出余量
CACHE_TTL = 300
HALF_LIFE_MINUTES = 90


class MusicUnavailable(ValueError):
    """上游不可用或没有可播放地址（继承 ValueError，按 400 返回可读提示）。"""


# 情绪词表：词 -> (valence, energy, weight)
# valence: -1 悲伤 ← 0 → +1 愉快；energy: 0 安静 → 1 激昂。
EMOTION_WORDS: dict[str, tuple[float, float, float]] = {
    # 明亮、轻快
    "快乐": (0.8, 0.7, 1.0),
    "开心": (0.8, 0.6, 1.0),
    "笑": (0.6, 0.5, 0.8),
    "阳光": (0.7, 0.6, 0.9),
    "晴天": (0.6, 0.5, 0.8),
    "夏天": (0.5, 0.6, 0.7),
    "恋爱": (0.6, 0.5, 0.8),
    "甜": (0.6, 0.4, 0.8),
    "告白": (0.5, 0.5, 0.8),
    "彩虹": (0.6, 0.5, 0.7),
    "春": (0.5, 0.4, 0.6),
    # 安静、温柔
    "晚安": (0.3, 0.15, 0.8),
    "月": (0.2, 0.2, 0.6),
    "温柔": (0.4, 0.2, 0.9),
    "安静": (0.2, 0.15, 0.8),
    "海": (0.3, 0.3, 0.6),
    "风": (0.2, 0.3, 0.5),
    "星": (0.3, 0.2, 0.6),
    "钢琴": (0.2, 0.15, 0.6),
    # 低落、伤感
    "雨": (-0.4, 0.2, 0.8),
    "孤独": (-0.6, 0.2, 1.0),
    "寂寞": (-0.6, 0.2, 1.0),
    "悲伤": (-0.8, 0.2, 1.0),
    "哭": (-0.8, 0.3, 1.0),
    "离": (-0.6, 0.3, 0.8),
    "遗憾": (-0.6, 0.25, 0.9),
    "错过": (-0.6, 0.3, 0.9),
    "冬": (-0.3, 0.2, 0.6),
    "夜": (-0.2, 0.25, 0.5),
    "碎": (-0.5, 0.4, 0.7),
    "旧": (-0.3, 0.2, 0.5),
    # 激昂、强烈
    "燃": (0.3, 0.95, 1.0),
    "摇滚": (0.2, 0.9, 0.9),
    "战": (0.1, 0.9, 0.9),
    "怒": (-0.6, 0.9, 1.0),
    "恨": (-0.7, 0.8, 1.0),
    "疯": (-0.3, 0.85, 0.8),
    "自由": (0.4, 0.7, 0.7),
    "奔跑": (0.4, 0.8, 0.8),
    "飞": (0.4, 0.7, 0.7),
    "电子": (0.1, 0.75, 0.5),
    "舞": (0.5, 0.8, 0.7),
    "鼓": (0.0, 0.7, 0.5),
    # English
    "love": (0.7, 0.5, 0.9),
    "happy": (0.8, 0.6, 1.0),
    "sun": (0.6, 0.5, 0.8),
    "smile": (0.7, 0.5, 0.8),
    "summer": (0.5, 0.6, 0.7),
    "sad": (-0.7, 0.2, 1.0),
    "cry": (-0.8, 0.3, 1.0),
    "alone": (-0.6, 0.2, 0.9),
    "rain": (-0.35, 0.2, 0.7),
    "night": (-0.15, 0.25, 0.5),
    "blue": (-0.4, 0.25, 0.7),
    "fire": (0.1, 0.85, 0.8),
    "rock": (0.2, 0.9, 0.9),
    "dance": (0.5, 0.8, 0.8),
    "dream": (0.3, 0.3, 0.6),
    "angel": (0.5, 0.3, 0.6),
}

_LATIN = re.compile(r"[a-z]+")


def emotion_for(title: str = "", artist: str = "", album: str = "") -> dict:
    """从文本推断情绪；没有命中时给中性默认值，并标注 confidence=0。"""
    text = f"{title} {artist} {album}".lower()
    latin = set(_LATIN.findall(text))
    matched = [
        (word, valence, energy, weight)
        for word, (valence, energy, weight) in EMOTION_WORDS.items()
        if (word in latin if word.isascii() else word in text)
    ]
    if not matched:
        return {
            "valence": 0.0,
            "energy": 0.45,
            "label": "平静",
            "confidence": 0.0,
            "hits": [],
        }
    total = sum(weight for _, _, _, weight in matched)
    valence = sum(value * weight for _, value, _, weight in matched) / total
    energy = sum(value * weight for _, _, value, weight in matched) / total
    return {
        "valence": round(max(-1.0, min(1.0, valence)), 3),
        "energy": round(max(0.0, min(1.0, energy)), 3),
        "label": label_for(valence, energy),
        "confidence": round(min(1.0, total / 2.4), 3),
        "hits": [word for word, _, _, _ in matched][:8],
    }


def label_for(valence: float, energy: float) -> str:
    if valence >= 0.15:
        return "乐" if energy >= 0.55 else "喜"
    if energy >= 0.55:
        return "怒"
    return "哀"


TONE = {
    "喜": "语气轻快些，愿意多聊两句，但别把正事拖着",
    "乐": "情绪高一点，可以更活泼，但结果仍然要准确",
    "怒": "别顺着火气走：语气收敛、直接推进，不嬉闹",
    "哀": "节奏放慢、句子更短更软，先接住情绪再办事",
    "平静": "照常",
}


class GDClient:
    """GD 音乐台的只读客户端：配额 + 缓存 + 统一错误。"""

    def __init__(self):
        self.lock = threading.Lock()
        self.calls: deque[float] = deque()
        self.cache: dict[tuple, tuple[float, object]] = {}

    def _budget(self):
        now = time.time()
        with self.lock:
            while self.calls and now - self.calls[0] > CALL_WINDOW:
                self.calls.popleft()
            if len(self.calls) >= CALL_LIMIT:
                wait = int(CALL_WINDOW - (now - self.calls[0])) + 1
                raise MusicUnavailable(
                    f"音乐接口调用太频繁，请 {max(1, wait)} 秒后再试"
                )
            self.calls.append(now)

    def get(self, **params):
        key = tuple(sorted(params.items()))
        now = time.time()
        with self.lock:
            cached = self.cache.get(key)
            if cached and cached[0] > now:
                return cached[1]
        self._budget()
        try:
            response = httpx.get(BASE, params=params, timeout=12)
        except httpx.HTTPError as failure:
            raise MusicUnavailable(
                f"连接音乐接口失败：{type(failure).__name__}"
            ) from None
        if response.status_code >= 400:
            raise MusicUnavailable(f"音乐接口返回 {response.status_code}")
        try:
            data = response.json()
        except ValueError:
            raise MusicUnavailable("音乐接口返回了非 JSON 内容") from None
        with self.lock:
            if len(self.cache) > 240:
                self.cache.clear()
            self.cache[key] = (now + CACHE_TTL, data)
        return data

    # ------------------------------------------------------------------
    def search(self, query: str, source: str = "netease", page: int = 1, limit: int = 20):
        source = source if source in SOURCES else "netease"
        data = self.get(
            types="search",
            source=source,
            name=query,
            count=max(1, min(limit, 30)),
            pages=max(1, min(page, 20)),
        )
        rows = data if isinstance(data, list) else data.get("data") or []
        tracks = []
        for row in rows:
            if not isinstance(row, dict) or not row.get("id"):
                continue
            artist = row.get("artist") or []
            if isinstance(artist, list):
                artist = " / ".join(str(name) for name in artist)
            track = {
                "id": str(row["id"]),
                "name": str(row.get("name") or "未命名"),
                "artist": artist or "未知歌手",
                "album": str(row.get("album") or ""),
                "pic_id": str(row.get("pic_id") or ""),
                "lyric_id": str(row.get("lyric_id") or ""),
                "source": str(row.get("source") or source),
            }
            track["emotion"] = emotion_for(
                track["name"], track["artist"], track["album"]
            )
            tracks.append(track)
        return {"source": source, "tracks": tracks}

    def url(self, track_id: str, source: str = "netease", br: int = 320):
        source = source if source in SOURCES else "netease"
        br = br if br in BITRATES else 320
        data = self.get(types="url", source=source, id=track_id, br=br)
        payload = data[0] if isinstance(data, list) and data else data
        if not isinstance(payload, dict) or not payload.get("url"):
            raise MusicUnavailable("这首在当前音源没有可播放地址，换一个音源试试")
        return {
            "url": payload["url"],
            "br": payload.get("br", br),
            "size": payload.get("size"),
        }

    def lyric(self, lyric_id: str, source: str = "netease"):
        source = source if source in SOURCES else "netease"
        data = self.get(types="lyric", source=source, id=lyric_id)
        payload = data[0] if isinstance(data, list) and data else data
        if not isinstance(payload, dict):
            return {"lyric": "", "tlyric": ""}
        return {
            "lyric": str(payload.get("lyric") or ""),
            "tlyric": str(payload.get("tlyric") or ""),
        }

    def pic(self, pic_id: str, source: str = "netease", size: int = 500):
        source = source if source in SOURCES else "netease"
        size = 500 if size not in (300, 500) else size
        data = self.get(types="pic", source=source, id=pic_id, size=size)
        payload = data[0] if isinstance(data, list) and data else data
        return {"url": (payload or {}).get("url") or ""} if isinstance(payload, dict) else {"url": ""}


client = GDClient()


# ----------------------------------------------------------------------
# 情绪聚合：播放记录 -> 当前氛围
# ----------------------------------------------------------------------
def record_play(store, track: dict, emotion: dict | None = None) -> dict:
    emotion = emotion or emotion_for(
        track.get("name", ""), track.get("artist", ""), track.get("album", "")
    )
    store.execute(
        "INSERT INTO music_plays(id,track_id,source,name,artist,album,valence,energy,label,created)"
        " VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            uid(),
            str(track.get("id") or track.get("track_id") or ""),
            str(track.get("source") or "netease"),
            str(track.get("name") or "未命名")[:200],
            str(track.get("artist") or "")[:200],
            str(track.get("album") or "")[:200],
            float(emotion["valence"]),
            float(emotion["energy"]),
            str(emotion["label"]),
            time.time(),
        ),
    )
    # 只保留最近 200 条，避免情绪历史无限增长
    store.execute(
        "DELETE FROM music_plays WHERE id NOT IN "
        "(SELECT id FROM music_plays ORDER BY created DESC LIMIT 200)"
    )
    return current_mood(store)


def recent_plays(store, limit: int = 12) -> list[dict]:
    rows = store.all(
        "SELECT track_id,name,artist,album,valence,energy,label,created"
        " FROM music_plays ORDER BY created DESC LIMIT ?",
        (max(1, min(limit, 50)),),
    )
    return [dict(row) for row in rows]


def current_mood(store) -> dict:
    plays = recent_plays(store, 20)
    now = time.time()
    total = valence = energy = 0.0
    for play in plays:
        age_minutes = max(0.0, (now - play["created"]) / 60)
        weight = 0.5 ** (age_minutes / HALF_LIFE_MINUTES)
        total += weight
        valence += play["valence"] * weight
        energy += play["energy"] * weight
    if total <= 0:
        return {
            "label": "平静",
            "valence": 0.0,
            "energy": 0.4,
            "intensity": 0.0,
            "tracks": 0,
            "influence": influence_enabled(store),
        }
    valence /= total
    energy /= total
    return {
        "label": label_for(valence, energy),
        "valence": round(valence, 3),
        "energy": round(energy, 3),
        "intensity": round(min(1.0, total / 3), 3),
        "tracks": len(plays),
        "influence": influence_enabled(store),
    }


def influence_enabled(store) -> bool:
    import json

    row = store.setting("music_influence")
    return True if row is None else bool(json.loads(row))


def set_influence(store, enabled: bool):
    import json

    store.set_setting("music_influence", json.dumps(bool(enabled)))


def clear_plays(store):
    store.execute("DELETE FROM music_plays")


def mood_note(store) -> str:
    """给系统提示的一段氛围说明；没有播放或已关闭时不产生任何文字。"""
    mood = current_mood(store)
    if not mood["influence"] or mood["intensity"] < 0.15:
        return ""
    recent = [play["name"] for play in recent_plays(store, 2) if play.get("name")]
    listening = f"（最近在听《{'》《'.join(recent)}》）" if recent else ""
    return (
        f"【此刻的氛围】他正在听偏「{mood['label']}」的音乐{listening}"
        f"（强度 {mood['intensity']:.2f}，越接近 1 越明显）。{TONE[mood['label']]}。"
        "这只是语气倾向：不要主动评论他的歌单，除非他先聊起；"
        "也不改变事实、权限与安全约束，不代表他本人的情绪。"
    )
