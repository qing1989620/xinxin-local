---
name: "mcp-builder"
description: "MCP 服务构建器：Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with externa。"
---

# mcp-builder

> 领域：技能工程　|　来源：member-import（Nexus skills/mcp-builder）　|　代际：G0

## 能力契约 / Capability

Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP) or Node/TypeScript (MCP SDK).

**输入**：外部服务/API 的能力边界说明；认证与调用方式

**输出**：MCP 服务端实现；工具定义与测试

**适用时机**：
- 需要创建高质量 MCP（Model Context Protocol）服务器，让 LLM 对接外部服务时触发

## 执行步骤

1. Specification overview and architecture
2. Transport mechanisms (streamable HTTP, stdio)
3. Tool, resource, and prompt definitions
4. MCP Best Practices: [📋 View Best Practices](./reference/mcpbestpractices.md) - Core guidelines
5. TypeScript SDK: Use WebFetch to load https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md
6. [⚡ TypeScript Guide](./reference/nodemcpserver.md) - TypeScript patterns and examples

## 常见陷阱

- 导入时未从原文提取到显式陷阱条目，执行前请复核原文正文

## 验证清单

- [ ] 产出物已按原文「验证」章节要求自查（原文未提供结构化清单）

## 标签

`MCP` `工具集成` `服务端`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Good |
| executability | Good |
| maintainability | Basic |
| cost_awareness | Average |

## 关联技能

- `compose_with` → `claude-api`

> 说明：本技能由开发组成员项目（Nexus）导入，契约字段依据原文提炼；
> 领域划分与关系边由本项目补充。深度改写请以原文 SKILL.md 为准。
