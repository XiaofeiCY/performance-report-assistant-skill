# Project Status

## Current Handoff Snapshot (2026-07-07)

Read this section immediately after switching Codex / Claude windows.

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
- WeCom Smart Summary bottom action bar copy-button fix has been accepted.
- Project documentation reduction / stale-state cleanup has been completed on 2026-07-07.
- Recent WeCom and output-safety work has been accepted and consolidated here.
- Completed / deferred task handoff docs under `docs/tasks/` have been removed after consolidation.
- Python cache under `performance-report-assistant/scripts/__pycache__/` has been removed again.
- The old retained WeCom diagnostic run directory was removed after key trace facts were consolidated here.
- Current report deliverables remain in `outputs/`.

## WeCom Bottom Action Bar Copy Fix Accepted

WeCom copy-stage failure investigated, fixed by Claude, and accepted on 2026-07-07.

Failed run directory:

```text
C:\Users\Lenovo\Desktop\wecom_runs\20260707-104525-A7K2\
```

Note: the screenshot looked like `AZK2`, but the actual directory is `A7K2`.

Fingerprint:

```text
PRAS-20260707-104607-9458
```

Observed result:

- Generation completed and stabilized.
- `wait_result` reached `result_detected`.
- `before_copy.png` and `copy_scroll_1.png` show the result page with the bottom action row visible.
- The bottom action row visibly contains the three actions: new smart document, send email, and copy.
- `trace.jsonl` copy stage reported `has_result_actions=false`, then `method=none error=all_strategies_failed`.
- `copy_scroll_1.png` was visually unchanged from `before_copy.png`; the scroll did not reveal a new copy target.

Root cause from read-only analysis:

- `_action_copy_result()` first builds `all_text` from `main_body` only.
- `_action_row_visible` is therefore false when the action buttons live in `bottom_action_bar`.
- The existing `lower_combined` bottom-of-window search is gated behind `_action_row_visible`, so it is skipped exactly when it is needed.
- Offline OCR on `bottom_action_bar` alone returned no text, but OCR on the full image bottom 30 percent detected the action row and `_estimate_copy_from_action_row()` estimated the copy button at approximately `(564, 959)`.

Accepted fix:

- `performance-report-assistant/scripts/collect_wecom_smart_summary.py` now runs main-body lower geometry and lower combined bottom-of-window search without gating them on `_action_row_visible` from `main_body` OCR.
- The lower combined search logs `lower_combined_search`, `combined_text_preview`, and `action_signals_found` diagnostics.
- Copy clicks still require verified result-page context before the copy stage and exact clipboard fingerprint verification after clicking.
- Forbidden strategies remain forbidden: no right-click copy, no unknown-area `Ctrl+A/Ctrl+C`, no multi-fixed-coordinate probing, no left-menu vertical scanning.

Acceptance validation:

```text
python -m py_compile performance-report-assistant/scripts/collect_wecom_smart_summary.py
python performance-report-assistant/scripts/_validate_copy_fix.py
python performance-report-assistant/scripts/analyze_trace.py C:\Users\Lenovo\Desktop\wecom_runs\20260707-104525-A7K2\trace.jsonl
```

Validation result:

- `py_compile`: PASS
- `_validate_copy_fix.py`: 49 passed, 0 failed
- `analyze_trace.py`: PASS on the retained A7K2 failure trace

## Recent Accepted Work

Output location safety:

- The skill must confirm an output location before any file-writing command.
- Evidence repositories are inputs only, not implicit output destinations.
- Script-side guardrails reject relative file-writing paths for:
  - `collect_git_commits.py --output`
  - `collect_wecom_smart_summary.py --output`
  - `collect_wecom_smart_summary.py --output-json`
  - `collect_wecom_smart_summary.py --screenshot-dir`
  - `fill_excel_template.py --output`
- `collect_git_commits.py` without `--output` remains stdout-only and file-free.
- `collect_wecom_smart_summary.py --prompt-only` remains file-free and prints absolute placeholder save commands.
- Installed Claude skill copies were synchronized and verified by SHA256 during acceptance.

WeCom progress and diagnostics lifecycle:

- Full-auto stage/progress messages flush immediately.
- `SKILL.md` instructs agents to use `python -u` for live WeCom collection so progress is visible.
- `--diagnostics-policy on-failure|keep` is available.
- Default `on-failure` policy cleans transient diagnostics after successful full-auto output save and fingerprint verification.
- Cleanup is guarded by run-directory identity and final-output-file checks; it must not delete final outputs or user files.
- Failed runs keep diagnostics and write `failure_summary.md`.
- `--probe-only` remains diagnostic by nature, so successful probe diagnostics may be retained for inspection.

WeCom collector maintenance already accepted:

