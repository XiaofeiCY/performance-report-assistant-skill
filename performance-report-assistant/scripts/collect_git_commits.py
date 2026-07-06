#!/usr/bin/env python
"""Collect git commits and repository metrics for report evidence."""

from __future__ import annotations

import argparse
from collections import Counter
import re
import sys
import tempfile
import subprocess
from pathlib import Path


CODE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".css",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".less",
    ".lua",
    ".m",
    ".mm",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".sass",
    ".scss",
    ".sh",
    ".sql",
    ".swift",
    ".ts",
    ".tsx",
    ".vue",
    ".xml",
    ".yaml",
    ".yml",
}


REPO_URL_PATTERN = re.compile(r"^(https?://|ssh://|git@).+")


def run_git(repo: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip()


def run_git_bytes(repo: Path, args: list[str]) -> bytes:
    result = subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
    return result.stdout


def is_repo_url(repo_text: str) -> bool:
    return bool(REPO_URL_PATTERN.match(repo_text))


def clone_repo(repo_url: str, branch: str | None, clone_parent: Path, all_branches: bool, shallow_depth: int = 0) -> Path:
    clone_parent.mkdir(parents=True, exist_ok=True)
    clone_dir = clone_parent / "repo"
    cmd = ["git", "clone"]
    if branch and not all_branches:
        cmd.extend(["--branch", branch, "--single-branch"])
    if shallow_depth > 0:
        cmd.extend(["--depth", str(shallow_depth)])
    cmd.extend([repo_url, str(clone_dir)])
    subprocess.run(cmd, check=True, capture_output=True, encoding="utf-8", errors="replace")
    return clone_dir


def resolve_git_root(repo: Path) -> Path:
    root_text = run_git(repo, ["rev-parse", "--show-toplevel"])
    return Path(root_text).resolve()


def resolve_branch(repo: Path, branch: str | None) -> str:
    if branch:
        try:
            run_git(repo, ["rev-parse", "--verify", f"{branch}^{{commit}}"])
            return branch
        except subprocess.CalledProcessError:
            remote_branch = f"origin/{branch}"
            run_git(repo, ["rev-parse", "--verify", f"{remote_branch}^{{commit}}"])
            return remote_branch

    try:
        origin_head = run_git(repo, ["symbolic-ref", "--short", "refs/remotes/origin/HEAD"])
        if origin_head:
            return origin_head
    except subprocess.CalledProcessError:
        pass

    current_branch = run_git(repo, ["rev-parse", "--abbrev-ref", "HEAD"])
    if current_branch == "HEAD":
        return "HEAD"
    return current_branch


def git_log_args(since: str, until: str, author: str | None) -> list[str]:
    args = [f"--since={since}", f"--until={until}"]
    if author:
        args.append(f"--author={author}")
    return args


def is_code_file(path_text: str) -> bool:
    path = Path(path_text)
    return path.suffix.lower() in CODE_EXTENSIONS


DATE_ONLY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def normalize_date_range(since: str, until: str) -> tuple[str, str]:
    if DATE_ONLY.match(since):
        since = f"{since} 00:00:00"
    if DATE_ONLY.match(until):
        until = f"{until} 23:59:59"
    return since, until


def log_scope_args(branch: str | None, all_branches: bool) -> list[str]:
    if all_branches:
        return ["--all"]
    if branch:
        return [branch]
    return []


def run_git_log(repo: Path, branch: str | None, all_branches: bool, since: str, until: str, author: str | None) -> str:
    args = [
        "log",
        *log_scope_args(branch, all_branches),
        *git_log_args(since, until, author),
        "--date=short",
        "--pretty=format:%H%x09%h%x09%ad%x09%an%x09%s",
    ]
    return run_git(repo, args)


def count_current_code_lines(repo: Path, branch: str) -> tuple[int, int]:
    files_text = run_git(repo, ["ls-tree", "-r", "--name-only", branch])
    code_files = [line for line in files_text.splitlines() if is_code_file(line)]
    total_lines = 0

    for file_text in code_files:
        try:
            content = run_git_bytes(repo, ["show", f"{branch}:{file_text}"])
        except subprocess.CalledProcessError:
            continue
        total_lines += len(content.splitlines())

    return len(code_files), total_lines


def collect_file_touch_counts(
    repo: Path,
    branch: str | None,
    all_branches: bool,
    since: str,
    until: str,
    author: str | None,
) -> Counter[str]:
    output = run_git(
        repo,
        [
            "log",
            *log_scope_args(branch, all_branches),
            *git_log_args(since, until, author),
            "--name-only",
            "--pretty=format:--COMMIT--%H",
        ],
    )
    counts: Counter[str] = Counter()
    current_files: set[str] = set()
    seen_commits: set[str] = set()
    skip_current_commit = False

    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("--COMMIT--"):
            commit_hash = line.removeprefix("--COMMIT--")
            skip_current_commit = commit_hash in seen_commits
            seen_commits.add(commit_hash)
            if not skip_current_commit:
                for file_text in current_files:
                    counts[file_text] += 1
            current_files = set()
        elif skip_current_commit:
            continue
        else:
            current_files.add(line)

    if not skip_current_commit:
        for file_text in current_files:
            counts[file_text] += 1
    return counts


def collect_numstat(
    repo: Path,
    branch: str | None,
    all_branches: bool,
    since: str,
    until: str,
    author: str | None,
) -> tuple[int, int, int]:
    output = run_git(
        repo,
        [
            "log",
            *log_scope_args(branch, all_branches),
            *git_log_args(since, until, author),
            "--numstat",
            "--pretty=format:--COMMIT--%H",
        ],
    )
    insertions = 0
    deletions = 0
    changed_files: set[str] = set()
    seen_commits: set[str] = set()
    skip_current_commit = False

    for line in output.splitlines():
        if line.startswith("--COMMIT--"):
            commit_hash = line.removeprefix("--COMMIT--").strip()
            skip_current_commit = commit_hash in seen_commits
            seen_commits.add(commit_hash)
            continue
        if skip_current_commit:
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added, deleted, file_text = parts[0], parts[1], parts[2]
        changed_files.add(file_text)
        if added.isdigit() and deleted.isdigit() and is_code_file(file_text):
            insertions += int(added)
            deletions += int(deleted)

    return len(changed_files), insertions, deletions


def build_repo_stats(
    repo: Path,
    branch: str,
    all_branches: bool,
    since: str,
    until: str,
    author: str | None,
    commit_count: int,
) -> list[str]:
    tracked_code_files, current_code_lines = count_current_code_lines(repo, branch)
    changed_file_count, insertions, deletions = collect_numstat(repo, branch, all_branches, since, until, author)
    touch_counts = collect_file_touch_counts(repo, branch, all_branches, since, until, author)
    top_files = touch_counts.most_common(10)

    lines = [
        "### Repository Metrics",
        "",
        f"- Commit count: {commit_count}",
        f"- Changed files in period: {changed_file_count}",
        f"- Code line changes in period: +{insertions} / -{deletions}",
        f"- Current tracked code files: {tracked_code_files}",
        f"- Current tracked code lines: {current_code_lines}",
    ]

    if top_files:
        lines.extend(["", "### File Touch Frequency", ""])
        for file_text, count in top_files:
            lines.append(f"- `{file_text}`: {count} commit(s)")

    return lines


def build_commit_distribution(commits: list[str]) -> list[str]:
    author_counts: Counter[str] = Counter()
    date_counts: Counter[str] = Counter()

    for line in commits:
        _full_hash, _short_hash, commit_date, commit_author, _subject = line.split("\t", 4)
        author_counts[commit_author] += 1
        date_counts[commit_date] += 1

    lines: list[str] = []
    if author_counts:
        lines.extend(["### Author Distribution", ""])
        for author, count in author_counts.most_common(10):
            lines.append(f"- {author}: {count} commit(s)")
        lines.append("")

    if date_counts:
        lines.extend(["### Daily Commit Distribution", ""])
        for commit_date, count in sorted(date_counts.items()):
            lines.append(f"- {commit_date}: {count} commit(s)")

    return lines


def build_repo_section(
    repo: Path,
    source_text: str,
    cloned_from_url: bool,
    branch: str | None,
    all_branches: bool,
    since: str,
    until: str,
    author: str | None,
    include_stats: bool,
) -> list[str]:
    repo = resolve_git_root(repo)
    selected_branch = resolve_branch(repo, branch)
    log_text = run_git_log(repo, selected_branch, all_branches, since, until, author)
    commit_rows = log_text.splitlines() if log_text else []
    seen_commits: set[str] = set()
    commits: list[str] = []
    for row in commit_rows:
        full_hash = row.split("\t", 1)[0]
        if full_hash in seen_commits:
            continue
        seen_commits.add(full_hash)
        commits.append(row)

    scope_label = "all branches" if all_branches else selected_branch
    sections = [f"## {repo.name}", "", f"- Source: `{source_text}`", f"- Scope: `{scope_label}`"]
    if all_branches:
        sections.append(f"- Default branch for current code size: `{selected_branch}`")
    if cloned_from_url:
        sections.append("- Temporary clone: cleaned up after this script finishes")
    sections.append("")

    if include_stats:
        sections.extend(build_repo_stats(repo, selected_branch, all_branches, since, until, author, len(commits)))
        sections.append("")
        sections.extend(build_commit_distribution(commits))
        sections.append("")

    sections.append("### Commits")
    sections.append("")
    if commits:
        for line in commits:
            _full_hash, short_hash, date, commit_author, subject = line.split("\t", 4)
            sections.append(f"- {date} `{short_hash}` {subject} ({commit_author})")
    else:
        sections.append("- No commits found in this date range.")

    return sections


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect git commits and repository metrics for report evidence.")
    parser.add_argument("--repo", action="append", required=True, help="Repository path or git URL. Repeat for multiple repos.")
    parser.add_argument("--since", required=True, help="Start date, e.g. 2026-05-01.")
    parser.add_argument("--until", required=True, help="End date, e.g. 2026-06-01.")
    parser.add_argument("--branch", help="Restrict statistics to this branch or revision. Omit to inspect all branches.")
    parser.add_argument(
        "--all-branches",
        action="store_true",
        help="Inspect commits reachable from all local and remote refs. This is also the default when --branch is omitted.",
    )
    parser.add_argument("--author", help="Optional git author filter.")
    parser.add_argument("--no-stats", action="store_true", help="Only output commit list, without repository metrics.")
    parser.add_argument(
        "--shallow-depth", type=int, default=0, metavar="N",
        help="Shallow clone depth for remote repos (default: 0 = full clone). "
             "Set to e.g. 100 for faster clones when you are certain all relevant "
             "commits are within the last N commits on every branch of interest. "
             "Not recommended with --all-branches unless you verify all target "
             "branches are fetched.",
    )
    parser.add_argument("--output", help="Output Markdown file (must be an absolute path). Prints to stdout when omitted.")
    args = parser.parse_args()

    if args.output and not Path(args.output).is_absolute():
        print(f"错误：--output 必须使用绝对路径，收到相对路径：{args.output}")
        print("示例：")
        print(f"  python collect_git_commits.py --repo ... --output E:\\confirmed-output\\git_stats.md")
        print("不带 --output 时输出到 stdout，不创建文件。")
        sys.exit(1)

    args.since, args.until = normalize_date_range(args.since, args.until)

    use_all_branches = args.all_branches or not args.branch

    with tempfile.TemporaryDirectory(prefix="performance-report-assistant-") as temp_dir_text:
        temp_dir = Path(temp_dir_text)
        sections: list[str] = []
        for index, repo_text in enumerate(args.repo, start=1):
            cloned_from_url = is_repo_url(repo_text)
            if cloned_from_url:
                repo = clone_repo(repo_text, args.branch, temp_dir / f"repo-{index}", use_all_branches, args.shallow_depth)
            else:
                repo = Path(repo_text).expanduser().resolve()
                if not repo.exists():
                    raise FileNotFoundError(f"Repository does not exist: {repo}")

            sections.extend(
                build_repo_section(
                    repo,
                    repo_text,
                    cloned_from_url,
                    args.branch,
                    use_all_branches,
                    args.since,
                    args.until,
                    args.author,
                    not args.no_stats,
                )
            )
            sections.append("")

        output = "\n".join(sections).strip() + "\n"
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
        else:
            print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
