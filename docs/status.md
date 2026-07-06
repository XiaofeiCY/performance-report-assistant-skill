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
- The weekly-report round for `2026-06-29 至 2026-07-03` is complete; the user accepted and used the draft.
- The WeCom Smart Summary collector has a retained successful supervised run from `2026-07-06`.
- The default WeCom prompt source fix, full-flow latency analysis helper, git evidence correctness return fix, and installed Claude skill sync have all been accepted.
- Project reduction was completed after those acceptances; completed task handoff docs and stale diagnostics were removed.

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

## Accepted Changes Since Last Report

WeCom default prompt source:

- `performance-report-assistant/SKILL.md` now requires agents to show the default WeCom prompt from `collect_wecom_smart_summary.py --prompt-only`.
- Agents must not invent or paraphrase a separate default prompt.
- Custom prompts must be explicit, for example via `--prompt-file`.

Full-flow latency optimization, low-risk phase:

- Added `performance-report-assistant/scripts/analyze_trace.py`, a read-only trace timing analyzer.
- Reduced unnecessary interview repetition through fast-path guidance in `SKILL.md` and `references/intake-questions.md`.
- Did not change WeCom collector core state machine, OCR decisions, copy strategy, wait-result logic, fingerprint verification, or foreground/page-state safety checks.

Git evidence correctness:

- `collect_git_commits.py` restores correctness-first behavior: remote URL clones are full clone by default (`--shallow-depth 0`).
- `--shallow-depth N` remains available only as explicit opt-in and is documented as unsafe for evidence-complete all-branches personal reports.
- Offline validation confirmed default full clone sees commits on both default and non-default remote branches.

Installed Claude skill sync:

- Completed on 2026-07-06.
- Source: `E:\work\performance-report-assistant-skill\performance-report-assistant`
- Destination: `C:\Users\Lenovo\.claude\skills\performance-report-assistant`
- Backup: `C:\Users\Lenovo\.claude\skills\performance-report-assistant.backup-20260706-110007`
- Excluded from mirror sync: `outputs`, `agents`, `__pycache__`, `.git`, `*.pyc`, `pc_commits.md`, `mini_commits.md`.
- Verified key file hashes and installed-copy `py_compile`.

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

Deleted:

- Completed task handoff docs from `docs/tasks/`.
- Old WeCom run directory `outputs/wecom_runs/20260703-160202-REJ2/`.
- Temporary git statistics outputs `outputs/commits_mini.md` and `outputs/commits_webapp.md`.
- Python cache directory `performance-report-assistant/scripts/__pycache__/`.

Kept:

- Short recovery entry docs: `AGENTS.md`, `docs/status.md`.
- Current report outputs and latest successful WeCom diagnostic run.
- Core skill, scripts, references, README files, template assets, and agent metadata.

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
