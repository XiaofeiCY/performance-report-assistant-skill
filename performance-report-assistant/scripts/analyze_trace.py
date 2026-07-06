#!/usr/bin/env python3
"""Offline trace timing analyzer for WeCom Smart Summary runs.

Reads one or more trace.jsonl files and produces a human-readable phase-by-phase
timing summary.  Does NOT modify the collector -- read-only analysis only.

Usage:
  python scripts/analyze_trace.py <run_dir> [<run_dir2> ...]
  python scripts/analyze_trace.py E:\\confirmed-output\\wecom_runs\\20260706-102206-RRI8
  python scripts/analyze_trace.py E:\\confirmed-output\\wecom_runs\\*/
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

# Force UTF-8 for stdout on Windows
if sys.platform == "win32":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)


BULLET = "*"


def parse_timestamp(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def phase_name(entry: dict[str, Any]) -> str:
    """Derive a human-readable phase name from a trace entry."""
    event = entry.get("event", "")
    stage = entry.get("stage", "")
    phase = entry.get("phase", "")

    if event == "automation_start":
        return "init: 启动"
    if event == "prompt_prepared":
        return "init: 提示词准备"
    if event == "init_complete":
        return "init: EasyOCR 加载完成"
    if event == "window_found":
        return "window: 发现企微窗口"
    if event == "window_normalized":
        return "window: 归一化 (1920x1080)"
    if event == "state_machine_cycle":
        cycle = entry.get("cycle", "?")
        state = entry.get("page_state", entry.get("state", "?"))
        return f"sm: cycle={cycle} -> {state}"
    if event == "capture_foreground_check":
        s = entry.get("stage", "?")
        p = entry.get("phase", "?")
        return f"fg: {s}.{p}"
    if event == "paste_verify":
        return "paste: 粘贴校验通过"
    if event == "automation_complete":
        return "done: 采集完成"

    if stage == "open_entry":
        return f"nav: 打开入口 ({entry.get('method', '?')})"
    if stage == "click_plus":
        return f"nav: + 新建 ({entry.get('method', '?')})"
    if stage == "paste_locate":
        return f"paste: 定位输入框 ({entry.get('method', '?')})"
    if stage == "paste_prompt":
        return "paste: 执行粘贴"
    if stage == "click_start":
        return f"click: 点击开始总结 ({entry.get('method', '?')})"
    if stage == "wait_result":
        state = entry.get("state", "?")
        wall = entry.get("wall_elapsed", 0)
        return f"wait: {state} @ {wall:.0f}s"
    if stage == "copy_result":
        p = entry.get("phase", "")
        method = entry.get("method", "")
        step = entry.get("step", "")
        if not p and method:
            return f"copy: {method} (result)"
        label = f"{p}/{step}".rstrip("/") if step else p
        return f"copy: {label}" if label else "copy: (final)"
    if event == "global_timeout":
        return f"timeout: @ {entry.get('stage', '?')}"

    return f"unk: {event}/{stage}/{phase}".strip("/")


# Group classification: prefix -> display name
GROUP_MAP = [
    ("init:",    "1.初始化 (EasyOCR加载+提示词)"),
    ("window:",  "2.窗口发现与归一化"),
    ("fg:",      "3.前台校验 (每步前后)"),
    ("sm:",      "4.状态机识别 (OCR分类)"),
    ("nav:",     "5.页面导航 (点击入口/+新建)"),
    ("paste:",   "6.粘贴提示词"),
    ("click:",   "7.点击开始总结"),
    ("wait:",    "8.等待智能总结生成 (WeCom服务端)"),
    ("copy:",    "9.复制结果"),
    ("done:",    "10.完成"),
]


def _group_for(name: str) -> str:
    for prefix, label in GROUP_MAP:
        if name.startswith(prefix):
            return label
    return "other"


def analyze_trace(trace_path: Path) -> dict[str, Any]:
    """Parse a trace.jsonl file and compute phase durations."""
    entries: list[dict[str, Any]] = []
    with open(trace_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))

    if not entries:
        return {"error": "No entries in trace file", "path": str(trace_path)}

    timestamps = [parse_timestamp(e["timestamp"]) for e in entries]
    t0 = timestamps[0]
    t_end = timestamps[-1]

    # Build phase list with durations.
    # Foreground checks are pass-through: their own before->after gap is
    # negligible (~50ms), but the gap from their "after" to the next real
    # event belongs to the NEXT phase, not to the FG check.
    phases: list[dict[str, Any]] = []
    carry: float = 0.0  # accumulated duration to attribute to next non-fg phase
    for i, entry in enumerate(entries):
        name = phase_name(entry)
        ts = timestamps[i]
        offset = (ts - t0).total_seconds()
        raw_dur = 0.0
        if i + 1 < len(entries):
            raw_dur = (timestamps[i + 1] - ts).total_seconds()

        is_fg = name.startswith("fg:")
        is_fg_after = is_fg and entry.get("phase") == "after"

        if is_fg:
            # FG entry: own duration is just the before->after capture gap
            own_dur = raw_dur if not is_fg_after else 0.0
            # The "after" carries forward to the next real phase
            if is_fg_after:
                carry += raw_dur
            phases.append({
                "name": name, "offset": round(offset, 2),
                "duration": round(own_dur, 2),
                "group": _group_for(name), "entry": entry,
            })
        else:
            # Non-FG: consume carry
            phases.append({
                "name": name, "offset": round(offset, 2),
                "duration": round(raw_dur + carry, 2),
                "group": _group_for(name), "entry": entry,
            })
            carry = 0.0

    total = (t_end - t0).total_seconds()
    groups = _build_groups(phases)

    return {
        "path": str(trace_path),
        "total_s": round(total, 1),
        "phases": phases,
        "groups": groups,
        "run_id": entries[0].get("run_id", ""),
        "fingerprint": entries[0].get("fingerprint", ""),
        "period": entries[0].get("period", ""),
        "start_time": t0.isoformat(),
        "end_time": t_end.isoformat(),
    }


def _build_groups(phases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build coalesced group summaries from phases."""
    group_order = [label for _, label in GROUP_MAP]
    group_data: dict[str, dict[str, Any]] = {}

    for p in phases:
        g = p["group"]
        if g not in group_data:
            group_data[g] = {"name": g, "duration": 0.0, "item_count": 0,
                             "max_single": 0.0, "max_single_name": ""}
        group_data[g]["duration"] += p["duration"]
        group_data[g]["item_count"] += 1
        if p["duration"] > group_data[g]["max_single"]:
            group_data[g]["max_single"] = p["duration"]
            group_data[g]["max_single_name"] = p["name"]

    # Return in GROUP_MAP order
    result: list[dict[str, Any]] = []
    seen_other = False
    for gname in group_order:
        if gname in group_data:
            result.append(group_data[gname])
    for gname, gd in group_data.items():
        if gname not in group_order:
            result.append(gd)

    return result


