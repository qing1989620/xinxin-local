# 云端与 Android 交付快速审查

2026-10-18，Asia/Shanghai。使用 [BadGoods 前端审查助手](https://github.com/BadbotAI/BadGoods/blob/76d20b19c8b2a6513d1516d42fdcc42a2b8c394f/skills/review-frontend-production/SKILL.md)，`review_depth=quick`、`mode=implement`。本次是构建、连接与交付的部分审查，未重做全站逐组件审查。

## 范围与基线

界面源码基于 `e357273`，本次增加发布包构建、私有签名和云端交付文档。界面仍为此前主人已验收的粒子技能中心、资源互通及 Agent。审查连接设置/API、原生配置、构建脚本、APK 实物、Caddy 交付；未触及后端源码或在前端放凭据。

## 已检查

- Release 组合禁止局域网 HTTP 与跳过网页构建。BackendUrl 限制 HTTPS origin，拒绝账号、路径、查询和片段，编译环境在 finally 恢复。
- 私人签名目录设置为当前 Windows 用户可访问；随机密码与 PKCS12 密钥库留在忽略目录 `.private/android-signing/`，命令用密码文件路径传递，Vite 不读取这些文件。现有密钥复用，缺失其中一项报错，不静默更换身份。
- 实际 `assembleRelease` 与lintVital通过。apksigner v2/v3校验通过，RSA3072且沿用同一发布证书；`aapt2`核对APK未启用debuggable、清文、系统备份，minSdk24 / targetSdk36。18项网页资源逐字节匹配构建时dist，默认后端为已绑定服务器的私有HTTPS origin，报告隐去私有域名。散列见android-cloud-verification.json。验证后本机dist重新构建为通用同源网页版本，不改变已签名的APK或云端静态网页。
- 真实服务内 TLS 验收了原生 origin `https://localhost` 的 Authorization / Content-Type / X-Upload-ID 预检；API 401、上传下载、SSE 事件与回放及认证注销通过。属于接口验证，不冒充实体 WebView 运行。
- 云端静态目录只有前端文件和签名后的 APK；模型 Key、SSH 私钥、数据库、原始聊天不在 APK 或 Git。APK 下载经服务内真实 TLS 返回正确 MIME 和相同 SHA-256。
- 新发布签名与旧调试包不同，同包名无法直接覆盖安装。安装说明明确首次卸载调试版再安装；云端资料保留。旧包也可改服务地址，后端切换仍清旧认证。

## 发现与修复

首次签名调用把同一个密码文件同时作为 keystore/key 两次输入，apksigner 顺序读取导致 EOF。PKCS12 共用密码后改为复用 keystore 密码，实际签名、验证和产物比对通过；未重建或丢弃已生成的私人签名密钥。

## 未验证 / 阻塞

此前公网HTTP实测是阿里云 `Non-compliance ICP Filing` 403，HTTPS被上游中断；用户确认未备案。主人最新选择保留杭州按量实例，通过Tailscale私有连接手机。新增 `deploy/Caddyfile.tailnet`，只监听回环8088，保留原上传限额、API no-store、静态安全头与SSE即时转发；真实Caddy validate、私有Host静态页面、回环健康、API401和监听地址核对通过。精确私有与原生CORS预检通过，无关origin拒绝；前端10项测试通过。主人完成账号绑定与Serve/HTTPS开启，实际标准TLS验证、短期验收会话、上传/下载、真实模型SSE/回放、APK的MIME和SHA-256匹配通过。该次由服务自身通过真实Tailscale地址发起；私有名称由已认证节点映射解析，不是另一节点或实体手机测试。证据在后端独立仓库 `docs/private-mobile-runtime.json`，没有复制其源码或凭据进入前端。

新Release真机安装与文件分享/软键盘/换网、私有PWA安装仍待测。旧局域网APK的主人验收不能替代这次发布包。Android与Clash轮流启用的限制、网络切换会短暂重连及安装签名差异已记录。没有把源码分析、手机尺寸模拟或服务内接口测试当成私有手机交付全部通过。
