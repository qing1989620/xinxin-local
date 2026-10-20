import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import {
  CloudOff,
  Disc3,
  Music2,
  Pause,
  Play,
  Search,
  Trash2,
  Waves,
} from "lucide-react";
import { api, post, put, remove } from "../api";
import { Empty, Loading, PageHeader, useToast } from "../ui";

type Emotion = {
  valence: number;
  energy: number;
  label: string;
  confidence: number;
  hits: string[];
};
type Track = {
  id: string;
  name: string;
  artist: string;
  album: string;
  pic_id: string;
  lyric_id: string;
  source: string;
  emotion: Emotion;
};
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
  return { 喜: "calm-joy", 乐: "bright", 怒: "intense", 哀: "low", 平静: "neutral" }[
    label
  ] || "neutral";
}

function minutesAgo(created: number) {
  const minutes = Math.max(0, Math.round((Date.now() / 1000 - created) / 60));
  if (minutes < 1) return "刚刚";
  if (minutes < 60) return `${minutes} 分钟前`;
  return `${Math.round(minutes / 60)} 小时前`;
}

export default function MusicPage() {
  const toast = useToast();
  const [query, setQuery] = useState(""),
    [source, setSource] = useState<string>("netease"),
    [tracks, setTracks] = useState<Track[] | null>(null),
    [busy, setBusy] = useState(false),
    [current, setCurrent] = useState<Track | null>(null),
    [stream, setStream] = useState(""),
    [playing, setPlaying] = useState(false),
    [loadingTrack, setLoadingTrack] = useState(""),
    [mood, setMood] = useState<Mood | null>(null),
    [plays, setPlays] = useState<Play[]>([]),
    [progress, setProgress] = useState({ current: 0, duration: 0 }),
    [lyric, setLyric] = useState("");
  const audio = useRef<HTMLAudioElement>(null),
    logged = useRef(""),
    [params, setParams] = useSearchParams();

  const loadMood = useCallback(async () => {
    try {
      const result = await api<{ mood: Mood; plays: Play[] }>("/music/mood");
      setMood(result.mood);
      setPlays(result.plays);
    } catch {
      // 氛围读取失败不阻断播放；下次操作会重试。
    }
  }, []);
  useEffect(() => {
    void loadMood();
  }, [loadMood]);

  // /music?q=… 直达一次检索（便于分享，也方便从别处跳进来）。
  useEffect(() => {
    const wanted = params.get("q");
    if (!wanted) return;
    setQuery(wanted);
    void api<{ tracks: Track[] }>(
      `/music/search?q=${encodeURIComponent(wanted)}&source=${params.get("source") || "netease"}`,
    )
      .then((result) => setTracks(result.tracks))
      .catch((failure) => toast((failure as Error).message, true));
    setParams(
      (previous) => {
        const next = new URLSearchParams(previous);
        next.delete("q");
        return next;
      },
      { replace: true },
    );
  }, [params]);

  async function search(event?: FormEvent) {
    event?.preventDefault();
    if (!query.trim()) return;
    setBusy(true);
    try {
      const result = await api<{ tracks: Track[] }>(
        `/music/search?q=${encodeURIComponent(query.trim())}&source=${source}`,
      );
      setTracks(result.tracks);
      if (!result.tracks.length) toast("没有搜到，换个关键词或音源试试");
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      setBusy(false);
    }
  }

  async function play(track: Track) {
    if (loadingTrack) return;
    // 同一首歌再次点击：不重新取链，直接续播 / 暂停。
    if (current?.id === track.id && stream) {
      void toggle();
      return;
    }
    setLoadingTrack(track.id);
    setLyric("");
    try {
      const result = await api<{ url: string }>(
        `/music/url?id=${encodeURIComponent(track.id)}&source=${track.source}`,
      );
      setCurrent(track);
      setStream(result.url);
      if (logged.current !== track.id) {
        logged.current = track.id;
        const result = await post<{ mood: Mood }>("/music/play", {
          id: track.id,
          source: track.source,
          name: track.name,
          artist: track.artist,
          album: track.album,
        });
        setMood(result.mood);
        void loadMood();
      }
      if (track.lyric_id) {
        void api<{ lyric: string; tlyric: string }>(
          `/music/lyric?id=${encodeURIComponent(track.lyric_id)}&source=${track.source}`,
        )
          .then((value) => setLyric(value.tlyric || value.lyric || ""))
          .catch(() => setLyric(""));
      }
    } catch (error) {
      toast((error as Error).message, true);
    } finally {
      setLoadingTrack("");
    }
  }

  useEffect(() => {
    if (!stream || !audio.current) return;
    audio.current.src = stream;
    void audio.current.play().catch(() => setPlaying(false));
  }, [stream]);

  async function toggle() {
    const element = audio.current;
    if (!element) return;
    if (element.paused) {
      await element.play().catch(() => toast("浏览器阻止了自动播放，点一下播放键", true));
    } else element.pause();
  }

  async function clearMood() {
    try {
      const result = await remove<{ mood: Mood }>("/music/mood");
      setMood(result.mood);
      setPlays([]);
      logged.current = "";
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

  return (
    <div className="page-enter">
      <PageHeader
        overline="AMBIENT LISTENING"
        title="背景音乐"
        description="放一首，房间的氛围会跟着变——Xinxin 的语气也会。音频直接从音乐平台 CDN 播放，不经过这台机器。"
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
            <button className="button secondary" disabled={busy}>
              {busy ? "搜索中…" : "搜索"}
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
            <ul className="track-list">
              {tracks.map((track) => (
                <li
                  key={`${track.source}-${track.id}`}
                  className={current?.id === track.id ? "active" : ""}
                >
                  <button
                    className="track-play"
                    onClick={() => void play(track)}
                    aria-label={`播放 ${track.name}`}
                  >
                    {loadingTrack === track.id ? (
                      <span className="track-loading" />
                    ) : current?.id === track.id && playing ? (
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
                <h3>{current.name}</h3>
                <p className="muted">
                  {current.artist}
                  {current.album ? ` · ${current.album}` : ""}
                </p>
                <div className="player-controls">
                  <button
                    className="play-toggle"
                    onClick={() => void toggle()}
                    aria-label={playing ? "暂停" : "播放"}
                  >
                    {playing ? <Pause size={18} /> : <Play size={18} />}
                  </button>
                  <div className="player-track">
                    <div
                      className="player-progress"
                      style={{
                        width: `${
                          progress.duration
                            ? Math.min(100, (progress.current / progress.duration) * 100)
                            : 0
                        }%`,
                      }}
                    />
                  </div>
                  <small>
                    {Math.floor(progress.current / 60)}:
                    {String(Math.floor(progress.current % 60)).padStart(2, "0")}
                  </small>
                </div>
                <audio
                  ref={audio}
                  onPlay={() => setPlaying(true)}
                  onPause={() => setPlaying(false)}
                  onEnded={() => setPlaying(false)}
                  onTimeUpdate={(event) =>
                    setProgress({
                      current: event.currentTarget.currentTime,
                      duration: event.currentTarget.duration || 0,
                    })
                  }
                  preload="none"
                />
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
                      <i style={{ width: `${Math.round(mood.energy * 100)}%` }} />
                    </div>
                  </div>
                  <div>
                    <span>强度</span>
                    <div className="mood-bar">
                      <i style={{ width: `${Math.round(mood.intensity * 100)}%` }} />
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
                      <button className="text-button" onClick={() => void clearMood()}>
                        <Trash2 size={13} />
                        清空
                      </button>
                    </div>
                    <ul className="mood-history">
                      {plays.slice(0, 8).map((play, index) => (
                        <li key={`${play.track_id}-${play.created}-${index}`}>
                          <span className={`emotion-dot ${moodTone(play.label)}`} />
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
              仅供个人学习使用；音频由原平台 CDN 提供，不下载、不转存。
            </p>
          </section>
        </aside>
      </div>
    </div>
  );
}
