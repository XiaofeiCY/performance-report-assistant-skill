---
name: performance-report-assistant
description: Create Chinese work reports from weekly reports, git commits, repository metrics, notes, and reusable templates while preserving template formatting. Use when drafting monthly performance self-reviews, weekly summaries, quarterly reviews, promotion/述职 materials, leadership updates, headquarters reports, customer-facing progress updates, or filling company report forms and templates across Excel, Word, PowerPoint, Markdown, or other formats.
---

# Performance Report Assistant

Turn scattered work evidence into a polished Chinese report through a guided interview, preferably by preserving and filling the user's original template only after the user confirms the planned edits.

## Core Principles

- Preserve the user's original format whenever a template exists. Copy the template and edit only intended content areas; do not recreate the artifact from scratch unless the user explicitly asks.
- Guide first-time users step by step. Start with a short interview instead of asking the user to provide every file up front.
- When any fixed template is provided, inspect it first, explain which pages/slides/sheets/cells/sections will be changed, and wait for explicit user confirmation before writing to the file.
- Treat old reports and filled examples as references only. Never return a pasted previous report as the new report unless the user explicitly asks to reuse it unchanged.
- Minimize manual work. Prefer connected tools, exported files, pasted weekly notes, git logs, repository metrics, and local scripts before asking the user to reorganize content.
- Treat the report as evidence-based. Extract facts first, then summarize impact, capability, risks, and next steps.
- Adapt wording to audience: direct manager, senior leadership/headquarters, cross-functional partners, or external customers.
- Ask only for missing information that materially changes the output.
- Do not produce the final report until current-period evidence has been gathered or the user explicitly confirms there is no more evidence to provide.
- Resolve relative dates such as "上周", "本周", and "上个月" using the current date and timezone. For weekly work reports, default to a Monday-Friday workweek unless the user explicitly asks for a natural week or weekend coverage. State the exact absolute date range back to the user. Do not reuse examples as if they were the user's actual date range.
- When a user provides a previous report and explicitly states it is for structure/format reference only, never reuse its work items, repository names, module names, commit counts, or statistics as current-period evidence. Do not ask whether its content describes the current period. Do not infer missing repositories or modules from it. Only extract formatting signals: grouping, indentation, bullet style, line breaks, bracket/label patterns, section order, tone, and granularity.
- When collecting evidence from multiple sources, treat each source independently. One source failing (e.g. WeCom automation, a remote repository) must not block other sources from completing. Record each source's state and report it to the user before drafting.

## Workflow

### 1. Start With a Guided Interview

Do not begin by demanding all inputs at once. Lead the user through the process.

Start with one concise message that explains the next step and asks only the first needed question:

```text
我会一步一步带你完成。先确认这次要写哪类材料：周报总结、月度绩效自评、季度复盘、述职材料、领导汇报，还是客户进度同步？
```

After the user answers, continue one step at a time:

1. Confirm report scenario.
2. Confirm audience.
3. Confirm date range. If the user gives a relative period such as "上周", convert it to exact dates using `scripts/resolve_report_period.py`, then continue.
4. Ask whether there is a fixed template file, a previous filled report/example, or no template.
5. Confirm where the final file should be saved.
6. Ask for evidence sources only after the scenario, template situation, and output location are clear.
7. If a repository is provided, use all branches by default unless the user explicitly names a branch.

Avoid asking more than 2-3 questions in one turn unless the user explicitly wants a checklist.

### 2. Classify the Report

Identify the scenario:

- `weekly-summary`: summarize one week of work.
- `monthly-performance`: fill a monthly performance review or self-review.
- `quarterly-review`: summarize broader outcomes, trends, and capability growth.
- `promotion-review`: emphasize scope expansion, ownership, and repeatable impact.
- `leadership-update`: concise progress and risk update for management or headquarters.
- `customer-progress`: non-jargon progress update for customers or non-specialists.

Identify audience:

