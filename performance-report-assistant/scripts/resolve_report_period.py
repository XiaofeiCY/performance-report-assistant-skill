#!/usr/bin/env python
"""Resolve relative report periods into exact date ranges."""

from __future__ import annotations

import argparse
from datetime import date, timedelta


def monday_of_week(value: date) -> date:
    return value - timedelta(days=value.weekday())


def resolve_week(today: date, offset_weeks: int, week_mode: str) -> tuple[date, date]:
    start = monday_of_week(today) + timedelta(weeks=offset_weeks)
    if week_mode == "natural":
        return start, start + timedelta(days=6)
    return start, start + timedelta(days=4)


def resolve_month(today: date, offset_months: int) -> tuple[date, date]:
    month_index = today.year * 12 + today.month - 1 + offset_months
    year = month_index // 12
    month = month_index % 12 + 1
    start = date(year, month, 1)
    next_month_index = month_index + 1
    next_month = date(next_month_index // 12, next_month_index % 12 + 1, 1)
    return start, next_month - timedelta(days=1)


def resolve_period(period: str, today: date, week_mode: str) -> tuple[date, date]:
    if period in {"this-week", "本周"}:
        return resolve_week(today, 0, week_mode)
    if period in {"last-week", "上周"}:
        return resolve_week(today, -1, week_mode)
    if period in {"this-month", "本月"}:
        return resolve_month(today, 0)
    if period in {"last-month", "上个月", "上月"}:
        return resolve_month(today, -1)
    raise ValueError(f"Unsupported period: {period}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve report periods to exact dates.")
    parser.add_argument("--period", required=True, help="this-week, last-week, this-month, last-month, or Chinese equivalents.")
    parser.add_argument("--today", help="Current date in YYYY-MM-DD. Defaults to system date.")
    parser.add_argument(
        "--week-mode",
        choices=["workweek", "natural"],
        default="workweek",
        help="workweek is Monday-Friday; natural is Monday-Sunday.",
    )
    args = parser.parse_args()

    today = date.fromisoformat(args.today) if args.today else date.today()
    since, until = resolve_period(args.period, today, args.week_mode)
    print(f"since={since.isoformat()}")
    print(f"until={until.isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
