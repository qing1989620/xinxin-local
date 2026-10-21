import { useState } from "react";
import { api, type EventItem, type Run } from "../api";
import AgentActivity from "./AgentActivity";
import SkillNetTrace from "./SkillNetTrace";

export default function HistoricalActivity({ run }: { run: Run }) {
  const [events, setEvents] = useState<EventItem[] | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  async function load() {
    if (events || loading) return;
    setLoading(true);
    setError("");
    try {
      setEvents(await api<EventItem[]>(`/runs/${run.id}/activity`));
    } catch (issue) {
      setError((issue as Error).message);
    } finally {
      setLoading(false);
    }
  }
  return (
    <>
      <SkillNetTrace run={run} />
      <details
        className="historical-activity"
        onToggle={(event) => {
          if (event.currentTarget.open) void load();
        }}
      >
        <summary>查看这轮执行过程与中间进度</summary>
        {loading && <p role="status">正在读取已保存的过程…</p>}
        {error && (
          <p role="alert">
            {error}
            <button className="text-button" onClick={() => void load()}>
              重试
            </button>
          </p>
        )}
        {events && (
          <AgentActivity run={run} events={events} showSkills={false} />
        )}
      </details>
    </>
  );
}
