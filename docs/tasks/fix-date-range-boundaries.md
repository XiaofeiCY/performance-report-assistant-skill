# Task: Fix Inclusive Date Range Boundaries for Git Evidence Collection

## Background

The `performance-report-assistant` skill resolves report periods such as "本周", "上周", "本月", and "上个月" into exact date ranges. For weekly reports, workweek mode is supposed to mean Monday through Friday inclusive. For monthly reports, the range should include the full last day of the month.

During Codex acceptance review, `resolve_report_period.py` returned correct human-readable date boundaries:

- `本周` on `2026-06-29` -> `since=2026-06-29`, `until=2026-07-03`
- `上周` on `2026-06-29` -> `since=2026-06-22`, `until=2026-06-26`
- `本月` on `2026-06-29` -> `since=2026-06-01`, `until=2026-06-30`
- `上个月` on `2026-06-29` -> `since=2026-05-01`, `until=2026-05-31`

However, `collect_git_commits.py` passes these date-only values directly to `git log`:

```python
args = [f"--since={since}", f"--until={until}"]
```

Git does not reliably interpret date-only values as full inclusive days. In local tests, date-only ranges omitted commits on the range boundary days.

## Problem

The git evidence collection can undercount work for any date-only range:

- A workweek range ending on Friday can omit Friday commits.
- A monthly range ending on the last day can omit that day's commits.
- A range starting on Monday can omit commits from earlier Monday hours, depending on Git's date parsing context.

This affects all report scenarios that rely on repository metrics, not only the "本周" example.

## Goal

Make date-only report ranges inclusive for the entire start and end dates when collecting git commits and repository metrics.

## Scope

Modify only what is needed for date-boundary correctness:

- `performance-report-assistant/scripts/collect_git_commits.py`
- related README or skill documentation only if the CLI behavior needs to be clarified
- optional tests or temporary validation notes if the project has a test location

Do not change report-writing workflow, template filling, or unrelated repository statistics behavior.

## Expected Behavior

When users pass date-only arguments:

```bash
python scripts/collect_git_commits.py --repo <repo> --since 2026-06-29 --until 2026-07-03
```

the script should collect commits from:

- `2026-06-29 00:00:00` through
- `2026-07-03 23:59:59`

For monthly ranges:

```bash
python scripts/collect_git_commits.py --repo <repo> --since 2026-07-01 --until 2026-07-31
```

the script should include commits made on `2026-07-31`.

If users pass an argument that already includes a time component, preserve the explicit time rather than forcing start/end-of-day.

## Suggested Implementation

Add a small normalization helper in `collect_git_commits.py`.

Suggested behavior:

- If `since` matches date-only format `YYYY-MM-DD`, convert to `YYYY-MM-DD 00:00:00`.
- If `until` matches date-only format `YYYY-MM-DD`, convert to `YYYY-MM-DD 23:59:59`.
- If either value already includes time, leave it unchanged.
- Use the normalized values everywhere `git_log_args()` is used, including:
  - commit list
  - file touch counts
  - numstat / changed file counts

## Validation Requirements

Create a temporary git repository and commit files at boundary times:

1. Commit on start date morning, for example `2026-06-29T09:00:00+08:00`.
2. Commit on end date evening, for example `2026-07-03T18:00:00+08:00`.
3. Run:

```bash
python performance-report-assistant/scripts/collect_git_commits.py --repo <temp-repo> --since 2026-06-29 --until 2026-07-03 --no-stats
```

Expected result:

- Both boundary commits appear.

Also validate a month-end case:

1. Commit on `2026-07-31T18:00:00+08:00`.
2. Run:

```bash
python performance-report-assistant/scripts/collect_git_commits.py --repo <temp-repo> --since 2026-07-01 --until 2026-07-31 --no-stats
```

Expected result:

- The `2026-07-31` commit appears.

Run help checks after the change:

```bash
python performance-report-assistant/scripts/collect_git_commits.py --help
python performance-report-assistant/scripts/resolve_report_period.py --help
```

## Acceptance Criteria

- Date-only ranges include the full start date and full end date.
- Weekly workweek ranges do not omit Friday commits.
- Monthly ranges do not omit commits from the last day of the month.
- Explicit datetime inputs are preserved.
- Commit list, numstat, and file-touch metrics all use the same normalized range.
- No unrelated behavior is changed.

## Risk Notes

- This is a correctness issue for evidence collection and performance reporting. Under-counting commits can make the generated report incomplete.
- The fix should be centralized so all git log calls share the same boundary behavior.
- Be careful not to convert explicit datetime values supplied by the user.
