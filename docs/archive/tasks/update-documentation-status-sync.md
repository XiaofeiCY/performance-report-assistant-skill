# Task: Synchronize Documentation With Current Skill State

## Background

The repository contains a Claude Code / Codex skill named `performance-report-assistant`. It helps users produce Chinese workplace reports from weekly notes, git commits, work records, and reusable templates. The skill emphasizes a safe workflow: inspect templates first, confirm exact edit targets, then write into a copied file rather than overwriting the original.

A read-only review found that the implementation is more complete than some documentation sections describe. The main skill file already references newer support files and scripts, but the README files and original build plan are not fully synchronized.

## User Request

The user asked Codex to read the project files, restate the understanding, and then check whether the project files need status or content updates.

Codex reviewed the files and concluded that documentation updates are needed, but no skill code or scripts should be changed for this task.

## Goal

Update project documentation so it accurately reflects the current repository state and leaves a clear handoff/validation status for future work.

## Scope

Update documentation only:

- `README.md`
- `README.zh-CN.md`
- `claude-code-skill-build-plan.md`
- optionally `docs/status.md` if new validation results are produced

Do not modify:

- `performance-report-assistant/SKILL.md`
- `performance-report-assistant/references/*.md`
- `performance-report-assistant/scripts/*.py`
- `performance-report-assistant/agents/openai.yaml`

## Required Updates

### 1. README Structure

In both `README.md` and `README.zh-CN.md`, update the repository structure block to include:

```text
performance-report-assistant/
  SKILL.md
  agents/
    openai.yaml
  references/
    intake-questions.md
    report-patterns.md
    template-workflow.md
    excel-template-workflow.md
  scripts/
    collect_git_commits.py
    fill_excel_template.py
    resolve_report_period.py
```

### 2. README Script Descriptions

In both README files, add a short section for `resolve_report_period.py`.

It should explain that the script resolves relative periods such as "this week", "last week", "this month", and "last month" into exact date ranges. For Chinese documentation, include "本周", "上周", "本月", and "上个月/上月".

Mention that weekly reports default to a Monday-Friday workweek unless natural-week mode is explicitly requested.

Example command:

```bash
python scripts/resolve_report_period.py --period last-week --today 2026-06-09
```

Chinese example:

```bash
python scripts/resolve_report_period.py --period 上周 --today 2026-06-09
```

### 3. Build Plan Status

Update `claude-code-skill-build-plan.md` so readers understand it is the original execution plan, not necessarily the latest state.

Add a concise "Current Status Notes" section near the top or before "Acceptance Criteria" that records:

- The current repository includes `references/template-workflow.md`.
- The current repository includes `scripts/resolve_report_period.py`.
- README files exist and should be treated as current user-facing documentation.
- Script help checks have been run successfully for:
  - `collect_git_commits.py`
  - `fill_excel_template.py`
  - `resolve_report_period.py`
- Excel sample fill validation has not yet been recorded in this review.

Keep the original plan intact unless a specific line is now actively misleading.

## Suggested Execution Steps

1. Read the current README files and build plan.
2. Patch only the documentation sections described above.
3. Run a read-only diff to confirm the changes are scoped to documentation.
4. Run these help checks:

```bash
python performance-report-assistant/scripts/collect_git_commits.py --help
python performance-report-assistant/scripts/fill_excel_template.py --help
python performance-report-assistant/scripts/resolve_report_period.py --help
```

5. If the help checks pass, optionally update `docs/status.md` with the validation result and timestamp/date.

## Deliverables

- Updated README structure in English and Chinese.
- Added README documentation for `resolve_report_period.py`.
- Updated build plan status notes.
- Optional updated `docs/status.md` if validation checks are rerun.

## Testing Requirements

Minimum required:

- Run the three script `--help` commands listed above.
- Confirm `git diff` only contains intended documentation changes.

Optional but recommended before publishing:

- Run the Excel sample fill validation described in `claude-code-skill-build-plan.md`.

## Acceptance Criteria

- README files match the actual repository structure.
- README files document all scripts currently present.
- The build plan no longer looks like the only source of current truth.
- No skill behavior, reference workflow, script code, or agent config is changed.
- Any unrun validation, especially Excel sample filling, is clearly marked as not yet recorded.

## Risks

- Avoid rewriting the skill design while doing documentation sync.
- Avoid treating the original build plan as obsolete; it is still useful as historical context and acceptance guidance.
- Do not claim Excel validation has passed unless it is actually run and inspected.