- Direct manager: concrete outcomes, blockers, collaboration, next-month plan.
- Higher-level leadership/headquarters: strategic value, measurable impact, risk control, resource asks.
- Cross-functional partner: dependencies, decisions, timeline, needed input.
- Customer or non-expert: business-facing progress, benefits, current limitations, next steps.

If the user provides a fixed template, inspect its structure and existing filled examples before drafting or writing. For Excel, inspect workbook sheets, merged cells, visible labels, formulas, and approval areas. For Word, inspect headings, tables, placeholders, and signature/approval blocks. For PowerPoint, inspect slide titles, layout placeholders, tables, charts, and speaker notes if relevant.

Distinguish input types:

- Fixed template: a blank or reusable `.xlsx`, `.docx`, `.pptx`, Markdown, or other file that should be copied and filled while preserving structure.
- Previous filled report: an old weekly/monthly report, pasted text, or filled document. Its treatment depends on what the user says:
  - If the user says it is for **structure/format reference only** (结构、缩进、换行、中括号、分组、统计行格式、口吻), mark it `reference_only`. Extract only formatting signals: grouping order, indentation, bullet style, line breaks, bracket/label patterns, section order, tone, granularity, and summary-line shape. Never reuse its work items, repository names, module names, commit counts, changed-file counts, or conclusions. Never ask "is this your current-period work". Never infer missing repositories or modules from it.
  - If the user is **unclear** about whether it is current evidence or format reference, ask once: "这份内容是本周期实际事项，还是只作为格式/结构参考？如果只是参考，我不会复用里面的事项、仓库名或统计数字。"
  - If the user says it **is** current-period evidence, treat it as such and cross-check with other sources.
- Current-period evidence: weekly notes, commits, repository metrics, tickets, meeting notes, user-provided facts, or other material from the target date range.

If the user provides a previous filled report after being asked for a template, acknowledge it as a reference and ask for current-period evidence. Do not treat the previous report as the completed answer.

### 3. Gather Evidence

Use the least-effort source available:

- Weekly reports: use exported/pasted Enterprise WeChat weekly reports, text files, docs, or meeting notes.
- Git commits and repository metrics: run `scripts/collect_git_commits.py` when the user gives repo paths and date range.
- Template file: inspect and preserve the original file using the appropriate tool for its format. For Excel, use spreadsheet tools or `scripts/fill_excel_template.py`; for Word or PowerPoint, use the relevant document or presentation tooling available in the environment.
- Existing examples: if the user has a previous successful report, use it as the strongest style and structure reference.

Repository handling:

- If the user provides one or more local git repository paths or git URLs, always collect quantitative evidence from those repositories for the target date range, regardless of report type.
- **Before running `collect_git_commits.py`, you must confirm branch scope, author filter, and other key parameters with the user, then present a pre-execution confirmation checklist and wait for explicit approval.** The script's internal default (all branches when `--branch` is omitted) is a safety net for the script itself; the agent interview must not silently default to any branch scope.
- If the user provides a repository but does not explicitly name a branch, ask: "代码统计前我先确认扫描范围：这些仓库要看当前分支、指定分支，还是全部分支？"
- If the user explicitly names a branch, pass it to `scripts/collect_git_commits.py --branch <branch>` and restrict statistics to that branch.
- If the user explicitly asks to use all branches, pass `--all-branches`; this is equivalent to omitting `--branch`.
- If the user asks for "我的提交" or a personal weekly/performance report, ask for the git author name/email to pass via `--author`, even if you think you already know it from context. Prompt: "如果只统计你的提交，请确认 git author 名称或邮箱。可以给一个或多个；如果你要统计全部作者，我会在报告里把它标为仓库整体证据，不写成全部都是你的个人提交。"
- If the user declines to provide an author, collect all authors, pass no `--author`, and label the result as repository-wide evidence, not personal work.
- For repository URLs, pass the URL directly to `scripts/collect_git_commits.py --repo <url>`. Do not manually clone into an arbitrary workspace location. The script clones URLs into a temporary directory and deletes the clone after it finishes.
- **Pre-execution confirmation checklist**: after branch, author, date range, and repository list are known, present a summary before running any script:

