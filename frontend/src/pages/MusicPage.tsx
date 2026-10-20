import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type FormEvent,
} from "react";
import { useSearchParams } from "react-router-dom";
import {
  CloudOff,
  Disc3,
  Music2,
  Pause,
  Play,
  Search,
  Trash2,
  Volume2,
  Waves,
  X,
} from "lucide-react";
import { api, put, remove } from "../api";
import { Empty, Loading, PageHeader, useToast } from "../ui";
import { useMusicPlayer, type PlayerTrack } from "../musicPlayer";

type Emotion = {
  valence: number;
  energy: number;
  label: string;
  confidence: number;
  hits: string[];
};
type Track = PlayerTrack & { emotion: Emotion };
type Mood = {
  label: string;
  valence: number;
  energy: number;
  intensity: number;
  tracks: number;
  influence: boolean;
};
type Play = {
  track_id: string;
  name: string;
  artist: string;
  valence: number;
  energy: number;
  label: string;
  created: number;
};

const SOURCES = [
  ["netease", "网易云"],
  ["kuwo", "酷我"],
  ["joox", "JOOX"],
  ["tencent", "QQ 音乐"],
] as const;

function moodTone(label: string) {
  return (
    { 喜: "calm-joy", 乐: "bright", 怒: "intense", 哀: "low", 平静: "neutral" }[
      label
    ] || "neutral"
  );
}

function minutesAgo(created: number) {
  const minutes = Math.max(0, Math.round((Date.now() / 1000 - created) / 60));
  if (minutes < 1) return "刚刚";
  if (minutes < 60) return `${minutes} 分钟前`;
  return `${Math.round(minutes / 60)} 小时前`;
}

function clock(seconds: number) {
  return `${Math.floor(seconds / 60)}:${String(
    Math.floor(seconds % 60),
  ).padStart(2, "0")}`;
}

