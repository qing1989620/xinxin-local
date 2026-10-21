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
  const busy = useRef(false);
  const [track, setTrack] = useState<PlayerTrack | null>(null);
  const [queue, setQueue] = useState<PlayerTrack[]>([]);
  const queueRef = useRef<PlayerTrack[]>([]);
  // 悬停就把播放地址取回来：点击时同步换 src，保留"用户手势"，避免自动播放被拦
  const urlCache = useRef(new Map<string, string>());
  const positionRef = useRef(0);
  const [cover, setCover] = useState("");
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState({ current: 0, duration: 0 });
  const [volume, setVolumeState] = useState(() => {
    const stored = localStorage.getItem("xinxin-volume");
    // 没存过时 Number(null) 会得到 0，直接当成静音；先区分"没设置"。
    const saved = stored === null ? Number.NaN : Number(stored);
    return Number.isFinite(saved) && saved >= 0 && saved <= 1 ? saved : 0.8;
  });

  useEffect(() => {
    if (audio.current) audio.current.volume = volume;
    localStorage.setItem("xinxin-volume", String(volume));
  }, [volume]);

  const setVolume = useCallback((value: number) => {
    setVolumeState(Math.max(0, Math.min(1, value)));
  }, []);

  const seek = useCallback((seconds: number) => {
    const element = audio.current;
    if (!element || !Number.isFinite(element.duration)) return;
    element.currentTime = Math.max(0, Math.min(seconds, element.duration));
    setProgress({
      current: element.currentTime,
      duration: element.duration || 0,
    });
  }, []);

  const toggle = useCallback(async () => {
    const element = audio.current;
    if (!element) return;
    if (element.paused) {
      try {
        await element.play();
      } catch {
        toast("浏览器阻止了播放，再点一次播放键", true);
      }
    } else element.pause();
  }, [toast]);

  const prefetch = useCallback((track: PlayerTrack) => {
    const key = `${track.source}:${track.id}`;
    if (urlCache.current.has(key)) return;
    void api<{ url: string }>(
      `/music/url?id=${encodeURIComponent(track.id)}&source=${track.source}`,
    )
      .then((value) => {
        if (value.url) urlCache.current.set(key, value.url);
      })
      .catch(() => {
        // 预取失败不影响点击后的正常流程
      });
  }, []);

  const play = useCallback(
    async (next: PlayerTrack, list?: PlayerTrack[]) => {
      const key = `${next.source}:${next.id}`;
      if (busy.current) return;
      if (active.current === key && audio.current?.src) {
        void toggle();
        return;
      }
      busy.current = true;
      setLoading(true);
      const cachedUrl = urlCache.current.get(key);
      if (list && list.length) {
        queueRef.current = list;
        positionRef.current = Math.max(
          0,
          list.findIndex((item) => item.id === next.id && item.source === next.source),
        );
        setQueue(list);
      } else if (!queueRef.current.length) {
        queueRef.current = [next];
        positionRef.current = 0;
        setQueue([next]);
      }
      try {
        const result = cachedUrl
          ? { url: cachedUrl }
          : await api<{ url: string }>(
              `/music/url?id=${encodeURIComponent(next.id)}&source=${next.source}`,
            );
        if (!cachedUrl && result.url) urlCache.current.set(key, result.url);
        active.current = key;
        setTrack(next);
        setCover("");
        setProgress({ current: 0, duration: 0 });
        if (audio.current) {
          audio.current.src = result.url;
          try {
            await audio.current.play();
          } catch (error) {
            // 自动播放被拦时保持暂停状态，等用户点播放键。
            const name = (error as DOMException)?.name;
            if (name === "NotAllowedError") {
              toast("浏览器要求先点一下播放键，再继续", true);
            } else {
              toast("这首暂时播不了，换一首试试", true);
            }
          }
        }
        void post("/music/play", {
          id: next.id,
          source: next.source,
          name: next.name,
          artist: next.artist,
          album: next.album,
        })
          .then(() =>
            window.dispatchEvent(new CustomEvent("xinxin:music-played")),
          )
          .catch(() => {});
        if (next.pic_id) {
          void api<{ url: string }>(
            `/music/pic?id=${encodeURIComponent(next.pic_id)}&source=${next.source}`,
          )
            .then((value) => {
              if (value.url) setCover(value.url);
            })
            .catch(() => {});
        }
      } catch (failure) {
        toast((failure as Error).message, true);
      } finally {
        busy.current = false;
        setLoading(false);
      }
    },
    [toggle, toast],
  );

  const next = useCallback(() => {
    const list = queueRef.current;
    if (positionRef.current + 1 >= list.length) return;
    positionRef.current += 1;
    void play(list[positionRef.current], list);
  }, [play]);

  const prev = useCallback(() => {
    const list = queueRef.current;
    if (positionRef.current <= 0) return;
    positionRef.current -= 1;
    void play(list[positionRef.current], list);
  }, [play]);

  const playQueue = useCallback(
    (list: PlayerTrack[], start = 0) => {
      if (!list.length) return;
      const index = Math.max(0, Math.min(start, list.length - 1));
      queueRef.current = list;
      positionRef.current = index;
      setQueue(list);
      void play(list[index], list);
    },
    [play],
  );

  const stop = useCallback(() => {
    audio.current?.pause();
    if (audio.current) audio.current.removeAttribute("src");
    active.current = "";
    setTrack(null);
    queueRef.current = [];
    positionRef.current = 0;
    setQueue([]);
    setCover("");
    setPlaying(false);
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
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => {
          setPlaying(false);
          next();
        }}
        onTimeUpdate={(event) =>
          setProgress({
            current: event.currentTarget.currentTime,
            duration: event.currentTarget.duration || 0,
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
            <img src={cover} alt="" referrerPolicy="no-referrer" loading="lazy" />
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
