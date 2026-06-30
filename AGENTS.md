# AGENTS.md

## 项目快速恢复入口

本文件用于切换 Codex / Claude 窗口后快速恢复项目上下文。进入本项目后，先读本文件，再按需要读取 `docs/status.md` 和最新任务文档。

最短恢复路径：

1. 读本文件。
2. 读 `docs/status.md` 顶部的 `Current Handoff Snapshot (2026-06-30)`。
3. 当前没有新的 Claude 返工任务；读 `docs/status.md` 顶部快照和最新第三轮验收结论即可。最新已完成验收文档：

```text
docs/tasks/fix-wecom-acceptance-regressions.zh-CN.md
```

不要把 `docs/archive/tasks/` 里的企微文档当成当前执行指令；它们只保留历史脉络。

不要恢复以下文件：

```text
CLAUDE.md
AGENT.md
```

用户已手动删除它们，当前唯一根入口是 `AGENTS.md`。

项目路径：

```text
E:\work\performance-report-assistant-skill
```

核心 skill 路径：

```text
performance-report-assistant/
```

## 当前项目是什么

这是一个 `performance-report-assistant` Claude Code / Codex skill 项目，用于把周报、git commits、工作记录、企业微信智能总结、固定模板等材料整理成中文绩效/周报/汇报内容。

## 最高优先级：周期文案一致性

当用户给出相对周期并已解析出绝对日期时，后续所有对话文案、采集提示词、文件名和报告描述必须保持周期标签一致。

强制规则：

- 用户说“上周”，解析为 `2026-06-22` 到 `2026-06-26` 后，后续只能写：
  - `上周（2026-06-22 至 2026-06-26）`
  - 或 `2026-06-22 至 2026-06-26 期间`
- 绝不能写成“本周”再搭配上一周日期。
- 如果不确定相对周期标签，就只写绝对日期或“目标周期内”。
- 企业微信智能总结采集提示词必须遵守同一规则。
- 在展示提示词给用户确认前，先自检：周期标签和日期范围是否一致。

核心原则：

- 先采访用户，确认报告类型、读者、周期、模板、输出位置、证据来源。
- 有固定模板时，必须先检查结构，再列出拟修改位置，等用户明确确认后才写入副本。
- 旧周报/旧绩效只能作为结构和口吻参考，不能复用旧事项、仓库名、统计数字。
- 仓库统计前必须确认时间范围、分支范围、作者过滤、仓库列表，并等用户明确同意。
- 企业微信智能总结只能在用户明确要求时触发，执行桌面自动化前必须确认授权、安全边界和输出路径。
- 多来源材料要独立记录状态，一个来源失败不能阻塞其他来源。
- 生成报告前要汇总所有材料来源状态，让用户确认是否继续。

## 协作规则

用户已明确要求：

- Codex 默认负责理解需求、复述范围、写任务文档、协助验收。
- 只要下一步需要 Claude 执行，Codex 必须先把任务/返工/验收意见沉淀到文档，再生成一段可直接复制给 Claude 的执行提示词。
- 除非用户明确要求 Codex 直接实现或修复，否则不要直接改代码。
- Claude 负责具体代码实现、调试和交付。
- Codex 与用户一起验收 Claude 的执行结果。

因此：

- 普通需求、范围、验收、任务拆解：写到 `docs/tasks/`。
- 项目状态、决策、阻塞点：同步到 `docs/status.md`。
- 派发给 Claude 前：必须给用户一段可直接复制的 Claude 执行提示词，提示词要包含入口文件、状态快照、任务文档路径、范围、不做事项和验证命令。
- 直接代码实现：只有用户明确要求时才做。

## 当前最重要的工作

当前重点是维护企业微信智能总结采集器的安全边界，并等待用户监督下的实机验证。

当前没有新的 Claude 返工任务。最新已完成验收文档：

```text
docs/tasks/fix-wecom-acceptance-regressions.zh-CN.md
```

该文档已通过第三轮验收，后续只作为历史和边界说明保留。原任务 `docs/tasks/fix-wecom-safety-copy-timeout-and-doc-cleanup.zh-CN.md` 作为验收基准历史保留，不再作为当前执行入口。

最新 Codex 第三轮验收结论：`docs/tasks/fix-wecom-acceptance-regressions.zh-CN.md` 中记录的两个剩余返工点已经通过验收：

- `click_new_summary_plus()` 已只接受 `smart_summary_history_result_page`，即时分类为 `smart_summary_unknown_page` 时会保存诊断并停止。
- `fill_excel_template.py` 的已知后缀拒绝路径已输出简洁中文错误并非 0 退出，不再打印 Python traceback。

当前没有新的 Claude 返工任务。后续仍未完成的事项只有：

- 企业微信实机自动化仍未测试，必须由用户在本机监督下执行。
- 真实 `.xlsm` / `.xltm` 宏文件的保宏能力仍需用真实宏工作簿验证，不能过度宣传强保宏能力。

参考项目：

```text
E:\work\AgentsShare\wecom_uia_probe
```

重点参考文件：

```text
E:\work\AgentsShare\wecom_uia_probe\README.md
E:\work\AgentsShare\wecom_uia_probe\stage3_v2.py
E:\work\AgentsShare\wecom_uia_probe\interception_test.py
E:\work\AgentsShare\wecom_uia_probe\stage3_copy.py
```

## 企业微信采集当前结论

企业微信智能总结自动化当前不稳定，不能宣传为稳定、无人值守、跨平台或适配所有企微 UI。

最新用户决策：

