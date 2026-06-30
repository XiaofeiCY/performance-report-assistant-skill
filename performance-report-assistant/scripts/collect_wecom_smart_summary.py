#!/usr/bin/env python
"""Collect Enterprise WeChat Smart Summary evidence on Windows.

This script intentionally follows the validated probe in:
E:/work/AgentsShare/wecom_uia_probe

The automation path is staged and conservative:
1. Find or open the Enterprise WeChat Smart Summary page.
2. Paste the prompt into the verified Smart Summary template page.
3. Click "开始总结".
4. Wait for completion and copy the result.

Manual-input mode is available as a fallback and does not touch the desktop.
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_PROMPT_BODY = (
    "聊天中涉及临时生产修数、生产数据处理、线上数据维护、"
    "业务方临时数据修正相关的事项。只列出真实发生的工作事项，按时间或事项分条。"
)


def format_period_for_prompt(period: str) -> str:
    normalized = " ".join((period or "").strip().split())
    if not normalized:
        return ""
    if ".." in normalized:
        start, end = normalized.split("..", 1)
        if start.strip() and end.strip():
            return f"{start.strip()} 至 {end.strip()}"
    return normalized


def require_windows() -> None:
    if sys.platform != "win32":
        print("Error: Desktop automation mode requires Windows.")
        print("Use --manual-input on other platforms.")
        sys.exit(1)


def load_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        return Path(args.prompt_file).read_text(encoding="utf-8").strip()
    period = format_period_for_prompt(args.period)
    if period:
        return f"总结 {period} 期间{DEFAULT_PROMPT_BODY}"
    return f"总结目标周期内{DEFAULT_PROMPT_BODY}"


def read_manual_input(args: argparse.Namespace) -> str:
    if args.from_clipboard:
        try:
            import pyperclip
        except ImportError:
            print("Error: --from-clipboard requires pyperclip. Install: pip install pyperclip")
            sys.exit(1)
        text = pyperclip.paste()
        if not text or not text.strip():
            print("Error: Clipboard is empty.")
            sys.exit(1)
        return text.strip()

    if not sys.stdin.isatty():
        raw_bytes = sys.stdin.buffer.read()
        return raw_bytes.decode("utf-8", errors="replace").strip()

    print("Paste your Smart Summary text below. Press Ctrl+Z then Enter to finish:")
    lines = []
    try:
        while True:
            lines.append(input())
    except EOFError:
        pass
    return "\n".join(lines).strip()


def write_markdown(
    output_path: str,
    scenario: str,
    period: str,
    collection_method: str,
    raw_summary: str,
) -> None:
    collected_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    content = f"""# Enterprise WeChat Smart Summary Evidence

- Source: wecom_smart_summary
- Collection method: {collection_method}
- Scenario: {scenario}
- Period: {period}
- Status: needs_user_confirmation
- Collected at: {collected_at}

## Raw Smart Summary

{raw_summary}
"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(content, encoding="utf-8", errors="replace")


def write_json(
    output_path: str,
    scenario: str,
    period: str,
    collection_method: str,
    raw_summary: str,
) -> None:
    data = {
        "source": "wecom_smart_summary",
        "collection_method": collection_method,
        "scenario": scenario,
        "period": period,
        "status": "needs_user_confirmation",
        "raw_summary": raw_summary,
        "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "runtime": {
            "platform": sys.platform,
            "client": "wecom_desktop",
            "collector": "collect_wecom_smart_summary.py",
            "probe_baseline": "E:/work/AgentsShare/wecom_uia_probe/stage3_v2.py",
        },
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def check_automation_dependencies() -> None:
    missing = []
    for mod in ["interception", "easyocr", "PIL", "pyperclip", "numpy"]:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        print(f"Error: Missing dependencies: {', '.join(missing)}")
        print("Install Python packages first, then install Interception driver separately.")
        print("See: performance-report-assistant/references/wecom-smart-summary-collector.md")
        sys.exit(1)


user32 = ctypes.WinDLL("user32", use_last_error=True) if sys.platform == "win32" else None
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True) if sys.platform == "win32" else None

SW_RESTORE = 9
SW_SHOW = 5
GA_ROOT = 2


def _window_class(hwnd: int) -> str:
    if not hwnd:
        return ""
    cn = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, cn, 256)
    return cn.value


def _window_title(hwnd: int) -> str:
    if not hwnd:
        return ""
    t = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, t, 256)
    return t.value


def _window_rect(hwnd: int) -> wintypes.RECT:
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r


def _root_window(hwnd: int) -> int:
    if not hwnd:
        return 0
    root = user32.GetAncestor(hwnd, GA_ROOT)
    return root or hwnd


def _enum_wecom_windows() -> list[tuple[int, wintypes.RECT, str, list]]:
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    results = []

    def cb(hwnd, _lp):
        if _window_class(hwnd) != "WeWorkWindow":
            return True
        rect = _window_rect(hwnd)
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        if width <= 0 or height <= 0:
            return True
        children = []

        def ecb(ch, _lp2):
            cr = _window_rect(ch)
            sz = (cr.right - cr.left, cr.bottom - cr.top)
            if sz[0] > 0 and sz[1] > 0:
                children.append((ch, _window_class(ch), _window_title(ch), cr, sz))
            return True

        user32.EnumChildWindows(hwnd, WNDENUMPROC(ecb), 0)
        results.append((hwnd, rect, _window_title(hwnd), children))
        return True

    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return results


def find_smart_summary() -> tuple[int | None, wintypes.RECT | None, int | None, wintypes.RECT | None]:
    for hwnd, rect, _title, children in _enum_wecom_windows():
        for ch, cn, title, cr, _sz in children:
            if "智能总结" in cn or "智能总结" in title:
                return hwnd, rect, ch, cr
    return None, None, None, None


def find_best_wecom_window() -> tuple[int | None, wintypes.RECT | None]:
    windows = _enum_wecom_windows()
    if not windows:
        return None, None
    windows.sort(
        key=lambda item: (
            any("智能总结" in c[1] or "智能总结" in c[2] for c in item[3]),
            user32.IsWindowVisible(item[0]),
            (item[1].right - item[1].left) * (item[1].bottom - item[1].top),
        ),
        reverse=True,
    )
    return windows[0][0], windows[0][1]


def _focus_window(hwnd: int) -> None:
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    else:
        user32.ShowWindow(hwnd, SW_SHOW)
    time.sleep(0.2)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.4)


