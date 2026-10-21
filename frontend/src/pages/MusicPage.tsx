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
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  CornerDownLeft,
  Heart,
  ListMusic,
  Music2,
  Pause,
  Play,
  Plus,
  Search,
  Trash2,
  Volume2,
  X,
} from "lucide-react";
import { api, post, put, remove } from "../api";
import { Dialog, Loading, useToast } from "../ui";
import { useMusicPlayer, type PlayerTrack } from "../musicPlayer";

type Emotion = {
  valence: number;
  energy: number;
  label: string;
  moods?: string[];
  confidence?: number;
  hits?: string[];
  reason?: string;
  source?: string;
};
type Track = PlayerTrack & { emotion?: Emotion; favorited?: boolean };
type Mood = {
  label: string;
  valence: number;
  energy: number;
  intensity: number;
  tracks: number;
  moods: Array<{ mood: string; share: number }>;
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
type Playlist = { id: string; name: string; tracks: number; updated: number };

const SOURCES = [
  ["netease", "网易云"],
  ["kuwo", "酷我"],
  ["joox", "JOOX"],
  ["tencent", "QQ 音乐"],
] as const;

const MOOD_PHRASE: Record<string, string> = {
  喜: "安静的愉悦",
  乐: "明亮的兴奋",
  怒: "绷紧的强烈",
  哀: "低回的安静",
  平静: "没什么起伏",
};

function tone(label: string) {
  return (
    { 喜: "tone-joy", 乐: "tone-bright", 怒: "tone-intense", 哀: "tone-low" }[
      label
    ] || "tone-neutral"
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

function Equalizer() {
  return (
    <span className="equalizer" aria-hidden="true">
      <i />
      <i />
      <i />
    </span>
  );
}

function trackKey(track: { id: string; source: string }) {
  return `${track.source}:${track.id}`;
}

export default function MusicPage() {
  const toast = useToast();
  const player = useMusicPlayer();
  const [query, setQuery] = useState(""),
    [source, setSource] = useState<string>("netease"),
    [tracks, setTracks] = useState<Track[] | null>(null),
    [searching, setSearching] = useState(false),
    [calibrating, setCalibrating] = useState(false),
    [pending, setPending] = useState(""),
    [mood, setMood] = useState<Mood | null>(null),
    [plays, setPlays] = useState<Play[]>([]),
    [lyric, setLyric] = useState(""),
    [view, setView] = useState<"search" | "favorites" | "playlists">("search"),
    [favorites, setFavorites] = useState<Track[]>([]),
    [playlists, setPlaylists] = useState<Playlist[]>([]),
    [openList, setOpenList] = useState<{ id: string; name: string } | null>(null),
    [listTracks, setListTracks] = useState<Track[]>([]),
    [addingTrack, setAddingTrack] = useState<Track | null>(null),
    [creating, setCreating] = useState(false),
    [newName, setNewName] = useState(""),
    [fallback, setFallback] = useState(false),
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

  const loadLibrary = useCallback(async () => {
    try {
      const [favorite, lists] = await Promise.all([
        api<{ favorites: Track[] }>("/music/favorites"),
        api<{ playlists: Playlist[] }>("/music/playlists"),
      ]);
      setFavorites(favorite.favorites);
      setPlaylists(lists.playlists);
    } catch {
      // 收藏/歌单读取失败不影响播放
    }
  }, []);

  useEffect(() => {
    void loadMood();
    void loadLibrary();
  }, [loadMood, loadLibrary]);

  useEffect(() => {
    const refresh = () => void loadMood();
    window.addEventListener("xinxin:music-played", refresh);
    return () => window.removeEventListener("xinxin:music-played", refresh);
  }, [loadMood]);

  // 词表只给保守估计；检索后异步让模型按歌曲本身校准，结果写进后端缓存。
  const calibrate = useCallback(async (list: Track[]) => {
    if (!list.length) return;
    setCalibrating(true);
    try {
      const result = await post<{ emotions: Record<string, Emotion> }>(
        "/music/score",
        {
          tracks: list.map(({ id, source: src, name, artist, album }) => ({
            id,
            source: src,
            name,
            artist,
            album,
          })),
        },
      );
      setTracks((current) =>
        current
          ? current.map((track) => {
              const found = result.emotions[trackKey(track)];
              return found ? { ...track, emotion: { ...track.emotion, ...found } } : track;
            })
          : current,
      );
    } catch {
      // 模型不可用时保留词表结果，不打断播放
    } finally {
      setCalibrating(false);
    }
  }, []);

  const runSearch = useCallback(
    async (text: string, src: string) => {
      setSearching(true);
      try {
        const result = await api<{ tracks: Track[]; fallback?: boolean }>(
          `/music/search?q=${encodeURIComponent(text)}&source=${src}`,
        );
        setTracks(result.tracks);
        setFallback(Boolean(result.fallback));
        if (!result.tracks.length) toast("没有搜到，换个关键词或音源试试");
        else void calibrate(result.tracks);
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
    [calibrate, toast],
  );

  async function search(event?: FormEvent) {
    event?.preventDefault();
    if (!query.trim() || searching) return;
    setPending("");
    setView("search");
    await runSearch(query.trim(), source);
  }

  // /music?q=… 直达一次检索；否则恢复上次搜过的关键词。
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

  async function play(track: Track, list?: Track[]) {
    if (!player) return;
    const key = trackKey(track);
    if (player.track?.id === track.id && player.track?.source === track.source) {
      await player.toggle();
      return;
    }
    setPending(key);
    try {
      await player.play(track, list);
    } finally {
      setPending("");
    }
  }

  async function toggleFavorite(track: Track) {
    const key = trackKey(track);
    const favorited = favorites.some((item) => trackKey(item) === key);
    try {
      if (favorited) {
        await remove(`/music/favorites?key=${encodeURIComponent(key)}`);
        setFavorites((current) => current.filter((item) => trackKey(item) !== key));
      } else {
        await post("/music/favorites", {
          id: track.id,
          source: track.source,
          name: track.name,
          artist: track.artist,
          album: track.album,
          cover: "",
        });
        setFavorites((current) => [{ ...track, favorited: true }, ...current]);
      }
      setTracks((current) =>
        current
          ? current.map((item) =>
              trackKey(item) === key ? { ...item, favorited: !favorited } : item,
            )
          : current,
      );
    } catch (error) {
      toast((error as Error).message, true);
    }
  }

  async function addToPlaylist(playlist: Playlist) {
    if (!addingTrack) return;
    try {
      const result = await post<{ added: boolean; reason?: string }>(
        `/music/playlists/${playlist.id}/tracks`,
        {
          id: addingTrack.id,
          source: addingTrack.source,
          name: addingTrack.name,
          artist: addingTrack.artist,
          album: addingTrack.album,
          cover: "",
        },
      );
      toast(
        result.added ? `已加入「${playlist.name}」` : result.reason || "已经在歌单里了",
      );
      setAddingTrack(null);
      void loadLibrary();
    } catch (error) {
      toast((error as Error).message, true);
    }
  }

  async function createPlaylist(event: FormEvent) {
    event.preventDefault();
    if (!newName.trim()) return;
    try {
      const created = await post<{ playlist: Playlist }>("/music/playlists", {
        name: newName.trim(),
      });
      setCreating(false);
      setNewName("");
      void loadLibrary();
      toast(`歌单「${created.playlist.name}」建好了`);
    } catch (error) {
      toast((error as Error).message, true);
    }
  }

  async function openPlaylist(playlist: Playlist) {
    try {
      const result = await api<{
        playlist: { id: string; name: string };
        tracks: Track[];
      }>(`/music/playlists/${playlist.id}`);
      setOpenList(result.playlist);
      setListTracks(result.tracks);
    } catch (error) {
      toast((error as Error).message, true);
    }
  }

  async function removeFromPlaylist(track: Track) {
    if (!openList) return;
    try {
      await remove(
        `/music/playlists/${openList.id}/tracks?key=${encodeURIComponent(trackKey(track))}`,
      );
      setListTracks((current) =>
        current.filter((item) => trackKey(item) !== trackKey(track)),
      );
      void loadLibrary();
    } catch (error) {
      toast((error as Error).message, true);
    }
  }

  async function dropPlaylist(playlist: Playlist) {
    if (!window.confirm(`删掉歌单「${playlist.name}」？`)) return;
    try {
      await remove(`/music/playlists/${playlist.id}`);
      if (openList?.id === playlist.id) {
        setOpenList(null);
        setListTracks([]);
      }
      void loadLibrary();
    } catch (error) {
      toast((error as Error).message, true);
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
  const active = Boolean(mood && mood.intensity > 0);
  const favoriteKeys = new Set(favorites.map((track) => trackKey(track)));

  function TrackList({
    list,
    empty,
    queue,
  }: {
    list: Track[];
    empty: React.ReactNode;
    queue?: Track[];
  }) {
    if (!list.length) return <div className="index-empty">{empty}</div>;
    return (
      <ol className={`track-index${searching ? " is-loading" : ""}`}>
        {list.map((track, index) => {
          const key = trackKey(track);
          const liked = favoriteKeys.has(key);
          return (
            <li key={key} className="track-item">
              <button
                className={`track-row${isCurrent(track) ? " active" : ""}`}
                onClick={() => void play(track, queue)}
                aria-current={isCurrent(track) || undefined}
              >
                <span className="track-ordinal">
                  {pending === key ? (
                    <span className="track-loading" />
                  ) : isCurrent(track) && player?.playing ? (
                    <Equalizer />
                  ) : (
                    String(index + 1).padStart(2, "0")
                  )}
                </span>
                <span className="track-title">
                  <strong>{track.name}</strong>
                  <small>
                    {track.artist}
                    {track.album ? ` · ${track.album}` : ""}
                  </small>
                </span>
                <span className="track-tags">
                  {track.emotion?.moods?.slice(0, 2).map((word) => (
                    <span key={word} className="mood-word">
                      {word}
                    </span>
                  ))}
                  {track.emotion && (
                    <span
                      className={`emotion-word ${tone(track.emotion.label)}`}
                      title={
                        track.emotion.reason ||
                        (track.emotion.hits?.length
                          ? `命中：${track.emotion.hits.join("、")}`
                          : "还没有校准，按中性处理")
                      }
                    >
                      {track.emotion.label}
                    </span>
                  )}
                </span>
              </button>
              <div className="row-actions">
                <button
                  className={`row-icon${liked ? " liked" : ""}`}
                  aria-label={liked ? "取消收藏" : "收藏"}
                  onClick={() => void toggleFavorite(track)}
                >
                  <Heart size={13} fill={liked ? "currentColor" : "none"} />
                </button>
                <button
                  className="row-icon"
                  aria-label="加入歌单"
                  onClick={() => setAddingTrack(track)}
                >
                  <Plus size={14} />
                </button>
              </div>
            </li>
          );
        })}
      </ol>
    );
  }

  return (
    <div className="page-enter listening">
      <header className="listening-head">
        <p className="eyebrow">AMBIENT LISTENING</p>
        <div className="listening-title">
          <h1>背景音乐</h1>
          <span className={`listening-state${player?.playing ? " live" : ""}`}>
            <i />
            {current ? (player?.playing ? "正在播放" : "已暂停") : "等待第一首"}
          </span>
        </div>
        <p className="lead">
          放一首歌，房间就有了底噪。音乐只改变 Xinxin 的语气，不影响它做事。
        </p>
      </header>

      <div className="listening-body">
        <section className="listening-index" aria-label="曲目检索">
          <div className="library-tabs" role="tablist">
            <button
              role="tab"
              aria-selected={view === "search"}
              className={view === "search" ? "active" : ""}
              onClick={() => {
                setView("search");
                setOpenList(null);
              }}
            >
              <Search size={13} />
              搜索
            </button>
            <button
              role="tab"
              aria-selected={view === "favorites"}
              className={view === "favorites" ? "active" : ""}
              onClick={() => {
                setView("favorites");
                setOpenList(null);
              }}
            >
              <Heart size={13} />
              收藏
              {favorites.length > 0 && <i>{favorites.length}</i>}
            </button>
            <button
              role="tab"
              aria-selected={view === "playlists"}
              className={view === "playlists" ? "active" : ""}
              onClick={() => {
                setView("playlists");
                setOpenList(null);
              }}
            >
              <ListMusic size={13} />
              歌单
              {playlists.length > 0 && <i>{playlists.length}</i>}
            </button>
          </div>

          {view === "search" && (
            <>
              <form className="search-line" onSubmit={search} role="search">
                <Search size={19} strokeWidth={1.5} />
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="搜一首歌、一张专辑，或者一个歌手"
                  aria-label="搜索音乐"
                />
                {query ? (
                  <button
                    type="button"
                    className="search-clear"
                    onClick={() => {
                      setQuery("");
                      setTracks(null);
                    }}
                    aria-label="清空搜索"
                  >
                    <X size={14} />
                  </button>
                ) : (
                  <span className="search-hint" aria-hidden="true">
                    <CornerDownLeft size={12} />
                  </span>
                )}
              </form>

              {fallback && (
                <p className="source-note">
                  GD 音乐台暂时不可用，已切到网易云直连；酷我 / QQ / JOOX 要等它恢复。
                </p>
              )}

              {fallback && (
                <p className="source-note">
                  GD 音乐台暂时不可用，已切到网易云直连；酷我 / QQ / JOOX 要等它恢复。
                </p>
              )}

              <div className="source-tabs" role="tablist" aria-label="音乐源">
                {SOURCES.map(([value, label]) => (
                  <button
                    key={value}
                    type="button"
                    role="tab"
                    aria-selected={source === value}
                    className={source === value ? "active" : ""}
                    onClick={() => setSource(value)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </>
          )}

          {view === "playlists" && openList ? (
            <>
              <div className="list-head">
                <button className="back-link" onClick={() => setOpenList(null)}>
                  <ChevronLeft size={15} />
                  全部歌单
                </button>
                <button
                  className="button secondary small"
                  disabled={!listTracks.length}
                  onClick={() => player?.playQueue(listTracks, 0)}
                >
                  <Play size={13} />
                  播放全部
                </button>
              </div>
              <div className="index-head">
                <span>{openList.name}</span>
                <span>{listTracks.length} 首</span>
              </div>
              <TrackList
                list={listTracks}
                queue={listTracks}
                empty={<p>这个歌单还是空的。去搜几首，点「+」放进来。</p>}
              />
              {listTracks.length > 0 && (
                <div className="list-foot">
                  {listTracks.map((track) => (
                    <button
                      key={trackKey(track)}
                      className="saved-remove"
                      onClick={() => void removeFromPlaylist(track)}
                    >
                      <X size={11} />
                      {track.name}
                    </button>
                  ))}
                </div>
              )}
            </>
          ) : view === "playlists" ? (
            <>
              <div className="index-head">
                <span>歌单</span>
                <button className="link-quiet" onClick={() => setCreating(true)}>
                  <Plus size={12} />
                  新建
                </button>
              </div>
              {playlists.length === 0 ? (
                <div className="index-empty">
                  <ListMusic size={22} strokeWidth={1.1} />
                  <p>还没有歌单。建一个「深夜」「通勤」这样的清单，把喜欢的歌攒起来。</p>
                </div>
              ) : (
                <ul className="playlist-list">
                  {playlists.map((playlist) => (
                    <li key={playlist.id}>
                      <button
                        className="playlist-row"
                        onClick={() => void openPlaylist(playlist)}
                      >
                        <span className="playlist-icon">
                          <ListMusic size={15} />
                        </span>
                        <span className="playlist-meta">
                          <strong>{playlist.name}</strong>
                          <small>{playlist.tracks} 首</small>
                        </span>
                        <ChevronRight size={14} className="playlist-arrow" />
                      </button>
                      <button
                        className="row-icon"
                        aria-label="删除歌单"
                        onClick={() => void dropPlaylist(playlist)}
                      >
                        <Trash2 size={13} />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </>
          ) : view === "favorites" ? (
            <>
              <div className="index-head">
                <span>收藏</span>
                <span>{favorites.length} 首</span>
              </div>
              <TrackList
                list={favorites}
                queue={favorites}
                empty={<p>还没有收藏。在搜索结果里点歌名右边的心，就会留在这里。</p>}
              />
              {favorites.length > 0 && (
                <button
                  className="button secondary small saved-play"
                  onClick={() => player?.playQueue(favorites, 0)}
                >
                  <Play size={13} />
                  播放全部
                </button>
              )}
            </>
          ) : (
            <>
              <div className="index-head">
                <span>曲目</span>
                <span>
                  {searching
                    ? "检索中"
                    : calibrating
                      ? "校准情绪中"
                      : tracks
                        ? `${tracks.length} 首`
                        : "按回车开始"}
                </span>
              </div>
              {tracks === null ? (
                <div className="index-empty">
                  <Music2 size={22} strokeWidth={1.1} />
                  <p>
                    还没有检索。每首歌会按标题与专辑的词义给出一个情绪指数，
                    最近播放的整体倾向，决定此刻房间的氛围。
                  </p>
                </div>
              ) : (
                <TrackList
                  list={tracks}
                  queue={tracks}
                  empty={<p>没有结果。换个关键词，或者切到酷我 / JOOX 再试。</p>}
                />
              )}
            </>
          )}
        </section>

        <aside className="listening-room">
          <section className={`sleeve${player?.playing ? " is-playing" : ""}`}>
            <div className={`sleeve-art${player?.cover ? " has-cover" : ""}`}>
              <span className="sleeve-vinyl" aria-hidden="true">
                <span className="vinyl-label">
                  <b>{(current?.name || "X").slice(0, 1)}</b>
                  <i>XINXIN · AMBIENT</i>
                </span>
              </span>
              {player?.cover && (
                <img
                  src={player.cover}
                  alt=""
                  referrerPolicy="no-referrer"
                  loading="lazy"
                />
              )}
            </div>

            {current ? (
              <>
                <div className="sleeve-meta">
                  <p className="sleeve-kicker">
                    {player?.playing ? "NOW PLAYING" : "PAUSED"}
                  </p>
                  <h2>{current.name}</h2>
                  <p className="sleeve-artist">
                    {current.artist}
                    {current.album ? ` — ${current.album}` : ""}
                  </p>
                </div>

                <div className="transport">
                  <button
                    className="transport-play"
                    onClick={() => void player?.toggle()}
                    aria-label={player?.playing ? "暂停" : "播放"}
                  >
                    {player?.playing ? (
                      <Pause size={16} fill="currentColor" />
                    ) : (
                      <Play size={16} fill="currentColor" />
                    )}
                  </button>
                  <div className="transport-time">
                    <small>{clock(progress.current)}</small>
                    <small>
                      {progress.duration ? clock(progress.duration) : "--:--"}
                    </small>
                  </div>
                </div>

                <input
                  type="range"
                  className="seek"
                  min={0}
                  max={Math.max(1, Math.floor(progress.duration || 0))}
                  value={Math.min(
                    Math.floor(progress.current),
                    Math.max(1, Math.floor(progress.duration || 0)),
                  )}
                  onChange={(event) => player?.seek(Number(event.target.value))}
                  aria-label="播放进度"
                  style={{ "--played": `${percent}%` } as CSSProperties}
                />

                <div className="sleeve-foot">
                  <label className="volume">
                    <Volume2 size={13} strokeWidth={1.6} />
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
                  </label>
                  {current.lyric_id && lyric && (
                    <details className="lyric">
                      <summary>歌词</summary>
                      <pre>{lyric}</pre>
                    </details>
                  )}
                </div>
              </>
            ) : (
              <div className="sleeve-empty">
                <p>还没放歌。</p>
                <p className="muted">从左边挑一首，封面和唱片会在这里展开。</p>
              </div>
            )}
          </section>

          <section className="mood-plate">
            <div className="mood-plate-head">
              <span className="plate-label">此刻的氛围</span>
              {plays.length > 0 && (
                <button className="link-quiet" onClick={() => void clearMood()}>
                  <Trash2 size={12} />
                  清空
                </button>
              )}
            </div>

            {mood ? (
              <>
                <div className="mood-summary">
                  <strong className={`mood-word ${tone(mood.label)}`}>
                    {mood.label}
                  </strong>
                  <span>
                    {active
                      ? `${MOOD_PHRASE[mood.label] ?? "没什么起伏"} · 强度 ${mood.intensity.toFixed(2)}`
                      : "还没有播放记录"}
                  </span>
                </div>

                {mood.moods.length > 0 && (
                  <div className="mood-words">
                    {mood.moods.map((item) => (
                      <span key={item.mood}>
                        {item.mood}
                        <i>{Math.round(item.share * 100)}%</i>
                      </span>
                    ))}
                  </div>
                )}

                <div className="compass" aria-hidden="true">
                  <span className="compass-axis x" />
                  <span className="compass-axis y" />
                  <span className="compass-label tl">怒</span>
                  <span className="compass-label tr">乐</span>
                  <span className="compass-label bl">哀</span>
                  <span className="compass-label br">喜</span>
                  <span
                    className={`compass-dot${active ? "" : " idle"}`}
                    style={
                      {
                        left: `${((mood.valence + 1) / 2) * 100}%`,
                        top: `${(1 - mood.energy) * 100}%`,
                        "--halo": `${4 + Math.round(mood.intensity * 9)}px`,
                      } as CSSProperties
                    }
                  />
                </div>

                <button
                  role="switch"
                  aria-checked={mood.influence}
                  className={`switch${mood.influence ? " on" : ""}`}
                  onClick={() => void toggleInfluence()}
                >
                  <span className="switch-track" aria-hidden="true">
                    <i />
                  </span>
                  <span>让音乐影响 Xinxin 的语气</span>
                </button>

                {plays.length > 0 && (
                  <ul className="history">
                    {plays.slice(0, 5).map((play, index) => (
                      <li key={`${play.track_id}-${play.created}-${index}`}>
                        <i className={`history-dot ${tone(play.label)}`} />
                        <span>{play.name}</span>
                        <small>{minutesAgo(play.created)}</small>
                      </li>
                    ))}
                  </ul>
                )}
              </>
            ) : (
              <Loading />
            )}

            <p className="plate-note">
              音乐数据来自 GD 音乐台（music.gdstudio.xyz），仅供个人学习使用；
              音频与封面由原平台 CDN 提供，不下载、不转存。
              <a
                href="https://music.gdstudio.xyz"
                target="_blank"
                rel="noreferrer noopener"
              >
                访问原站 <ArrowUpRight size={11} />
              </a>
            </p>
          </section>
        </aside>
      </div>

      {addingTrack && (
        <Dialog
          title={`把《${addingTrack.name}》加入`}
          onClose={() => setAddingTrack(null)}
        >
          <div className="stack">
            {playlists.length === 0 && <p className="hint">还没有歌单，先建一个。</p>}
            {playlists.map((playlist) => (
              <button
                key={playlist.id}
                className="picker-row"
                onClick={() => void addToPlaylist(playlist)}
              >
                <ListMusic size={14} />
                <span>{playlist.name}</span>
                <small>{playlist.tracks} 首</small>
              </button>
            ))}
            <button
              className="button secondary"
              onClick={() => {
                setAddingTrack(null);
                setCreating(true);
              }}
            >
              <Plus size={14} />
              新建歌单
            </button>
          </div>
        </Dialog>
      )}

      {creating && (
        <Dialog title="新建歌单" onClose={() => setCreating(false)}>
          <form className="stack" onSubmit={createPlaylist}>
            <label className="field">
              <span>名字</span>
              <input
                value={newName}
                onChange={(event) => setNewName(event.target.value)}
                placeholder="深夜 / 通勤 / 写代码"
                maxLength={30}
                autoFocus
              />
            </label>
            <div className="dialog-actions">
              <button
                type="button"
                className="button ghost"
                onClick={() => setCreating(false)}
              >
                取消
              </button>
              <button className="button primary" disabled={!newName.trim()}>
                建好
              </button>
            </div>
          </form>
        </Dialog>
      )}
    </div>
  );
}