def _fmt_duration(s: float) -> str:
    if s >= 60:
        return f"{s/60:.1f}min"
    return f"{s:.1f}s"


def print_summary(analysis: dict[str, Any]) -> None:
    """Print a human-readable timing summary."""
    total = analysis["total_s"]
    print(f"\n{'='*70}")
    print(f"Trace Timing Analysis: {analysis['run_id']}")
    print(f"{'='*70}")
    print(f"  Period:    {analysis['period']}")
    print(f"  Total:     {_fmt_duration(total)} ({total:.1f}s)")
    print(f"  Trace:     {analysis['path']}")

    # Group summary
    print(f"\n{'Phase Group':<40} {'Time':>8} {'%':>7}  Bar")
    print(f"{'-'*70}")
    for g in analysis["groups"]:
        pct = g["duration"] / total * 100 if total > 0 else 0
        bar = "#" * int(pct / 2)
        print(f"  {g['name']:<38} {_fmt_duration(g['duration']):>8} {pct:>5.1f}%  {bar}")
    print(f"{'-'*70}")

    # Detail: show non-fg phases
    print(f"\nDetailed Timeline (non-fg phases only):")
    print(f"{'Offset':>7} {'Dur':>7}  Phase")
    print(f"{'-'*70}")
    for p in analysis["phases"]:
        if p["name"].startswith("fg:"):
            continue
        flag = " <--" if p["duration"] > 5.0 else ""
        print(f"{p['offset']:>6.1f}s {p['duration']:>6.1f}s  {p['name']}{flag}")
    print(f"{'-'*70}")

    # Observations
    observations = _find_observations(analysis)
    if observations:
        print(f"\nObservations:")
        for obs in observations:
            print(f"  {BULLET} {obs}")

    print(f"{'='*70}\n")


