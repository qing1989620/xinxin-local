# 源码与入口库存核对

当前第一方 Python 模块 43 个，main.py 显式 HTTP 路由 122 个；计数来自 AST/文件枚举，不表示每个端点都做了真实外部交付。前端 16 个路由声明归并为 29 个责任页面、132 个定义、136 个实例，完整清单见 audit.json。

## 后端边界与回归组

| 边界 | 实现 | 主要测试 |
| --- | --- | --- |
| 身份与邮件 | auth/main/email/resend | platform, email, resend, project_review |
| Agent 与执行 | agent/model/context/progress/execution/runtime/SSH/WindowsJob | agent_lifecycle, execution_recovery, agent_usability, runtime, context_tiers |
| 文件与数据 | files/store/uploads/conversations/private backup | file_media, upload_boundary, conversation_deletion, private_backup, project_review |
| 学习 | learning/learning_imports/learning_studio/learning_evidence/document_text | learning*, learning_live_check（测试本地调用额度控制，不发真实请求） |
| 技能 | skillnet/skills/semantic | semantic, skillnet_corpus, skillnet_fabric, skill_trace |
| 音乐与人格 | music/persona/imagegen | music*, persona_prompt, project_review |
| 本机/网关 | network/根脚本/desktop | desktop*, gateway_upload, network, tunnel_ownership, script_encoding |

上述为责任边界索引；实际文件名及逐项路由如下。第三方依赖按固定版本与接入信任边界审查，未声称重审每个依赖内部的所有实现。

## 第一方模块

- `backend/app/__init__.py`
- `backend/app/agent.py`
- `backend/app/auth.py`
- `backend/app/config.py`
- `backend/app/context.py`
- `backend/app/conversations.py`
- `backend/app/creative.py`
- `backend/app/document_text.py`
- `backend/app/execution.py`
- `backend/app/figure_recipe.py`
- `backend/app/files.py`
- `backend/app/imagegen.py`
- `backend/app/learning.py`
- `backend/app/learning_answers.py`
- `backend/app/learning_evidence.py`
- `backend/app/learning_imports.py`
- `backend/app/learning_quality.py`
- `backend/app/learning_studio.py`
- `backend/app/learning_visual.py`
- `backend/app/mail.py`
- `backend/app/main.py`
- `backend/app/model.py`
- `backend/app/music.py`
- `backend/app/network.py`
- `backend/app/persona.py`
- `backend/app/progress.py`
- `backend/app/public_text.py`
- `backend/app/recovery.py`
- `backend/app/remote_runner.py`
- `backend/app/runtime.py`
- `backend/app/skill_packages.py`
- `backend/app/skill_trace.py`
- `backend/app/skillnet/__init__.py`
- `backend/app/skillnet/bandit.py`
- `backend/app/skillnet/catalog.py`
- `backend/app/skillnet/index.py`
- `backend/app/skillnet/schema.py`
- `backend/app/skillnet/semantic.py`
- `backend/app/skillnet_corpus.py`
- `backend/app/skills.py`
- `backend/app/store.py`
- `backend/app/uploads.py`
- `backend/app/windows_job.py`

## 编排与窗口入口

已跟踪根脚本（以 git ls-files 作为最终提交范围）：

- `Setup-Lan-Access.ps1`
- `Start-Tunnel.ps1`
- `Start-Xinxin-Local.ps1`
- `Stop-Tunnel.ps1`
- `Stop-Xinxin-Local.ps1`

桌面脚本：

- `desktop/Install-Xinxin-Desktop.ps1`
- `desktop/Local-ServiceState.ps1`
- `desktop/Tunnel-State.ps1`
- `desktop/Uninstall-Xinxin-Desktop.ps1`
- `desktop/Xinxin-Desktop.ps1`

本机 ignored 的三个旧启停文件只做兼容转发，不作为发布文件。快捷方式只读核对目标正确；本轮后续已受管启用本机修复版，真实网关仍被系统阻止。

## main.py HTTP 路由声明

