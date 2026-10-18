---
name: "claude-api"
description: "Claude 接口参考：Reference for the Claude API / Anthropic SDK — model ids, pricing, params, streaming, tool use, MCP, agents, c。"
---

# claude-api

> 领域：技能工程　|　来源：member-import（Nexus skills/claude-api）　|　代际：G0

## 能力契约 / Capability

Reference for the Claude API / Anthropic SDK — model ids, pricing, params, streaming, tool use, MCP, agents, caching, token counting, model migration. TRIGGER — read BEFORE opening the target file; don't skip because it "looks like a one-liner" — whenever: the prompt names Claude/Anthropic in any fo

**输入**：待接入的模型调用需求

**输出**：正确的接口调用参数与代码

**适用时机**：
- 涉及 Claude API / Anthropic SDK 开发——模型选择、定价、参数、流式、工具调用、缓存等参考查询时触发

## 执行步骤

1. The official Anthropic SDK for the project's language (anthropic, @anthropic-ai/sdk, com.anthropic., etc.). This is the default whenever a supported SDK exists for the project
2. Raw HTTP (curl, requests, fetch, httpx, etc.) - only when the user explicitly asks for cURL/REST/raw HTTP, the project is a shell/cURL project, or the language has no official SDK
3. Look at project files to infer the language:
4. .py, requirements.txt, pyproject.toml, setup.py, Pipfile -> Python - read from python/
5. .ts, .tsx, package.json, tsconfig.json -> TypeScript - read from typescript/

## 常见陷阱

- The {lang}/ files in this skill are authoritative over recalled patterns

## 验证清单

- [ ] 产出物已按原文「验证」章节要求自查（原文未提供结构化清单）

## 标签

`API` `模型调用` `参数` `版本漂移`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Good |
| maintainability | Basic |
| cost_awareness | Average |

## 关联技能

- `similar_to` → `mcp-builder`

> 说明：本技能由开发组成员项目（Nexus）导入，契约字段依据原文提炼；
> 领域划分与关系边由本项目补充。深度改写请以原文 SKILL.md 为准。