def _foreground_is_wecom(target_hwnd: int) -> bool:
    fg = user32.GetForegroundWindow()
    return _root_window(fg) == _root_window(target_hwnd) or _window_class(_root_window(fg)) == "WeWorkWindow"


def ensure_wecom_foreground(stage: str, main_hwnd: int, max_attempts: int = 3) -> None:
    """Bring WeCom to foreground with retries. Only fail after all attempts exhausted."""
    if _foreground_is_wecom(main_hwnd):
        return

    for attempt in range(1, max_attempts + 1):
        print(f"企微采集：前台不是企业微信，第 {attempt}/{max_attempts} 次恢复尝试。")

        if user32.IsIconic(main_hwnd):
            user32.ShowWindow(main_hwnd, SW_RESTORE)
        else:
            user32.ShowWindow(main_hwnd, SW_SHOW)
        time.sleep(0.15)
        user32.SetForegroundWindow(main_hwnd)
        user32.BringWindowToTop(main_hwnd)
        time.sleep(0.25)
        if _foreground_is_wecom(main_hwnd):
            return

        # AttachThreadInput fallback
        fg = user32.GetForegroundWindow()
        fg_thread = user32.GetWindowThreadProcessId(fg, None)
        target_thread = user32.GetWindowThreadProcessId(main_hwnd, None)
        our_thread = kernel32.GetCurrentThreadId()
        attached = []
        try:
            for tid in {fg_thread, target_thread}:
                if tid and tid != our_thread:
                    user32.AttachThreadInput(our_thread, tid, True)
                    attached.append(tid)
            user32.ShowWindow(main_hwnd, SW_RESTORE)
            user32.SetForegroundWindow(main_hwnd)
            user32.BringWindowToTop(main_hwnd)
            time.sleep(0.25)
        finally:
            for tid in attached:
                user32.AttachThreadInput(our_thread, tid, False)
        if _foreground_is_wecom(main_hwnd):
            return

        # Topmost nudge
        HWND_TOPMOST = -1
        HWND_NOTOPMOST = -2
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_SHOWWINDOW = 0x0040
        user32.SetWindowPos(main_hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
        time.sleep(0.15)
        user32.SetForegroundWindow(main_hwnd)
        user32.BringWindowToTop(main_hwnd)
        time.sleep(0.15)
        user32.SetWindowPos(main_hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
        time.sleep(0.2)
        if _foreground_is_wecom(main_hwnd):
            return

        # Interception click on title bar (last attempt only)
        if attempt == max_attempts:
            try:
                import interception
                rect = _window_rect(main_hwnd)
                interception.move_to(rect.left + 200, rect.top + 10)
                time.sleep(0.1)
                interception.click(button="left")
                time.sleep(0.4)
                if _foreground_is_wecom(main_hwnd):
                    return
            except Exception:
                pass

    fg = user32.GetForegroundWindow()
    print(f"企微采集失败：[{stage}] 多次尝试后仍无法将企业微信置于前台，已停止以避免误操作其他窗口。")
    print(f"当前前台窗口：class={_window_class(fg)}, title={_window_title(fg)[:80]}")
    print("请手动点击企业微信窗口后重试，或使用 --manual-input。")
    sys.exit(1)


def capture_rect(rect: wintypes.RECT, path: str):
    from PIL import ImageGrab

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    img = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom), all_screens=True)
    img.save(path)
    return img


def ocr_all(img: object, reader: object, min_conf: float = 0.3) -> list:
    import numpy as np

    results = reader.readtext(np.array(img))
    return [(bbox, text, conf) for bbox, text, conf in results if conf >= min_conf]


def ocr_find(img: object, target: str, reader: object) -> tuple[int | None, int | None, float | None, str | None]:
    for bbox, text, conf in ocr_all(img, reader, 0.2):
        if target in text:
            cx = int((bbox[0][0] + bbox[2][0]) / 2)
            cy = int((bbox[0][1] + bbox[2][1]) / 2)
            return cx, cy, conf, text
    return None, None, None, None


def save_ocr(path: str, img: object, reader: object, min_conf: float = 0.1) -> None:
    lines = []
    for bbox, text, conf in ocr_all(img, reader, min_conf):
        cx = int((bbox[0][0] + bbox[2][0]) / 2)
        cy = int((bbox[0][1] + bbox[2][1]) / 2)
        lines.append(f"[{conf:.2f}] '{text}' @ ({cx},{cy})")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8", errors="replace")


def _ocr_texts(img: object, reader: object, min_conf: float = 0.2) -> list[str]:
    return [text for _bbox, text, _conf in ocr_all(img, reader, min_conf)]


def _joined_text(img: object, reader: object, min_conf: float = 0.2) -> str:
    return " ".join(_ocr_texts(img, reader, min_conf))


def smart_summary_page_visible(img: object, reader: object) -> bool:
    texts = _joined_text(img, reader, 0.2)
    required = ["智能总结"]
    page_hints = ["开始总结", "输入你想总结", "你想总结", "暂无历史总结", "总结团队周报", "总结聊天内容"]
    return all(item in texts for item in required) and any(item in texts for item in page_hints)


def smart_summary_history_visible(img: object, reader: object) -> bool:
    import re

    texts = _joined_text(img, reader, 0.2)
    if "智能总结" not in texts:
        return False

    # If input-page hints are present, this is not a history page.
    input_hints = ["开始总结", "输入你想总结", "暂无历史总结", "总结团队周报", "总结聊天内容"]
    if any(item in texts for item in input_hints):
        return False

    # Bottom result-action buttons visible (strongest signal).
    if any(item in texts for item in ["新建文档", "发送邮件"]):
        return True

    # History content patterns: Smart Summary output is structured as numbered
    # items with timestamped chat citations. The input page has none of these.
    numbered_items = bool(re.search(r'(?:^|\s)\d+\.\s*\S{3}', texts))
    date_pattern = bool(re.search(r'\d{4}[-/]\d{2}[-/]\d{2}', texts))
    time_pattern = bool(re.search(r'\d{1,2}:\d{2}(:\d{2})?', texts))

    return sum([numbered_items, date_pattern, time_pattern]) >= 2


