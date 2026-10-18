from __future__ import annotations

import json
from urllib.parse import urlsplit

import httpx

from .config import DEFAULT_MODEL_CALLS, TOKENS_PER_MODEL_CALL, CONTEXT_WINDOW_TOKENS
from .context import token_count
from .store import encode


class ModelBudgetExceeded(RuntimeError):
    def __init__(self, kind, used, limit):
        self.kind, self.used, self.limit = kind, used, limit
        label = "模型调用次数" if kind == "calls" else "累计令牌"
        super().__init__(
            f"本轮{label}达到预算（{used}/{limit}），尚未形成最终答复；"
            "可点“继续原任务”使用新一轮预算续接，已执行的工具记录会保留。"
        )


def endpoint(value):
    parsed = urlsplit(value)
    if (
        parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or not parsed.hostname
    ):
        raise ValueError("服务地址不能含凭据或查询参数")
    if parsed.scheme != "https" and not (
        parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    ):
        raise ValueError("远程模型服务必须使用 HTTPS")
    return value.rstrip("/")


class ModelGateway:
    """Tina-compatible LLM transport with durable usage accounting and bounded calls."""

    def __init__(
        self,
        url,
        model,
        key,
        record_usage,
        cancelled,
        max_calls=DEFAULT_MODEL_CALLS,
        max_tokens=None,
        transport=None,
        context_window_tokens=CONTEXT_WINDOW_TOKENS,
    ):
        self.url, self.model, self.key = endpoint(url), model, key
        self.record_usage, self.cancelled = record_usage, cancelled
        self.max_calls = max_calls
        self.max_tokens = (
            max_tokens if max_tokens is not None else max_calls * TOKENS_PER_MODEL_CALL
        )
        self.calls, self.tokens = 0, 0
        self.request_tokens = 0
        self.transport = transport
        self.context_tokens = 0
        self.context_window_tokens = context_window_tokens

    async def apredict(self, messages, tools=None, stream=False, **kwargs):
        if self.cancelled.is_set():
            raise RuntimeError("任务已取消")
        self.check_budget()
        self.calls += 1
        self.request_tokens = 0
        self.record_usage(self.usage())
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "max_tokens": min(16384, self.max_tokens - self.tokens),
            "temperature": 0.5,
            "thinking": {"type": "disabled"},
        }
        if tools:
            payload["tools"] = tools
        self.context_tokens = token_count(encode(payload)) + 1024
        if self.context_tokens + payload["max_tokens"] > self.context_window_tokens:
            raise RuntimeError("本次请求超过当前会话的上下文档位；完整历史仍保存在对话，请提高档位、压缩或分批处理。")
        self.record_usage(self.usage())
        if stream:
            payload["stream_options"] = {"include_usage": True}
            return self._stream(payload)
        async with httpx.AsyncClient(
            timeout=120, transport=self.transport, follow_redirects=False
        ) as client:
            response = await client.post(
                self.url, json=payload, headers={"Authorization": "Bearer " + self.key}
            )
            self._check(response)
            data = response.json()
            self._usage(data)
            return data["choices"][0]["message"]

    @staticmethod
    def _check(response):
        if response.status_code >= 300:
            messages = {
                401: "模型密钥无效",
                402: "模型账户余额不足",
                429: "模型服务限流，请稍后重试",
            }
            raise RuntimeError(
                messages.get(
                    response.status_code, f"模型服务返回异常状态 {response.status_code}"
                )
            )

    def _usage(self, data):
        usage = data.get("usage")
        if usage:
            total = int(usage.get("total_tokens", 0))
            self.tokens += max(0, total - self.request_tokens)
            self.request_tokens = max(self.request_tokens, total)
            self.record_usage(
                {
                    **self.usage(),
                    "prompt_tokens_last": usage.get("prompt_tokens", 0),
                    "completion_tokens_last": usage.get("completion_tokens", 0),
                }
            )

    def usage(self):
        return {
            "calls": self.calls,
            "total_tokens": self.tokens,
            "max_calls": self.max_calls,
            "max_total_tokens": self.max_tokens,
            "context_window_tokens": self.context_window_tokens,
            "context_tokens_estimate": self.context_tokens,
        }

    def check_budget(self):
        if self.calls >= self.max_calls:
            raise ModelBudgetExceeded("calls", self.calls, self.max_calls)
        if self.tokens >= self.max_tokens:
            raise ModelBudgetExceeded("tokens", self.tokens, self.max_tokens)

    async def _stream(self, payload):
        calls = {}
        finish = None
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(120, connect=15),
            transport=self.transport,
            follow_redirects=False,
        ) as client:
            async with client.stream(
                "POST",
                self.url,
                json=payload,
                headers={"Authorization": "Bearer " + self.key},
            ) as response:
                self._check(response)
                async for line in response.aiter_lines():
                    if self.cancelled.is_set():
                        raise RuntimeError("任务已取消")
                    if not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if raw == "[DONE]":
                        break
                    data = json.loads(raw)
                    self._usage(data)
                    if not data.get("choices"):
                        continue
                    choice = data["choices"][0]
                    finish = choice.get("finish_reason") or finish
                    delta = choice.get("delta") or {}
                    if delta.get("content"):
                        yield {"role": "assistant", "content": delta["content"]}
                    for fragment in delta.get("tool_calls") or []:
                        idx = fragment["index"]
                        if idx not in calls:
                            if len(calls) >= 8:
                                raise RuntimeError("模型在一轮请求中过多工具调用")
                            calls[idx] = {
                                "id": fragment.get("id", ""),
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                            }
                        call = calls[idx]
                        if fragment.get("id"):
                            call["id"] = fragment["id"]
                        for key in ("name", "arguments"):
                            call["function"][key] += (
                                fragment.get("function") or {}
                            ).get(key, "")
                        if len(call["function"]["arguments"]) > 64000:
                            raise RuntimeError("工具参数超出长度限制")
        if finish not in {"stop", "tool_calls"}:
            raise RuntimeError("模型输出未完整结束：" + str(finish or "连接中断"))
        if calls:
            if not all(
                call["id"] and call["function"]["name"] for call in calls.values()
            ):
                raise RuntimeError("模型返回不完整的工具调用")
            yield {
                "id": "tools-complete",
                "content": "",
                "tool_calls": [calls[i] for i in sorted(calls)],
            }
