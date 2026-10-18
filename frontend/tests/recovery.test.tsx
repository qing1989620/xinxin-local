import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import RunFailureNotice, {
  failureReason,
  budgetStopped,
} from "../src/pages/RunFailureNotice";
import MemoryGrant from "../src/pages/MemoryGrant";
import AgentActivity, { activityEvents } from "../src/pages/AgentActivity";
import type { EventItem, Run } from "../src/api";

const run = {
  status: "failed",
  permission: "full",
  max_calls: 8,
  max_seconds: 300,
  max_total_tokens: 50000,
  usage: JSON.stringify({ total_tokens: 55701 }),
  error: "任务达到模型调用或 token [redacted]",
} as Run;

describe("failed task recovery", () => {
  it("keeps public progress visible with the newest terminal snapshot and actual step statuses", () => {
    const events = [
      {
        seq: 1,
        kind: "assistant.progress",
        data: { text: "依赖已经检查，开始构建。" },
      },
      {
        seq: 2,
        kind: "command.progress",
        data: {
          command_id: "one",
          name: "run_remote_command",
          elapsed_seconds: 1,
          output: "old output",
        },
      },
      {
        seq: 3,
        kind: "command.progress",
        data: {
          command_id: "one",
          name: "run_remote_command",
          elapsed_seconds: 3,
          output: "STEP_ONE\n<img src=x onerror=bad()>",
        },
      },
      {
        seq: 4,
        kind: "plan.updated",
        data: {
          steps: [{ id: "build", title: "构建项目", status: "in_progress" }],
        },
      },
    ] as EventItem[];
    const html = renderToStaticMarkup(
      <AgentActivity run={{ ...run, status: "cancelling" }} events={events} />,
    );
    expect(activityEvents(events).map((event) => event.seq)).toEqual([1, 3, 4]);
    expect(html).toContain("依赖已经检查");
    expect(html).toContain("STEP_ONE");
    expect(html).toContain("构建项目");
    expect(html).toContain("正在结束命令");
    expect(html).not.toContain("old output");
    expect(html).not.toContain("<img");
  });
  it("knows the legacy fixed limit even before the backend schema is upgraded", () => {
    expect(failureReason({ ...run, max_total_tokens: undefined })).toContain(
      "55701/50000",
    );
  });
  it("explains the legacy hidden budget without claiming permissions are missing", () => {
    expect(failureReason(run)).toContain("55701/50000");
    const html = renderToStaticMarkup(
      <RunFailureNotice
        run={run}
        onContinue={() => {}}
        onOptions={() => {}}
        onTrace={() => {}}
      />,
    );
    expect(html).toContain('role="alert"');
    expect(html).toContain("调整预算");
    expect(html).toContain("查看过程");
    expect(html).toContain("继续原任务");
    expect(html).not.toContain("调整权限");
  });
  it("shows the actual tool error and escapes provider markup", () => {
    const error = "SSH连接失败 <img src=x onerror=alert(1)>";
    const html = renderToStaticMarkup(
      <RunFailureNotice
        run={{ ...run, error }}
        onContinue={() => {}}
        onOptions={() => {}}
        onTrace={() => {}}
      />,
    );
    expect(html).toContain("SSH连接失败");
    expect(html).toContain("&lt;img");
    expect(html).not.toContain("<img");
    expect(failureReason({ ...run, usage: "invalid" })).toBe(run.error);
  });
  it("shows readable progress and only the newest waiting notice with folded terminal details", () => {
    const events = [
      {
        seq: 1,
        kind: "progress.note",
        data: { text: "已完成仓库检查，接下来安装依赖。", source: "agent" },
      },
      {
        seq: 2,
        kind: "progress.wait",
        data: { command_id: "one", text: "old waiting", finished: false },
      },
      {
        seq: 3,
        kind: "progress.wait",
        data: {
          command_id: "one",
          text: "已运行50秒；没有新输出，暂时无法判断原因。",
          finished: false,
        },
      },
      {
        seq: 4,
        kind: "command.progress",
        data: {
          command_id: "one",
          output: "dependency logs",
          elapsed_seconds: 50,
        },
      },
    ] as EventItem[];
    const html = renderToStaticMarkup(
      <AgentActivity run={{ ...run, status: "running" }} events={events} />,
    );
    expect(html).toContain("已完成仓库检查");
    expect(html).toContain("没有新输出");
    expect(html).not.toContain("old waiting");
    expect(html).toContain('<details class="activity-terminal">');
    expect(html).not.toContain("<details open");
    expect(
      activityEvents([
        ...events,
        {
          seq: 5,
          kind: "progress.wait",
          data: { command_id: "one", finished: true },
        } as EventItem,
      ]).some((event) => event.kind === "progress.wait"),
    ).toBe(false);
  });
  it("explains budget continuation and disables repeated submissions while sending", () => {
    expect(
      budgetStopped({ ...run, error: "本轮模型调用次数达到预算（1/1）" }),
    ).toBe(true);
    const html = renderToStaticMarkup(
      <RunFailureNotice
        run={run}
        continuing
        onContinue={() => {}}
        onOptions={() => {}}
        onTrace={() => {}}
      />,
    );
    expect(html).toContain("原任务仍然保留");
    expect(html).toContain("直接开启新一轮预算");
    expect(html).toContain("正在续接");
    expect(html).toContain("disabled");
  });
  it("makes memory consent actionable from read-only mode with the permission change explained", () => {
    const html = renderToStaticMarkup(
      <MemoryGrant
        permission="read"
        checked={false}
        disabled={false}
        onChange={() => {}}
      />,
    );
    expect(html).toContain("勾选时将本轮权限切换为工作区");
    expect(html).toContain("不包含系统命令执行");
    expect(html).not.toContain("disabled");
  });
});
