import {
  createContext,
  useCallback,
  useContext,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useLocation } from "react-router-dom";
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
  cover: string;
  playing: boolean;
  loading: boolean;
  progress: { current: number; duration: number };
  play: (track: PlayerTrack) => Promise<void>;
  toggle: () => Promise<void>;
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
  const [cover, setCover] = useState("");
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState({ current: 0, duration: 0 });

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

  const play = useCallback(
    async (next: PlayerTrack) => {
      const key = `${next.source}:${next.id}`;
      if (busy.current) return;
      if (active.current === key && audio.current?.src) {
        void toggle();
        return;
      }
      busy.current = true;
      setLoading(true);
      try {
        const result = await api<{ url: string }>(
          `/music/url?id=${encodeURIComponent(next.id)}&source=${next.source}`,
        );
        active.current = key;
        setTrack(next);
        setCover("");
        setProgress({ current: 0, duration: 0 });
        if (audio.current) {
          audio.current.src = result.url;
          try {
            await audio.current.play();
          } catch {
            // 自动播放被拦时保持暂停状态，等用户点播放键。
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

  const stop = useCallback(() => {
    audio.current?.pause();
    if (audio.current) audio.current.removeAttribute("src");
    active.current = "";
    setTrack(null);
    setCover("");
    setPlaying(false);
    setProgress({ current: 0, duration: 0 });
  }, []);

  return (
    <Context.Provider
      value={{ track, cover, playing, loading, progress, play, toggle, stop }}
    >
      {children}
      <audio
        ref={audio}
        preload="none"
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => setPlaying(false)}
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
  if (!player?.track || location.pathname === "/music") return null;
  const { track, cover, playing, toggle, stop } = player;
  return (
    <div className="mini-player" role="region" aria-label="背景音乐">
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
    </div>
  );
}
