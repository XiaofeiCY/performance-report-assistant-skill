---
name: performance-report-assistant
description: Create Chinese work reports from weekly reports, git commits, repository metrics, notes, and reusable templates while preserving template formatting. Use when drafting monthly performance self-reviews, weekly summaries, quarterly reviews, promotion/述职 materials, leadership updates, headquarters reports, customer-facing progress updates, or filling company report forms and templates across Excel, Word, PowerPoint, Markdown, or other formats.
---

# Performance Report Assistant

Turn scattered work evidence into a polished Chinese report through a guided interview. Default to an in-conversation preview; create persistent files only when the user explicitly requests export.

## Core Principles

- **Current-session evidence isolation**: every new report request starts with a fresh task-local state ledger. Conversation memory may inform preferences or style, but it is never current evidence by default. Previous generated reports, old WeCom results, old git statistics, old run directories, and prior task evidence do not enter the new evidence ledger automatically.
- **Template/reference is not evidence**: when the user calls an old report a template or reference (`模板`, `参考`, `只看格式`, `按这个结构`, etc.), classify it as `reference_only` immediately. Extract only structure and style (section order, grouping, indentation, bullets, line breaks, labels/brackets, tone, granularity). Never reuse its work items, repository/module names, people, dates, status, metrics, commit counts, conclusions, risks, or plans. Never ask whether its data is current or usable — the user's explicit label already answers that.
- **Preview-first**: default to drafting the full report in the conversation. Ask for an output location only after the user has reviewed the draft and explicitly requests a persistent file, export, or filled template copy.
- **Evidence-based**: extract facts first, then summarize impact, capability, risks, and next steps. Treat each evidence source independently — one failing must not block others.
- **Adapt wording to audience**: direct manager, senior leadership/headquarters, cross-functional partners, or external customers.
- **Preserve the user's template**: when a fixed template exists, copy and edit only intended content areas; do not recreate from scratch.
- **Templates are per-task**: do not persist a user's template or accepted draft as a global default unless the user explicitly agrees.

## Workflow

### 0. Initialize Session State

At the start of every new report-generation or content-integration request, initialize a task-local ledger:

```
report_type
audience
target_period
template_role        (none | fixed_blank | reference_only | current_evidence)
current_evidence_sources
reference_only_sources
source_status         (per source: pending | succeeded | failed | needs_user_input)
output_intent = preview
```

Old generated content is excluded from `current_evidence_sources` unless the user explicitly reintroduces it for the current period. Period-mismatched materials are silently classified as `skipped_period_mismatch` — do not ask the user to confirm their exclusion.

### 1. Guided Interview (Canonical Sequence)

Ask one step at a time. Skip fields the user has already answered. The canonical order and decision logic is in `references/intake-questions.md`.

1. Report type.
2. Audience.
3. Exact target period (resolve relative dates with `scripts/resolve_report_period.py`).
4. Template situation: fixed blank template, previous report as reference, or none.
5. Complete evidence-source menu (see Step 3).
6. Source-specific missing parameters only (git branch/author, WeCom authorization, etc.).
7. Evidence status summary.
8. Draft the complete report in the conversation.
9. Revise until the user accepts the content.
10. Only then, if the user wants a persistent artifact, confirm format and output location and write the file.

Do not ask an output-location question during steps 1-9 unless the user has already explicitly requested saving, exporting, or a filled file copy.

**Bundled answers (fast path)**: when the user provides answers to multiple interview steps in one message, accept all of them and jump ahead. Do not re-ask answered questions.

### 2. Classify Template / Reference

Classification rules, in priority order:

- If the user says `模板`, `参考`, `以前写过的内容供参考`, `只看格式`, `按这个结构`, or equivalent, classify as `reference_only` immediately. Extract only structural/style signals. Do not reuse content.
- If the user provides a previous filled report without saying whether it is evidence or reference, ask once: "这份内容是本周期实际事项，还是只作为格式/结构参考？如果只是参考，我不会复用里面的事项、仓库名或统计数字。"
- Fixed blank templates (`.xlsx`, `.docx`, `.pptx`, etc.) are inspected read-only during preview. A filled copy is written only after content is accepted and the user explicitly asks for one.
- A `reference_only` mark is final for the current session. Do not ask follow-up questions about whether its data could be current.

### 3. Gather Evidence

After report type, audience, period, and template role are known, present the complete evidence-source menu:

```
本周期素材可以组合选择：
1. 直接粘贴工作事项、周报草稿或补充说明
2. 当前周期的文档、会议纪要、需求/工单、PR 或截图
3. Git 本地仓库或仓库 URL（需要时再确认分支和 author）
4. 企业微信智能总结（仅在你选择后，按监督式采集流程执行）
5. 其他你指定的材料
6. 暂无更多素材，先基于现有内容起草
```

