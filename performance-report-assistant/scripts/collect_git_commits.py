#!/usr/bin/env python
"""Collect git commits across one or more repositories for report evidence."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def run_git_log(repo: Path, since: str, until: str, author: str | None) -> str:
    cmd = [
        "git",
        "-C",
        str(repo),
        "log",
        f"--since={since}",
        f"--until={until}",
        "--date=short",
        "--pretty=format:%h%x09%ad%x09%an%x09%s",
    ]
    if author:
        cmd.append(f"--author={author}")

    result = subprocess.run(cmd, check=True, text=True, capture_output=True)
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect git commits for report evidence.")
    parser.add_argument("--repo", action="append", required=True, help="Repository path. Repeat for multiple repos.")
    parser.add_argument("--since", required=True, help="Start date, e.g. 2026-05-01.")
    parser.add_argument("--until", required=True, help="End date, e.g. 2026-06-01.")
    parser.add_argument("--author", help="Optional git author filter.")
    parser.add_argument("--output", help="Output Markdown file. Prints to stdout when omitted.")
    args = parser.parse_args()

    sections: list[str] = []
    for repo_text in args.repo:
        repo = Path(repo_text).expanduser().resolve()
        if not repo.exists():
            raise FileNotFoundError(f"Repository does not exist: {repo}")

        log_text = run_git_log(repo, args.since, args.until, args.author)
        sections.append(f"## {repo.name}\n")
        if log_text:
            for line in log_text.splitlines():
                commit_hash, date, author, subject = line.split("\t", 3)
                sections.append(f"- {date} `{commit_hash}` {subject} ({author})")
        else:
            sections.append("- No commits found in this date range.")
        sections.append("")

    output = "\n".join(sections).strip() + "\n"
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
