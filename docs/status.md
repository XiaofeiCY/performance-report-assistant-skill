# Project Status

## Current Handoff Snapshot (2026-07-03)

This is the first section to read after switching Codex / Claude windows.

Current project entry file:

```text
AGENTS.md
```

Do not recreate:

```text
CLAUDE.md
AGENT.md
```

## Current Outcome

The current weekly-report round is complete.

- Report type: 周报
- Audience: 直属领导
- Period: `2026-06-29 至 2026-07-03`
- User accepted the drafted report and copied it for use.
- The user-provided report structure was only used as this task's reference and was not saved as a global template.

Current retained report and evidence:

```text
outputs/weekly_report_2026-06-29_2026-07-03.md
outputs/weekly_git_stats_2026-06-29_2026-07-03.md
outputs/wecom_summary_live_2026-06-29_2026-07-03.md
outputs/wecom_summary_live_2026-06-29_2026-07-03.json
outputs/wecom_runs/20260703-160202-REJ2/
```

## Latest Collector Maintenance

Latest completed maintenance: optimize WeCom Smart Summary copy-stage latency while preserving safe automation.

Accepted on 2026-07-03 by Codex static/offline review.

Modified file:

```text
performance-report-assistant/scripts/collect_wecom_smart_summary.py
```

What changed:

- Reuses `fp_scroll_*` OCR text in Phase 2 instead of recomputing the same full-frame OCR.
- Merges lower `main_body` OCR for both `main_body_ocr` and action-row geometry.
- Keeps `main_body_ocr` before geometry / `lower_combined` / scroll fallbacks.
- Keeps `lower_combined` for the already verified boundary case where the action row straddles `main_body` and `bottom_action_bar`.
- Adds `copy_timing` trace logs for key copy-stage steps.
- Keeps `wheel_without_click`, `foreground_lost` fail-fast, and exact clipboard fingerprint verification.

Validated statically:

```powershell
python -m py_compile .\performance-report-assistant\scripts\collect_wecom_smart_summary.py
python .\performance-report-assistant\scripts\collect_wecom_smart_summary.py --prompt-only --period "2026-06-29..2026-07-03"
rg -n "main_body_ocr|lower_combined|copy_frame_source|use_frame|wheel_without_click|foreground_lost|fingerprint_match|manual|Ctrl\\+A|Ctrl\\+C|right-click|右键|content_cx|content_cy" performance-report-assistant\scripts\collect_wecom_smart_summary.py
```

No full-auto WeCom live automation was run during Codex acceptance. Any future full-auto live test must be supervised and explicitly authorized by the user in the current conversation.

## Latest WeCom Live Evidence

Latest successful supervised live run:

```text
outputs/wecom_runs/20260703-160202-REJ2/
```

Key trace facts:

- `copy_result phase=fp_scroll context_confirmed=true use_frame=fp_scroll_1`
- `copy_result phase=copy_search source_frame=fp_scroll_1`
- `copy_result phase=action_row_geometry region=lower_combined ... selected="复制" screen_coords=[564,1050]`
- `copy_result method=ocr_direct result_len=2087 fingerprint_match=true`
- `automation_complete fingerprint_match=true`

Earlier same-day failure and repair runs have been summarized here and removed during cleanup.

## Git Evidence

User-provided repos:

```text
http://47.105.186.81:9006/asi2.x/asi-station-mini.git
http://47.105.186.81:9006/asi2.x/asi-station-webapp.git
```

Scope:

- Branches: all branches
- Author: `chayne`
- Period: `2026-06-29 至 2026-07-03`

Remote access timed out. Local fallback repos were used only because their `origin` remotes match the user-provided URLs:

```text
E:\work\asi-station-mini
E:\work\asi-station-webapp
```

Result:

- `asi-station-mini`: 4 commits, 2 changed files, `+33/-3`
- `asi-station-webapp`: 0 commits for `chayne` in the target period

## Cleanup Completed

Project reduction completed on 2026-07-03.

Deleted:

- Completed task handoff docs from `docs/tasks/`.
- Old WeCom run directories except the latest successful current-period run `outputs/wecom_runs/20260703-160202-REJ2/`.
- Early root build plan `claude-code-skill-build-plan.md`.

Kept:

- Short recovery entry docs: `AGENTS.md`, `docs/status.md`.
- Current weekly report and evidence outputs.
- Latest successful WeCom run diagnostics.
- Core skill, scripts, references, README files, and template assets.

## Standing Rules

Current-period evidence:

- Each new report interview uses the target period from that interview as authoritative.
- Old WeCom summaries, old reports, old traces, old run directories, or old output files are automatically excluded from current evidence when their period does not match, unless the user explicitly asks to reuse them.

Template memory:

- User-provided templates/examples/accepted drafts are current-task references by default.
- Do not save them as global/default templates unless the user explicitly agrees.

Git evidence:

- If repo list, target period, branch scope, and author filter are already explicit in the current interview, run read-only git statistics without demanding a fixed confirmation phrase.
- If remote repo access times out, local fallback is allowed only when local `origin` matches the user-provided URL, and the fallback must be disclosed.

WeCom automation:

- Do not run full-auto WeCom live automation unless the user again supervises and explicitly authorizes it.
- Do not describe the collector as unattended, cross-environment stable, or generally compatible with all WeCom UI variants.
- Forbidden: sending/deleting/editing/forwarding messages, continuing when WeCom is not foreground, right-click copy, unknown-area `Ctrl+A/Ctrl+C`, multi-fixed-coordinate probing, left-menu vertical scanning, or clicking body text/URLs to obtain scroll focus.

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
