import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Music2, Pause, Play, X } from "lucide-react";
import { api, post } from "./api";
import { useToast } from "./ui";

export type PlayerTrack = {
  id: string;
  name: string;
  artist: string;
  album: string;
  source: string;
  pic_id?: string;
  lyric_id?: string;
  emotion?: { label: string };
};

type Player = {
  track: PlayerTrack | null;
  queue: PlayerTrack[];
  cover: string;
  playing: boolean;
  loading: boolean;
  progress: { current: number; duration: number };
  volume: number;
  play: (track: PlayerTrack, list?: PlayerTrack[]) => Promise<void>;
  prefetch: (track: PlayerTrack) => void;
  playQueue: (list: PlayerTrack[], start?: number) => void;
  next: () => void;
  prev: () => void;
  hasNext: boolean;
  toggle: () => Promise<void>;
  seek: (seconds: number) => void;
  setVolume: (value: number) => void;
  stop: () => void;
};

const Context = createContext<Player | null>(null);

/** 全局播放器：放在 App 外层，切页/关页面都不中断（后台音乐）。 */
export function MusicPlayerProvider({ children }: { children: ReactNode }) {
  const toast = useToast();
  const audio = useRef<HTMLAudioElement | null>(null);
  const active = useRef("");
  const request = useRef(0);
  const playingTrack = useRef<PlayerTrack | null>(null);
  const recorded = useRef(false);
  const [track, setTrack] = useState<PlayerTrack | null>(null);
  const [queue, setQueue] = useState<PlayerTrack[]>([]);
  const queueRef = useRef<PlayerTrack[]>([]);
  // 悬停就把播放地址取回来：点击时同步换 src，保留"用户手势"，避免自动播放被拦
  const urlCache = useRef(new Map<string, { url: string; expires: number }>());
  const urlRequests = useRef(new Map<string, Promise<{ url: string }>>());
  const positionRef = useRef(0);
  const [cover, setCover] = useState("");
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState({ current: 0, duration: 0 });
  const [volume, setVolumeState] = useState(() => {
    let stored: string | null = null;
    try {
      stored = localStorage.getItem("xinxin-volume");
    } catch {
      /* 可选偏好 */
    }
    // 没存过时 Number(null) 会得到 0，直接当成静音；先区分"没设置"。
    const saved = stored === null ? Number.NaN : Number(stored);
    return Number.isFinite(saved) && saved >= 0 && saved <= 1 ? saved : 0.8;
  });

  useEffect(() => {
    if (audio.current) audio.current.volume = volume;
    try {
      localStorage.setItem("xinxin-volume", String(volume));
    } catch {
      /* 可选偏好 */
    }
  }, [volume]);

  const setVolume = useCallback((value: number) => {
    if (Number.isFinite(value)) setVolumeState(Math.max(0, Math.min(1, value)));
  }, []);

  const seek = useCallback((seconds: number) => {
    const element = audio.current;
    if (
      !element ||
      !Number.isFinite(seconds) ||
      !Number.isFinite(element.duration)
    )
      return;
    element.currentTime = Math.max(0, Math.min(seconds, element.duration));
    setProgress({
      current: element.currentTime,
      duration: element.duration || 0,
    });
  }, []);

  const toggle = useCallback(async () => {
    // 暂停/恢复是新的播放意图，也要取消尚未返回的换歌请求。
    const generation = ++request.current;
    setLoading(false);
    const element = audio.current;
    if (!element) return;
    if (element.paused) {
      try {
        await element.play();
      } catch {
        if (generation === request.current)
          toast("浏览器阻止了播放，再点一次播放键", true);
      }
    } else element.pause();
  }, [toast]);

  const resolveUrl = useCallback((track: PlayerTrack) => {
    const key = `${track.source}:${track.id}`;
    const pending = urlRequests.current.get(key);
    if (pending) return pending;
    const promise = api<{ url: string }>(
      `/music/url?id=${encodeURIComponent(track.id)}&source=${track.source}`,
    )
      .then((value) => {
        if (!value.url) throw new Error("这首暂时没有可用的播放地址");
        if (urlCache.current.size >= 100) {
          const oldest = urlCache.current.keys().next().value;
          if (oldest) urlCache.current.delete(oldest);
        }
        urlCache.current.set(key, {
          url: value.url,
          expires: Date.now() + 180_000,
        });
        return value;
      })
      .finally(() => {
        urlRequests.current.delete(key);
      });
    urlRequests.current.set(key, promise);
    return promise;
  }, []);

  const prefetch = useCallback(
    (track: PlayerTrack) => {
      const cached = urlCache.current.get(`${track.source}:${track.id}`);
      if (cached && cached.expires > Date.now()) return;
      void resolveUrl(track).catch(() => {
        /* 预取失败后点击仍可重试。 */
      });
    },
    [resolveUrl],
  );

  const play = useCallback(
    async (next: PlayerTrack, list?: PlayerTrack[], ensurePlaying = false) => {
      const key = `${next.source}:${next.id}`;
      const generation = ++request.current;
      const updateQueue = () => {
        const existing = queueRef.current;
        const selected = list?.length
          ? list
          : existing.some(
                (item) => item.id === next.id && item.source === next.source,
              )
            ? existing
            : [next];
        queueRef.current = selected;
        positionRef.current = Math.max(
          0,
          selected.findIndex(
            (item) => item.id === next.id && item.source === next.source,
          ),
        );
        setQueue(selected);
      };
      if (active.current === key && audio.current?.src) {
        updateQueue();
        setLoading(false);
        if (!ensurePlaying || audio.current.paused) await toggle();
        return;
      }
      setLoading(true);
      const cached = urlCache.current.get(key);
      const cachedUrl = cached && cached.expires > Date.now() ? cached.url : "";
      try {
        const result = cachedUrl ? { url: cachedUrl } : await resolveUrl(next);
        if (generation !== request.current) return;
        updateQueue();
        active.current = key;
        playingTrack.current = next;
        recorded.current = false;
        setTrack(next);
        setCover("");
        setPlaying(false);
        setProgress({ current: 0, duration: 0 });
        if (audio.current) {
          audio.current.src = result.url;
          try {
            await audio.current.play();
          } catch (error) {
            if (generation !== request.current) return;
            const name = (error as DOMException)?.name;
            if (name === "NotAllowedError") {
              // 自动播放被拦时保持暂停状态，等用户点播放键。
              toast("浏览器要求先点一下播放键，再继续", true);
            } else if (cachedUrl) {
              // 预取的地址可能过期，丢掉重取一次再试
              urlCache.current.delete(key);
              try {
                const fresh = await resolveUrl(next);
                if (generation === request.current && audio.current) {
                  audio.current.src = fresh.url;
                  await audio.current.play();
                }
              } catch {
                if (generation === request.current)
                  toast("这首暂时播不了，换一首试试", true);
              }
            } else {
              toast("这首暂时播不了，换一首试试", true);
            }
          }
        }
        if (next.pic_id) {
          void api<{ url: string }>(
            `/music/pic?id=${encodeURIComponent(next.pic_id)}&source=${next.source}`,
          )
            .then((value) => {
              if (active.current === key && value.url) setCover(value.url);
            })
            .catch(() => {});
        }
      } catch (failure) {
        if (generation === request.current)
          toast((failure as Error).message, true);
      } finally {
        if (generation === request.current) setLoading(false);
      }
    },
    [toggle, toast, resolveUrl],
  );

  const next = useCallback(() => {
    const list = queueRef.current;
    if (positionRef.current + 1 >= list.length) return;
    void play(list[positionRef.current + 1], list);
  }, [play]);

  const prev = useCallback(() => {
    const list = queueRef.current;
    if (positionRef.current <= 0) return;
    void play(list[positionRef.current - 1], list);
  }, [play]);

  const playQueue = useCallback(
    (list: PlayerTrack[], start = 0) => {
      if (!list.length) return;
      const index = Math.max(0, Math.min(start, list.length - 1));
      void play(list[index], list, true);
    },
    [play],
  );

  const stop = useCallback(() => {
    request.current += 1;
    playingTrack.current = null;
    recorded.current = false;
    audio.current?.pause();
    if (audio.current) audio.current.removeAttribute("src");
    active.current = "";
    setTrack(null);
    queueRef.current = [];
    positionRef.current = 0;
    setQueue([]);
    setCover("");
    setPlaying(false);
    setLoading(false);
    setProgress({ current: 0, duration: 0 });
  }, []);

  return (
    <Context.Provider
      value={{
        track,
        queue,
        cover,
        playing,
        loading,
        progress,
        volume,
        play,
        prefetch,
        playQueue,
        next,
        prev,
        hasNext: queue.length > 0 && positionRef.current + 1 < queue.length,
        toggle,
        seek,
        setVolume,
        stop,
      }}
    >
      {children}
      <audio
        ref={audio}
        preload="none"
        onPlaying={() => {
          setPlaying(true);
          const current = playingTrack.current;
          if (!current || recorded.current) return;
          recorded.current = true;
          void post("/music/play", {
            id: current.id,
            source: current.source,
            name: current.name,
            artist: current.artist,
            album: current.album,
          })
            .then(() =>
              window.dispatchEvent(new CustomEvent("xinxin:music-played")),
            )
            .catch(() => {});
        }}
        onPause={() => setPlaying(false)}
        onEnded={() => {
          setPlaying(false);
          next();
        }}
        onTimeUpdate={(event) =>
          setProgress({
            current: event.currentTarget.currentTime,
            duration: Number.isFinite(event.currentTarget.duration)
              ? event.currentTarget.duration
              : 0,
          })
        }
        onError={() => setPlaying(false)}
      />
    </Context.Provider>
  );
}