export default function MusicPage() {
  const toast = useToast();
  const player = useMusicPlayer();
  const [query, setQuery] = useState(""),
    [source, setSource] = useState<string>("netease"),
    [tracks, setTracks] = useState<Track[] | null>(null),
    [searching, setSearching] = useState(false),
    [pending, setPending] = useState(""),
    [mood, setMood] = useState<Mood | null>(null),
    [plays, setPlays] = useState<Play[]>([]),
    [lyric, setLyric] = useState(""),
    [params, setParams] = useSearchParams();

  const loadMood = useCallback(async () => {
    try {
      const result = await api<{ mood: Mood; plays: Play[] }>("/music/mood");
      setMood(result.mood);
      setPlays(result.plays);
    } catch {
      // 氛围读取失败不阻断播放；下一次操作会重试。
    }
  }, []);
  useEffect(() => {
    void loadMood();
  }, [loadMood]);

  // 播放器记录一次播放后，这里刷新氛围（两个组件通过事件解耦）。
  useEffect(() => {
    const refresh = () => void loadMood();
    window.addEventListener("xinxin:music-played", refresh);
    return () => window.removeEventListener("xinxin:music-played", refresh);
  }, [loadMood]);

  const runSearch = useCallback(
    async (text: string, src: string) => {
      setSearching(true);
      try {
        const result = await api<{ tracks: Track[] }>(
          `/music/search?q=${encodeURIComponent(text)}&source=${src}`,
        );
        setTracks(result.tracks);
        if (!result.tracks.length) toast("没有搜到，换个关键词或音源试试");
        sessionStorage.setItem(
          "xinxin-music-search",
          JSON.stringify({ q: text, source: src }),
        );
      } catch (error) {
        toast((error as Error).message, true);
      } finally {
        setSearching(false);
      }
    },
    [toast],
  );

  async function search(event?: FormEvent) {
    event?.preventDefault();
    if (!query.trim() || searching) return;
    setPending("");
    await runSearch(query.trim(), source);
  }

  // /music?q=… 直达一次检索；否则恢复上次搜过的关键词（切页回来列表还在）。
  const restored = useRef(false);
  useEffect(() => {
    if (restored.current) return;
    restored.current = true;
    const wanted = params.get("q");
    if (wanted) {
      const src = params.get("source") || "netease";
      setQuery(wanted);
      setSource(src);
      void runSearch(wanted, src);
      setParams(
        (previous) => {
          const next = new URLSearchParams(previous);
          next.delete("q");
          return next;
        },
        { replace: true },
      );
      return;
    }
    const saved = sessionStorage.getItem("xinxin-music-search");
    if (!saved) return;
    try {
      const parsed = JSON.parse(saved) as { q?: string; source?: string };
      if (!parsed?.q) return;
      const src = parsed.source || "netease";
      setQuery(parsed.q);
      setSource(src);
      void runSearch(parsed.q, src);
    } catch {
      // 缓存损坏就当作没有
    }
    // 只在挂载时跑一次；runSearch/params 的后续变化不需要重放。
  }, []);

  // 换歌时拉一次歌词；没有 lyric_id 就清空。
  const lyricId = player?.track?.lyric_id || "";
  const trackSource = player?.track?.source || "netease";
  useEffect(() => {
    if (!lyricId) {
      setLyric("");
      return;
    }
    let alive = true;
    void api<{ lyric: string; tlyric: string }>(
      `/music/lyric?id=${encodeURIComponent(lyricId)}&source=${trackSource}`,
    )
      .then((value) => {
        if (alive) setLyric(value.tlyric || value.lyric || "");
      })
      .catch(() => {
        if (alive) setLyric("");
      });
    return () => {
      alive = false;
    };
  }, [lyricId, trackSource]);

  async function play(track: Track) {
    if (!player) return;
    const key = `${track.source}:${track.id}`;
    if (player.track?.id === track.id && player.track?.source === track.source) {
      await player.toggle();
      return;
    }
    setPending(key);
    try {
      await player.play(track);
    } finally {
      setPending("");
    }
  }

  async function clearMood() {
    try {
      const result = await remove<{ mood: Mood }>("/music/mood");
      setMood(result.mood);
      setPlays([]);
      toast("已清空播放记录，氛围回到平静");
    } catch (error) {
      toast((error as Error).message, true);
    }
  }

  async function toggleInfluence() {
    if (!mood) return;
    try {
      const result = await put<{ mood: Mood }>("/music/settings", {
        influence: !mood.influence,
      });
      setMood(result.mood);
      toast(
        result.mood.influence
          ? "已开启：当前氛围会影响 Xinxin 的语气"
          : "已关闭：Xinxin 不再受音乐影响",
      );
    } catch (error) {
      toast((error as Error).message, true);
    }
  }

  const current = player?.track || null;
  const isCurrent = (track: Track) =>
    current?.id === track.id && current?.source === track.source;
  const progress = player?.progress || { current: 0, duration: 0 };
  const percent = progress.duration
    ? Math.min(100, (progress.current / progress.duration) * 100)
    : 0;

  return (
    <div className="page-enter">
      <PageHeader
        overline="AMBIENT LISTENING"
        title="背景音乐"
        description="放一首，房间的氛围会跟着变——Xinxin 的语气也会。音频直接从音乐平台 CDN 播放，不经过这台机器；切到别的页面也会继续放。"
      />
      <div className="music-layout">
        <section className="music-panel">
          <form className="music-search" onSubmit={search}>
            <div className="music-search-field">
              <Search size={16} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="歌名、歌手或专辑"
                aria-label="搜索音乐"
              />
              {query && (
                <button
                  type="button"
                  className="field-clear"
                  onClick={() => {
                    setQuery("");
                    setTracks(null);
                  }}
                  aria-label="清空搜索"
                >
                  <X size={13} />
                </button>
              )}
            </div>
            <select
              value={source}
              onChange={(event) => setSource(event.target.value)}
              aria-label="音乐源"
            >
              {SOURCES.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
            <button className="button secondary" disabled={searching}>
              {searching ? "搜索中…" : "搜索"}
            </button>
          </form>
          {tracks === null ? (
            <div className="music-hint">
              <Music2 size={22} strokeWidth={1.3} />
              <p>
                搜索一首歌开始。每首歌会根据标题与专辑的词义给出一个情绪指数，
                最近播放的整体倾向决定此刻的氛围。
              </p>
            </div>
          ) : tracks.length ? (
            <ul className={`track-list${searching ? " loading" : ""}`}>
              {tracks.map((track) => (
                <li
                  key={`${track.source}-${track.id}`}
                  className={isCurrent(track) ? "active" : ""}
                >
                  <button
                    className="track-play"
                    onClick={() => void play(track)}
                    aria-label={`播放 ${track.name}`}
                  >
                    {pending === `${track.source}:${track.id}` ? (
                      <span className="track-loading" />
                    ) : isCurrent(track) && player?.playing ? (
                      <Pause size={15} />
                    ) : (
                      <Play size={15} />
                    )}
                  </button>
                  <div className="track-meta">
                    <strong>{track.name}</strong>
                    <small>
                      {track.artist}
                      {track.album ? ` · ${track.album}` : ""}
                    </small>
                  </div>
                  <span
                    className={`emotion-chip ${moodTone(track.emotion.label)}`}
                    title={
                      track.emotion.hits.length
                        ? `命中：${track.emotion.hits.join("、")}`
                        : "没有命中情绪词，按中性处理"
                    }
                  >
                    {track.emotion.label}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <Empty
              title="没有结果"
              description="换一个关键词，或者切换到酷我 / JOOX 音源再试。"
            />
          )}
        </section>

        <aside className="music-side">
          <section className="music-panel now-playing">
            <div className="panel-label">
              <Disc3 size={14} />
              正在播放
            </div>
            {current ? (
              <>
                <div className="now-head">
                  <span className="now-cover">
                    {player?.cover ? (
                      <img
                        src={player.cover}
                        alt=""
                        referrerPolicy="no-referrer"
                        loading="lazy"
                      />
                    ) : (
                      <Music2 size={16} />
                    )}
                  </span>
                  <div>
                    <h3>{current.name}</h3>
                    <p className="muted">
                      {current.artist}
                      {current.album ? ` · ${current.album}` : ""}
                    </p>
                  </div>
                </div>
                <div className="player-controls">
                  <button
                    className="play-toggle"
                    onClick={() => void player?.toggle()}
                    aria-label={player?.playing ? "暂停" : "播放"}
                  >
                    {player?.playing ? <Pause size={18} /> : <Play size={18} />}
                  </button>
                  <div className="player-timeline">
                    <input
                      type="range"
                      className="player-range"
                      min={0}
                      max={Math.max(1, Math.floor(progress.duration || 0))}
                      value={Math.min(
                        Math.floor(progress.current),
                        Math.max(1, Math.floor(progress.duration || 0)),
                      )}
                      onChange={(event) =>
                        player?.seek(Number(event.target.value))
                      }
                      aria-label="播放进度"
                      style={{ "--played": `${percent}%` } as CSSProperties}
                    />
                    <div className="player-times">
                      <small>{clock(progress.current)}</small>
                      <small>
                        {progress.duration ? clock(progress.duration) : "--:--"}
                      </small>
                    </div>
                  </div>
                </div>
                <div className="player-volume">
                  <Volume2 size={13} />
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={Math.round((player?.volume ?? 0.8) * 100)}
                    onChange={(event) =>
                      player?.setVolume(Number(event.target.value) / 100)
                    }
                    aria-label="音量"
                    style={
                      {
                        "--played": `${Math.round((player?.volume ?? 0.8) * 100)}%`,
                      } as CSSProperties
                    }
                  />
                </div>
                {lyric && (
                  <details className="lyric-box">
                    <summary>歌词</summary>
                    <pre>{lyric}</pre>
                  </details>
                )}
              </>
            ) : (
              <p className="muted">
                还没放歌。选一首，房间会安静地开始有声音。
              </p>
            )}
          </section>

          <section className="music-panel mood-card">
            <div className="panel-label">
              <Waves size={14} />
              此刻的氛围
            </div>
            {mood ? (
              <>
                <div className="mood-head">
                  <strong className={`mood-label ${moodTone(mood.label)}`}>
                    {mood.label}
                  </strong>
                  <small>{mood.tracks} 首近期播放</small>
                </div>
                <div className="mood-visual">
                  <div className="mood-plot" aria-hidden="true">
                    <span className="plot-label tl">怒</span>
                    <span className="plot-label tr">乐</span>
                    <span className="plot-label bl">哀</span>
                    <span className="plot-label br">喜</span>
                    <i
                      style={{
                        left: `${((mood.valence + 1) / 2) * 100}%`,
                        top: `${(1 - mood.energy) * 100}%`,
                      }}
                    />
                  </div>
                  <div className="mood-meters">
                    <div>
                      <span>愉悦</span>
                      <div className="mood-bar">
                        <i
                          style={{
                            width: `${Math.round(((mood.valence + 1) / 2) * 100)}%`,
                          }}
                        />
                      </div>
                    </div>
                    <div>
                      <span>能量</span>
                      <div className="mood-bar">
                        <i
                          style={{ width: `${Math.round(mood.energy * 100)}%` }}
                        />
                      </div>
                    </div>
                    <div>
                      <span>强度</span>
                      <div className="mood-bar">
                        <i
                          style={{
                            width: `${Math.round(mood.intensity * 100)}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
                <label className="mood-toggle">
                  <input
                    type="checkbox"
                    checked={mood.influence}
                    onChange={() => void toggleInfluence()}
                  />
                  让音乐影响 Xinxin 的语气
                </label>
                {!mood.influence && (
                  <p className="field-help">
                    已关闭：只记录播放，不改变人格提示。
                  </p>
                )}
                {plays.length > 0 && (
                  <>
                    <div className="mood-history-label">
                      最近播放
                      <button
                        className="text-button"
                        onClick={() => void clearMood()}
                      >
                        <Trash2 size={13} />
                        清空
                      </button>
                    </div>
                    <ul className="mood-history">
                      {plays.slice(0, 8).map((play, index) => (
                        <li key={`${play.track_id}-${play.created}-${index}`}>
                          <span
                            className={`emotion-dot ${moodTone(play.label)}`}
                          />
                          <span className="mood-history-name">{play.name}</span>
                          <small>{minutesAgo(play.created)}</small>
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </>
            ) : (
              <Loading />
            )}
            <p className="field-help music-source-note">
              <CloudOff size={12} /> 音乐数据来自 GD 音乐台（music.gdstudio.xyz），
              仅供个人学习使用；音频与封面由原平台 CDN 提供，不下载、不转存。
            </p>
          </section>
        </aside>
      </div>
    </div>
  );
}
