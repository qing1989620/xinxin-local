# 最终真实学习链路：独立双轴审查

依据仓库指定的 [mattpocock code-review](https://github.com/mattpocock/skills/blob/49dd158d1076134a641b33efb035946536778336/skills/engineering/code-review/SKILL.md)，通过两个独立审查代理分别执行 Standards 与 Spec。未向其他服务发送私有资料，两位审查者不调用真实模型或访问主人数据库。

固定基线 `250e6fa9f615c152aeca51a86334ac8cfc9f8e78`，初审头 `49fb4a4d8686e756cf0640c257e834d684c240e1`，修复复审头 `81cdea3ee08819cd7af5f6ae143d241e562c8355`，最终兼容补丁头 `11e10c363c9a87649a697386320b5a19d66159ea`。各阶段比较前确认基线可解析且 diff 非空。

```text
git diff 250e6fa...49fb4a4
git diff 250e6fa...81cdea3
git diff 49fb4a4...81cdea3
git diff 81cdea3...11e10c3
```

提交：`49fb4a4 fix(learning): reason through solutions and audit every proof step`；`81cdea3 fix(learning): close TeX shorthand conflicts and preserve local startup`。需求：[真实验收合同](../specs/2026-10-23-learning-live-acceptance.md)。规范来源为根/两侧 AGENTS、两侧审查计划及适用架构约束；根约定覆盖陈旧的分仓语句。Standards 使用技能规定的完整 12 项 Fowler 启发，区分文档硬规则和判断，不重复工具格式检查。

## Standards

初审全部 19 个变更文件，硬违反 0、可确认且需要行动的 Fowler 判断项 0。重点检查推理接口兼容、内部推理字段剥离、逐段完整性、数值否决、发送前额度记录和 ASGI 导入前数据隔离。

复审 `81cdea3`：硬违反 0、判断项 0。可选网关仅识别明确 Win32 错误码 4551，包装异常遍历有上限，其他异常继续抛出；没有放宽进程归属、回环监听或系统策略。TeX 数值解析以 fullmatch 保留参数边界，长度、指数、符号、零分母和额外 token 限制仍有效。

## Spec

初审 1 项 P2：合同要求“明确填空数值冲突不能由模型总评覆盖”，但 `number(r'-\frac12')` 原来返回 None。审查者从固定提交加载旧解析器合成复现：候选 `1/2`、盲解为负二分之一、审题器全部批准时，结果仍通过。

修复后有限支持 TeX 两个单数字参数及单数字/花括号混合参数；相反数值即使被模型批准也由程序拒绝，等值写法保留，多余 token、零分母及超限指数不解析。新增 11 项相关回归。Spec 独立复验确认原 P2 关闭。

新增的实际桌面恢复需求也经复审：仅可选网关的应用控制错误降级，后端和前端先验证就绪，受阻后不公布可用局域网地址。系统阻止的 Caddy 真实测试继续单列，没有改写为通过。其余范围未发现新偏差或越界。

最终增量 `11e10c3`：Standards 硬违反 0、判断项 0；Spec 新增发现 0，原 P2 保持关闭。实机发现 PS 5.1 丢失原生错误码，兼容分支严格限定 InvalidOperationException 类型及完整应用控制消息。Spec 合成复验确认普通拒绝访问、不同异常类型及附加无关错误均不降级；没有绕过系统策略。其他学习源码未变，`81cdea3` 复审继续适用。

两轴结果不互相抵消，也不将源码审查当作真实模型数学验收。完整回归在 `81cdea3`，最终启动兼容补丁在 `11e10c3` 另经 2 项定向回归及本机启动退出码 0 验证；真实 Caddy 上传仍为环境阻塞。
