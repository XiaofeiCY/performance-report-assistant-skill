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

User accepted the drafted report and copied it for use.

## Latest Claude Task Acceptance

User requested changing the WeCom Smart Summary default prompt scope.

Task document:

```text
docs/tasks/update-wecom-summary-prompt-scope.zh-CN.md
```

Acceptance result: passed on 2026-07-03.

Requested change:

- Replace the narrow default focus on temporary production data fixes / online data maintenance.
- New default focus: summarize what was done during the target period, which people and groups contacted the user, and what work output the user produced in each relevant conversation.
- Keep truthfulness constraints and do not run full-auto WeCom desktop tests unless the user supervises and explicitly authorizes.

Verified by Codex:

- `python .\performance-report-assistant\scripts\collect_wecom_smart_summary.py --prompt-only --period "2026-06-29..2026-07-03"` generated the new prompt with people/group/work-output scope.
- `rg -n "临时生产修数|生产数据处理|线上数据维护|业务方临时数据修正|只列出真实发生" performance-report-assistant` found only the retained truthfulness constraint.
- `python -m py_compile .\performance-report-assistant\scripts\collect_wecom_smart_summary.py` passed.

Final retained draft:

```text
outputs/weekly_report_2026-06-29_2026-07-03.md
```

## Current Report Context

- Report type: 周报
- Audience: 直属领导
- Period label from user: 本周
- Resolved workweek period: `2026-06-29 至 2026-07-03`
- Template/example: user-pasted text structure only, used as current-task reference
- Template persistence: not saved as a global/default template

Accepted report content summarized:

- 智检小程序【业务统计】：业务人员选择器清空重置、默认值调整为“请选择”、无匹配时不自动选中第一项、月度明细筛选/查询稳定性调整。
- 智检小程序【预检】：预检开始页接入“是否新车”数据回填，动态字段必填规则同步，接口字段缺失问题跟进验证。
- 业务支持【临时数据修正】：和县精诚车检客户跨月挂账数据归属 / 报表口径沟通，建议财务备注记录。

Accepted stats line:

```text
本周 2 个仓库，chayne 共 4 次提交（PC 0 / 小程序 4），变更文件 2 个，+33/-3 行。
```

## Evidence Kept

```text
outputs/weekly_git_stats_2026-06-29_2026-07-03.md
outputs/wecom_summary_live_2026-06-29_2026-07-03.md
outputs/wecom_summary_live_2026-06-29_2026-07-03.json
outputs/wecom_runs/20260703-110152-77IJ/
```

Git evidence:

- User provided repos:
  - `http://47.105.186.81:9006/asi2.x/asi-station-mini.git`
  - `http://47.105.186.81:9006/asi2.x/asi-station-webapp.git`
- Branch scope: all branches
- Author: `chayne`
- Remote access timed out.
- Local fallback repos were used because their `origin` remotes match the provided URLs:
  - `E:\work\asi-station-mini`
  - `E:\work\asi-station-webapp`
- Result:
  - `asi-station-mini`: 4 commits, 2 changed files, `+33/-3`
  - `asi-station-webapp`: 0 commits for `chayne` in the target period

WeCom evidence:

- User explicitly authorized supervised full-auto collection.
- Command period: `2026-06-29..2026-07-03`
- Run directory: `outputs/wecom_runs/20260703-110152-77IJ/`
- Fingerprint: `PRAS-20260703-110152-4089`
- Trace ended with `automation_complete` and `fingerprint_match=true`
- Copy method: `main_body_ocr`
- Output Markdown/JSON saved and valid UTF-8 when read programmatically.

## Cleanup Completed

Project reduction was completed on 2026-07-03.

Deleted:

- Old `docs/archive/tasks/` historical task files.
- Completed `docs/tasks/` files that were no longer active entry points.
- Old WeCom run directories except `outputs/wecom_runs/20260703-110152-77IJ/`.
- Old probe, Excel validation, smoke, June, and previous WeCom output artifacts.
- Stale root WeCom diagnostic reports.

Kept:

- Current report draft and current-period evidence.
- Current WeCom run diagnostics.
- Core skill files and scripts.
- Validation/helper scripts.
- WeCom template assets.

Approximate output size after cleanup: about 4.5 MB.

## Standing Rules

Current-period evidence:

- Each new report interview uses the target period from that interview as authoritative.
- Old WeCom summaries, old reports, old traces, old run directories, or old output files are automatically excluded from current evidence when their period does not match, unless the user explicitly asks to reuse them.
- Do not repeatedly ask whether an obviously period-mismatched old collection should be used.

Template memory:

- User-provided templates/examples/accepted drafts are current-task references by default.
- Do not save them as global/default templates.
- After successful delivery, Codex may ask once whether to record the structure as that user's future 【周报/绩效/述职】 template.
- Only explicit user approval permits persisting a reusable template with owner/scope, report type, structure rules, and limits.

Git evidence:

- If repo list, target period, branch scope, and author filter are already explicit in the current interview, run read-only git statistics without demanding a fixed confirmation phrase.
- If remote repo access times out, local fallback is allowed only when local `origin` matches the user-provided URL, and the fallback must be disclosed in evidence status.

WeCom automation:

- Do not run full-auto WeCom live automation unless the user again supervises and explicitly authorizes.
- Do not describe the collector as unattended, cross-environment stable, or generally compatible with all WeCom UI variants.

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
