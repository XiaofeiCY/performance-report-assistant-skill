---
name: performance-report-assistant
description: Create Chinese work reports from weekly reports, git commits, repository metrics, notes, and Excel templates while preserving template formatting. Use when drafting monthly performance self-reviews, weekly summaries, quarterly reviews, promotion/述职 materials, leadership updates, headquarters reports, customer-facing progress updates, or filling company Excel performance forms across different departments.
---

# Performance Report Assistant

Turn scattered work evidence into a polished Chinese report through a guided interview, preferably by filling the user's original Excel template only after the user confirms the planned edits.

## Core Principles

- Preserve the user's original format whenever a template exists. Copy the `.xlsx` template and write values into cells; do not recreate the workbook from scratch unless the user explicitly asks.
- Guide first-time users step by step. Start with a short interview instead of asking the user to provide every file up front.
- When an Excel template is provided, inspect it first, explain which sheets/cells/sections will be changed, and wait for explicit user confirmation before writing to the workbook.
- Treat old reports and filled examples as references only. Never return a pasted previous report as the new report unless the user explicitly asks to reuse it unchanged.
- Minimize manual work. Prefer connected tools, exported files, pasted weekly notes, git logs, repository metrics, and local scripts before asking the user to reorganize content.
- Treat the report as evidence-based. Extract facts first, then summarize impact, capability, risks, and next steps.
- Adapt wording to audience: direct manager, senior leadership/headquarters, cross-functional partners, or external customers.
- Ask only for missing information that materially changes the output.
- Do not produce the final report until current-period evidence has been gathered or the user explicitly confirms there is no more evidence to provide.
- Resolve relative dates such as "上周", "本周", and "上个月" using the current date and timezone. State the exact absolute date range back to the user. Do not reuse examples as if they were the user's actual date range.

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
3. Confirm date range. If the user gives a relative period such as "上周", convert it to exact dates using the current date, then continue.
4. Ask whether there is a fixed Excel template or only a previous filled report/example.
5. Confirm where the final file should be saved.
6. Ask for evidence sources only after the scenario, template situation, and output location are clear.
7. If a repository is provided and no branch is named, ask for the branch before collecting repository evidence.

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

If the user provides a fixed Excel template, inspect workbook sheets, merged cells, visible labels, and existing filled examples before drafting or writing.

Distinguish input types:

- Fixed Excel template: a blank or reusable `.xlsx` form that should be copied and filled.
- Previous filled report: an old weekly/monthly report, pasted text, or filled form used only as style, structure, tone, and granularity reference.
- Current-period evidence: weekly notes, commits, repository metrics, tickets, meeting notes, user-provided facts, or other material from the target date range.

If the user provides a previous filled report after being asked for a template, acknowledge it as a reference and ask for current-period evidence. Do not treat the previous report as the completed answer.

### 3. Gather Evidence

Use the least-effort source available:

- Weekly reports: use exported/pasted Enterprise WeChat weekly reports, text files, docs, or meeting notes.
- Git commits and repository metrics: run `scripts/collect_git_commits.py` when the user gives repo paths and date range.
- Excel template: inspect and preserve the original `.xlsx` using spreadsheet tools or `scripts/fill_excel_template.py`.
- Existing examples: if the user has a previous successful report, use it as the strongest style and structure reference.

Repository handling:

- If the user provides one or more local git repository paths or git URLs, collect quantitative evidence from those repositories for the target date range.
- When the user provides a repository path or URL, ask which branch should be inspected before collecting data unless the user already named a branch. Stop and wait for the branch answer if the branch is missing.
- If the user says to use the default branch, omit `--branch`; the script will use `origin/HEAD` when available, then the current branch as a fallback.
- Pass an explicit branch choice to `scripts/collect_git_commits.py --branch <branch>`.
- For repository URLs, pass the URL directly to `scripts/collect_git_commits.py --repo <url>`. Do not manually clone into an arbitrary workspace location. The script clones URLs into a temporary directory and deletes the clone after it finishes.
- After the repository path, date range, and branch/default-branch choice are known, run `scripts/collect_git_commits.py` before drafting. Do not skip repository metrics when a repository is available.
- Include metrics such as commit count, changed file count, current tracked code files, current tracked code lines, code insertions/deletions, and top files by commit touch frequency.
- Treat changed file count as all files touched in the period; treat code line count and code insertions/deletions as recognized source/config files, excluding Markdown documentation.
- Treat these metrics as supporting evidence, not as the report's main narrative. Use them to strengthen claims about delivery volume, refactoring scope, stabilization effort, or cross-module impact.
- If the user provides only non-repository materials such as weekly reports, meeting notes, screenshots, documents, or Excel templates, do not invent repository metrics and do not ask for a repository unless code evidence would materially improve the report.
- If the repository date range has no commits, say that no commits were found and rely on the user's other evidence.