```text
执行代码数据统计前，请你确认以下信息：
- 时间范围：[YYYY-MM-DD] 到 [YYYY-MM-DD]
- 仓库：[repo A]、[repo B]
- 分支范围：[当前分支 / 指定分支 xxx / 全部分支]
- 作者过滤：[author 名称/邮箱 / 不过滤全部作者]
- 统计口径：[仅个人提交 / 仓库整体证据]
- 旧周报用途：仅参考结构，不复用内容和仓库名

确认无误后我再执行统计。请明确回复"确认执行"或指出要调整的项。
```

Only run the script after the user explicitly approves (e.g. "确认执行", "可以执行", "按这个范围统计", "没问题，开始"). If the user changes any parameter, re-display the updated checklist and wait again.

- After the repository path, date range, optional branch restriction, and optional author filter are known, run `scripts/collect_git_commits.py` before drafting. Do not skip repository metrics when a repository is available, even if the user also provided notes, a previous report, or a template.
- Include metrics such as commit count, changed file count, current tracked code files, current tracked code lines, code insertions/deletions, and top files by commit touch frequency.
- Also include additional useful angles when available, such as author distribution, daily commit distribution, and high-frequency modules/files.
- Treat changed file count as all files touched in the period; treat code line count and code insertions/deletions as recognized source/config files, excluding Markdown documentation.
- Treat these metrics as supporting evidence, not as the report's main narrative. Use them to strengthen claims about delivery volume, refactoring scope, stabilization effort, or cross-module impact.
- If the user provides only non-repository materials such as weekly reports, meeting notes, screenshots, documents, or templates, do not invent repository metrics and do not ask for a repository unless code evidence would materially improve the report.
- If the repository date range has no commits, say that no commits were found and rely on the user's other evidence.
- Do not infer missing repositories from old reports. If an old report mentions repositories the user has not provided, do not ask whether those repositories should also be included, unless the user explicitly says the old report's content is also current-period evidence.

Date range handling:

- For `weekly-summary`, default to workweek mode: Monday through Friday.
- Resolve "上周" as the previous Monday through Friday. For example, if today is 2026-06-09, "上周" means 2026-06-01 through 2026-06-05.
- Resolve "本周" as the current Monday through Friday. For example, if today is 2026-06-09, "本周" means 2026-06-08 through 2026-06-12.
- Use natural week mode, Monday through Sunday, only when the user explicitly says "自然周", "包含周末", or gives dates that include weekend work.
- Use `scripts/resolve_report_period.py --period last-week --today YYYY-MM-DD` or `--period this-week` to avoid date arithmetic mistakes.

Enterprise WeChat Smart Summary:

- Only trigger when the user explicitly requests it, e.g. "采集企微智能总结", "从企业微信智能总结提取", "用企微智能总结作为材料". Never auto-trigger.
- After the user requests it, confirm the collection goal. If the report period is known, generate a dynamic default prompt using the current date range context (never hardcoded dates). Show the prompt to the user and let them confirm, edit, or provide their own.
- The default WeCom prompt must keep the period label semantically consistent with the user's request. If the user said "上周", use either the same relative label plus dates, e.g. "总结上周（2026-06-22 至 2026-06-26）期间...", or only absolute dates, e.g. "总结 2026-06-22 至 2026-06-26 期间...". If the period label is unknown, use neutral wording such as "目标周期内". Never combine a current-week label with a previous-week date range.
- Treat Enterprise WeChat Smart Summary as a small state machine, not a single page. The collector may encounter the normal chat page, a first-use/new-summary input page, or a previously generated history-result page. If a history-result page is visible, the correct recovery is to click the Smart Summary `+` new-summary button, wait for the input page, and verify it before pasting the prompt.
- Do not describe Smart Summary entry detection as coordinate scanning. Enterprise WeChat windows can be resized freely; the collector must rely on verified UI Automation/OCR signals and must not perform left-menu vertical scanning or multi-point trial clicks.
- Treat Smart Summary generation as variable-duration work. Fixed timeout is only a hard safety cap; completion should be inferred from observable UI/result signals such as result text stability, result action area, or a verified copy button.
- Treat copying as a verified result-page operation. The copy button may be below the visible area or behind long scrollable content. The collector should search by UIA/OCR and bounded in-page scrolling after confirming the result page; it must not use right-click, fixed-coordinate copy guesses, or Ctrl+A/Ctrl+C on unknown regions as a default fallback.
- Before any desktop automation, present a precondition checklist and wait for explicit user approval:

```text
执行企微智能总结采集前，请确认：
- 你已登录企业微信 Windows 客户端；
- 已打开目标聊天/群/范围所在界面；如果已经进入“智能总结”，历史结果页也可以，脚本应先点击 `+` 新建本次总结再继续；
- 你正在电脑前监督；
- 允许脚本使用截图、OCR、Interception 输入和剪贴板读取；
- 脚本不会发送、删除、编辑或转发任何消息；
- 当前企微自动化仍处于本机验证/不稳定状态，只支持已验证的企微主界面、智能总结输入页和智能总结历史结果页恢复路径；如果自动化失败，可以改用手动粘贴智能总结结果；
- 输出路径为：[path]。

确认无误后我再执行。请明确回复"确认执行企微采集"。
```

- During execution, report progress at each stage: dependency check, window location, prompt paste, button click, polling, copy, save.
- On failure, report the stage and reason clearly. Offer retry or `--manual-input` fallback. Never continue clicking blindly on timeout.
- If the collector cannot verify the Smart Summary entry, generation result, or copy button, stop and preserve diagnostics instead of attempting broader clicks or global copy shortcuts.
- Do not describe the WeCom collector as stable, unattended, cross-platform, or generally capable of handling all Smart Summary UI variants. It currently follows the validated `E:/work/AgentsShare/wecom_uia_probe` flow plus a supervised recovery path for Smart Summary history-result pages, and still requires live retesting.
- Never treat a previous Smart Summary history result as current evidence. If Smart Summary opens to a historical result, create a new summary session with the `+` button first; only the newly generated result may be saved as current-period evidence.
- Mark WeCom Smart Summary results as `Status: needs_user_confirmation`. Remind the user before using in a report: "企微智能总结是聊天记录摘要，可能遗漏或误解上下文。我会把它作为待确认证据使用，不会直接把讨论、计划或风险提醒写成已完成工作。"
- Use `scripts/collect_wecom_smart_summary.py` for the actual collection. Read `references/wecom-smart-summary-collector.md` for the collector's capabilities, dependencies, and safety boundaries.

Multi-source evidence orchestration:

- Model each evidence source as an independent unit with its own type, state, and output. Source types: `repository`, `word_document`, `weekly_draft`, `previous_report_reference`, `wecom_smart_summary`, `free_text`, `template`.
- Track per-source state: `pending`, `confirming`, `running`, `succeeded`, `failed`, `skipped`, `needs_user_input`.
- Process only the sources the user provides. If the user gives only repositories, do not trigger Word or WeCom collection. If the user gives repositories and Word docs, process both independently.
- **Failure isolation**: one source failing must not stop others. Record the failure reason and continue. Do not clear successfully collected evidence. Do not silently ignore failures.

```text
企微智能总结采集失败：未找到智能总结窗口。
我会保留这个失败状态，并继续处理已提供的仓库和文档材料。
稍后你可以选择重试企微采集、改用手动粘贴，或先基于现有材料继续。
```

- **Pre-report evidence summary**: before drafting or filling a template, present a complete source status summary:

```text
当前材料采集状态：
- 仓库 A：成功，输出 outputs/repo_a_commits.md
- 仓库 B：失败，原因：认证失败
- Word 文档：成功，已读取
- 旧周报：仅参考结构，不复用内容
- 企微智能总结：失败，原因：未找到智能总结窗口

是否基于已成功材料继续？你也可以选择重试失败来源或补充手动材料。
```

- When a failed source could materially affect report quality, let the user choose: continue with available evidence, retry the failed source, switch to manual input, or pause.