export function useMusicPlayer() {
  return useContext(Context);
}

/** 非音乐页常驻的小播放条；离开 /music 后音乐继续，这里给出控制入口。 */
export function MiniPlayer() {
  const player = useMusicPlayer();
  const location = useLocation();
  const navigate = useNavigate();
  if (!player?.track) return null;
  const onMusicPage = location.pathname === "/music";
  const { track, cover, playing, toggle, stop, progress } = player;
  const percent = progress.duration
    ? Math.min(100, (progress.current / progress.duration) * 100)
    : 0;
  return (
    <div
      className={`mini-player${onMusicPage ? " on-music" : ""}`}
      role="region"
      aria-label="背景音乐"
    >
      <button
        className="mini-open"
        onClick={() => navigate("/music")}
        aria-label="打开背景音乐页"
        aria-current={onMusicPage ? "page" : undefined}
      >
        <span className="mini-cover">
          {cover ? (
            <img
              src={cover}
              alt=""
              referrerPolicy="no-referrer"
              loading="lazy"
            />
          ) : (
            <Music2 size={15} />
          )}
        </span>
        <span className="mini-meta">
          <strong>{track.name}</strong>
          <small>{track.artist}</small>
        </span>
      </button>
      <button
        className="mini-toggle"
        onClick={() => void toggle()}
        aria-label={playing ? "暂停背景音乐" : "继续播放背景音乐"}
      >
        {playing ? <Pause size={14} /> : <Play size={14} />}
      </button>
      <button className="mini-close" onClick={stop} aria-label="停止背景音乐">
        <X size={13} />
      </button>
      <span className="mini-progress" style={{ width: `${percent}%` }} />
    </div>
  );
}
