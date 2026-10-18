import { api, post, stableRequestKey, type Run } from "./api";

export type AgentSettings = {
  model: string;
  model_configured: boolean;
  context_window_tokens?: number;
  context_tiers?: { label: string; tokens: number }[];
  execution_defaults?: {
    max_calls: number;
    max_seconds: number;
    max_total_tokens: number;
  };
  execution_limits?: {
    max_calls: number;
    max_seconds: number;
    max_total_tokens: number;
  };
  capabilities?: {
    run_token_budget?: boolean;
    run_recovery?: boolean;
    command_progress?: boolean;
    context_checkpoints?: boolean;
    conversation_delete?: boolean;
    context_tiers?: boolean;
    public_progress?: boolean;
    run_continuation?: boolean;
    conversation_batch_delete?: boolean;
  };
};

export type RunSubmission = {
  task: string;
  conversation_id: string | null;
  permission: string;
  server_id: string | null;
  max_calls: number;
  max_seconds: number;
  max_total_tokens?: number;
  context_window_tokens?: number;
  allow_memory: boolean;
  file_ids: string[];
  resume_run_id?: string;
};

export async function submitAgentRun(payload: RunSubmission): Promise<Run> {
  const settings = await api<AgentSettings>("/settings");
  if (payload.resume_run_id && !settings.capabilities?.run_continuation)
    throw new Error("当前后端不支持一键续接，请更新后端后重试。");
  if (
    payload.context_window_tokens !== undefined &&
    !settings.capabilities?.context_tiers
  )
    throw new Error("当前后端不支持会话上下文档位，请刷新连接或更新后端。");
  const limits = settings.execution_limits || {
    max_calls: 20,
    max_seconds: 1800,
    max_total_tokens: 1000000,
  };
  if (
    payload.max_calls > limits.max_calls ||
    payload.max_seconds > limits.max_seconds ||
    (payload.max_total_tokens !== undefined &&
      payload.max_total_tokens > limits.max_total_tokens)
  )
    throw new Error(
      "执行预算超过当前后端支持范围，请刷新连接或更新后端后再提交。",
    );
  if (
    payload.max_total_tokens !== undefined &&
    !settings.capabilities?.run_token_budget
  )
    throw new Error(
      "当前后端不支持自定义令牌预算，请刷新连接或更新后端后再提交。",
    );
  const request_key = await stableRequestKey("agent", payload);
  if (payload.resume_run_id) {
    const {
      resume_run_id,
      conversation_id: _conversation,
      task,
      ...execution
    } = payload;
    return post<Run>(`/runs/${resume_run_id}/continue`, {
      ...execution,
      instruction: task,
      request_key,
    });
  }
  return post<Run>("/runs", { ...payload, request_key });
}
