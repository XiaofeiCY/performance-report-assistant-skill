# Claude Code Execution Plan: Build `performance-report-assistant` Skill

## Objective

Create a reusable Codex/Claude Code skill named `performance-report-assistant`.

The skill should help Chinese workplace users turn weekly reports, git commits, notes, and fixed Excel templates into polished work reports while preserving the user's original Excel formatting.

This skill is intended for:

- Weekly summaries.
- Monthly performance self-reviews.
- Quarterly reviews.
- Promotion or 述职 materials.
- Leadership/headquarters updates.
- Customer or non-expert progress updates.
- Company Excel performance forms across different departments.

## Core User Problems

Solve these specific problems:

1. The company uses fixed Excel performance forms, and different departments may use different templates.
2. Users currently collect monthly weekly reports manually from Enterprise WeChat, paste them into a new file, and ask an AI agent to summarize them.
3. Existing generated Excel files lose too much styling, so users still have to copy generated content back into the original company workbook.
4. The workflow should support different audiences, such as direct manager, headquarters leadership, cross-functional stakeholders, and external customers.
5. The skill should be generic enough to publish on GitHub so colleagues can reuse it.

## Required Deliverables

Create or update this skill folder:

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

Do not create extra documentation files such as README, changelog, or installation guide unless explicitly asked.

## Skill Design Requirements

### `SKILL.md`

The skill frontmatter must contain only:

```yaml
---
name: performance-report-assistant
description: ...
---
```

The description must clearly trigger on:

- Chinese work reports.
- Weekly reports.
- Monthly performance self-reviews.
- Excel performance templates.
- Git commits.
- Leadership updates.
- Customer progress updates.

The body must instruct the agent to:

- Preserve the original Excel template whenever one exists.
- Copy the template and write values into cells instead of recreating the workbook.
- Ask only necessary interview questions.
- Prefer evidence from weekly reports, git commits, docs, tickets, meeting notes, or pasted text.
- Adapt output by audience.
- Use Chinese by default.
- Avoid overclaiming ownership.

### `references/intake-questions.md`

Include selective interview questions for:

- Report scenario.
- Audience.
- Date range.
- Whether a fixed Excel template exists.
- Most important work items.
- Evidence and measurable impact.
- Ownership level.
- Things to emphasize or avoid.

The skill should not ask all questions every time. It should ask only what is needed.

### `references/report-patterns.md`

Include default structures for:

- Weekly summary.
- Monthly performance self-review.
- Quarterly review.
- Leadership/headquarters update.
- Customer or non-expert progress update.
- Promotion or 述职 review.

Each structure should be easy to paste into company forms.

### `references/excel-template-workflow.md`

Include a checklist for:

- Inspecting workbook sheets, merged cells, formulas, hidden rows/columns, comments, and examples.
- Mapping report sections to exact cells.
- Filling a copied workbook.
- Preserving styles, row heights, column widths, merged cells, formulas, print areas, and sheet order.
- Verifying the output workbook.

### `scripts/collect_git_commits.py`

Create a Python script that:

- Accepts one or more repo paths.
- Accepts `--since` and `--until`.
- Optionally accepts `--author`.
- Outputs Markdown evidence grouped by repository.
- Uses `git -C <repo> log`.
- Does not modify repositories.

Example:

```bash
python scripts/collect_git_commits.py --repo C:\path\repo --since 2026-05-01 --until 2026-06-01 --output commits.md
```

### `scripts/fill_excel_template.py`

Create a Python script that:

- Accepts `--template`, `--mapping`, and `--output`.
- Copies the original `.xlsx` template.
- Loads the copied workbook with `openpyxl`.
- Writes only mapped cell values.
- Supports mapping formats like:

```json
{
  "Sheet1!B4": "本月重点完成...",
  "Sheet1!B5": "下月计划..."
}
```

and:

```json
{
  "Sheet1": {
    "B4": "本月重点完成...",
    "B5": "下月计划..."
  }
}
```

- Handles merged cells by writing to the merged range anchor cell.
- Turns on wrap text for written narrative cells when possible.
- Preserves existing styles and workbook structure.

## Enterprise WeChat Requirement

Do not assume Enterprise WeChat content can be fetched automatically.

The skill should use this fallback order:

1. If an authorized connector or browser automation path exists, try to fetch/export relevant weekly reports.
2. If no authorization exists, ask the user for the smallest manual action:
   - Export the target month's weekly reports.
   - Paste all weekly reports into one text file.
   - Provide screenshots or copied text.
3. Do not require the user to reformat weekly reports unless absolutely necessary.

## Writing Rules

Use Chinese by default.

Prefer this style:

- Specific.
- Outcome-first.
- Evidence-based.
- Professional but not inflated.
- Honest about blockers.
- Suitable for managers and non-technical readers.

Ownership wording must be accurate:

- `我主导`: the user drove planning, coordination, or final delivery.
- `我负责`: the user owned a defined module or deliverable.
- `我参与`: the user contributed but did not own the whole result.
- `我协同`: the user supported alignment or execution.

Avoid unsupported claims such as:

- “显著提升效率” without evidence.
- “大幅降低风险” without a concrete risk or mitigation.
- “为公司创造巨大价值” without business context.

## Validation Steps

After implementation, run these checks:

1. Validate the skill folder with the skill-creator validation script if available:

```bash
python path/to/quick_validate.py path/to/performance-report-assistant
```

If `PyYAML` or another validator dependency is missing, record that the validator could not run and continue with manual checks.

2. Run script help commands:

```bash
python scripts/collect_git_commits.py --help
python scripts/fill_excel_template.py --help
```

3. Test Excel filling:

- Create a tiny `.xlsx` template with:
  - one styled title cell,
  - one merged range,
  - one target cell.
- Create a mapping JSON.
- Run `fill_excel_template.py`.
- Confirm:
  - target content is written,
  - original title style remains,
  - merged range remains.

4. Inspect generated files and confirm:

- No placeholder TODO remains.
- `SKILL.md` frontmatter contains only `name` and `description`.
- `agents/openai.yaml` contains a short display name, short description, default prompt, and implicit invocation policy.
- Reference files are useful but not overly long.

## Acceptance Criteria

The work is complete only when:

- The skill folder exists with the required structure.
- The skill can guide an agent through template-preserving Excel report generation.
- It includes a clear fallback for Enterprise WeChat access limitations.
- It supports multiple report scenarios and audiences.
- It includes executable scripts for git commit collection and Excel template filling.
- Excel filling has been tested on a sample workbook.
- Any validation failure is explained clearly.

## Handoff Back For Review

After Claude Code finishes execution, provide:

- The final skill folder path.
- A short summary of files created or changed.
- The validation/test results.
- Any limitations, especially around Enterprise WeChat authorization or Excel rendering.
- Any suggested follow-up improvements before publishing to GitHub.