def classify_smart_summary_page(img: object, reader: object) -> str:
    if smart_summary_page_visible(img, reader):
        return "smart_summary_input_page"
    if smart_summary_history_visible(img, reader):
        return "smart_summary_history_result_page"
    texts = _joined_text(img, reader, 0.2)
    if "智能总结" in texts:
        return "smart_summary_unknown_page"
    return "main_or_unknown_page"


def _uia_find_summary_entry(main_hwnd: int) -> list[tuple[int, int, str]]:
    """Search for Smart Summary entry via UI Automation. Returns candidate click positions."""
    try:
        import uiautomation as auto
    except ImportError:
        return []
    candidates = []
    try:
        wecom_root = auto.GetRootControl()
        for win in wecom_root.GetChildren():
            try:
                if win.NativeWindowHandle == main_hwnd:
                    _collect_uia_candidates(win, candidates, depth=0, max_depth=6)
            except Exception:
                continue
    except Exception:
        pass
    return candidates


def _collect_uia_candidates(control, candidates: list, depth: int, max_depth: int) -> None:
    if depth > max_depth:
        return
    try:
        name = (control.Name or "").strip()
        auto_id = (control.AutomationId or "").strip()
        if "智能总结" in name or "智能总结" in auto_id:
            rect = control.BoundingRectangle
            cx = rect.left + rect.width() // 2
            cy = rect.top + rect.height() // 2
            if cx > 0 and cy > 0 and rect.width() > 0 and rect.height() > 0:
                candidates.append((cx, cy, f"UIA name='{name[:40]}' autoId='{auto_id[:40]}'"))
        for child in control.GetChildren():
            _collect_uia_candidates(child, candidates, depth + 1, max_depth)
    except Exception:
        pass


def click_smart_summary_entry(main_hwnd: int, main_rect: wintypes.RECT, reader: object, screenshot_dir: str) -> None:
    """Open Smart Summary from the main WeCom window with bounded, verified candidates only."""
    import interception

    print("企微采集阶段 1：未检测到智能总结页，尝试点击左侧智能总结入口。")
    ensure_wecom_foreground("点击智能总结入口前", main_hwnd)
    img = capture_rect(main_rect, os.path.join(screenshot_dir, "stage1_before_entry.png"))
    save_ocr(os.path.join(screenshot_dir, "stage1_before_entry.ocr.txt"), img, reader)
    page_state = classify_smart_summary_page(img, reader)
    if page_state not in {"main_or_unknown_page", "smart_summary_unknown_page", "smart_summary_history_result_page"}:
        print(f"企微采集失败：入口扫描前页面状态为 {page_state}，拒绝扫描企业微信左侧菜单。")
        print(f"诊断截图/OCR 已保存：{screenshot_dir}")
        sys.exit(1)
    if page_state != "main_or_unknown_page":
        print(f"企微采集阶段 1：入口扫描前页面已是 {page_state}，跳过左侧栏扫描，直接尝试 + 新建恢复。")
        _try_click_plus_loose(main_hwnd, main_rect, reader, screenshot_dir)
        return

    width = main_rect.right - main_rect.left
    height = main_rect.bottom - main_rect.top
    candidates: list[tuple[int, int, str]] = []

    # Strategy A: UI Automation search for named controls
    uia_candidates = _uia_find_summary_entry(main_hwnd)
    if uia_candidates:
        print(f"企微采集阶段 1：UIA 发现 {len(uia_candidates)} 个候选控件。")
        candidates.extend(uia_candidates)

    # Strategy B: OCR in left sidebar area, exact label only.
    for bbox, text, _conf in ocr_all(img, reader, 0.15):
        cx = int((bbox[0][0] + bbox[2][0]) / 2)
        cy = int((bbox[0][1] + bbox[2][1]) / 2)
        if cx < width * 0.35 and "智能总结" in text:
            candidates.append((main_rect.left + cx, main_rect.top + cy, f"OCR '{text}'"))

    # Strategy C: Single unstable probe fallback — only when UIA and OCR both fail.
    # The probe coordinate (31, 499 at 1080px height) is an approximate center
    # of the Smart Summary entry area. Marked unstable because windows resize freely.
    # This is the ONLY hardcoded coordinate allowed. No scanning, no multi-point probing.
    if not candidates:
        base_y = int(height * 499 / 1080)
        candidates.append((main_rect.left + 31, main_rect.top + base_y, "unstable probe (31,499 scaled)"))

    if not candidates:
        print("企微采集失败：未找到可验证的智能总结入口候选。")
        print(f"诊断截图/OCR 已保存：{screenshot_dir}")
        sys.exit(1)

    for sx, sy, label in candidates:
        print(f"企微采集阶段 1：点击入口候选 {label} -> ({sx},{sy})")
        ensure_wecom_foreground("点击智能总结入口候选前", main_hwnd)
        interception.move_to(sx, sy)
        time.sleep(0.1)
        interception.click(button="left")
        time.sleep(1.5)
        new_main, new_rect, _child, _child_rect = find_smart_summary()
        check_rect = new_rect or main_rect
        img_after = capture_rect(check_rect, os.path.join(screenshot_dir, "stage1_after_entry.png"))
        save_ocr(os.path.join(screenshot_dir, "stage1_after_entry.ocr.txt"), img_after, reader)
        page_state = classify_smart_summary_page(img_after, reader)
        if page_state == "smart_summary_input_page":
            print("企微采集阶段 1：已确认进入智能总结输入页。")
            return
        if page_state == "smart_summary_history_result_page":
            print("企微采集阶段 1：检测到历史结果页，尝试点击 + 新建本次总结。")
            click_new_summary_plus(main_hwnd, main_rect, reader, screenshot_dir)
            return
        if page_state == "smart_summary_unknown_page":
            print("企微采集失败：智能总结页类型无法确定，已停止以保护数据安全。")
            print(f"诊断截图/OCR 已保存：{screenshot_dir}")
            sys.exit(1)

    print("企微采集失败：所有策略均未能打开智能总结入口。")
    print(f"诊断截图/OCR 已保存：{screenshot_dir}")
    sys.exit(1)


