# Intake Questions

Use these questions selectively. Ask only what is needed. Lead the user step by step instead of presenting the whole list at once.

## Session Initialization

At the start of every new report-generation or content-integration request, the agent must initialize a fresh task-local state ledger. Conversation memory may inform stable preferences or style suggestions, but it is never current evidence by default. Previous generated reports, old WeCom results, old git statistics, old run directories, and prior task evidence do not enter the new evidence ledger automatically.

If the user explicitly asks to reuse an older fact or source, record that opt-in narrowly — do not reopen all prior content.

## Canonical Interview Sequence

Ask one question at a time. Skip fields already answered. The same missing field should use the same canonical question across runs (natural acknowledgement may vary, but decision order, choices, and semantics must not drift).

1. **Report type**: 周报总结、月度绩效自评、季度复盘、晋升述职、领导汇报、客户进度同步？
2. **Audience**: 直属领导、部门负责人/总部领导、跨部门伙伴、甲方/客户、还是多人混合？
3. **Target period**: 目标周期是什么？例如 2026 年 5 月、某个自然周、某个季度。Resolve relative dates with `scripts/resolve_report_period.py`. Default to Monday-Friday workweek for weekly reports.
4. **Template situation**: 是否有固定模板文件？可以是 Excel、Word、PPT、Markdown 或其他格式。如果只是以前提交过的周报/绩效表作为参考，我会只提取格式和结构。
5. **Evidence-source menu** (see below).
6. **Source-specific missing parameters** (git branch/author, WeCom authorization, etc.).
7. **Evidence status summary**.
8. **Draft in conversation** (preview phase).
9. **Revise until accepted**.
10. **Export only on explicit request** (confirm format and path).

Do not ask an output-location question during steps 1-9 unless the user has already explicitly requested saving, exporting, or a filled file copy.

### Bundled Answers (Fast Path)

When the user provides answers to multiple interview questions in one message, accept all of them and jump ahead. Example: "周报 直属 上周" covers report type + audience + date range. Do not re-ask answered questions.

### Relative Date Resolution

- Resolve "上周" as the previous Monday through Friday.
- Resolve "本周" as the current Monday through Friday.
- Default to workweek mode; natural week only on explicit request.
- Use `scripts/resolve_report_period.py` for date arithmetic.
- After resolving, state the exact date range and continue.

## Template / Reference Classification

Classification rules, in priority order:

- If the user says `模板`, `参考`, `以前写过的内容供参考`, `只看格式`, `按这个结构`, or equivalent, classify as `reference_only` immediately. Extract only structural/style signals. Do not reuse work items, repository/module names, people, dates, status, metrics, commit counts, conclusions, risks, or plans.
- Do not ask whether its data belongs to the current period or can be used. The user's explicit `模板/参考` label already answers that question.
- If the user provides a previous filled report without saying whether it is evidence or reference, ask once: "这份内容是本周期实际事项，还是只作为格式/结构参考？如果只是参考，我不会复用里面的事项、仓库名或统计数字。"
- A `reference_only` mark is final for the current session.
- Keep fixed blank artifact templates separate from previous filled-report references. Inspect both read-only; write a filled copy only after content is accepted and the user asks for a file.

## Complete Evidence-Source Menu

After report type, audience, period, and template role are known, present this compact multi-select menu:

```
本周期素材可以组合选择：
1. 直接粘贴工作事项、周报草稿或补充说明
2. 当前周期的文档、会议纪要、需求/工单、PR 或截图
3. Git 本地仓库或仓库 URL（需要时再确认分支和 author）
4. 企业微信智能总结（仅在你选择后，按监督式采集流程执行）
5. 其他你指定的材料
6. 暂无更多素材，先基于现有内容起草
```

Do not present a repository as the only or default evidence source. Do not auto-trigger WeCom. Template/reference material is not listed as current evidence merely because it was provided earlier.

## Evidence Questions

### General

- 这段时间最重要的 1-3 件事是什么？
- 哪些工作是你主导，哪些是参与或协同？
- 有无可量化结果：节省时间、减少问题、交付数量、上线范围、反馈评分、客户/领导反馈？
- 如果没有指标，有无定性证据：关键节点按期完成、风险被提前暴露、流程被沉淀、问题被闭环？

