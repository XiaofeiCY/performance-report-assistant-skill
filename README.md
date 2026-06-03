# Performance Report Assistant Skill

[English](README.md) | [简体中文](README.zh-CN.md)

An open-source Claude Code / Codex skill, published as `performance-report-assistant-skill`, for turning weekly notes, git commits, work logs, and Excel templates into polished performance reports.

Previously known as `anche-report-skill`.

This skill is designed for people who need to write recurring work updates or performance reviews, especially when the final output must fit a fixed company spreadsheet template.

## What It Helps With

- Weekly work summaries
- Monthly performance self-reviews
- Quarterly business or project reviews
- Promotion review and career-growth narratives
- Manager, leadership, or headquarters updates
- Customer-facing progress updates
- Excel-based performance forms where formatting must be preserved

## Why This Exists

Many workplace reports are not written from scratch. They are assembled from scattered evidence:

- weekly reports,
- project notes,
- tickets,
- meeting notes,
- git commits,
- product or engineering milestones,
- customer feedback,
- and fixed Excel forms.

Most AI-generated spreadsheets lose the original template style, which forces users to copy the content back into their company file manually. This skill focuses on a safer workflow:

1. Interview the user step by step.
2. Inspect the Excel template before editing.
3. Explain exactly which sheets, cells, or sections will be changed.
4. Wait for user confirmation.
5. Fill a copy of the original workbook.
6. Return the final file path.

## Key Features

- Guided interview workflow for first-time users
- Audience-aware writing for managers, executives, partners, or customers
- Evidence-based summaries from weekly reports and git commit history
- Excel template preservation with `openpyxl`
- Explicit confirmation before modifying any workbook
- Support for Chinese workplace reports by default
- Reusable scripts for commit collection and Excel cell filling

## Repository Structure

```text
performance-report-assistant/
  SKILL.md
  agents/
    openai.yaml
  references/
    intake-questions.md
    report-patterns.md
    excel-template-workflow.md
  scripts/
    collect_git_commits.py
    fill_excel_template.py
```

## Installation

Copy the `performance-report-assistant` folder into your local skills directory.

Example for Claude Code / Codex environments that use `.agents\skills`:

```powershell
Copy-Item -Path ".\performance-report-assistant" -Destination "C:\Users\<your-user-name>\.agents\skills" -Recurse -Force
```

If your environment uses `.codex\skills`, copy it there instead:

```powershell
Copy-Item -Path ".\performance-report-assistant" -Destination "C:\Users\<your-user-name>\.codex\skills" -Recurse -Force
```

Restart Claude Code / Codex or open a new session after installation.

## Usage

After installation, ask:

```text
Use $performance-report-assistant to guide me step by step through a monthly performance review.
```

For Chinese reports:

```text
使用 $performance-report-assistant，一步一步采访我，帮我完成一份月度绩效汇报。
```

You can also reference the skill by path without installing it:

```text
Use E:\path\to\performance-report-assistant as the skill and guide me through a performance report.
```

## Recommended Workflow

1. Choose the report type: weekly summary, monthly review, quarterly review, promotion review, leadership update, or customer update.
2. Choose the audience: direct manager, senior leadership, cross-functional partners, customers, or non-expert stakeholders.
3. Provide the reporting period.
4. Provide an Excel template if one exists.
5. Let the agent inspect the template and propose the exact edit plan.
6. Confirm the edit plan.
7. Provide evidence such as weekly notes, work logs, ticket summaries, or git repository paths.
8. Generate the report and fill a copy of the template.
9. Check the returned final file path.

## Excel Template Safety

When an Excel template is provided, the skill instructs the agent to:

- inspect before editing,
- list planned sheet/cell/section changes,
- avoid formulas, score fields, approval fields, signature areas, headers, styles, borders, and merged-cell structures,
- wait for explicit confirmation,
- write to a copied workbook instead of overwriting the original file.

## Scripts

### `collect_git_commits.py`

Collect git commits across one or more repositories and output Markdown evidence.

```bash
python scripts/collect_git_commits.py --repo C:\path\repo --since 2026-05-01 --until 2026-06-01 --output commits.md
```

### `fill_excel_template.py`

Fill mapped values into a copied Excel template while preserving workbook structure and styling.

```bash
python scripts/fill_excel_template.py --template template.xlsx --mapping mapping.json --output filled.xlsx
```

Mapping example:

```json
{
  "Performance Review!C6": "Completed the core project delivery and documented a reusable process.",
  "Performance Review!C7": "Next month plan..."
}
```

Chinese mapping example:

```json
{
  "绩效自评!C6": "本月重点完成...",
  "绩效自评!C7": "下月计划..."
}
```

## Search Keywords

performance-report-assistant-skill, performance report assistant skill, performance report assistant, anche-report-skill, anche report skill, Claude Code skill, Codex skill, AI agent skill, performance review assistant, performance report skill, work report assistant, weekly report summarizer, Excel template filling, Chinese performance review, self-review generator, git commit work summary, stakeholder update, workplace report automation.

## Limitations

- Enterprise WeChat / WeCom reports cannot always be fetched automatically. Access depends on authorization, connectors, browser automation, or exported text.
- Complex Excel templates may still require human confirmation for cell mapping.
- The skill currently focuses on guided workflow and template-safe filling. More advanced automatic template scanning can be added later.

## Roadmap Ideas

- Add an Excel template scanner that proposes candidate fill cells automatically.
- Add example fixtures for common performance-review templates.
- Add role-specific writing modes for engineering, product, QA, operations, project management, and sales.
- Add configurable personal or team writing-style profiles.

## 中文简介

`performance-report-assistant` 是一个面向 Claude Code / Codex 的开源 skill，用来把周报、git commit、项目记录和 Excel 模板整理成可提交的工作汇报。

它的核心不是替某一个人写绩效，而是提供一个通用流程：先采访用户，再读取模板，确认拟修改位置，最后把内容写入原始模板副本，尽量保留 Excel 样式和结构。
