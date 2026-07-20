# Git Evidence Collection Rules

## Remote URL Collection

- **Full clone is the default** for remote URLs. The collector clones the full repository history to produce accurate statistics.
- **Shallow clone is explicit opt-in only.** The user must explicitly request `--shallow-depth`. Agents must not auto-apply shallow clone to save time or disk space.

## Local Fallback

- If remote access fails (network error, authentication, unreachable host), a local path may be used as fallback **only** when the local repository's `origin` remote URL matches the user-provided URL exactly.
- Every local fallback must be disclosed to the user before statistics are collected. The disclosure must include:
  - The local path being used
  - The matched origin URL
  - A note that the local working tree state (uncommitted changes, branch) reflects the local checkout, not necessarily the remote HEAD
- If no local repository with a matching origin exists, report the remote access failure and ask the user to provide an alternative.

## Pre-Execution Confirmation

Before running git statistics, confirm with the user using a compact summary:

```
确认参数：
- 周期：YYYY-MM-DD 到 YYYY-MM-DD
- 仓库：repo A, repo B
- 分支范围：全部分支 / 当前分支 / 指定分支 xxx
- 作者过滤：author name/email / 不过滤（仓库整体）
- 统计口径：仅个人提交 / 仓库整体证据

确认无误后我再执行统计。请明确回复"确认执行"或指出要调整的项。
```

Only execute after the user explicitly confirms.

## Branch Scope

- When the user provides a repository, ask them to choose: current branch, a specific named branch, or all branches.
- Do not assume the current branch is the intended scope.

## Author Attribution

- For personal weekly reports or "我的提交" scenarios, confirm the git author name or email.
- If the user does not provide an author filter, collect all authors and label the result as repository-wide evidence — never present all-author statistics as personal work.
- Accept one or multiple author names/emails.

## Expected Quantitative Metrics

The collector must produce, where available:

- **Commit count**: total commits in the period matching the author/branch filter
- **Touched files**: number of files modified
- **Insertions / deletions**: line-level change summary
- **Code scale**: net change (insertions minus deletions), total lines changed
- **Top files/modules**: files or directories with the most activity, ranked by commits or lines changed
- **Author distribution**: commits per author (when collecting all-authors)
- **Daily distribution**: commits per day within the period

These metrics feed into the evidence summary and the draft report. Do not invent or approximate missing metrics; mark unavailable fields explicitly.

## Evidence Integrity

- **Never infer repositories, modules, work items, or statistics from `reference_only` material.** Template/reference reports may mention repositories or modules that belong to a different period, different project, or different person. Only use repositories explicitly provided by the user for the current period.
- If the user previously provided an old report that mentions `仓库 X` but the current evidence only includes `仓库 A` and `仓库 B`, do not ask "should I also check 仓库 X?" — the old report is not a source of truth for current evidence.
- Git statistics are stdout-only by default. Use `--output` only after the user has confirmed an export location.