def _try_click_plus_loose(main_hwnd: int, main_rect: wintypes.RECT, reader: object, screenshot_dir: str) -> None:
    """Click the '+' new-summary button from a confirmed smart_summary_history_result_page ONLY.

    This is a variant of click_new_summary_plus used during recovery.
    It must NOT accept smart_summary_unknown_page — unknown pages must fail safely.
    Calibrated coordinate guesses are forbidden; only OCR-detected '+' is used.
    """
    import interception

    # Non-negotiable: verify we are on a history result page before any click
    img = capture_rect(main_rect, os.path.join(screenshot_dir, "stage1b_loose_before_plus.png"))
    save_ocr(os.path.join(screenshot_dir, "stage1b_loose_before_plus.ocr.txt"), img, reader)
    page_state = classify_smart_summary_page(img, reader)
    if page_state == "smart_summary_unknown_page":
        print("企微采集失败：页面状态为未知智能总结页，拒绝执行 + 点击。")
        print(f"诊断截图/OCR 已保存：{screenshot_dir}")
        sys.exit(1)
    if page_state not in ("smart_summary_history_result_page",):
        print(f"企微采集失败：+ 点击前页面状态为 {page_state}，不是历史结果页，已停止。")
        print(f"诊断截图/OCR 已保存：{screenshot_dir}")
        sys.exit(1)

    print("企微采集阶段 1B-loose：已确认历史结果页，尝试点击 + 新建。")
    ensure_wecom_foreground("点击智能总结 + 新建前(loose)", main_hwnd)
    width = main_rect.right - main_rect.left
    height = main_rect.bottom - main_rect.top

    candidates: list[tuple[int, int, str]] = []
    for bbox, text, _conf in ocr_all(img, reader, 0.1):
        cx = int((bbox[0][0] + bbox[2][0]) / 2)
        cy = int((bbox[0][1] + bbox[2][1]) / 2)
        if cy < height * 0.16 and width * 0.12 < cx < width * 0.25 and ("+" in text or "＋" in text):
            candidates.append((main_rect.left + cx, main_rect.top + cy, f"OCR '{text}'"))

    if not candidates:
        print("企微采集失败：已确认历史结果页，但 OCR 未找到 + 按钮，已停止。")
        print(f"诊断截图/OCR 已保存：{screenshot_dir}")
        sys.exit(1)

    for sx, sy, label in candidates:
        print(f"企微采集阶段 1B-loose：点击候选 {label} -> ({sx},{sy})")
        ensure_wecom_foreground("点击 + 候选前(loose)", main_hwnd)
        interception.move_to(sx, sy)
        time.sleep(0.1)
        interception.click(button="left")
        time.sleep(1.2)
        img_after = capture_rect(main_rect, os.path.join(screenshot_dir, "stage1b_loose_after_plus.png"))
        save_ocr(os.path.join(screenshot_dir, "stage1b_loose_after_plus.ocr.txt"), img_after, reader)
        state = classify_smart_summary_page(img_after, reader)
        if state == "smart_summary_input_page":
            print("企微采集阶段 1B-loose：已进入智能总结输入页。")
            return
        if state == "main_or_unknown_page":
            print("企微采集阶段 1B-loose：点击 + 后离开智能总结页，停止此恢复路径。")
            return

    print("企微采集失败：历史结果页 + 点击未产生输入页，已停止。")
    print(f"诊断截图/OCR 已保存：{screenshot_dir}")
    sys.exit(1)



def click_new_summary_plus(main_hwnd: int, main_rect: wintypes.RECT, reader: object, screenshot_dir: str) -> None:
    """On a Smart Summary history-result page, click the page-local '+' new summary button."""
    import interception

    print("企微采集阶段 1B：检测到智能总结历史结果页，准备点击页内 + 新建本次总结。")
    ensure_wecom_foreground("点击智能总结 + 新建前", main_hwnd)
    img = capture_rect(main_rect, os.path.join(screenshot_dir, "stage1b_before_plus.png"))
    save_ocr(os.path.join(screenshot_dir, "stage1b_before_plus.ocr.txt"), img, reader)
    cur_state = classify_smart_summary_page(img, reader)
    if cur_state == "smart_summary_unknown_page":
        print("企微采集失败：点击 + 前即时分类为未知智能总结页，已停止以保护数据安全。")
        print("unknown page 不能走任何 + 恢复路径。")
        print(f"诊断截图/OCR 已保存：{screenshot_dir}")
        sys.exit(1)
    if cur_state != "smart_summary_history_result_page":
        print(f"企微采集失败：点击 + 前页面状态为 {cur_state}，不是历史结果页，已停止。")
        print(f"诊断截图/OCR 已保存：{screenshot_dir}")
        sys.exit(1)

    width = main_rect.right - main_rect.left
    height = main_rect.bottom - main_rect.top
    candidates: list[tuple[int, int, str]] = []

    # In the verified history-result page, the '+' is inside the Smart Summary
    # conversation header, near the top-right of the left summary-session pane.
    for bbox, text, _conf in ocr_all(img, reader, 0.1):
        cx = int((bbox[0][0] + bbox[2][0]) / 2)
        cy = int((bbox[0][1] + bbox[2][1]) / 2)
        if cy < height * 0.16 and width * 0.12 < cx < width * 0.25 and ("+" in text or "＋" in text):
            candidates.append((main_rect.left + cx, main_rect.top + cy, f"OCR '{text}'"))

    for sx, sy, label in candidates:
        print(f"企微采集阶段 1B：点击 + 新建候选 {label} -> ({sx},{sy})")
        ensure_wecom_foreground("点击智能总结 + 新建候选前", main_hwnd)
        interception.move_to(sx, sy)
        time.sleep(0.1)
        interception.click(button="left")
        time.sleep(1.2)
        img_after = capture_rect(main_rect, os.path.join(screenshot_dir, "stage1b_after_plus.png"))
        save_ocr(os.path.join(screenshot_dir, "stage1b_after_plus.ocr.txt"), img_after, reader)
        page_state = classify_smart_summary_page(img_after, reader)
        if page_state == "smart_summary_input_page":
            print("企微采集阶段 1B：已进入智能总结输入页。")
            return
        if page_state == "main_or_unknown_page":
            print("企微采集阶段 1B：点击 + 后离开智能总结页，已停止以避免继续误操作。")
            print(f"诊断截图/OCR 已保存：{screenshot_dir}")
            sys.exit(1)

    print("企微采集失败：检测到历史结果页，但未能通过页内 + 新建进入输入页。")
    print("已停止，避免切换企业微信左侧菜单或查看无关信息。")
    print(f"诊断截图/OCR 已保存：{screenshot_dir}")
    sys.exit(1)