- 不允许沿企业微信左侧菜单做纵向扫描或多点试探。企业微信窗口可任意伸缩，绝对坐标和多点扫描偏差概率高，也有隐私暴露风险。
- 触发智能总结后，生成时长不可固定。固定超时只能作为硬上限，完成判断应依赖 UI 状态、结果文本稳定、复制按钮或结果操作区出现等可观察信号。
- 复制结果必须处理长结果、滚动条、底部按钮不可见、窗口未完整显示等情况。找不到复制按钮时应安全失败并引导手动输入，不能右键乱试、固定坐标乱点或对未知区域 Ctrl+A/Ctrl+C。
- 需要增加基础交叉验证，保证 CLI、手动模式、周期提示词、页面分类和关键安全边界可回归。
- 用户已手动删除 `CLAUDE.md` 和 `AGENT.md`，不要恢复。项目入口统一使用 `AGENTS.md`。
- Excel 填充脚本需要处理 `.xlsx` / `.xlsm` / `.xltx` / `.xltm` / `.xls` 等后缀兼容或明确拒绝策略。

最近测试进展：

- 脚本已经能尝试恢复/置前企业微信。
- 脚本已经能从企微主聊天页继续扫描智能总结入口。
- 最新失败点不是完全没有进入智能总结，而是进入后默认打开了最近一次历史总结结果页。

关键判断：

企业微信智能总结至少有三类页面状态：

```text
main_chat_page
smart_summary_input_page
smart_summary_history_result_page
```

含义：

- `main_chat_page`：企业微信主聊天页、联系人页、群列表、聊天内容页。它不是失败终点，而是入口扫描起点。
- `smart_summary_input_page`：新建/初始化输入页，可以粘贴 prompt 并点击“开始总结”。
- `smart_summary_history_result_page`：历史总结结果页，显示旧总结正文和底部“新建文档 / 发送邮件 / 复制”等操作。它不是本次证据，必须先点击 `+` 新建本次总结。

正确状态机：

```text
start
-> ensure_wecom_foreground
-> capture_and_classify_page
-> main_chat_page:
      open_smart_summary_entry_with_verified_uia_or_ocr_only
      -> capture_and_classify_page
-> smart_summary_history_result_page:
      click_new_summary_plus
      -> wait
      -> capture_and_classify_page
-> smart_summary_input_page:
      paste_prompt
      -> click_start
      -> wait
      -> copy_result
-> unknown_page:
      save screenshot/OCR and fail after bounded retries
```

重要边界：

- 前台不是企业微信时，不要立即失败；先尝试多次恢复/置前企业微信。
- 多次恢复失败后才停止。
- 前台是企业微信但不是智能总结输入页时，不要直接停；应分类页面并尝试恢复。
- 发现“智能总结”子窗口不等于已经进入输入页。
- 历史结果页不能直接复制为本次结果，也不能直接粘贴 prompt。
- 只有确认进入 `smart_summary_input_page` 后，才允许粘贴 prompt。
- 粘贴、点击开始、复制等危险动作前必须确认企业微信在前台且页面状态正确。
- 不得使用左侧纵向扫描、多固定坐标试探、右键菜单复制未知区域、未知区域 Ctrl+A/Ctrl+C 作为默认策略。

## 最近同步过的文档

已同步以下文件，后续接手时应先读：

```text
docs/status.md
docs/tasks/fix-wecom-acceptance-regressions.zh-CN.md
docs/tasks/fix-wecom-safety-copy-timeout-and-doc-cleanup.zh-CN.md
performance-report-assistant/SKILL.md
performance-report-assistant/references/intake-questions.md
performance-report-assistant/references/wecom-smart-summary-collector.md
```

其中 `performance-report-assistant/references/wecom-smart-summary-collector.md` 当前还是未跟踪文件，但已作为当前企微采集器参考文档使用。

## 当前未提交改动

工作区已有未提交改动和新增文件。不要回滚用户或 Claude 已有改动。

当前已知改动包括：

- `.gitignore`
- `docs/status.md`
- `performance-report-assistant/SKILL.md`
- `performance-report-assistant/references/intake-questions.md`
- `docs/tasks/fix-wecom-safety-copy-timeout-and-doc-cleanup.zh-CN.md`
- `docs/tasks/fix-wecom-acceptance-regressions.zh-CN.md`
- `performance-report-assistant/references/wecom-smart-summary-collector.md`
- `performance-report-assistant/scripts/collect_wecom_smart_summary.py`
- `performance-report-assistant/scripts/requirements-wecom.txt`
- `docs/archive/tasks/` 中的历史任务文档

执行前应运行：

```powershell
git status --short
```

## 常用验证

文档或脚本改动后，至少运行：

```powershell
python performance-report-assistant\scripts\collect_wecom_smart_summary.py --help
```

手动模式验证：

```powershell
"测试智能总结内容" | python performance-report-assistant\scripts\collect_wecom_smart_summary.py `
  --manual-input `
  --output outputs\wecom_summary_manual_test.md `
  --output-json outputs\wecom_summary_manual_test.json
```

企业微信自动化实机测试必须由用户在本机监督下执行。

## 给下一个窗口的建议

如果用户说“继续企微修复”：

1. 先读本文件。
2. 再读 `docs/status.md` 最新几节。
3. 再读 `docs/tasks/fix-wecom-acceptance-regressions.zh-CN.md`。
4. 对照 `E:\work\AgentsShare\wecom_uia_probe` 的成功链路。
5. 如果用户没有明确要求 Codex 直接实现，则不要改代码，先把任务交给 Claude 或协助验收。
