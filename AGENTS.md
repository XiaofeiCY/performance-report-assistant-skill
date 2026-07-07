# AGENTS.md

## Project Recovery Entry

Project path:

```text
E:\work\performance-report-assistant-skill
```

Core skill path:

```text
performance-report-assistant/
```

After entering this project, read in order:

1. `AGENTS.md`
2. `docs/status.md` top `Current Handoff Snapshot (2026-07-07)`
3. If maintaining the WeCom collector, read `performance-report-assistant/references/wecom-smart-summary-collector.md`
4. If working on report interview/generation behavior, read `performance-report-assistant/SKILL.md`

Do not recreate:

```text
CLAUDE.md
AGENT.md
```

The user deleted those files. The only root recovery entry is `AGENTS.md`.

## Collaboration Rules

When the user discusses requirements, product scope, acceptance criteria, task breakdown, project status, or execution handoff, Codex defaults to:

1. Understand and restate the need, including target, scope, constraints, risks, and acceptance criteria.
2. Convert the need into a professional task document that can be handed to Claude.
3. If Claude needs to execute work, first write/update project docs, then provide a copyable Claude prompt.
4. After Claude finishes, help the user review and accept/reject the result.

Unless the user explicitly asks Codex to implement, fix, delete, or run an operation directly, Codex should not bypass task documentation and do Claude's implementation work.

Project collaboration, execution handoff, acceptance results, blockers, and next plans must be reflected in `docs/status.md`. Ordinary Q&A should not create or update project files.

## Current State

- No pending Claude task.
- Recent output-location safety work is accepted.
- Recent WeCom progress/diagnostics lifecycle work is accepted.
- Project reduction was completed on 2026-07-07.
- Completed/deferred handoff docs under `docs/tasks/` were deleted after consolidation.
- Python cache under `performance-report-assistant/scripts/__pycache__/` was deleted.
- Old WeCom diagnostic run directory `outputs/wecom_runs/20260706-102206-RRI8/` was deleted after key facts were consolidated into `docs/status.md`.
- Current accepted report outputs remain in `outputs/`.

Current retained report outputs:

```text
outputs/weekly_report_2026-06-29_2026-07-03.md
outputs/weekly_git_stats_2026-06-29_2026-07-03.md
outputs/wecom_summary_live_2026-06-29_2026-07-03.md
outputs/wecom_summary_live_2026-06-29_2026-07-03.json
```

## Current Evidence Rules

Each new report interview/content-integration session must use the target period from the current interview as authoritative.

- Old windows, old WeCom summaries, old reports, old traces, old run directories, and old output files may be used as current evidence only when their period matches the current target period or the user explicitly asks to reuse them.
- If old materials clearly belong to a different period, automatically exclude them from current evidence.
- Period-mismatched materials may be used only as historical background, process validation records, or formatting/style references.

## Template Memory Rules

This skill supports multiple users and multiple report templates.

- User-provided templates, examples, and accepted drafts are current-task references by default.
- Do not persist them as global/default templates unless the user explicitly agrees.

## WeCom Collection Rules

Enterprise WeChat Smart Summary automation may run only after the user explicitly requests it and supervises/authorizes the current run.

Allowed:

- foreground/normalize Enterprise WeChat;
- screenshots, regional OCR, template matching;
- Interception input;
- add the current-run fingerprint to the prompt;
- click verified targets;
- read clipboard and verify the fingerprint.

Forbidden:

- send, delete, edit, or forward messages;
- continue when Enterprise WeChat is not foreground;
- click, paste, or copy before page state is verified;
- right-click copy;
- unknown-area `Ctrl+A/Ctrl+C`;
- multi-fixed-coordinate probing;
- left-menu vertical scanning;
- clicking body URLs, quotes, attachments, or body center to obtain scroll focus.

Recent accepted WeCom behavior:

- Live collection should be invoked with `python -u` so stage progress is visible.
- `--diagnostics-policy on-failure` is the default: successful full-auto runs clean transient diagnostics after outputs are saved and fingerprint verification passes.
- Failed runs retain diagnostics and write `failure_summary.md`.
- Cleanup must only touch the current run-specific diagnostics directory and must not delete final outputs or user files.
- `--probe-only` is diagnostic by nature and may retain diagnostics.

## Next Step Guidance

- Continuing the accepted weekly report: no further collection or git statistics are needed.
- Starting a new report period: re-confirm report type, audience, period, template situation, output location, and evidence sources.
- Maintaining the WeCom collector: read `performance-report-assistant/references/wecom-smart-summary-collector.md` first; do not run live automation unless the user again supervises and explicitly authorizes it.