def paste_prompt(main_hwnd: int, main_rect: wintypes.RECT, child_rect: wintypes.RECT, prompt: str) -> None:
    import interception
    import pyperclip

    print("企微采集阶段 2：向智能总结输入框粘贴提示词。")
    ensure_wecom_foreground("粘贴提示词前", main_hwnd)
    pyperclip.copy(prompt)

    input_x = child_rect.left + (child_rect.right - child_rect.left) // 2
    input_y = child_rect.top + (child_rect.bottom - child_rect.top) // 2
    interception.move_to(input_x, input_y)
    time.sleep(0.2)
    interception.click(button="left")
    time.sleep(0.3)
    ensure_wecom_foreground("发送 Ctrl+V 前", main_hwnd)
    with interception.hold_key("ctrl"):
        interception.press("v")
    time.sleep(0.5)


def find_start_button(main_rect: wintypes.RECT, img: object, reader: object) -> tuple[int, int]:
    bx, by, conf, text = ocr_find(img, "开始总结", reader)
    if bx is not None and by is not None:
        print(f"企微采集阶段 3：OCR 找到 '{text}' conf={conf:.2f}。")
        return main_rect.left + bx, main_rect.top + by

    all_texts = ocr_all(img, reader, 0.2)
    width = main_rect.right - main_rect.left
    height = main_rect.bottom - main_rect.top
    for bbox, text, conf in all_texts:
        cx = int((bbox[0][0] + bbox[2][0]) / 2)
        cy = int((bbox[0][1] + bbox[2][1]) / 2)
        if "总结" in text and cx > width * 0.55 and cy > height * 0.45:
            print(f"企微采集阶段 3：使用按钮候选 '{text}' conf={conf:.2f}。")
            return main_rect.left + cx, main_rect.top + cy

    # stage3_v2.py validated fallback: bottom-right button area.
    print("企微采集阶段 3：OCR 未找到开始总结，使用 probe fallback 按钮坐标。")
    return main_rect.right - 90, main_rect.top + int(height * 0.55)