- Windows keep-awake guard during supervised desktop automation.
- Console-only stage prompts; no overlay, GUI, toast, or visual element over WeCom.
- History/result page classification fix: old Smart Summary result pages no longer classify as ordinary `main_page`; old fingerprints are history evidence only.
- Default WeCom prompt source fix: agents must show the default prompt from `collect_wecom_smart_summary.py --prompt-only`.

Workflow and evidence:

- Full-flow low-risk latency optimization accepted: added read-only `analyze_trace.py`, reduced unnecessary interview repetition, and preserved the WeCom safety gates.
- Git evidence correctness accepted: remote URL clones are full clone by default; shallow clone remains explicit opt-in only.
- Installed Claude skill sync accepted after recent changes.

## Current Retained Outputs

Keep these accepted report outputs:

```text
outputs/weekly_report_2026-06-29_2026-07-03.md
outputs/weekly_git_stats_2026-06-29_2026-07-03.md
outputs/wecom_summary_live_2026-06-29_2026-07-03.md
outputs/wecom_summary_live_2026-06-29_2026-07-03.json
```

The old diagnostic run directory below has been deleted during the 2026-07-07 cleanup:

```text
outputs/wecom_runs/20260706-102206-RRI8/
```

Retained key facts from that deleted successful run:

- Fingerprint: `PRAS-20260706-102206-5678`
- `paste_verify visible_fingerprint=true`
- `copy_result phase=fp_scroll context_confirmed=true use_frame=fp_scroll_1`
- `copy_result phase=action_row_geometry region=lower_combined selected="copy" screen_coords=[564,1050]`
- `copy_result method=ocr_direct result_len=1883 fingerprint_match=true`
- `automation_complete fingerprint_match=true`

## Accepted Report Evidence Snapshot

Report type: weekly report

Audience: direct manager

Period:

```text
2026-06-29 to 2026-07-03
```

Git evidence used for the accepted report:

```text
Repos:
http://47.105.186.81:9006/asi2.x/asi-station-mini.git
http://47.105.186.81:9006/asi2.x/asi-station-webapp.git

Scope:
- Branches: all branches
- Author: chayne
- Period: 2026-06-29 to 2026-07-03

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

- User-provided templates, examples, and accepted drafts are current-task references by default.
- Do not save them as global/default templates unless the user explicitly agrees.

Git evidence:

- If repo list, target period, branch scope, and author filter are already explicit in the current interview, use the compact pre-execution summary and avoid repeated questioning.
- If remote repo access times out, local fallback is allowed only when local `origin` matches the user-provided URL, and the fallback must be disclosed.
- Full clone is the default for remote URL evidence collection. Shallow clone is explicit opt-in only.

WeCom automation:

- Do not run full-auto WeCom live automation unless the user again supervises and explicitly authorizes it.
- Do not describe the collector as unattended, cross-environment stable, or generally compatible with all WeCom UI variants.
- Forbidden: sending/deleting/editing/forwarding messages, continuing when WeCom is not foreground, right-click copy, unknown-area `Ctrl+A/Ctrl+C`, multi-fixed-coordinate probing, left-menu vertical scanning, or clicking body text/URLs to obtain scroll focus.
- If copy-stage instability recurs, first request the failed run-specific `--screenshot-dir` and inspect `trace.jsonl`, `ocr/`, and `regions/` before proposing code changes.

## Cleanup Completed

Project reduction completed on 2026-07-07.

Latest reduction pass completed on 2026-07-07:

- Removed empty `docs/tasks/` directory after accepted task consolidation.
- Refreshed `AGENTS.md` current state with the accepted bottom action bar copy-button fix.
- Refreshed `performance-report-assistant/references/wecom-smart-summary-collector.md` so it no longer claims the deleted `outputs/wecom_runs/20260706-102206-RRI8/` run directory is retained.
- Confirmed `outputs/` contains only the accepted report deliverables listed above.
- Confirmed no `CLAUDE.md`, `AGENT.md`, `outputs/wecom_runs/`, or `performance-report-assistant/scripts/__pycache__/` project artifacts remain.

Deleted in this cleanup:

- Completed task handoff docs from `docs/tasks/`.
- Deferred copy-stage task handoff doc after status consolidation.
- Empty `docs/tasks/` directory after task consolidation.
- Python cache directory `performance-report-assistant/scripts/__pycache__/`.
- Old WeCom diagnostic run directory `outputs/wecom_runs/20260706-102206-RRI8/`.

Previously deleted in earlier cleanup:

- Old WeCom run directory `outputs/wecom_runs/20260703-160202-REJ2/`.
- Temporary git statistics outputs `outputs/commits_mini.md` and `outputs/commits_webapp.md`.
- Earlier Python cache files.

Kept:

- Short recovery entry docs: `AGENTS.md`, `docs/status.md`.
- Current accepted report outputs listed above.
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