def _find_observations(analysis: dict[str, Any]) -> list[str]:
    """Generate notable observations from the timing data."""
    observations: list[str] = []
    total = analysis["total_s"]

    for g in analysis["groups"]:
        pct = g["duration"] / total * 100 if total > 0 else 0
        if pct > 30:
            observations.append(
                f"[{g['name']}] dominates at {pct:.0f}% of total ({_fmt_duration(g['duration'])})"
            )

    # Slow single phases (> 10s) excluding server-side generation wait
    slow = [p for p in analysis["phases"]
            if p["duration"] > 10.0
            and not p["name"].startswith("wait:")
            and not p["name"].startswith("fg:")]
    for p in slow:
        observations.append(
            f"Slow step: '{p['name']}' took {_fmt_duration(p['duration'])} at offset {p['offset']:.0f}s"
        )

    # Count OCR-heavy state machine cycles
    sm_phases = [p for p in analysis["phases"] if p["name"].startswith("sm:")]
    sm_total = sum(p["duration"] for p in sm_phases)
    if sm_phases:
        observations.append(
            f"State machine: {len(sm_phases)} cycle(s), total OCR time {_fmt_duration(sm_total)}"
        )

    # Foreground check stats
    fg_phases = [p for p in analysis["phases"] if p["name"].startswith("fg:")]
    fg_total = sum(p["duration"] for p in fg_phases)
    if fg_phases:
        observations.append(
            f"Foreground checks: {len(fg_phases)} checks, "
            f"total {_fmt_duration(fg_total)} "
            f"(avg {fg_total/len(fg_phases):.1f}s each)"
        )

    # Idle/gap detection: find phases where the REAL time (foreground check + OCR)
    # accounts for only a small fraction of wall clock and the rest is sleep
    # Look for phases that are preceded by fg checks where the actual processing
    # is fast but the inter-phase gap is large
    # This shows where sleeps/pauses are eating 1.5s-3s at a time

    if not observations:
        observations.append("No significant timing anomalies detected.")

    return observations


def compare_runs(analyses: list[dict[str, Any]]) -> None:
    """Compare multiple runs side by side."""
    if len(analyses) < 2:
        return

    print(f"\n{'='*70}")
    print("Cross-Run Comparison")
    print(f"{'='*70}")

    # Collect all group names
    all_names: list[str] = []
    for a in analyses:
        for g in a["groups"]:
            if g["name"] not in all_names:
                all_names.append(g["name"])

    header = f"  {'Phase Group':<38}"
    for a in analyses:
        header += f" {a['run_id'][-4:]:>10}"
    print(header)
    print(f"  {'-'*66}")

    for gname in all_names:
        row = f"  {gname:<38}"
        for a in analyses:
            g = next((g for g in a["groups"] if g["name"] == gname), None)
            if g:
                row += f" {_fmt_duration(g['duration']):>10}"
            else:
                row += f" {'--':>10}"
        print(row)

    print(f"  {'-'*66}")
    total_row = f"  {'TOTAL':<38}"
    for a in analyses:
        total_row += f" {_fmt_duration(a['total_s']):>10}"
    print(total_row)

    # Delta
    if len(analyses) == 2:
        a0, a1 = analyses[0], analyses[1]
        diff = a0["total_s"] - a1["total_s"]
        print(f"\n  Delta: {_fmt_duration(abs(diff))} "
              f"({'slower' if diff > 0 else 'faster'} than {a1['run_id'][-4:]})")

    print(f"{'='*70}\n")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    analyses: list[dict[str, Any]] = []
    for arg in sys.argv[1:]:
        p = Path(arg)
        if p.is_dir():
            trace_file = p / "trace.jsonl"
        else:
            trace_file = p

        if not trace_file.exists():
            print(f"ERROR: trace file not found: {trace_file}")
            continue

        analysis = analyze_trace(trace_file)
        if "error" in analysis:
            print(f"ERROR: {analysis['error']} ({analysis['path']})")
            continue

        analyses.append(analysis)
        print_summary(analysis)

    if len(analyses) > 1:
        compare_runs(analyses)

    return 0


if __name__ == "__main__":
    sys.exit(main())
