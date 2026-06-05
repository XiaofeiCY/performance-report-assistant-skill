#!/usr/bin/env python
"""Collect git commits and repository metrics for report evidence."""

from __future__ import annotations

import argparse
from collections import Counter
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


def run_git(repo: Path, args: list[str]) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], check=True, text=True, capture_output=True)
    return result.stdout.strip()


def run_git_bytes(repo: Path, args: list[str]) -> bytes:
    result = subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
    return result.stdout


def resolve_git_root(repo: Path) -> Path:
    root_text = run_git(repo, ["rev-parse", "--show-toplevel"])
    return Path(root_text).resolve()


def resolve_branch(repo: Path, branch: str | None) -> str:
    if branch:
        run_git(repo, ["rev-parse", "--verify", f"{branch}^{{commit}}"])
        return branch

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


def run_git_log(repo: Path, branch: str, since: str, until: str, author: str | None) -> str:
    args = [
        "log",
        branch,
        *git_log_args(since, until, author),
        "--date=short",
        "--pretty=format:%h%x09%ad%x09%an%x09%s",
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


def collect_file_touch_counts(repo: Path, branch: str, since: str, until: str, author: str | None) -> Counter[str]:
    output = run_git(
        repo,
        [
            "log",
            branch,
            *git_log_args(since, until, author),
            "--name-only",
            "--pretty=format:--COMMIT--",
        ],
    )
    counts: Counter[str] = Counter()
    current_files: set[str] = set()

    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        if line == "--COMMIT--":
            for file_text in current_files:
                counts[file_text] += 1
            current_files = set()
        else:
            current_files.add(line)

    for file_text in current_files:
        counts[file_text] += 1
    return counts


def collect_numstat(repo: Path, branch: str, since: str, until: str, author: str | None) -> tuple[int, int, int]:
    output = run_git(
        repo,
        [
            "log",
            branch,
            *git_log_args(since, until, author),
            "--numstat",
            "--pretty=format:",
        ],
    )
    insertions = 0
    deletions = 0
    changed_files: set[str] = set()

    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added, deleted, file_text = parts[0], parts[1], parts[2]
        changed_files.add(file_text)
        if added.isdigit() and deleted.isdigit() and is_code_file(file_text):
            insertions += int(added)
            deletions += int(deleted)

    return len(changed_files), insertions, deletions


def build_repo_stats(repo: Path, branch: str, since: str, until: str, author: str | None, commit_count: int) -> list[str]:
    tracked_code_files, current_code_lines = count_current_code_lines(repo, branch)
    changed_file_count, insertions, deletions = collect_numstat(repo, branch, since, until, author)
    touch_counts = collect_file_touch_counts(repo, branch, since, until, author)
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


def build_repo_section(
    repo: Path,
    branch: str | None,
    since: str,
    until: str,
    author: str | None,
    include_stats: bool,
) -> list[str]:
    repo = resolve_git_root(repo)
    selected_branch = resolve_branch(repo, branch)
    log_text = run_git_log(repo, selected_branch, since, until, author)
    commits = log_text.splitlines() if log_text else []
    sections = [f"## {repo.name}", "", f"- Branch: `{selected_branch}`", ""]

    if include_stats:
        sections.extend(build_repo_stats(repo, selected_branch, since, until, author, len(commits)))
        sections.append("")

    sections.append("### Commits")
    sections.append("")
    if commits:
        for line in commits:
            commit_hash, date, commit_author, subject = line.split("\t", 3)
            sections.append(f"- {date} `{commit_hash}` {subject} ({commit_author})")
    else:
        sections.append("- No commits found in this date range.")

    return sections


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect git commits and repository metrics for report evidence.")
    parser.add_argument("--repo", action="append", required=True, help="Repository path. Repeat for multiple repos.")
    parser.add_argument("--since", required=True, help="Start date, e.g. 2026-05-01.")
    parser.add_argument("--until", required=True, help="End date, e.g. 2026-06-01.")
    parser.add_argument("--branch", help="Branch or revision to inspect. Defaults to origin/HEAD, then current branch.")
    parser.add_argument("--author", help="Optional git author filter.")
    parser.add_argument("--no-stats", action="store_true", help="Only output commit list, without repository metrics.")
    parser.add_argument("--output", help="Output Markdown file. Prints to stdout when omitted.")
    args = parser.parse_args()

    sections: list[str] = []
    for repo_text in args.repo:
        repo = Path(repo_text).expanduser().resolve()
        if not repo.exists():
            raise FileNotFoundError(f"Repository does not exist: {repo}")

        sections.extend(build_repo_section(repo, args.branch, args.since, args.until, args.author, not args.no_stats))
        sections.append("")

    output = "\n".join(sections).strip() + "\n"
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