Enterprise WeChat handling:

- If a WeCom/Enterprise WeChat connector or browser automation is available and authorized, try to fetch or export the relevant weekly reports directly.
- If access is unavailable, ask the user for the smallest manual action: export the target month's weekly reports, paste them into one file, or provide screenshots/text. Do not require unnecessary reformatting.
- Never imply messages can be fetched without user authorization.

### 4. Confirm Output Location

Before generating files, ask where the output should be saved.

Prefer this order:

1. User-specified folder.
2. Same folder as the Excel template, using a clear filename.
3. Current workspace `outputs/` folder if available.
4. Current working directory as a fallback.

Use clear filenames that include scenario and period, for example:

```text
绩效汇报_2026年5月_已填写.xlsx
周报总结_2026年第22周.md
领导汇报_2026年5月.md
```

If the user does not choose a location, say the planned save path before creating the file and ask for confirmation when writing outside the current workspace.

### 5. Inspect and Confirm Excel Template Changes

When the user uploads or points to an Excel template:

1. Inspect the workbook before modifying it.
2. Summarize the structure:
   - sheet names,
   - obvious report sections,
   - merged cell areas relevant to writing,
   - formulas or protected/approval areas that should not be touched,
   - candidate cells or sections for generated content.
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

4. Wait for explicit confirmation before running `scripts/fill_excel_template.py` or writing any workbook.

If the mapping is uncertain, ask the user to confirm the target columns/cells before drafting final content.

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
- If a repository was provided, branch/default-branch choice is known and repository metrics have been collected.
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

1. Build a cell mapping from template labels to drafted content.
2. Show the mapping and planned workbook changes to the user.
3. Wait for user confirmation.
4. Copy the original workbook.
5. Write values into the copy with `scripts/fill_excel_template.py` or equivalent spreadsheet tooling.
6. Verify that formatting, merged cells, sheet names, row heights, formulas, and styles remain intact.

If no template exists:

- Produce a clean default report in Markdown or Excel using `references/report-patterns.md`.
- Keep sections easy to paste into company forms.

Always provide a short summary of:

- Inputs used.
- Assumptions made.
- Repository metrics used, if any.
- Cells/sections filled.
- Final file path.
- Any missing evidence or questions for final polish.

## Scripts

### collect_git_commits.py

Use this when the user wants weekly or monthly work facts from local git repositories or git URLs. By default it outputs both a commit list and repository metrics.

Example:

```bash
python scripts/collect_git_commits.py --repo C:\path\repo --branch main --since 2026-05-01 --until 2026-06-01 --output commits.md
```

Git URL example:

```bash
python scripts/collect_git_commits.py --repo https://github.com/example/project.git --branch main --since 2026-05-01 --until 2026-06-01 --output commits.md
```

If `--branch` is omitted, the script uses `origin/HEAD` when available, then the current branch as a fallback.

For git URLs, the script clones into an OS temporary directory named like `performance-report-assistant-*` and automatically deletes that clone when the script exits. Do not keep cloned repositories unless the user explicitly asks for a persistent local copy.

It reports:

- selected branch,
- repository source,
- whether a temporary URL clone was cleaned up,
- commit count,
- changed files in the period,
- code line changes in the period,
- current tracked code files,
- current tracked code lines,
- top files by commit touch frequency.

Use `--no-stats` only when the user explicitly wants a commit list without metrics.

### fill_excel_template.py

Use this to preserve `.xlsx` styling by writing only cell values into a copied template.

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
- `references/excel-template-workflow.md`: checklist for preserving Excel template formatting.