Do not present a repository as the only or default evidence source. Do not auto-trigger WeCom; it remains explicit opt-in. Template/reference material already classified as `reference_only` is not listed as current evidence.

**Git evidence**: see `references/intake-questions.md` for the branch/author confirmation workflow, and `references/git-evidence-rules.md` for collection rules (full-clone default, local fallback policy, pre-execution confirmation, expected metrics, evidence integrity). Run `scripts/collect_git_commits.py` without `--output` (stdout only) when no output location has been confirmed.

**WeCom Smart Summary**: explicit opt-in only. Full automation requires the user-supervised authorization checklist from `references/wecom-smart-summary-collector.md`. Preferred preview flow: run full-auto without `--output` or `--output-json` so the verified result prints to stdout and temporary diagnostics are cleaned on success. Only pass `--output`/`--output-json` when the user explicitly requests a persistent WeCom result file.

**Multi-source orchestration**: track each source independently. One source failing must not block others. Present a source status summary before drafting.

### 4. Draft & Revise (Preview Phase)

- Draft the complete report in the conversation. Do not write files.
- `先生成看看`, `先给我看`, `起草一版`, or an ordinary report request defaults to the preview phase.
- In preview phase, do not ask for an output directory.
- Git collection remains stdout-only. WeCom collection returns stdout-only (no Markdown/JSON files) unless the user explicitly requests persistent WeCom output files.
- A fixed template may be inspected read-only during preview. Draft the intended field content in the conversation. Ask for an output path only after the user approves the content and asks for a filled copy.
- Group work by themes over raw chronology unless the form requires dates.
- Use Chinese by default. Outcome-first, not activity-first. Specific but not boastful.

### 5. Export (Only on Explicit Request)

Enter the export phase only when the user explicitly requests a persistent file: "保存", "导出", "输出成文件", "帮我写成 Markdown", "填到模板里", etc.

1. Confirm format and absolute output path. Show the planned file path.
2. If the user provided a fixed template, inspect it, explain which sections/cells will be changed, and wait for confirmation before writing.
3. Write the file.
4. Report the final file path and any missing evidence.

If the user explicitly requests a file/export at the beginning (before the preview phase), it is valid to confirm the absolute output path before the first file-writing operation. Do not ask twice.

Evidence repositories are never implicit output destinations.

## Scripts

### collect_git_commits.py

Stdout-only by default (no file created):

```bash
python scripts/collect_git_commits.py --repo <path|url> --since YYYY-MM-DD --until YYYY-MM-DD [--author <name>] [--branch <branch>|--all-branches]
```

With output file — only after the user has confirmed an output location:

```bash
python scripts/collect_git_commits.py --repo <path|url> --since YYYY-MM-DD --until YYYY-MM-DD --output <absolute-path>
```

Full-clone is the default for remote URLs. Shallow clone (`--shallow-depth`) is explicit opt-in only. Local fallback, pre-execution confirmation, and expected metrics are documented in `references/git-evidence-rules.md`.

### resolve_report_period.py

```bash
python scripts/resolve_report_period.py --period last-week --today YYYY-MM-DD
python scripts/resolve_report_period.py --period this-week --today YYYY-MM-DD
```

Default weekly mode is `workweek` (Monday-Friday). Use `--week-mode natural` for Monday-Sunday.

### collect_wecom_smart_summary.py

Preferred preview flow (no persistent files; temp diagnostics auto-cleaned on success):

```bash
python -u scripts/collect_wecom_smart_summary.py --period "YYYY-MM-DD..YYYY-MM-DD"
```

With explicit output files (user explicitly requested persistent WeCom results):

```bash
python -u scripts/collect_wecom_smart_summary.py --period "YYYY-MM-DD..YYYY-MM-DD" --output <absolute-path>.md --output-json <absolute-path>.json --screenshot-dir <absolute-run-dir>
```

All modes: `--prompt-only` (print prompt, no files), `--probe-only` (read-only diagnostic, requires `--screenshot-dir`), `--semi-manual`, `--manual-input`. Full reference at `references/wecom-smart-summary-collector.md`.

### fill_excel_template.py

```bash
python scripts/fill_excel_template.py --template <path> --mapping mapping.json --output <absolute-path>
```

## Reference Files

- `references/intake-questions.md`: canonical interview sequence, complete evidence menu, guardrail prompts, reusable template memory rules.
- `references/git-evidence-rules.md`: remote full-clone default, local fallback policy, pre-execution confirmation, expected quantitative metrics, evidence integrity.
- `references/report-patterns.md`: default structures for weekly summaries, performance reviews, leadership updates, customer progress updates.
- `references/template-workflow.md`: checklist for preserving fixed templates across Excel, Word, PowerPoint, Markdown.
- `references/excel-template-workflow.md`: Excel-specific checklist.
- `references/wecom-smart-summary-collector.md`: collector capabilities, safety boundaries, state machine, diagnostics lifecycle.