### Git Evidence

- 如果提供了代码仓库：必须先确认分支范围后再做研发数据统计。
- **分支范围确认**: 用户提供仓库后，必须让用户选择当前分支、指定分支还是全部分支。
- **作者确认**: 对个人周报或"我的提交"场景，必须确认 git author 名称或邮箱。
- **紧凑预执行汇总**: 当用户已在同一轮采访中明确提供了仓库列表、分支范围、作者过滤和日期范围，使用紧凑格式：

```
确认参数：周期 [YYYY-MM-DD 到 YYYY-MM-DD]、仓库 [repo 列表]、[全部分支 / 分支 xxx]、作者 [name]、仅个人提交。

开始执行统计？
```

仅当用户回复"确认"或"可以"后执行。

- 如果用户不提供 author：统计全部作者并标注为仓库整体证据。
- Git 统计默认 stdout 模式。仅在用户确认输出目录后使用 `--output`。
- 远程 URL 默认全量克隆；浅克隆是显式选择。

### WeCom Smart Summary

仅在用户明确要求采集企微智能总结时使用。不要自动触发。

- 采集模式选择：完整自动（推荐路径）、探针诊断（`--probe-only`，只读）、半自动（`--semi-manual`）、仅生成提示词（`--prompt-only`）。
- 首次采集或换了新窗口布局时建议先跑 `--probe-only`。
- 默认采集提示词来自 `scripts/collect_wecom_smart_summary.py` 的 `DEFAULT_PROMPT_BODY` 常量。展示给用户确认时，运行 `--prompt-only --period "<period>"` 获取脚本生成的规范提示词，不要自行编写或改写。
- 企微采集结果标记为 `needs_user_confirmation`，生成报告前提醒用户确认。
- 完整自动化前提清单、安全边界、诊断生命周期详见 `references/wecom-smart-summary-collector.md`。

### Multi-Source Orchestration

- 每个证据源独立跟踪状态：`pending`, `succeeded`, `failed`, `needs_user_input`。
- 一个来源失败不阻断其他来源。
- 起草前展示完整的来源状态汇总：

```
当前材料采集状态：
- 仓库 A：成功，git 统计已收集（stdout 模式，尚未落盘）
- 旧周报：仅参考结构，不复用内容（reference_only）
- 企微智能总结：待确认（needs_user_confirmation）

是否基于已成功材料继续？你也可以选择重试失败来源或补充手动材料。
```

## Preview-First Rules

Define two distinct phases:

- **preview phase**: read/collect evidence and return the full draft in the conversation; no durable report artifact.
- **export phase**: only after explicit user request, confirm format/path and create a persistent file.

Required behavior:

- `先生成看看`, `先给我看`, `起草一版`, or an ordinary report request defaults to preview.
- In preview phase, do not ask for an output directory and do not create final report, git-statistics Markdown, template copy, or WeCom Markdown/JSON result files.
- Git collection remains stdout-only when no export location has been confirmed.
- A fixed template may be inspected read-only during preview. Ask for an output path only after content is accepted and the user asks for a filled copy.
- If the user explicitly requests a file/export at the beginning, confirm the absolute output path before the first file-writing operation. Do not ask twice when already confirmed.
- Evidence repositories are never implicit output locations.

## Guardrail Prompts

Use these when the conversation is about to go wrong.

### Template / Reference Guardrails

```
我看到你提供的是以前提交过的周报，并且你说只参考结构/格式。我会只提取缩进、换行、中括号、分组方式、统计行形态等格式信号；不会复用里面的事项、仓库名、模块名、commit 数或统计数字。当前周期证据只以你接下来的仓库、周报、说明或其他材料为准。
```

```
这份内容是本周期实际事项，还是只作为格式/结构参考？如果只是参考，我不会复用里面的事项、仓库名或统计数字。
```

```
我看到你提供的是以前提交过的周报。我会把它当作格式和口吻参考，不会直接作为本周答案。请继续给我本周实际完成的事项、周报草稿、会议记录，或代码仓库路径。
```

### Session Isolation Guardrails

