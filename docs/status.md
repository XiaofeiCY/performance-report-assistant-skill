# Project Status

## Current Handoff Snapshot (2026-07-06)

This is the first section to read after switching Codex / Claude windows.

Project entry file:

```text
AGENTS.md
```

Do not recreate:

```text
CLAUDE.md
AGENT.md
```

Current state:

- No pending Claude task.
- Current handoff task is complete: project documentation was reduced and current status was consolidated.
- Completed task handoff docs under `docs/tasks/` were removed after acceptance.
- Python cache under `performance-report-assistant/scripts/__pycache__/` was removed.
- Current retained report outputs and the latest successful WeCom run were kept.

Accepted task document:

```text
docs/tasks/2026-07-06-output-location-safety.md
```

Trigger:

- User tested the installed skill from a random business repository and observed that the agent created `outputs/` plus git/WeCom artifacts under that repository without first asking for an output location.
- This is considered a safety issue because evidence repositories must not be treated as implicit output destinations.

Acceptance state:

- Output-location safety accepted after final Codex review.
- Relative file-writing outputs are rejected by script-side guardrails for git evidence, WeCom markdown/JSON outputs, WeCom diagnostic directories, and Excel template filling.
- `collect_git_commits.py` without `--output` remains stdout-only and file-free.
- `collect_wecom_smart_summary.py --prompt-only` remains file-free and prints absolute placeholder save commands.
- Installed Claude skill copies were synchronized and verified by SHA256.

## Recent Accepted Work

WeCom Smart Summary collector:

- Temporary Windows keep-awake guard accepted. During supervised desktop automation, the collector requests Windows to keep the display/system awake with `SetThreadExecutionState`, logs enable/disable/failure to the current run trace, and releases the request when the process exits.
- Console-stage prompts accepted. The supervised automation path now prints clear stage banners without adding overlays, GUI windows, toasts, or anything that can enter WeCom screenshots.
- History/result page classification fix accepted. Saved failure artifacts confirmed `cycle0` remains `main_page`, while `cycle1` and `cycle2` now classify as `summary_history_page`; old fingerprints are treated only as history/header evidence, not current-run result evidence.
- Default WeCom prompt source fix accepted. Agents must show the default prompt from `collect_wecom_smart_summary.py --prompt-only` and must not invent a separate default prompt.

Workflow and evidence:

- Full-flow low-risk latency optimization accepted: added read-only `analyze_trace.py`, reduced unnecessary interview repetition, and did not change the WeCom core state machine or safety gates.
- Git evidence correctness accepted: remote URL clones are full clone by default (`--shallow-depth 0`); shallow clone remains explicit opt-in only.
- Installed Claude skill sync accepted on 2026-07-06.

## Current Retained Outputs

Keep these current-period report outputs:

```text
outputs/weekly_report_2026-06-29_2026-07-03.md
outputs/weekly_git_stats_2026-06-29_2026-07-03.md
outputs/wecom_summary_live_2026-06-29_2026-07-03.md
outputs/wecom_summary_live_2026-06-29_2026-07-03.json
```

Latest retained successful WeCom diagnostic run:

```text
outputs/wecom_runs/20260706-102206-RRI8/
```

Key trace facts:

- Fingerprint: `PRAS-20260706-102206-5678`
- `paste_verify visible_fingerprint=true`
- `copy_result phase=fp_scroll context_confirmed=true use_frame=fp_scroll_1`
- `copy_result phase=action_row_geometry region=lower_combined selected="复制" screen_coords=[564,1050]`
- `copy_result method=ocr_direct result_len=1883 fingerprint_match=true`
- `automation_complete fingerprint_match=true`

## Report Evidence Snapshot

Report type: 周报

Audience: 直属领导

Period:

```text
2026-06-29 至 2026-07-03
```

Git evidence used for the accepted report:

```text
Repos:
http://47.105.186.81:9006/asi2.x/asi-station-mini.git
http://47.105.186.81:9006/asi2.x/asi-station-webapp.git

Scope:
- Branches: all branches
- Author: chayne
- Period: 2026-06-29 至 2026-07-03

Fallback:
- Remote access timed out during the accepted report round.
- Local fallback repos were used only because their origin remotes matched the user-provided URLs:
  E:\work\asi-station-mini
  E:\work\asi-station-webapp

Accepted report result:
- asi-station-mini: 4 commits, 2 changed files, +33/-3
- asi-station-webapp: 0 commits for chayne in the target period
```

Note:

- Later full-clone validation found additional all-branch remote commits in a test run. Those were used to validate git evidence correctness, not to rewrite the already accepted report.

## Standing Rules

Current-period evidence:

- Each new report interview uses the target period from that interview as authoritative.
- Old WeCom summaries, old reports, old traces, old run directories, or old output files are automatically excluded from current evidence when their period does not match, unless the user explicitly asks to reuse them.

Template memory:

- User-provided templates/examples/accepted drafts are current-task references by default.
- Do not save them as global/default templates unless the user explicitly agrees.

Git evidence:

- If repo list, target period, branch scope, and author filter are already explicit in the current interview, use the compact pre-execution summary and avoid repeated questioning.
- If remote repo access times out, local fallback is allowed only when local `origin` matches the user-provided URL, and the fallback must be disclosed.
- Full clone is the default for remote URL evidence collection. Shallow clone is explicit opt-in only.

WeCom automation:

- Do not run full-auto WeCom live automation unless the user again supervises and explicitly authorizes it.
- Do not describe the collector as unattended, cross-environment stable, or generally compatible with all WeCom UI variants.
- Forbidden: sending/deleting/editing/forwarding messages, continuing when WeCom is not foreground, right-click copy, unknown-area `Ctrl+A/Ctrl+C`, multi-fixed-coordinate probing, left-menu vertical scanning, or clicking body text/URLs to obtain scroll focus.

## Cleanup Completed

Project reduction completed on 2026-07-06.

Deleted in this cleanup:

- Completed task handoff docs from `docs/tasks/`.
- Python cache directory `performance-report-assistant/scripts/__pycache__/`.

Previously deleted in earlier cleanup:

- Old WeCom run directory `outputs/wecom_runs/20260703-160202-REJ2/`.
- Temporary git statistics outputs `outputs/commits_mini.md` and `outputs/commits_webapp.md`.
- Earlier Python cache files.

Kept:

- Short recovery entry docs: `AGENTS.md`, `docs/status.md`.
- Current report outputs and latest successful WeCom diagnostic run.
- Core skill, scripts, references, README files, template assets, and agent metadata.
- Tracked validation/extraction helper scripts, because they are repository tooling rather than disposable handoff docs.

## If Work Continues

For a new report:

1. Ask report type, audience, period, template situation, output location, and evidence sources.
2. Resolve relative periods with `performance-report-assistant/scripts/resolve_report_period.py`.
3. Filter old evidence by period before using it.
4. If repos are provided, collect git evidence after scope is clear.
5. Trigger WeCom collection only after explicit user request and authorization.

For collector maintenance:

1. Read `performance-report-assistant/references/wecom-smart-summary-collector.md`.
2. Keep changes narrow.
3. Do not run live automation without explicit supervised authorization.
