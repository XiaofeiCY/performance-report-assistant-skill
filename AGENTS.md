# AGENTS.md

## 项目快速恢复入口

项目路径：

```text
E:\work\performance-report-assistant-skill
```

核心 skill 路径：

```text
performance-report-assistant/
```

进入本项目后按顺序读取：

1. `AGENTS.md`
2. `docs/status.md` 顶部 `Current Handoff Snapshot (2026-07-06)`
3. 如需企微采集器边界，再读 `performance-report-assistant/references/wecom-smart-summary-collector.md`
4. 如需报告采访规则，再读 `performance-report-assistant/SKILL.md`

不要恢复以下文件：

```text
CLAUDE.md
AGENT.md
```

用户已手动删除它们，当前唯一根入口是 `AGENTS.md`。

## 全局协作铁律

当用户讨论需求、产品范围、验收标准、任务拆解、项目状态或执行安排时，Codex 默认负责：

1. 理解并复述用户需求，确认目标、范围、约束、风险和验收标准。
2. 将需求转化为专业、可执行、可派发给 Claude 的任务文档。
3. 在需要 Claude 执行时，先沉淀文档，再给用户可直接复制给 Claude 的执行提示词。
4. Claude 完成后，与用户一起验收。

除非用户明确要求 Codex 直接实现、修复或运行某项操作，否则 Codex 不直接改代码，不越过任务文档替 Claude 执行实现工作。

项目协作、执行交接、验收、阻塞点、后续计划必须及时更新 `docs/status.md`。普通问答不主动写文件。

## 当前状态

当前没有新的 Claude 待执行任务。

本轮已完成并验收：

- 周报生成闭环，用户已采用草稿。
- 企微智能总结默认提示词来源修复，并已同步到 Claude 内部 skill。
- 完整流程低风险耗时优化：新增只读 `analyze_trace.py`，优化采访 fast path，恢复 git 统计 full clone 默认以保证证据完整。
- 企微采集器 Windows 防息屏：采集期间临时请求保持系统/屏幕唤醒，退出时释放，trace 记录启用/释放/失败。
- 企微采集器控制台阶段提示：仅控制台横幅，不做 overlay/GUI，避免影响截图/OCR。
- 企微采集器历史/旧结果页分类修复：进入智能总结旧结果页时不再误判为普通 `main_page`，旧指纹只作为历史页证据，不作为当前结果证据。
- 项目减重：已删除已验收任务文档、Python 缓存和旧临时输出；保留当前报告输出与最新成功企微 run。

当前保留的关键输出：

```text
outputs/weekly_report_2026-06-29_2026-07-03.md
outputs/weekly_git_stats_2026-06-29_2026-07-03.md
outputs/wecom_summary_live_2026-06-29_2026-07-03.md
outputs/wecom_summary_live_2026-06-29_2026-07-03.json
outputs/wecom_runs/20260706-102206-RRI8/
```

最新企微成功 run：

```text
outputs/wecom_runs/20260706-102206-RRI8/
```

重要边界：

- 不要运行全自动企微实机测试，除非用户再次监督并明确授权。
- 不要宣传企微采集器为无人值守、跨环境稳定或适配所有企微 UI。
- 不要恢复 `CLAUDE.md` 或 `AGENT.md`。
- 如果继续维护企微采集器，先读 `performance-report-assistant/references/wecom-smart-summary-collector.md`。

## 当前周期证据规则

每次进入新的报告采访 / 内容整合环境时，必须以用户在本轮采访中给出的目标周期为准。

- 旧窗口、旧采集、旧周报、旧绩效、旧 trace 或旧输出文件，只有在周期与本轮目标周期一致，或用户明确要求沿用时，才能作为当前证据。
- 若旧材料周期与本轮目标周期不一致，自动排除为当前证据；不要反复询问用户是否使用明显不匹配的旧材料。
- 不匹配的旧材料最多只能作为历史背景、流程验证记录或格式/结构参考，不能作为本轮工作事实、统计数字或报告依据。

## 模板记忆规则

这个 skill 面向多人、多种报告模板。

- 用户提供的模板、示例、已通过草稿，默认只作为本次任务参考。
- 不自动固化为全局模板，也不自动影响其他用户。
- 只有用户明确同意，才记录为可复用模板。

## 企微采集规则

企业微信智能总结自动化只能在用户明确要求并监督授权后执行。

允许：

- 恢复/置前/最大化企业微信窗口
- 截图、区域 OCR、模板匹配
- Interception 输入
- 在 prompt 中加入本次采集指纹
- 点击已验证目标
- 读取剪贴板并校验指纹

禁止：

- 自动发送、删除、编辑或转发消息
- 未确认企业微信前台时继续操作
- 未确认页面状态时点击、粘贴或复制
- 右键菜单复制
- 未知区域 `Ctrl+A/Ctrl+C`
- 多固定坐标试探
- 沿左侧菜单纵向扫描
- 点击正文 URL、引用、附件或正文中心来获取滚动焦点

## 下一步建议

当前可以直接切换窗口。

- 若是继续周报：本轮已完成，无需再跑采集或 git 统计。
- 若是新周期报告：重新采访周期、读者、模板、输出位置和证据来源；旧材料按周期规则自动筛选。
- 若是企微采集器维护：先读 `performance-report-assistant/references/wecom-smart-summary-collector.md`，不要直接运行实机测试，除非用户再次监督并明确授权。
