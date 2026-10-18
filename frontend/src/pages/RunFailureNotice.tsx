import { PanelRightOpen, RotateCcw, SlidersHorizontal } from "lucide-react";
import type { Run } from "../api";

function tokenLimit(run: Run): number | undefined {
  return (
    run.max_total_tokens ??
    (run.error?.startsWith("任务达到模型调用或 token") ? 50000 : undefined)
  );
}

export function failureReason(run: Run): string {
  if (run.error?.startsWith("任务达到模型调用或 token")) {
    try {
      const usage = JSON.parse(run.usage || "{}");
      const limit = tokenLimit(run) ?? usage.max_total_tokens;
      if (limit > 0 && usage.total_tokens >= limit)
        return `本轮累计令牌达到预算（${usage.total_tokens}/${limit}）。可调整预算后继续，前轮工具记录会用于续接。`;
    } catch {
      // Legacy rows may not have parseable usage; keep the actual error below.
    }
  }
  return run.error || "任务未完成，请查看过程中的工具记录。";
}

export function budgetStopped(run: Run) {
  return /达到预算|达到模型调用|工具调用预算|本轮累计令牌达到/.test(
    run.error || "",
  );
}

export default function RunFailureNotice({
  run,
  onContinue,
  onOptions,
  onTrace,
  continuing = false,
  disabled = false,
}: {
  run: Run;
  onContinue: () => void;
  onOptions: () => void;
  onTrace: () => void;
  continuing?: boolean;
  disabled?: boolean;
}) {
  return (
    <div className="conversation-recovery" role="alert">
      <div className="recovery-reason">
        <strong>
          {budgetStopped(run)
            ? "本轮预算已用完，原任务仍然保留"
            : "本轮尚未完成"}
        </strong>
        <p>{failureReason(run)}</p>
        <small>
          本轮预算：{run.max_calls ?? "—"} 次模型调用 ·{" "}
          {tokenLimit(run)?.toLocaleString() ?? "由服务端决定"} 令牌 ·{" "}
          {run.max_seconds ?? "—"} 秒
        </small>
        <p className="field-help">
          点击继续会直接开启新一轮预算，恢复原任务、附件和执行记录。沿用下方选定的权限和目标；输入框的补充要求会一并发送。
        </p>
      </div>
      <div className="recovery-actions">
        <button className="text-button" onClick={onTrace}>
          <PanelRightOpen size={14} />
          查看过程
        </button>
        <button className="text-button" onClick={onOptions}>
          <SlidersHorizontal size={14} />
          调整预算
        </button>
        <button
          className="text-button"
          onClick={onContinue}
          disabled={continuing || disabled}
        >
          <RotateCcw size={14} />
          {continuing ? "正在续接…" : "继续原任务"}
        </button>
      </div>
    </div>
  );
}