def click_start_and_wait(
    main_hwnd: int,
    main_rect: wintypes.RECT,
    reader: object,
    screenshot_dir: str,
    max_wait_seconds: int,
    stable_seconds: int,
    poll_interval: int,
) -> str:
    """Click '开始总结' and wait for result using observable UI state machine.

    States: submitted -> generating -> result_detected -> copy_available -> copied.
    Returns the final page state to inform the caller whether copying is safe.
    """
    import interception

    print("企微采集阶段 3：点击开始总结。")
    img = capture_rect(main_rect, os.path.join(screenshot_dir, "stage3_before_start.png"))
    save_ocr(os.path.join(screenshot_dir, "stage3_before_start.ocr.txt"), img, reader)
    bx, by = find_start_button(main_rect, img, reader)

    ensure_wecom_foreground("点击开始总结前", main_hwnd)
    interception.move_to(main_rect.left + (main_rect.right - main_rect.left) // 2, main_rect.top + 15)
    time.sleep(0.1)
    interception.click(button="left")
    time.sleep(0.2)
    interception.move_to(bx, by)
    time.sleep(0.1)
    interception.click(button="left")

    print("企微采集阶段 4：等待结果生成（状态机：submitted → generating → result_detected → copy_available）。")
    waited = 0
    last_texts_snapshot = ""
    stable_since = 0
    state = "submitted"

    while waited < max_wait_seconds:
        time.sleep(poll_interval)
        waited += poll_interval

        img_poll = capture_rect(main_rect, os.path.join(screenshot_dir, "stage4_poll.png"))
        save_ocr(os.path.join(screenshot_dir, "stage4_poll.ocr.txt"), img_poll, reader, min_conf=0.1)
        texts = " ".join(text for _bbox, text, _conf in ocr_all(img_poll, reader, 0.3))
        texts_low = " ".join(text for _bbox, text, _conf in ocr_all(img_poll, reader, 0.1))

        # Transition: submitted -> generating
        if state == "submitted":
            bx_check, _, _, _ = ocr_find(img_poll, "开始总结", reader)
            if bx_check is None:
                state = "generating"
                print(f"企微采集进度：开始总结按钮已消失，进入生成状态（已等待 {waited} 秒）。")
                continue
            print(f"企微采集进度：等待开始总结按钮消失，已等待 {waited} 秒。")
            continue

        # Transition: generating -> result_detected
        if state == "generating":
            has_result_content = (
                "新建文档" in texts_low
                or "发送邮件" in texts_low
                or "复制" in texts_low
            )
            has_body_text = len(texts) > 50
            if has_result_content or has_body_text:
                state = "result_detected"
                print(f"企微采集进度：检测到结果内容（已等待 {waited} 秒），监控文本稳定性。")
                continue
            print(f"企微采集进度：智能总结生成中，已等待 {waited} 秒；等待结果内容出现。")
            continue

        # Transition: result_detected -> copy_available (text stability check)
        if state == "result_detected":
            has_copy = "复制" in texts_low and "开始总结" not in texts
            uia_x, uia_y = _uia_find_copy_button(main_hwnd, main_rect)
            if has_copy or (uia_x is not None):
                state = "copy_available"
                print(f"企微采集进度：检测到复制按钮可用，准备进入复制阶段（已等待 {waited} 秒）。")
                return state

            # Monitor text stability
            if texts == last_texts_snapshot:
                stable_since += poll_interval
                if stable_since >= stable_seconds:
                    state = "copy_available"
                    print(f"企微采集进度：结果文本 {stable_seconds} 秒未变化，准备进入复制阶段（已等待 {waited} 秒）。")
                    return state
            else:
                stable_since = 0
                last_texts_snapshot = texts
                print(f"企微采集进度：结果文本仍在增长，已等待 {waited} 秒。")
            continue

        # copy_available: already set above, return immediately
        if state == "copy_available":
            return state

        # Heartbeat at ~12s intervals
        if waited % 12 <= poll_interval:
            print(f"企微采集进度：状态={state}，已等待 {waited}/{max_wait_seconds} 秒。")

    # Hard timeout reached
    print(f"企微采集进度：达到硬上限 {max_wait_seconds} 秒，状态={state}。")
    if state in ("result_detected", "copy_available"):
        print("企微采集进度：硬上限到达时已检测到结果页或复制按钮，允许尝试复制。")
        return state
    if state == "generating":
        # Check one last time if result page is visible
        img_final = capture_rect(main_rect, os.path.join(screenshot_dir, "stage4_timeout_final.png"))
        save_ocr(os.path.join(screenshot_dir, "stage4_timeout_final.ocr.txt"), img_final, reader, min_conf=0.1)
        final_texts = " ".join(text for _bbox, text, _conf in ocr_all(img_final, reader, 0.1))
        if "新建文档" in final_texts or "发送邮件" in final_texts or "复制" in final_texts:
            print("企微采集进度：超时后检测到结果操作区，允许进入复制阶段。")
            return "copy_available"
        print("企微采集失败：等待超时且未确认智能总结结果页，已停止。")
        print(f"诊断截图/OCR 已保存：{screenshot_dir}")
        sys.exit(1)

    print("企微采集失败：等待超时且状态无法确认，已停止。")
    print(f"诊断截图/OCR 已保存：{screenshot_dir}")
    sys.exit(1)


def _uia_find_copy_button(main_hwnd: int, main_rect: wintypes.RECT) -> tuple[int | None, int | None]:
    """Search for the '复制' / 'copy' button in the Smart Summary result via UI Automation."""
    try:
        import uiautomation as auto
    except ImportError:
        return None, None
    try:
        wecom_root = auto.GetRootControl()
        for win in wecom_root.GetChildren():
            try:
                if win.NativeWindowHandle == main_hwnd:
                    for control, _depth in auto.WalkTree(win, lambda c, d: d < 8):
                        try:
                            name = (control.Name or "").strip()
                            if name in ("复制", "copy"):
                                rect = control.BoundingRectangle
                                if rect.width() > 0 and rect.height() > 0:
                                    cx = rect.left + rect.width() // 2
                                    cy = rect.top + rect.height() // 2
                                    return cx, cy
                        except Exception:
                            continue
            except Exception:
                continue
    except Exception:
        pass
    return None, None



def copy_result(main_hwnd: int, main_rect: wintypes.RECT, child_rect: wintypes.RECT, reader: object, screenshot_dir: str, wait_state: str) -> str:
    """Copy the Smart Summary result using verified strategies only.

    Args:
        wait_state: The final state from click_start_and_wait(). Must be
                    'result_detected' or 'copy_available' to prove this is
                    a current-generation result, not a stale history page.

    Priority:
    1. UIA to find and click "复制" button.
    2. Confirm result page, then bounded in-page scrolling + OCR to find "复制".
    3. If copy button not found after bounded scroll, stop and save diagnostics.

    Forbidden: right-click menu, fixed-coordinate copy guesses, Ctrl+A/Ctrl+C on unknown regions.
    History result pages may contain a "复制" button but are NOT current evidence.
    """
    import interception
    import pyperclip

    # --- Non-negotiable guard: must have been generated in this session ---
    if wait_state not in ("result_detected", "copy_available"):
        print(f"企微采集失败：复制前等待状态为 {wait_state}，不是本次生成的结果，拒绝复制。")
        print(f"诊断截图/OCR 已保存：{screenshot_dir}")
        sys.exit(1)

    print("企微采集阶段 5：复制智能总结结果。")
    ensure_wecom_foreground("复制结果前", main_hwnd)
    width = main_rect.right - main_rect.left
    height = main_rect.bottom - main_rect.top

    # --- Gate: verify page is a Smart Summary result page, not history/input/unknown ---
    img = capture_rect(main_rect, os.path.join(screenshot_dir, "stage5_before_copy.png"))
    save_ocr(os.path.join(screenshot_dir, "stage5_before_copy.ocr.txt"), img, reader, min_conf=0.1)
    page_state = classify_smart_summary_page(img, reader)

    if page_state == "smart_summary_history_result_page":
        # After generation the page may OCR-classify as history_result_page
        # because it contains result content, numbered items, and action buttons.
        # This is safe ONLY because wait_state already proves we generated it.
        print("企微采集阶段 5：页面分类为历史结果页特征，但状态机已确认本次生成，允许复制。")
    elif page_state == "smart_summary_unknown_page":
        print("企微采集失败：复制前页面状态为未知智能总结页，拒绝复制。")
        print(f"诊断截图/OCR 已保存：{screenshot_dir}")
        sys.exit(1)
    elif page_state == "smart_summary_input_page":
        print("企微采集失败：复制前页面仍为输入页，无结果可复制。")
        print(f"诊断截图/OCR 已保存：{screenshot_dir}")
        sys.exit(1)
    elif page_state == "main_or_unknown_page":
        print("企微采集失败：复制前页面状态为未知/主聊天页，拒绝复制。")
        print(f"诊断截图/OCR 已保存：{screenshot_dir}")
        sys.exit(1)

    # --- Strategy A: UI Automation to find and click "复制" button ---
    uia_x, uia_y = _uia_find_copy_button(main_hwnd, main_rect)
    if uia_x is not None and uia_y is not None:
        print(f"企微采集阶段 5：UIA 找到复制按钮 @ ({uia_x},{uia_y})，点击。")
        pyperclip.copy("")
        ensure_wecom_foreground("UIA 点击复制前", main_hwnd)
        interception.move_to(uia_x, uia_y)
        time.sleep(0.1)
        interception.click(button="left")
        time.sleep(0.6)
        result = pyperclip.paste()
        if result and len(result.strip()) >= 10:
            return result.strip()
        print("企微采集阶段 5：UIA 复制后剪贴板为空或过短，继续尝试 OCR。")

    # Bounded in-page scrolling to find "复制" at bottom
    content_cx = child_rect.left + (child_rect.right - child_rect.left) // 2
    content_cy = child_rect.top + (child_rect.bottom - child_rect.top) // 2

    max_scrolls = 6
    for scroll_pass in range(max_scrolls + 1):
        # Move mouse into content area, scroll down
        if scroll_pass > 0:
            ensure_wecom_foreground(f"结果页内滚动第{scroll_pass}次", main_hwnd)
            interception.move_to(content_cx, content_cy)
            time.sleep(0.15)
            interception.click(button="left")
            time.sleep(0.15)
            # Scroll down one viewport
            interception.scroll(clicks=-8)
            time.sleep(0.5)

            # Re-verify we're still on Smart Summary result page
            img_scroll = capture_rect(main_rect, os.path.join(screenshot_dir, f"stage5_scroll_{scroll_pass}.png"))
            save_ocr(os.path.join(screenshot_dir, f"stage5_scroll_{scroll_pass}.ocr.txt"), img_scroll, reader, min_conf=0.1)
            scroll_texts = " ".join(text for _bbox, text, _conf in ocr_all(img_scroll, reader, 0.1))
            if "智能总结" not in scroll_texts:
                print(f"企微采集阶段 5：滚动 {scroll_pass} 次后不再检测到智能总结页，停止滚动。")
                break

        # OCR search for "复制" / "拷贝"
        img_cur = capture_rect(main_rect, os.path.join(screenshot_dir, f"stage5_ocr_pass_{scroll_pass}.png"))
        save_ocr(os.path.join(screenshot_dir, f"stage5_ocr_pass_{scroll_pass}.ocr.txt"), img_cur, reader, min_conf=0.05)
        for bbox, text, conf in ocr_all(img_cur, reader, 0.05):
            cx = int((bbox[0][0] + bbox[2][0]) / 2)
            cy = int((bbox[0][1] + bbox[2][1]) / 2)
            if ("复制" in text or "拷贝" in text) and cy > height * 0.3:
                print(f"企微采集阶段 5：OCR 找到 '{text}' conf={conf:.2f} @ ({cx},{cy})，点击。")
                pyperclip.copy("")
                ensure_wecom_foreground("OCR 点击复制前", main_hwnd)
                interception.move_to(main_rect.left + cx, main_rect.top + cy)
                time.sleep(0.1)
                interception.click(button="left")
                time.sleep(0.6)
                result = pyperclip.paste()
                if result and len(result.strip()) >= 10:
                    return result.strip()

        # If text hasn't changed meaningfully, stop scrolling
        if scroll_pass > 1:
            prev_texts = ""
            try:
                prev_path = os.path.join(screenshot_dir, f"stage5_ocr_pass_{scroll_pass - 1}.ocr.txt")
                prev_texts = Path(prev_path).read_text(encoding="utf-8", errors="replace")
                cur_texts = Path(os.path.join(screenshot_dir, f"stage5_ocr_pass_{scroll_pass}.ocr.txt")).read_text(encoding="utf-8", errors="replace")
                if prev_texts == cur_texts:
                    print(f"企微采集阶段 5：滚动 {scroll_pass} 次后文本无变化，已到达内容底部。")
                    break
            except Exception:
                pass

    # All strategies exhausted
    print("企微采集失败：所有复制策略均失败，未找到可复制的智能总结结果。")
    print("建议操作：手动在企业微信智能总结结果页点击复制按钮，然后使用 --manual-input 提供内容。")
    print(f"诊断截图/OCR 已保存：{screenshot_dir}")
    sys.exit(1)


def run_automation(args: argparse.Namespace) -> str:
    require_windows()
    check_automation_dependencies()

    import easyocr
    import interception

    screenshot_dir = args.screenshot_dir or "outputs/wecom_screenshots"
    prompt = load_prompt(args)

    print("企微采集：初始化 Interception 设备。")
    interception.auto_capture_devices()
    print("企微采集：初始化 OCR，首次加载可能需要几十秒。")
    reader = easyocr.Reader(["ch_sim", "en"])

    # State 1: Find WeCom window — not found is terminal
    main_hwnd, main_rect, child_hwnd, child_rect = find_smart_summary()
    if main_hwnd is None:
        main_hwnd, main_rect = find_best_wecom_window()
    if main_hwnd is None or main_rect is None:
        print("企微采集失败：未找到企业微信窗口。")
        sys.exit(1)

    # State 2: Ensure WeCom foreground — retry before giving up
    ensure_wecom_foreground("自动化启动", main_hwnd)

    # State 3: Classify the visible page. Child window existence is NOT proof.
    img_verify = capture_rect(main_rect, os.path.join(screenshot_dir, "stage2_verify_page.png"))
    save_ocr(os.path.join(screenshot_dir, "stage2_verify_page.ocr.txt"), img_verify, reader)
    page_state = classify_smart_summary_page(img_verify, reader)
    print(f"企微采集：当前页面状态 {page_state}。")

    # State 4: Recover toward a verified Smart Summary input page.
    if page_state == "smart_summary_unknown_page":
        print("企微采集失败：初始页面为未知智能总结页，已停止。")
        print(f"诊断截图/OCR 已保存：{screenshot_dir}")
        sys.exit(1)
    elif page_state == "smart_summary_history_result_page":
        print("企微采集：初始页面为历史结果页，尝试点击 + 新建以进入输入页。")
        _try_click_plus_loose(main_hwnd, main_rect, reader, screenshot_dir)
        main_hwnd, main_rect, child_hwnd, child_rect = find_smart_summary()
        if main_hwnd is None:
            main_hwnd, main_rect = find_best_wecom_window()
        if main_hwnd is None or main_rect is None:
            print("企微采集失败：+ 新建后未找到企业微信窗口。")
            sys.exit(1)
        ensure_wecom_foreground("+ 新建恢复后", main_hwnd)
        img_after_plus = capture_rect(main_rect, os.path.join(screenshot_dir, "stage1_after_entry_verify.png"))
        save_ocr(os.path.join(screenshot_dir, "stage1_after_entry_verify.ocr.txt"), img_after_plus, reader)
        page_state = classify_smart_summary_page(img_after_plus, reader)
        print(f"企微采集：+ 新建后页面状态 {page_state}。")
        if page_state == "smart_summary_history_result_page":
            click_new_summary_plus(main_hwnd, main_rect, reader, screenshot_dir)
            main_hwnd, main_rect, child_hwnd, child_rect = find_smart_summary()
        elif page_state != "smart_summary_input_page":
            print("企微采集：+ 未达到输入页，尝试入口扫描。")
            click_smart_summary_entry(main_hwnd, main_rect, reader, screenshot_dir)
            main_hwnd, main_rect, child_hwnd, child_rect = find_smart_summary()
    elif page_state != "smart_summary_input_page":
        print("企微采集：当前不是智能总结页，尝试打开智能总结入口。")
        click_smart_summary_entry(main_hwnd, main_rect, reader, screenshot_dir)
        main_hwnd, main_rect, child_hwnd, child_rect = find_smart_summary()
        if main_hwnd is None:
            main_hwnd, main_rect = find_best_wecom_window()
        if main_hwnd is None or main_rect is None:
            print("企微采集失败：打开智能总结入口后未找到企业微信窗口。")
            sys.exit(1)
        ensure_wecom_foreground("打开智能总结入口后", main_hwnd)
        img_after_entry = capture_rect(main_rect, os.path.join(screenshot_dir, "stage1_after_entry_verify.png"))
        save_ocr(os.path.join(screenshot_dir, "stage1_after_entry_verify.ocr.txt"), img_after_entry, reader)
        page_state = classify_smart_summary_page(img_after_entry, reader)
        print(f"企微采集：打开入口后页面状态 {page_state}。")
        if page_state == "smart_summary_unknown_page":
            print("企微采集失败：打开入口后页面为未知智能总结页，已停止。")
            print(f"诊断截图/OCR 已保存：{screenshot_dir}")
            sys.exit(1)
        elif page_state == "smart_summary_history_result_page":
            _try_click_plus_loose(main_hwnd, main_rect, reader, screenshot_dir)
            main_hwnd, main_rect, child_hwnd, child_rect = find_smart_summary()

    if main_hwnd is None or main_rect is None:
        print("企微采集失败：未找到企业微信窗口。")
        print(f"诊断截图/OCR 已保存：{screenshot_dir}")
        sys.exit(1)

    if child_hwnd is None or child_rect is None:
        img_child_fallback = capture_rect(main_rect, os.path.join(screenshot_dir, "stage2_child_fallback_verify.png"))
        save_ocr(os.path.join(screenshot_dir, "stage2_child_fallback_verify.ocr.txt"), img_child_fallback, reader)
        if classify_smart_summary_page(img_child_fallback, reader) == "smart_summary_input_page":
            print("企微采集：未取得智能总结子窗口句柄，但页面已验证为输入页，使用主窗口区域继续。")
            child_hwnd = main_hwnd
            child_rect = main_rect
        else:
            print("企微采集失败：未找到智能总结界面。")
            print(f"诊断截图/OCR 已保存：{screenshot_dir}")
            sys.exit(1)

    if child_rect is None:
        print("企微采集失败：未找到智能总结界面。")
        print(f"诊断截图/OCR 已保存：{screenshot_dir}")
        sys.exit(1)

    print(
        "企微采集：找到智能总结窗口 "
        f"main=0x{main_hwnd:x} ({main_rect.right-main_rect.left}x{main_rect.bottom-main_rect.top}), "
        f"child=0x{child_hwnd:x}."
    )

    # State 5: Final page verification before dangerous actions (non-negotiable)
    ensure_wecom_foreground("粘贴提示词前", main_hwnd)
    img_final = capture_rect(main_rect, os.path.join(screenshot_dir, "stage2_verify_page.png"))
    save_ocr(os.path.join(screenshot_dir, "stage2_verify_page.ocr.txt"), img_final, reader)
    final_state = classify_smart_summary_page(img_final, reader)
    if final_state == "smart_summary_history_result_page":
        print("企微采集失败：当前仍是智能总结历史结果页，拒绝粘贴提示词或复制旧结果。")
        print(f"诊断截图/OCR 已保存：{screenshot_dir}")
        sys.exit(1)
    if final_state != "smart_summary_input_page":
        print("企微采集失败：多次尝试后仍无法进入智能总结输入页。")
        print("已停止，避免把提示词输入到错误界面。")
        print(f"诊断截图/OCR 已保存：{screenshot_dir}")
        sys.exit(1)

    # State 6: Paste → click start → wait → copy (all have internal safety checks)
    paste_prompt(main_hwnd, main_rect, child_rect, prompt)
    img_after_paste = capture_rect(main_rect, os.path.join(screenshot_dir, "stage2_after_paste.png"))
    save_ocr(os.path.join(screenshot_dir, "stage2_after_paste.ocr.txt"), img_after_paste, reader)
    max_wait = args.max_wait_seconds if args.max_wait_seconds != 180 or args.timeout == 120 else args.timeout
    wait_state = click_start_and_wait(main_hwnd, main_rect, reader, screenshot_dir, max_wait, args.stable_seconds, args.poll_interval)
    if wait_state not in ("result_detected", "copy_available"):
        print(f"企微采集失败：等待结束后状态为 {wait_state}，无法安全复制。")
        print(f"诊断截图/OCR 已保存：{screenshot_dir}")
        sys.exit(1)
    return copy_result(main_hwnd, main_rect, child_rect, reader, screenshot_dir, wait_state)


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect Enterprise WeChat Smart Summary evidence on Windows.")
    parser.add_argument("--scenario", default="weekly-summary", help="Report scenario tag.")
    parser.add_argument("--period", default="", help="Report period, e.g. '2026-06-22..2026-06-26'.")
    parser.add_argument("--prompt-file", help="Read smart summary prompt from file instead of default.")
    parser.add_argument("--output", help="Output Markdown file path.")
    parser.add_argument("--output-json", help="Output JSON file path.")
    parser.add_argument("--manual-input", action="store_true", help="Manual mode: read from stdin or clipboard.")
    parser.add_argument("--from-clipboard", action="store_true", help="With --manual-input: read text from clipboard.")
    parser.add_argument("--debug", action="store_true", help="Accepted for compatibility; staged screenshots are always saved.")
    parser.add_argument("--screenshot-dir", default="outputs/wecom_screenshots", help="Directory for staged screenshots/OCR.")
    parser.add_argument("--max-wait-seconds", type=int, default=180, help="Hard upper limit for summary generation wait.")
    parser.add_argument("--stable-seconds", type=int, default=15, help="Seconds of stable result text before attempting copy.")
    parser.add_argument("--timeout", type=int, default=120, help="Deprecated. Use --max-wait-seconds instead.")
    parser.add_argument("--poll-interval", type=int, default=3, help="Seconds between OCR poll checks.")
    args = parser.parse_args()

    if args.manual_input:
        raw_summary = read_manual_input(args)
        collection_method = "manual_input"
    else:
        raw_summary = run_automation(args)
        collection_method = "desktop_automation"

    if args.output:
        write_markdown(args.output, args.scenario, args.period, collection_method, raw_summary)
        print(f"Markdown saved: {args.output}")
    else:
        print(raw_summary)

    if args.output_json:
        write_json(args.output_json, args.scenario, args.period, collection_method, raw_summary)
        print(f"JSON saved: {args.output_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
