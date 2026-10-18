---
name: "webapp-testing"
description: "网页应用测试：Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend 。"
---

# webapp-testing

> 领域：技能工程　|　来源：member-import（Nexus skills/webapp-testing）　|　代际：G0

## 能力契约 / Capability

Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend functionality, debugging UI behavior, capturing browser screenshots, and viewing browser logs.

**输入**：本地 Web 应用地址或代码

**输出**：浏览器自动化测试结果；截图与问题清单

**适用时机**：
- 需要用 Playwright 与本地 Web 应用交互、验证功能、调试 UI 或截图时触发

## 执行步骤

1. scripts/withserver.py - Manages server lifecycle (supports multiple servers)
2. Navigate and wait for networkidle
3. Take screenshot or inspect DOM
4. Identify selectors from rendered state
5. Execute actions with discovered selectors

## 常见陷阱

- ❌ Don't inspect the DOM before waiting for networkidle on dynamic apps
- ✅ Do wait for page.waitforloadstate('networkidle') before inspection

## 验证清单

- [ ] 产出物已按原文「验证」章节要求自查（原文未提供结构化清单）

## 标签

`Web 测试` `浏览器自动化` `Playwright`

## 质量评估

| 维度 | 评级 |
| --- | --- |
| safety | Good |
| completeness | Average |
| executability | Good |
| maintainability | Average |
| cost_awareness | Average |

## 关联技能

- `compose_with` → `web-artifacts-builder`

> 说明：本技能由开发组成员项目（Nexus）导入，契约字段依据原文提炼；
> 领域划分与关系边由本项目补充。深度改写请以原文 SKILL.md 为准。
