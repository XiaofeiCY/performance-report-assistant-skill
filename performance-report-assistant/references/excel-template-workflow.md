# Excel Template Workflow

Use this checklist when the user provides a company Excel performance form.

## Inspect

- Identify sheet names and visible sections.
- Check merged cells, formulas, protected sheets, hidden rows/columns, comments, and existing examples.
- Determine whether fields are free-text, score fields, dates, dropdowns, or formula-driven cells.
- Never overwrite approval, signature, formula, or metadata cells unless the user asks.
- Stop after inspection and report the proposed edit plan to the user. Do not fill the workbook yet.

## Map

Create a mapping from report sections to exact cells:

```json
{
  "绩效自评!C6": "本月重点完成...",
  "绩效自评!C7": "存在问题及改进..."
}
```

If labels are ambiguous, quote the label and ask the user to confirm the target cell.

## Confirm

Before writing to any workbook, show the user:

- The exact workbook copy that will be created.
- The exact sheets and cells or sections that will be edited.
- The areas that will not be touched, especially formulas, score fields, approval fields, signatures, and formatting.
- Any uncertain mappings that need confirmation.

Wait for explicit confirmation such as "确认", "可以执行", or "按这个方案继续".

## Fill

- Copy the original workbook before editing.
- Write only target cell values.
- Preserve styles, merged cells, row heights, column widths, formulas, print areas, and sheet order.
- Turn on wrap text for filled narrative cells when possible.

## Verify

- Open or inspect the output workbook after filling.
- Confirm the original template and filled copy have the same sheet names.
- Confirm formulas still exist where expected.
- Confirm text did not land inside the wrong merged cell.
- If rendering tools are available, render or screenshot the workbook for visual QA.

## If Template Is Missing

Use `references/report-patterns.md` and create a simple workbook only as a fallback. Tell the user that a future run will preserve formatting better if they provide the actual company template.
