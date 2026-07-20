# AGENTS.md

## Recovery Entry

Project: `E:\work\performance-report-assistant-skill`

Core skill: `performance-report-assistant/`

Read in order:

1. `AGENTS.md`
2. `docs/status.md` top `Current Handoff Snapshot (2026-07-20)`
3. For WeCom collector work, `performance-report-assistant/references/wecom-smart-summary-collector.md`
4. For report interview/generation behavior, `performance-report-assistant/SKILL.md`

Do not recreate `CLAUDE.md` or `AGENT.md`. This is the only root recovery entry.

## Collaboration Workflow

For requirements, scope, acceptance, task breakdown, project status, or execution handoff:

1. Codex clarifies the objective, scope, constraints, risks, and acceptance criteria.
2. Codex writes an executable task document for Claude.
3. The user gives that document to Claude for implementation.
4. Codex and the user verify Claude's result.

Unless the user explicitly asks Codex to implement, fix, delete, or run an operation directly, Codex must not bypass
the task-document handoff or modify implementation code. Read-only inspection, analysis, documentation, task dispatch,
and acceptance are allowed.

When Claude execution is needed, first update project documentation, then provide a copyable Claude prompt containing
the entry files, task path, scope, exclusions, validation commands, and any supervised-operation prohibitions.

Record material project decisions, handoffs, acceptance results, blockers, and next steps in `docs/status.md`. Do not
create project documents for ordinary Q&A.

## Current State

- No pending Claude task.
- The interview, template/reference isolation, preview-first output lifecycle, Git evidence, WeCom diagnostics, and
  validator-safety refactor was accepted on 2026-07-20.
- Project reduction was completed on 2026-07-20. Completed task history and installed-only test artifacts were removed
  after consolidation into `docs/status.md`.
- Source-backed files are synchronized to `C:\Users\Lenovo\.claude\skills\performance-report-assistant`.
- Do not run WeCom full-auto without fresh user supervision and explicit authorization.

Retained accepted outputs:

```text
outputs/weekly_report_2026-06-29_2026-07-03.md
outputs/weekly_git_stats_2026-06-29_2026-07-03.md
outputs/wecom_summary_live_2026-06-29_2026-07-03.md
outputs/wecom_summary_live_2026-06-29_2026-07-03.json
```

These outputs are historical deliverables, not automatic evidence for a new period.

## Standing Report Rules

- The current interview's exact target period is authoritative.
- Old reports, outputs, WeCom results, traces, and git statistics are excluded from current evidence unless their period
  matches or the user explicitly opts in.
- Material explicitly called a template/reference is `reference_only`: use structure/style only, never its work facts.
- Do not re-ask whether template data is usable after the user has classified it as a template/reference.
- Present the complete evidence-source menu, including direct material, files, git, supervised WeCom collection, other
  sources, and no additional evidence.
- Default to an in-conversation preview. Ask for format and absolute output location only after an explicit export/save
  request.
- User templates and accepted drafts remain current-task references unless broader persistence is explicitly approved.

## WeCom Safety Rules

Allowed only during a supervised, explicitly authorized run:

- foreground/normalize WeCom;
- screenshots, regional OCR, and template matching;
- prompt input with the current fingerprint;
- verified target clicks, bounded result scrolling, clipboard read, and exact fingerprint verification.

Forbidden:

- send, delete, edit, or forward messages;
- continue while WeCom is not foreground;
- click, paste, or copy before page state is verified;
- right-click copy or unknown-area `Ctrl+A/Ctrl+C`;
- multi-fixed-coordinate probing or left-menu vertical scanning;
- clicking body URLs, quotes, attachments, or body center to obtain scroll focus.

Operational requirements:

- run live collection with `python -u`;
- default to stdout-first and `%TEMP%\wecom_runs\<run-id>` diagnostics;
- clean only the current owned run after success;
- retain failed diagnostics with `failure_summary.md`;
- never delete failure diagnostics without separate authorization;
- preserve lower combined action-bar search and exact final clipboard fingerprint verification.

If copying becomes unstable, obtain the failed run's `--screenshot-dir` and inspect `trace.jsonl`, `ocr/`, and
`regions/` before proposing a fix.

## Next Step

- New report: reconfirm report type, audience, exact period, template role, and evidence sources; preview before export.
- WeCom maintenance: read the collector reference first and do not run live automation without fresh authorization.