| 方法 | 模板 | 源码行 |
| --- | --- | ---: |
| GET | `/health` | 462 |
| GET | `/api/v1/network` | 466 |
| GET | `/api/v1/auth/status` | 470 |
| POST | `/api/v1/auth/setup` | 478 |
| POST | `/api/v1/auth/login` | 495 |
| POST | `/api/v1/auth/email/code` | 502 |
| POST | `/api/v1/auth/email/login` | 510 |
| POST | `/api/v1/auth/email/reset` | 520 |
| GET | `/api/v1/settings/email` | 538 |
| PUT | `/api/v1/settings/email` | 553 |
| POST | `/api/v1/settings/email/test` | 561 |
| GET | `/api/v1/settings/email/domains` | 566 |
| POST | `/api/v1/settings/email/domains` | 570 |
| POST | `/api/v1/settings/email/domains/{domain_id}/verify` | 579 |
| GET | `/api/v1/music/search` | 589 |
| GET | `/api/v1/music/url` | 602 |
| GET | `/api/v1/music/lyric` | 610 |
| GET | `/api/v1/music/pic` | 614 |
| GET | `/api/v1/music/mood` | 618 |
| GET | `/api/v1/music/favorites` | 625 |
| POST | `/api/v1/music/favorites` | 629 |
| DELETE | `/api/v1/music/favorites` | 636 |
| GET | `/api/v1/music/playlists` | 640 |
| POST | `/api/v1/music/playlists` | 644 |
| PUT | `/api/v1/music/playlists/{playlist_id}` | 651 |
| DELETE | `/api/v1/music/playlists/{playlist_id}` | 658 |
| GET | `/api/v1/music/playlists/{playlist_id}` | 662 |
| POST | `/api/v1/music/playlists/{playlist_id}/tracks` | 669 |
| DELETE | `/api/v1/music/playlists/{playlist_id}/tracks` | 676 |
| POST | `/api/v1/music/score` | 680 |
| POST | `/api/v1/music/play` | 687 |
| DELETE | `/api/v1/music/mood` | 691 |
| PUT | `/api/v1/music/settings` | 696 |
| GET | `/api/v1/auth/me` | 706 |
| POST | `/api/v1/auth/logout` | 710 |
| PUT | `/api/v1/auth/password` | 718 |
| GET | `/api/v1/dashboard` | 733 |
| GET | `/api/v1/conversations` | 783 |
| POST | `/api/v1/conversations` | 790 |
| GET | `/api/v1/conversations/{ident}` | 794 |
| PUT | `/api/v1/conversations/{ident}/context` | 812 |
| GET | `/api/v1/conversations/{ident}/deletion-preview` | 825 |
| DELETE | `/api/v1/conversations/{ident}/permanent` | 830 |
| POST | `/api/v1/conversations/batch/deletion-preview` | 835 |
| POST | `/api/v1/conversations/batch/permanent` | 839 |
| DELETE | `/api/v1/conversations/{ident}` | 862 |
| PUT | `/api/v1/conversations/{ident}` | 875 |
| POST | `/api/v1/conversations/{ident}/restore` | 884 |
| GET | `/api/v1/runs` | 892 |
| POST | `/api/v1/runs` | 896 |
| GET | `/api/v1/runs/{ident}` | 927 |
| POST | `/api/v1/runs/{ident}/continue` | 937 |
| GET | `/api/v1/runs/{ident}/activity` | 969 |
| POST | `/api/v1/runs/{ident}/cancel` | 988 |
| GET | `/api/v1/runs/{ident}/events` | 992 |
| GET | `/api/v1/skills` | 1032 |
| GET | `/api/v1/skills/status` | 1036 |
| GET | `/api/v1/skills/graph` | 1040 |
| GET | `/api/v1/skills/network-model` | 1044 |
| GET | `/api/v1/skills/activity` | 1048 |
| GET | `/api/v1/images/providers` | 1085 |
| GET | `/api/v1/images` | 1089 |
| POST | `/api/v1/images` | 1093 |
| GET | `/api/v1/skills/{name}` | 1105 |
| GET | `/api/v1/skills/{name}/resource` | 1109 |
| POST | `/api/v1/skills/{name}/feedback` | 1113 |
| GET | `/api/v1/records` | 1153 |
| POST | `/api/v1/records` | 1190 |
| PUT | `/api/v1/records/{ident}` | 1194 |
| DELETE | `/api/v1/records/{ident}` | 1199 |
| GET | `/api/v1/files` | 1208 |
| POST | `/api/v1/files` | 1218 |
| GET | `/api/v1/files/search` | 1243 |
| GET | `/api/v1/files/{ident}/text` | 1247 |
| GET | `/api/v1/files/{ident}/metadata` | 1255 |
| GET | `/api/v1/files/{ident}/columns` | 1259 |
| GET | `/api/v1/files/{ident}/preview` | 1270 |
| GET | `/api/v1/files/{ident}/download` | 1295 |
| DELETE | `/api/v1/files/{ident}` | 1318 |
| GET | `/api/v1/servers` | 1325 |
| POST | `/api/v1/servers` | 1338 |
| DELETE | `/api/v1/servers/{ident}` | 1350 |
| PUT | `/api/v1/servers/{ident}` | 1364 |
| GET | `/api/v1/memories` | 1388 |
| POST | `/api/v1/memories` | 1392 |
| PUT | `/api/v1/memories/{ident}` | 1401 |
| DELETE | `/api/v1/memories/{ident}` | 1410 |
| POST | `/api/v1/learning/imports` | 1431 |
| GET | `/api/v1/learning/imports` | 1439 |
| GET | `/api/v1/learning/imports/{ident}` | 1444 |
| GET | `/api/v1/learning/books` | 1451 |
| POST | `/api/v1/learning/books` | 1455 |
| GET | `/api/v1/learning/books/{book_id}` | 1465 |
| DELETE | `/api/v1/learning/books/{book_id}` | 1472 |
| GET | `/api/v1/learning/chapters/{chapter_id}` | 1480 |
| POST | `/api/v1/learning/books/{book_id}/questions` | 1487 |
| GET | `/api/v1/learning/questions` | 1524 |
| GET | `/api/v1/learning/books/{book_id}/sources` | 1531 |
| GET | `/api/v1/learning/sources/{source_id}` | 1548 |
| PUT | `/api/v1/learning/sources/{source_id}` | 1555 |
| GET | `/api/v1/learning/sources/{source_id}/pages/{page}` | 1563 |
| GET | `/api/v1/learning/books/{book_id}/generation` | 1575 |
| GET | `/api/v1/learning/generations/{job_id}` | 1579 |
| POST | `/api/v1/learning/books/{book_id}/generations` | 1586 |
| POST | `/api/v1/learning/quiz` | 1598 |
| GET | `/api/v1/learning/quiz/{session_id}` | 1605 |
| POST | `/api/v1/learning/quiz/{session_id}/answer` | 1612 |
| GET | `/api/v1/learning/questions/{question_id}/tutor` | 1625 |
| POST | `/api/v1/learning/questions/{question_id}/explain` | 1636 |
| GET | `/api/v1/learning/stats` | 1644 |
| GET | `/api/v1/settings` | 1648 |
| PUT | `/api/v1/settings` | 1683 |
| GET | `/api/v1/tools/gallery` | 1701 |
| GET | `/api/v1/tools/gallery/{name}` | 1705 |
| GET | `/api/v1/tools/gallery/{name}/reference` | 1715 |
| POST | `/api/v1/tools/plot` | 1730 |
| POST | `/api/v1/tools/image` | 1763 |
| GET | `/api/v1/schedules` | 1781 |
| POST | `/api/v1/schedules` | 1785 |
| PUT | `/api/v1/schedules/{ident}` | 1807 |
| DELETE | `/api/v1/schedules/{ident}` | 1836 |
| GET | `/api/v1/audit` | 1841 |

公开健康/身份状态及初始化/邮件入口与主人接口分开；后端认证、字段校验及失败时序由测试验证，页面隐藏按钮不作为授权。仅测试夹具提供的合成路由不在正式 main.py 中。