```
这是一个新的报告周期。上一份报告的内容（事项、仓库、统计数据、企微结果）不会自动带入本次。请提供本周期的实际材料，或告诉我你想复用上一周期的哪些具体内容。
```

### Period Guardrails

```
我会按工作周处理周报：默认周一到周五，不包含周末。按当前日期换算，这里的"上周"是 [YYYY-MM-DD] 到 [YYYY-MM-DD]；如果你要自然周或包含周末，请告诉我。
```

### Git Evidence Guardrails

```
你提供了代码仓库。代码统计前我先确认扫描范围：这些仓库要看当前分支、指定分支，还是全部分支？如果选指定分支，请给分支名。
```

```
如果只统计你的提交，请确认 git author 名称或邮箱。可以给一个或多个；如果你要统计全部作者，我会在报告里把它标为仓库整体证据，不写成全部都是你的个人提交。
```

```
执行代码数据统计前，请你确认以下信息：
- 时间范围：[YYYY-MM-DD] 到 [YYYY-MM-DD]
- 仓库：[repo A]、[repo B]
- 分支范围：[当前分支 / 指定分支 xxx / 全部分支]
- 作者过滤：[author 名称/邮箱 / 不过滤全部作者]
- 统计口径：[仅个人提交 / 仓库整体证据]
- 旧周报用途：仅参考结构，不复用内容和仓库名

确认无误后我再执行统计。请明确回复"确认执行"或指出要调整的项。
```

```
你之前提供的旧周报里出现了 [仓库X/模块Y]，但当前你只给了 [仓库A 和 仓库B]。我不会把旧周报里的仓库或模块当作当前缺失项来追问；如果你需要补充其他仓库或材料，请直接告诉我。
```

### WeCom Guardrails

```
你提到要采集企微智能总结。根据已确认的报告周期 [YYYY-MM-DD 到 YYYY-MM-DD]，默认提示词来自脚本：

[运行 `python scripts/collect_wecom_smart_summary.py --prompt-only --period "YYYY-MM-DD..YYYY-MM-DD"`，将其输出的完整内容展示给用户。不要自行编写"默认提示词"或改写脚本输出。]

你可以直接确认脚本输出的提示词、提出修改意见，或通过 `--prompt-file` 提供自定义提示词文件。
```

```
执行企微智能总结采集前，请确认：
- 你已登录企业微信 Windows 客户端；
- 已打开目标聊天/群/范围所在界面；如果当前已在智能总结历史结果页，脚本会先点击 `+` 新建本次总结；
- 你正在电脑前监督；
- 允许脚本使用截图、OCR、Interception 输入和剪贴板读取；
- 脚本不会发送、删除、编辑或转发任何消息；
- 当前企微自动化仍处于本机验证/不稳定状态，只支持已验证的企微主界面、智能总结输入页和历史结果页新建恢复路径；
- 脚本不会沿企微左侧菜单纵向扫描，也不会在未知区域右键复制或 Ctrl+A/Ctrl+C；
- 如果自动化失败，可以改用手动粘贴智能总结结果。

确认无误后我再执行。请明确回复"确认执行企微采集"。
```

```
企微智能总结是聊天记录摘要，可能遗漏或误解上下文。我会把它作为待确认证据使用，不会直接把讨论、计划或风险提醒写成已完成工作。
```

### Preview / Export Guardrails

```
我已经在对话中生成了报告预览。如果需要保存为文件，请告诉我你想要的格式（Markdown/Word/Excel 等）和保存路径，我再输出文件。
```

### Template Confirmation

```
我已经读完模板。计划改动以下位置：
- [文件区域/字段/章节/页面/幻灯片]：[用途]

我不会改动：
- 公式单元格/图表/自动计算区域
- 评分/评级栏
- 审批/签名区域
- 表头、样式、边框、合并单元格、页面版式、幻灯片布局

请确认是否按这个方案继续？确认后我再生成填写后的文件副本。
```

## Reusable Template Memory

- A user-provided template, example, or accepted draft is current-task reference by default.
- After successful delivery, when useful, ask once: "是否把这套结构记录为你后续的【周报/绩效/述职】模板？如果不需要，我只把它作为本次参考。"
- Persist a reusable template only after explicit user approval. Record its owner/scope, report type, structure rules, and limits.
