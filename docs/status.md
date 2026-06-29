# Project Status

## Current Understanding

This repository contains the `performance-report-assistant` Claude Code / Codex skill. The skill helps Chinese workplace users turn weekly reports, git commits, work notes, and fixed templates into polished work reports while preserving the user's original template format whenever possible.

The core workflow is:

1. Interview the user step by step.
2. Confirm report type, audience, date range, template situation, output location, and evidence sources.
3. Inspect fixed templates before editing.
4. Show exact planned changes and wait for explicit user confirmation.
5. Fill a copied template, not the original file.
6. Summarize inputs, assumptions, repository metrics, filled fields, output path, and remaining evidence gaps.

## Files Reviewed

- `README.md`
- `README.zh-CN.md`
- `claude-code-skill-build-plan.md`
- `performance-report-assistant/SKILL.md`
- `performance-report-assistant/agents/openai.yaml`
- `performance-report-assistant/references/intake-questions.md`
- `performance-report-assistant/references/report-patterns.md`
- `performance-report-assistant/references/template-workflow.md`
- `performance-report-assistant/references/excel-template-workflow.md`
- `performance-report-assistant/scripts/collect_git_commits.py`
- `performance-report-assistant/scripts/fill_excel_template.py`
- `performance-report-assistant/scripts/resolve_report_period.py`

## Validation Results (2026-06-29)

- `python scripts/collect_git_commits.py --help` — passed.
- `python scripts/fill_excel_template.py --help` — passed.
- `python scripts/resolve_report_period.py --help` — passed.

## Documentation Sync Completed

- `README.md` and `README.zh-CN.md`: repository structure block updated to include `template-workflow.md` and `resolve_report_period.py`; script description section added for `resolve_report_period.py`.
- `claude-code-skill-build-plan.md`: "Current Status Notes" section added, preserving original plan as historical context.

## Open Items

- Excel sample fill validation has not yet been recorded. Should be run before publishing or handoff.
- No skill behavior, reference workflow, script code, or agent config was changed in this sync.

## Date Boundary Fix Validation (2026-06-29)

- Claude updated `performance-report-assistant/scripts/collect_git_commits.py` to normalize date-only `--since` and `--until` values.
- `YYYY-MM-DD` `--since` values are now expanded to `YYYY-MM-DD 00:00:00`.
- `YYYY-MM-DD` `--until` values are now expanded to `YYYY-MM-DD 23:59:59`.
- Explicit datetime inputs are preserved.
- Codex validated with a temporary git repository:
  - Workweek range `2026-06-29` to `2026-07-03` included Monday morning, Wednesday noon, and Friday evening commits.
  - The same workweek range excluded a Saturday commit.
  - Monthly range `2026-07-01` to `2026-07-31` included a `2026-07-31` evening commit.
  - Explicit datetime range `2026-06-29 10:00:00` to `2026-07-03 17:00:00` preserved the narrower boundary and excluded commits outside that time window.
  - Repository metrics, file touch frequency, author distribution, and daily distribution used the corrected range.

## Remaining Open Items

- Excel sample fill validation has not yet been recorded. Should be run before publishing or handoff.
