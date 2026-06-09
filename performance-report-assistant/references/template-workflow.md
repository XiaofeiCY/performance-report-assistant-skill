# Template Workflow

Use this checklist when the user provides any fixed template, including Excel, Word, PowerPoint, Markdown, or another reusable report form.

## Classify

- Identify the file type and whether it is a blank template, a partially filled template, or a previous completed report.
- Treat previous completed reports as style and structure references only unless the user explicitly asks to reuse old content.
- If the template is Excel, also read `references/excel-template-workflow.md`.

## Inspect

- Identify visible sections, required fields, labels, headings, slides, pages, tables, placeholders, charts, comments, and examples.
- Identify protected areas that should not be touched: approvals, signatures, ratings, formulas, charts, metadata, headers/footers, and legal or customer-sensitive wording.
- Determine which areas are intended for generated content.
- Stop after inspection and report the proposed edit plan to the user. Do not write the file yet.

## Map

Create a mapping from report content to exact template locations:

```text
[Template area] -> [Generated content purpose]
```

Examples:

- `Excel: 绩效自评!C6` -> 本月重点工作
- `Word: “本周完成” section` -> 本周完成事项
- `PowerPoint: Slide 3 / progress table` -> 关键进展与风险
- `Markdown: ## 下周计划` -> 下周计划

If labels are ambiguous, quote the label and ask the user to confirm the target area.

## Confirm

Before writing to any template copy, show the user:

- the exact output copy that will be created,
- the exact fields, cells, paragraphs, sections, pages, or slides that will be edited,
- the areas that will not be touched,
- any uncertain mappings that need confirmation.

Wait for explicit confirmation such as "确认", "可以执行", or "按这个方案继续".

## Fill

- Copy the original template before editing.
- Write only confirmed content areas.
- Preserve layout, styles, tables, slide order, formulas, charts, page setup, and approval/signature areas.
- Keep generated content aligned with the original template's tone, length, and granularity.

## Verify

- Inspect the output after filling.
- Confirm the template structure is preserved.
- Confirm generated content landed in the intended areas.
- If rendering or screenshot tools are available, use them for visual QA on Word, PowerPoint, Excel, or other rich formats.