- If a WeCom/Enterprise WeChat connector or browser automation is available and authorized, try to fetch or export the relevant weekly reports directly.
- If access is unavailable, ask the user for the smallest manual action: export the target month's weekly reports, paste them into one file, or provide screenshots/text. Do not require unnecessary reformatting.
- Never imply messages can be fetched without user authorization.

### 4. Confirm Output Location

Before generating files, ask where the output should be saved.

Prefer this order:

1. User-specified folder.
2. Same folder as the template, using a clear filename.
3. Current workspace `outputs/` folder if available.
4. Current working directory as a fallback.

Use clear filenames that include scenario and period, for example:

```text
绩效汇报_2026年5月_已填写.xlsx
周报总结_2026年第22周.md
领导汇报_2026年5月.md
```

If the user does not choose a location, say the planned save path before creating the file and ask for confirmation when writing outside the current workspace.

### 5. Inspect and Confirm Template Changes

When the user uploads or points to a fixed template, read `references/template-workflow.md`. If the template is Excel, also read `references/excel-template-workflow.md`.

1. Inspect the template before modifying it.
2. Summarize the structure:
   - file type,
   - sheet/page/slide names or headings,
   - obvious report sections,
   - tables, placeholders, merged cells, text boxes, or slide regions relevant to writing,
   - formulas, protected areas, charts, approval/signature blocks, or metadata areas that should not be touched,
   - candidate cells, paragraphs, placeholders, slides, or sections for generated content.
3. Produce a proposed change plan, such as:

```text
我计划只改动以下位置：
- 「绩效自评」!C6：本月重点工作
- 「绩效自评」!C7：成果与影响
- 「绩效自评」!C8：问题与改进
- 「绩效自评」!C9：下月计划

我不会改动：
- 分数/评级栏
- 审批/签名区域
- 公式单元格
- 表头、边框、颜色、合并单元格

请确认是否按这个方案继续。
```

4. Wait for explicit confirmation before running any file-writing tool or writing any template copy.

If the mapping is uncertain, ask the user to confirm the target fields, cells, paragraphs, placeholders, slides, or sections before drafting final content.

### 6. Analyze Before Writing

Create a compact evidence map:

- Work item or theme.
- Source evidence: weekly report date, commit hash, document, meeting, ticket, or user note.
- Repository metrics when available: branch, commit count, touched files, top changed files, current code line count, and code insertions/deletions.
- Reference-only material: previous report/template used for structure or tone, clearly marked as not current-period evidence.
- User role: owner, contributor, coordinator, reviewer, supporter.
- Output: shipped feature, resolved issue, delivered document, aligned decision, reduced risk.
- Impact: business value, customer value, efficiency, quality, risk reduction, team enablement.
- Metric status: exact metric, estimated metric, qualitative evidence, or missing.

Before drafting, check:

- The target report period is known.
- Current-period evidence exists, or the user explicitly said to draft with limited evidence.
- If a repository was provided, repository metrics have been collected across all branches unless the user explicitly restricted the scan to one branch.
- Any previous report is being used only for style and structure unless the user explicitly asked to reuse old content.

Prefer grouping by themes over raw chronology unless the form requires dates.

### 7. Fill Gaps with a Short Interview

Read `references/intake-questions.md` when evidence is incomplete or the target format is unclear.

Ask concise questions only for gaps such as:

- What format or template must be followed?
- Who will read this report?
- Which work mattered most this period?
- What outcomes, metrics, or feedback can prove impact?
- What should be emphasized or avoided?

If no template exists, read `references/report-patterns.md` and choose the default format for the scenario.

### 8. Draft in the Right Style

Use Chinese by default unless the user requests another language.

Writing style:

- Specific but not boastful.
- Outcome-first, not activity-first.
- Honest about blockers and tradeoffs.
- Use "我主导/我推进/我参与/我协同" accurately; do not overclaim ownership.
- Translate technical work into management-readable value.

For weakly quantified work, use credible qualitative phrasing:

- "提升了问题定位效率" only when evidence supports it.
- "为后续规模化复用打下基础" only when a reusable artifact or process exists.
- "降低沟通成本/返工风险" only when there was cross-team alignment, documentation, or review.

### 9. Output

If a template exists:

1. Build a mapping from template labels/sections/placeholders to drafted content.
2. Show the mapping and planned template changes to the user.
3. Wait for user confirmation.
4. Copy the original template.
5. Write values into the copy with the appropriate tool for the file type.
6. Verify that formatting, layout, formulas, tables, placeholders, slide order, page structure, and styles remain intact where applicable.

If no template exists:

- Produce a clean default report in Markdown, or another user-requested format, using `references/report-patterns.md`.
- Keep sections easy to paste into company forms.

Always provide a short summary of:

- Inputs used.
- Assumptions made.
- Repository metrics used, if any.
- Template fields/cells/sections/slides filled.
- Final file path.
- Any missing evidence or questions for final polish.

## Scripts

### collect_git_commits.py

Use this whenever the user provides local git repositories or git URLs as evidence. By default it outputs both a commit list and repository metrics.

Example:

```bash
python scripts/collect_git_commits.py --repo C:\path\repo --branch main --since 2026-05-01 --until 2026-06-01 --output commits.md
```

All-branches example:

```bash
python scripts/collect_git_commits.py --repo C:\path\repo --all-branches --author "Your Name" --since 2026-05-01 --until 2026-05-31 --output commits.md
```

Git URL example:

```bash
python scripts/collect_git_commits.py --repo https://github.com/example/project.git --branch main --since 2026-05-01 --until 2026-06-01 --output commits.md
```

When `--branch` is omitted, commit statistics search all branches by default to avoid missing work spread across feature, release, and hotfix branches. If both `--all-branches` and `--branch` are provided, commit statistics use all branches while current code size is measured from the selected/default branch.

If a branch is provided, statistics are restricted to that branch.

For git URLs, the script clones into an OS temporary directory named like `performance-report-assistant-*` and automatically deletes that clone when the script exits. Do not keep cloned repositories unless the user explicitly asks for a persistent local copy.

It reports:

- selected scan scope,
- repository source,
- whether a temporary URL clone was cleaned up,
- commit count,
- changed files in the period,
- code line changes in the period,
- current tracked code files,
- current tracked code lines,
- top files by commit touch frequency.
- author distribution,
- daily commit distribution.

Use `--no-stats` only when the user explicitly wants a commit list without metrics.

### resolve_report_period.py

Use this before asking follow-up questions when the user gives a relative period such as "上周" or "本周".

Examples:

```bash
python scripts/resolve_report_period.py --period last-week --today 2026-06-09
python scripts/resolve_report_period.py --period this-week --today 2026-06-09
python scripts/resolve_report_period.py --period last-week --today 2026-06-09 --week-mode natural
```

Default weekly mode is `workweek`, Monday through Friday. Use `--week-mode natural` only when the user explicitly wants Monday through Sunday.

### fill_excel_template.py

Use this only for Excel templates to preserve `.xlsx` styling by writing cell values into a copied template. For Word, PowerPoint, or other template formats, use the relevant document or presentation tooling instead.

Mapping JSON examples:

```json
{
  "Sheet1!B4": "本月重点完成...",
  "Sheet1!B5": "下月计划..."
}
```

or:

```json
{
  "Sheet1": {
    "B4": "本月重点完成...",
    "B5": "下月计划..."
  }
}
```

Run:

```bash
python scripts/fill_excel_template.py --template template.xlsx --mapping mapping.json --output filled.xlsx
```

## Reference Files

- `references/intake-questions.md`: interview questions for missing context.
- `references/report-patterns.md`: default structures for weekly summaries, performance reviews, leadership updates, and customer progress updates.
- `references/template-workflow.md`: checklist for preserving fixed templates across Excel, Word, PowerPoint, Markdown, and other formats.
- `references/excel-template-workflow.md`: Excel-specific checklist for preserving workbook formatting.
