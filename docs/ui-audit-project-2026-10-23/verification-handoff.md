# 验证命令与后续交接

前轮完整回归代码头 `2a1fdf6`；当前桌面增量头见下段，整体状态见 [主报告](review.md)。以下“通过”只对应实际执行命令及其条件。

10月24日桌面增量头`71e46ce`：中英文/混合语言应用控制4551识别已修复。`python -m pytest tests/test_desktop_updates.py tests/test_desktop_ownership.py tests/test_desktop_native_output.py -q --disable-warnings`：8 passed、0 skipped，包含中文UI/全流重定向下的真实隔离服务启动。自动审批曾拒绝代为执行快捷方式，未换方式重试；随后主人明确报告桌面已能正常打开（EV-058），SCN-057/TASK-048通过、FND-026关闭。后续仅需另验重复点击激活及关闭重开（SCN-056/TASK-049）；网关等既有门槛保持。证据类型是主人手工确认，前轮全量结果不代替实际开窗。[增量报告](../desktop-startup-2026-10-24.md)。

| 位置 | 命令 | 当前结果 / 证据 |
| --- | --- | --- |
| backend | 全部39个 tests/test_*.py 分别启动pytest，合并JUnit并核对原521节点 | 520通过/1项Caddy失败；project-review-full-isolated-final6.xml及各文件log |
| frontend | `npm test -- --reporter=verbose` | 78通过；project-review-unit-final6.log |
| frontend | `npm run test:build` | 类型和隔离构建通过；project-review-build-final6.log |
| frontend | `npx playwright test --workers=1` | 143通过/3既定跳过；project-review-browser-final6-report.json |
| frontend | `npx playwright test --config playwright.production.config.ts` | 2通过；project-review-production-final6-report.json |
| frontend / backend | `npm audit --json` / `.venv/Scripts/python.exe -m pip check` | 0已知漏洞/安装一致；不能作为依赖安全认证 |
| 仓库 | BadGoods `audit_ledger.py check ... --require-plan` | 结构与方案通过；完整覆盖/发布门槛仍为false |

后端原生生命周期测试和浏览器测试必须顺序执行：两者会操作测试用构建和端口，不能同时运行。最终所有后端测试也先于浏览器执行；TestClient/纯单元测试使用独立临时库；所有测试不读取主人账号或把其密钥交给模型。私有备份是单独明确只读输入，不属于合成测试夹具。

## 先解决原生门槛

主人已选择核对Caddy的系统运行许可。不要修改或绕过应用控制策略，也不要替换被阻止的程序来制造通过。恢复许可后先确认 `tools/caddy.exe version` 能正常执行，再运行：

```powershell
# backend/；该测试启动自己创建的临时服务和端口
.venv/Scripts/python.exe -m pytest tests/test_gateway_upload.py -q
```

这必须真实走Caddy验证256MiB接受、加一字节拒绝、删除后原件清理；不能只跑源码配置断言。另须启动具有独立DataDirectory、RuntimeDirectory和非默认前后端/网关端口的受管夹具，验证API和前端均转发到该夹具，未进入默认主人实例；检查三端口变动后的指纹与重建。只停止经过PID/启动时间/路径或父子身份核对的本次服务。

完成后更新SCN-034/050、FND-009/021、相关TASK/GATE及真实EV。补齐实体设备与外部交付/长期使用的阻塞场景；若产品支持范围需调整，应记录主人明确决定，不能由审查者把blocked改成passed或自行接受风险。

## 正式服务与发布

1. 当前私有备份位于backend/.qa-data/project-review-owner-backup。本机已追加备份并受管启用，前后端指纹/HTML/资产匹配，启用前后12张关键表一致。后续再次切换前仍须备份并检查活动任务，不能依赖旧时刻的0活动任务。
2. 使用当前Local受管入口切换，仅处理本项目确认归属的服务。按实际构建指纹复验本机入口、快捷方式、LAN地址和资源；核对原书、题库、作答、对话及凭据仍保留。
3. 检查未暂存内容、私密文件和远端更新；再次确认必要门槛通过。当前只有本地提交和本机启用，没有合并到本地main或推送。后续普通整合/推送，不强制覆盖远端。
4. 外部模型调用额度本轮未增加，30次验收已耗尽；测试不要自动调用真实模型或向真实邮箱/SSH发送操作。

审查台账、组件合同和任务顺序分别见 audit.json、[components.md](components.md)、[refactor-plan.md](refactor-plan.md)。原始日志、数据库、教材、密钥、备份和临时解包目录留在被忽略的本机区域，不上传GitHub。

## 低内存的完整后端复现

最终验收按文件顺序隔离进程，没有重试、删减或跳过。每文件都有原始log/XML；用`(classname,name)`计数逐项比对原完整套件，确认521个节点完全相同。本机审查脚本在`.qa-data/run-project-backend-isolated.py`，不随Git发布。普通checkout可在backend目录按以下方式完整运行：

```powershell
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$reportDir = Join-Path '.qa-data' ('pytest-isolated-' + $stamp)
New-Item -ItemType Directory -Path $reportDir | Out-Null
$hadFailure = $false
foreach ($testFile in (Get-ChildItem -LiteralPath tests -File -Filter 'test_*.py' | Sort-Object Name)) {
  $xml = Join-Path $reportDir ($testFile.BaseName + '.xml')
  .venv/Scripts/python.exe -m pytest $testFile.FullName -q --disable-warnings "--junitxml=$xml"
  if ($LASTEXITCODE -ne 0) { $hadFailure = $true }
}
if ($hadFailure) { throw '有测试未通过，请检查各文件报告；不能忽略失败。' }
```

这不降低产品断言。内存充足时仍可直接`python -m pytest tests -q`；本轮原始单进程518通过/3失败（两项MemoryError、Caddy4551）以及两项隔离复验通过的日志均保留。浏览器在后端全部结束后以`--workers=1`运行；不与原生生命周期测试并行。
