#!/usr/bin/env python
"""Collect Enterprise WeChat Smart Summary evidence on Windows.

Supervised full-auto visual state machine with:
- Window normalization
- Region-based OCR
- OpenCV template matching
- Interception driver input
- Current-run fingerprint verification
- Trace diagnostics (outputs/wecom_runs/<run-id>/)

Fallback: --semi-manual, --prompt-only, --manual-input.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import random
import shutil
import sys
import atexit
import time
from ctypes import wintypes
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PROMPT_BODY = (
    "聊天中做了哪些事情，哪些人、哪些群找到我，"
    "按真实工作对话逐条梳理。"
    "每条尽量包含：时间或顺序、来源人/来源群、对方诉求或上下文、"
    "我做了什么、我产出的工作内容/结论/交付物、"
    "是否适合写入周报或报告素材。"
    "只列真实发生的工作事项，不编造；"
    "不把闲聊、通知或无明确产出的对话写成工作成果；"
    "无法判断的字段标注「不明确」。"
)

GLOBAL_BUDGET_SECONDS_DEFAULT = 300

MAX_RECOVERY_CYCLES = 8
CYCLE_MAX_REPEATS = 3

# Region model as fractions of window (left, top, right, bottom)
REGION_FRACTIONS: dict[str, tuple[float, float, float, float]] = {
    "app_sidebar":             (0.00, 0.00, 0.17, 1.00),
    "summary_sidebar_header":  (0.00, 0.00, 0.17, 0.10),
    "summary_history_list":    (0.00, 0.10, 0.17, 0.92),
    "main_header":             (0.17, 0.00, 1.00, 0.10),
    "main_body":               (0.17, 0.10, 0.98, 0.85),
    "bottom_action_bar":       (0.17, 0.85, 1.00, 1.00),
    "right_scrollbar":         (0.98, 0.00, 1.00, 1.00),
}

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "assets" / "wecom"

# Non-WeCom content patterns — if OCR detects these, the capture is likely from
# Codex / terminal / editor, not from Enterprise WeChat.
NON_WECOM_KEYWORDS = [
    "AGENTS.md", "docs/status.md", "Claude执行完毕", "你可以验收",
    "collect_wecom_smart_summary.py", "--probe-only", "--semi-manual",
    "def run_probe_only", "def classify_page", "import argparse",
]

# Ordinary chat page indicators — if multiple of these appear in main_body,
# the current page is a normal chat/group page, NOT a smart summary page.
MAIN_PAGE_STRONG_INDICATORS = [
    "群公告", "群成员", "快速会议", "@所有人", "发送消息", "聊天记录",
    "条消息", "你撤回了",
]
MAIN_PAGE_WEAK_INDICATORS = [
    "智能表格", "群应用", "群设置", "语音通话", "视频通话", "群聊",
    "文件", "相册", "消息免打扰", "星期",
]

# Suggestion card texts that must NOT be treated as the "开始总结" button.
# OCR may read "进展" as "迸展" and "内容" as "内穸".
START_BUTTON_BLOCKLIST = [
    "总结团队周报", "汇总项目进展", "汇总项目迸展",
    "跟踪任务进度", "总结聊天内容", "总结聊天内穸",
]

# Input-page indicators that suggest generation was never triggered.
# If these persist after clicking "start", the click likely hit a suggestion card
# or missed the button entirely.
INPUT_PAGE_PERSISTENT_INDICATORS = [
    "开始总结", "你想总结的主题", "添加成员",
    "总结团队周报", "汇总项目迸展", "跟踪任务进度", "总结聊天内穸",
]

# ---------------------------------------------------------------------------
# Fingerprint & Run ID
# ---------------------------------------------------------------------------


def generate_fingerprint() -> str:
    """Generate a per-run fingerprint with OCR-friendly all-digit suffix.

    Suffix uses only digits 0-9 to avoid EasyOCR/Chinese-OCR character confusion
    (e.g. Z→队, R→, K→).
    """
    now = datetime.now()
    rand = "".join(random.choices("0123456789", k=4))
    return f"PRAS-{now.strftime('%Y%m%d-%H%M%S')}-{rand}"


def make_fingerprint_instruction(fingerprint: str) -> str:
    return f"请在总结结果第一行原样保留采集标识：{fingerprint}"


def generate_run_id() -> str:
    now = datetime.now()
    rand = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=4))
    return f"{now.strftime('%Y%m%d-%H%M%S')}-{rand}"


# ---------------------------------------------------------------------------
# Trace Logger
# ---------------------------------------------------------------------------


class TraceLogger:
    """Writes structured trace entries as JSONL."""

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        self.path = run_dir / "trace.jsonl"
        self._entries: list[dict[str, Any]] = []

    def log(self, **kwargs: Any) -> None:
        entry: dict[str, Any] = {"timestamp": datetime.now(timezone.utc).isoformat()}
        entry.update(kwargs)
        self._entries.append(entry)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            "\n".join(json.dumps(e, ensure_ascii=False) for e in self._entries) + "\n",
            encoding="utf-8", errors="replace",
        )

    def stage_screenshot(self, stage_name: str) -> Path:
        p = self.run_dir / f"{stage_name}.png"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def region_screenshot(self, stage_name: str, region_name: str) -> Path:
        p = self.run_dir / "regions" / f"{stage_name}-{region_name}.png"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def ocr_path(self, stage_name: str) -> Path:
        p = self.run_dir / "ocr" / f"{stage_name}.txt"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p


# ---------------------------------------------------------------------------
# Window Utilities (Win32)
# ---------------------------------------------------------------------------

user32 = ctypes.WinDLL("user32", use_last_error=True) if sys.platform == "win32" else None
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True) if sys.platform == "win32" else None

SW_RESTORE = 9
SW_SHOW = 5
SW_MAXIMIZE = 3
GA_ROOT = 2
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_SHOWWINDOW = 0x0040

# SetThreadExecutionState flags for keep-awake guard
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002


def _window_class(hwnd: int) -> str:
    if not hwnd or user32 is None:
        return ""
    cn = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, cn, 256)
    return cn.value


def _window_title(hwnd: int) -> str:
    if not hwnd or user32 is None:
        return ""
    t = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, t, 256)
    return t.value


def _window_rect(hwnd: int) -> wintypes.RECT:
    r = wintypes.RECT()
    if user32 is not None:
        user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r


def _root_window(hwnd: int) -> int:
    if not hwnd or user32 is None:
        return 0
    root = user32.GetAncestor(hwnd, GA_ROOT)
    return root or hwnd


def _enum_wecom_windows() -> list:
    if user32 is None:
        return []
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    results: list = []

    def _cb(hwnd: int, _lp: int) -> bool:
        if _window_class(hwnd) != "WeWorkWindow":
            return True
        rect = _window_rect(hwnd)
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        if width <= 0 or height <= 0:
            return True
        children: list = []

        def _ecb(ch: int, _lp2: int) -> bool:
            cr = _window_rect(ch)
            sz = (cr.right - cr.left, cr.bottom - cr.top)
            if sz[0] > 0 and sz[1] > 0:
                children.append((ch, _window_class(ch), _window_title(ch), cr, sz))
            return True

        user32.EnumChildWindows(hwnd, WNDENUMPROC(_ecb), 0)
        results.append((hwnd, rect, _window_title(hwnd), children))
        return True

    user32.EnumWindows(WNDENUMPROC(_cb), 0)
    return results


def find_best_wecom_window() -> tuple[int | None, wintypes.RECT | None, list | None]:
    windows = _enum_wecom_windows()
    if not windows:
        return None, None, None
    windows.sort(
        key=lambda item: (
            any("智能总结" in c[1] or "智能总结" in c[2] for c in item[3]),
            user32.IsWindowVisible(item[0]) if user32 else False,
            (item[1].right - item[1].left) * (item[1].bottom - item[1].top),
        ),
        reverse=True,
    )
    best = windows[0]
    return best[0], best[1], best[3]


def find_smart_summary_child(
    children: list | None = None,
) -> tuple[int | None, wintypes.RECT | None]:
    if children is None:
        _, _, children = find_best_wecom_window()
    if children:
        for ch, cn, title, cr, _sz in children:
            if "智能总结" in cn or "智能总结" in title:
                return ch, cr
    return None, None


def find_smart_summary_full() -> tuple[int | None, wintypes.RECT | None, int | None, wintypes.RECT | None]:
    for hwnd, rect, _title, children in _enum_wecom_windows():
        for ch, cn, title, cr, _sz in children:
            if "智能总结" in cn or "智能总结" in title:
                return hwnd, rect, ch, cr
    return None, None, None, None


def _foreground_is_wecom(target_hwnd: int) -> bool:
    if user32 is None:
        return False
    fg = user32.GetForegroundWindow()
    return _root_window(fg) == _root_window(target_hwnd) or _window_class(_root_window(fg)) == "WeWorkWindow"


def _foreground_snapshot() -> dict[str, Any]:
    """Return current foreground window info for trace."""
    if user32 is None:
        return {"hwnd": "0", "class": "", "title": ""}
    fg = user32.GetForegroundWindow()
    return {
        "hwnd": f"0x{fg:x}" if fg else "0",
        "class": _window_class(fg),
        "title": _window_title(fg)[:120],
    }


def _verify_foreground_or_fail(target_hwnd: int, target_class: str, stage: str, trace: TraceLogger) -> None:
    """Verify target window is still foreground. Calls sys.exit(1) on failure."""
    if _foreground_is_wecom(target_hwnd):
        return
    fg_snap = _foreground_snapshot()
    trace.log(event="foreground_lost", stage=stage, target_hwnd=f"0x{target_hwnd:x}",
              target_class=target_class, **fg_snap)
    print(f"\n企微安全失败 [{stage}]：采集期间前台窗口发生变化。")
    print(f"  目标窗口：class=WeWorkWindow hwnd=0x{target_hwnd:x}")
    print(f"  当前前台：class={fg_snap['class']} title={fg_snap['title'][:80]}")
    print("屏幕截图可能已被其他窗口遮挡，拒绝继续分类或操作。")
    print("请重试，采集期间不要操作鼠标键盘。若需接管请等待本轮结束或按 Ctrl+C 中断。")
    sys.exit(1)


def ensure_wecom_foreground(main_hwnd: int, max_attempts: int = 4) -> bool:
    if _foreground_is_wecom(main_hwnd):
        return True

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
            return True

        fg = user32.GetForegroundWindow()
        fg_thread = user32.GetWindowThreadProcessId(fg, None)
        target_thread = user32.GetWindowThreadProcessId(main_hwnd, None)
        our_thread = kernel32.GetCurrentThreadId()
        attached: list[int] = []
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
            return True

        user32.SetWindowPos(main_hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
        time.sleep(0.15)
        user32.SetForegroundWindow(main_hwnd)
        user32.BringWindowToTop(main_hwnd)
        time.sleep(0.15)
        user32.SetWindowPos(main_hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
        time.sleep(0.2)
        if _foreground_is_wecom(main_hwnd):
            return True

        if attempt == max_attempts:
            try:
                import interception
                rect = _window_rect(main_hwnd)
                interception.move_to(rect.left + 200, rect.top + 10)
                time.sleep(0.1)
                interception.click(button="left")
                time.sleep(0.4)
                if _foreground_is_wecom(main_hwnd):
                    return True
            except Exception:
                pass

    fg = user32.GetForegroundWindow()
    print(f"企微采集：多次尝试后仍无法将企业微信置于前台。")
    print(f"当前前台窗口：class={_window_class(fg)}, title={_window_title(fg)[:80]}")
    return False


def normalize_window(main_hwnd: int) -> wintypes.RECT | None:
    if not ensure_wecom_foreground(main_hwnd):
        print("企微采集：无法置前企业微信窗口，跳过归一化。")
        return None

    if user32.IsIconic(main_hwnd):
        user32.ShowWindow(main_hwnd, SW_RESTORE)
        time.sleep(0.3)

    user32.ShowWindow(main_hwnd, SW_MAXIMIZE)
    time.sleep(0.5)

    new_rect = _window_rect(main_hwnd)
    width = new_rect.right - new_rect.left
    height = new_rect.bottom - new_rect.top
    print(f"企微采集：窗口归一化完成，尺寸 {width}x{height}。")
    return new_rect


# ---------------------------------------------------------------------------
# Region Model
# ---------------------------------------------------------------------------


def compute_regions(window_rect: wintypes.RECT) -> dict[str, tuple[int, int, int, int]]:
    left = window_rect.left
    top = window_rect.top
    w = window_rect.right - window_rect.left
    h = window_rect.bottom - window_rect.top
    regions: dict[str, tuple[int, int, int, int]] = {}
    for name, (fx1, fy1, fx2, fy2) in REGION_FRACTIONS.items():
        regions[name] = (
            left + int(w * fx1),
            top + int(h * fy1),
            left + int(w * fx2),
            top + int(h * fy2),
        )
    return regions


# ---------------------------------------------------------------------------
# Trusted Capture (single grab → crop regions)
# ---------------------------------------------------------------------------


@dataclass
class CapturedFrame:
    """A single trusted screen capture with region crops derived from the same image."""
    full_image: object  # PIL Image
    window_rect: wintypes.RECT
    regions: dict[str, object] = field(default_factory=dict)  # region_name -> PIL crop
    captured_at: float = 0.0
    target_hwnd: int = 0
    fg_snapshot: dict[str, Any] = field(default_factory=dict)


def capture_trusted_frame(
    target_hwnd: int,
    window_rect: wintypes.RECT,
    trace: TraceLogger,
    stage: str,
    region_names: list[str] | None = None,
) -> CapturedFrame:
    """Capture ONE full-window screenshot after verifying foreground, then crop regions from it.

    Verifies foreground before AND after the grab.  If foreground changes mid-capture,
    this is treated as a safety failure (sys.exit(1)).
    """
    from PIL import ImageGrab

    if region_names is None:
        region_names = ["app_sidebar", "main_header", "main_body",
                        "bottom_action_bar", "summary_history_list"]

    # 1. Verify foreground BEFORE capture
    fg_before = _foreground_snapshot()
    trace.log(event="capture_foreground_check", stage=stage, phase="before", target_hwnd=f"0x{target_hwnd:x}", **fg_before)
    _verify_foreground_or_fail(target_hwnd, "WeWorkWindow", stage, trace)

    # 2. SINGLE screen grab — this is the only ImageGrab.grab call
    captured_at = time.time()
    bbox = (window_rect.left, window_rect.top, window_rect.right, window_rect.bottom)
    full_img = ImageGrab.grab(bbox=bbox, all_screens=True)

    # 3. Verify foreground AFTER capture (detect mid-capture foreground switch)
    fg_after = _foreground_snapshot()
    trace.log(event="capture_foreground_check", stage=stage, phase="after", target_hwnd=f"0x{target_hwnd:x}", **fg_after)
    if not _foreground_is_wecom(target_hwnd):
        # Save the (possibly tainted) screenshot for diagnostics, then fail
        diag_path = trace.stage_screenshot(f"{stage}-tainted")
        full_img.save(str(diag_path))
        print(f"企微安全失败 [{stage}]：截图后发现前台窗口已变化。")
        print(f"  截图可能已被其它窗口遮挡，已保存至 {diag_path} 供诊断。")
        print(f"  当前前台：class={fg_after['class']} title={fg_after['title'][:80]}")
        trace.log(event="capture_tainted", stage=stage, screenshot=str(diag_path))
        sys.exit(1)

    # 4. Crop regions from the SAME image (no additional screen grabs)
    w = window_rect.right - window_rect.left
    h = window_rect.bottom - window_rect.top
    regions: dict[str, object] = {}
    for rname in region_names:
        if rname not in REGION_FRACTIONS:
            continue
        fx1, fy1, fx2, fy2 = REGION_FRACTIONS[rname]
        rx1 = int(w * fx1)
        ry1 = int(h * fy1)
        rx2 = int(w * fx2)
        ry2 = int(h * fy2)
        regions[rname] = full_img.crop((rx1, ry1, rx2, ry2))

    return CapturedFrame(
        full_image=full_img,
        window_rect=window_rect,
        regions=regions,
        captured_at=captured_at,
        target_hwnd=target_hwnd,
        fg_snapshot=fg_before,
    )


def save_frame_artifacts(frame: CapturedFrame, trace: TraceLogger, stage: str) -> None:
    """Save full screenshot, region crops, and OCR text from a CapturedFrame."""
    from PIL import Image

    # Full screenshot
    full_path = trace.stage_screenshot(stage)
    frame.full_image.save(str(full_path))

    # Region crops
    for rname, crop in frame.regions.items():
        rpath = trace.region_screenshot(stage, rname)
        if isinstance(crop, Image.Image):
            crop.save(str(rpath))


# ---------------------------------------------------------------------------
# Screenshot Utilities (for automation actions that need one-off captures)
# ---------------------------------------------------------------------------


def capture_rect(rect: wintypes.RECT, path: str | Path) -> object:
    from PIL import ImageGrab

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    img = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom), all_screens=True)
    img.save(str(path))
    return img


def capture_rect_safe(
    rect: wintypes.RECT, path: str | Path,
    target_hwnd: int, trace: TraceLogger, stage: str,
) -> object:
    """capture_rect with foreground verification before and after."""
    _verify_foreground_or_fail(target_hwnd, "WeWorkWindow", stage, trace)
    img = capture_rect(rect, path)
    _verify_foreground_or_fail(target_hwnd, "WeWorkWindow", f"{stage}_post", trace)
    return img


def capture_region_from_frame(
    frame: CapturedFrame, region_name: str, path: str | Path,
) -> object:
    """Save a region crop from an existing CapturedFrame (no new screen grab)."""
    if region_name in frame.regions:
        crop = frame.regions[region_name]
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        crop.save(str(path))
        return crop
    raise KeyError(f"Region '{region_name}' not in CapturedFrame")


# ---------------------------------------------------------------------------
# OCR Utilities
# ---------------------------------------------------------------------------

_ocr_text_cache: dict[str, str] = {}


def _image_hash(img: object) -> str:
    import numpy as np
    arr = np.array(img)
    return hashlib.md5(arr.tobytes()).hexdigest()


def ocr_all(img: object, reader: object, min_conf: float = 0.3) -> list[tuple]:
    import numpy as np
    results = reader.readtext(np.array(img))
    return [(bbox, text, conf) for bbox, text, conf in results if conf >= min_conf]


def ocr_texts(img: object, reader: object, min_conf: float = 0.2) -> list[str]:
    return [text for _bbox, text, _conf in ocr_all(img, reader, min_conf)]


def ocr_texts_cached(img: object, reader: object, min_conf: float = 0.2) -> list[str]:
    key = _image_hash(img)
    cached = _ocr_text_cache.get(key)
    if cached is not None:
        return cached.split("\x00")
    texts = ocr_texts(img, reader, min_conf)
    _ocr_text_cache[key] = "\x00".join(texts)
    if len(_ocr_text_cache) > 32:
        oldest = next(iter(_ocr_text_cache))
        del _ocr_text_cache[oldest]
    return texts


def clear_ocr_cache() -> None:
    _ocr_text_cache.clear()


def ocr_joined(img: object, reader: object, min_conf: float = 0.2) -> str:
    return " ".join(ocr_texts(img, reader, min_conf))


def save_ocr(path: str | Path, img: object, reader: object, min_conf: float = 0.1) -> None:
    lines = []
    for bbox, text, conf in ocr_all(img, reader, min_conf):
        cx = int((bbox[0][0] + bbox[2][0]) / 2)
        cy = int((bbox[0][1] + bbox[2][1]) / 2)
        lines.append(f"[{conf:.2f}] '{text}' @ ({cx},{cy})")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8", errors="replace")


def _save_ocr_lines(
    path: str | Path, results: list[tuple], tag: str,
) -> None:
    """Write pre-computed OCR results to a diagnostic file (avoids re-running OCR)."""
    lines: list[str] = []
    for bbox, text, conf in results:
        cx = int((bbox[0][0] + bbox[2][0]) / 2)
        cy = int((bbox[0][1] + bbox[2][1]) / 2)
        lines.append(f"[{tag} {conf:.2f}] '{text}' @ ({cx},{cy})")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8", errors="replace")


def ocr_find(img: object, target: str, reader: object) -> tuple[int | None, int | None, float | None, str | None]:
    for bbox, text, conf in ocr_all(img, reader, 0.2):
        if target in text:
            cx = int((bbox[0][0] + bbox[2][0]) / 2)
            cy = int((bbox[0][1] + bbox[2][1]) / 2)
            return cx, cy, conf, text
    return None, None, None, None


def _ocr_contains_non_wecom(texts_joined: str) -> bool:
    """Check if OCR text contains patterns that clearly indicate non-WeCom content."""
    return any(kw in texts_joined for kw in NON_WECOM_KEYWORDS)


# ---------------------------------------------------------------------------
# Multi-Engine OCR Adapter (RapidOCR primary → EasyOCR fallback)
# ---------------------------------------------------------------------------

_rapid_ocr_engine: object | None = None
_rapid_ocr_load_attempted: bool = False


def _get_rapid_ocr() -> object | None:
    """Lazy-load RapidOCR engine. Returns None if unavailable."""
    global _rapid_ocr_engine, _rapid_ocr_load_attempted
    if _rapid_ocr_load_attempted:
        return _rapid_ocr_engine
    _rapid_ocr_load_attempted = True
    try:
        from rapidocr_onnxruntime import RapidOCR
        _rapid_ocr_engine = RapidOCR()
        return _rapid_ocr_engine
    except ImportError:
        return None


def _rapid_ocr_texts(img: object, min_conf: float = 0.2) -> list[str]:
    """Run RapidOCR on an image and return text lines."""
    import numpy as np
    engine = _get_rapid_ocr()
    if engine is None:
        return []
    arr = np.array(img)
    if len(arr.shape) == 3 and arr.shape[2] == 4:
        arr = arr[:, :, :3]
    result, _ = engine(arr)
    if result is None:
        return []
    texts: list[str] = []
    for _box, text, conf in result:
        try:
            c = float(conf)
        except (TypeError, ValueError):
            c = 0.5
        if c >= min_conf:
            texts.append(str(text))
    return texts


def _rapid_ocr_all(img: object, min_conf: float = 0.2) -> list[tuple]:
    """Run RapidOCR and return (bbox, text, conf) tuples in EasyOCR-compatible format."""
    import numpy as np
    engine = _get_rapid_ocr()
    if engine is None:
        return []
    arr = np.array(img)
    if len(arr.shape) == 3 and arr.shape[2] == 4:
        arr = arr[:, :, :3]
    result, _ = engine(arr)
    if result is None:
        return []
    out: list[tuple] = []
    for box, text, conf in result:
        try:
            c = float(conf)
        except (TypeError, ValueError):
            c = 0.5
        if c >= min_conf:
            # RapidOCR box format: [[x1,y1],[x2,y1],[x2,y2],[x1,y2]] → EasyOCR format
            bbox = [[int(box[0][0]), int(box[0][1])],
                    [int(box[1][0]), int(box[1][1])],
                    [int(box[2][0]), int(box[2][1])],
                    [int(box[3][0]), int(box[3][1])]]
            out.append((bbox, str(text), c))
    return out


def ocr_texts_multi(img: object, easyocr_reader: object, min_conf: float = 0.2,
                    fingerprint: str = "") -> list[str]:
    """OCR using RapidOCR (primary) merged with EasyOCR (supplemental).

    RapidOCR results come first, followed by EasyOCR results that are not already
    present in the RapidOCR output.  This gives RapidOCR precedence for fingerprint
    recognition while EasyOCR fills in any gaps.

    If *fingerprint* is provided and appears in RapidOCR output, EasyOCR is skipped
    entirely — RapidOCR is known to be more accurate for Latin alphanumeric patterns.
    """
    rapid_texts = _rapid_ocr_texts(img, min_conf)
    # Skip EasyOCR when RapidOCR already confirmed the exact fingerprint
    if fingerprint and fingerprint in " ".join(rapid_texts):
        return rapid_texts
    easy_texts = ocr_texts(img, easyocr_reader, min_conf)
    # Merge: RapidOCR first, then EasyOCR texts not already covered
    rapid_set = set(rapid_texts)
    merged = list(rapid_texts)
    for t in easy_texts:
        if t not in rapid_set:
            merged.append(t)
    return merged


def ocr_all_multi(img: object, easyocr_reader: object, min_conf: float = 0.2) -> list[tuple]:
    """Multi-engine OCR returning unified (bbox, text, conf) results.

    RapidOCR results come first, then EasyOCR results not already present.
    """
    rapid_results = _rapid_ocr_all(img, min_conf)
    easy_results = ocr_all(img, easyocr_reader, min_conf)
    rapid_texts = {text for _bbox, text, _conf in rapid_results}
    merged = list(rapid_results)
    for bbox, text, conf in easy_results:
        if text not in rapid_texts:
            merged.append((bbox, text, conf))
    return merged


def save_ocr_multi(
    path: str | Path, img: object, easyocr_reader: object, min_conf: float = 0.1,
) -> None:
    """Save OCR output with per-engine labelling for diagnostics."""
    lines: list[str] = []
    # RapidOCR
    rapid_results = _rapid_ocr_all(img, min_conf)
    for bbox, text, conf in rapid_results:
        cx = int((bbox[0][0] + bbox[2][0]) / 2)
        cy = int((bbox[0][1] + bbox[2][1]) / 2)
        lines.append(f"[R {conf:.2f}] '{text}' @ ({cx},{cy})")
    # EasyOCR
    for bbox, text, conf in ocr_all(img, easyocr_reader, min_conf):
        cx = int((bbox[0][0] + bbox[2][0]) / 2)
        cy = int((bbox[0][1] + bbox[2][1]) / 2)
        lines.append(f"[E {conf:.2f}] '{text}' @ ({cx},{cy})")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8", errors="replace")


def _ocr_region_once(
    crop: object, rname: str, reader: object, trace: TraceLogger, stage: str,
    fingerprint: str = "",
) -> list[str]:
    """Single-pass OCR for a region: save diagnostics AND return texts.

    For main_body, uses multi-engine (RapidOCR + EasyOCR).  For other regions,
    uses EasyOCR only.  This avoids the previous double-OCR pattern where
    ocr_texts_multi/ocr_texts and save_ocr_multi/save_ocr each ran OCR separately.

    If *fingerprint* is provided and RapidOCR finds it in main_body, EasyOCR is
    skipped — RapidOCR is more accurate for Latin alphanumeric patterns.
    """
    path = trace.ocr_path(f"{stage}-{rname}")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    texts: list[str] = []

    if rname == "main_body":
        rapid = _rapid_ocr_all(crop, 0.15)
        for bbox, text, conf in rapid:
            cx = int((bbox[0][0] + bbox[2][0]) / 2)
            cy = int((bbox[0][1] + bbox[2][1]) / 2)
            lines.append(f"[R {conf:.2f}] '{text}' @ ({cx},{cy})")
            texts.append(text)
        rapid_joined = " ".join(texts)
        if fingerprint and fingerprint in rapid_joined:
            # RapidOCR confirmed the fingerprint — skip EasyOCR
            pass
        else:
            easy = ocr_all(crop, reader, 0.15)
            rapid_set = set(texts)
            for bbox, text, conf in easy:
                cx = int((bbox[0][0] + bbox[2][0]) / 2)
                cy = int((bbox[0][1] + bbox[2][1]) / 2)
                lines.append(f"[E {conf:.2f}] '{text}' @ ({cx},{cy})")
                if text not in rapid_set:
                    texts.append(text)
    else:
        for bbox, text, conf in ocr_all(crop, reader, 0.15):
            cx = int((bbox[0][0] + bbox[2][0]) / 2)
            cy = int((bbox[0][1] + bbox[2][1]) / 2)
            lines.append(f"[E {conf:.2f}] '{text}' @ ({cx},{cy})")
            texts.append(text)

    Path(path).write_text("\n".join(lines), encoding="utf-8", errors="replace")
    return texts


# ---------------------------------------------------------------------------
# Template Matching (OpenCV)
# ---------------------------------------------------------------------------


def _load_template(name: str) -> object | None:
    path = TEMPLATE_DIR / name
    if not path.exists():
        return None
    import cv2
    return cv2.imread(str(path))


def template_match(screenshot: object, template_name: str, threshold: float = 0.7) -> tuple[int | None, int | None, float]:
    template = _load_template(template_name)
    if template is None:
        return None, None, 0.0

    import cv2
    import numpy as np

    # Reject blank or near-blank templates: a template with effectively zero
    # variance (uniform color) matches everywhere and produces false positives.
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    t_std = float(np.std(template_gray))
    if t_std < 5.0:
        return None, None, 0.0

    screen_np = np.array(screenshot)
    if len(screen_np.shape) == 3 and screen_np.shape[2] == 4:
        screen_np = screen_np[:, :, :3]
    screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)

    result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val < threshold:
        return None, None, float(max_val)

    h, w = template_gray.shape
    cx = max_loc[0] + w // 2
    cy = max_loc[1] + h // 2
    return cx, cy, float(max_val)


def template_available(name: str) -> bool:
    return (TEMPLATE_DIR / name).exists()


# ---------------------------------------------------------------------------
# State Classification (History-First) — operates on a CapturedFrame
# ---------------------------------------------------------------------------


def classify_page_structured(
    frame: CapturedFrame,
    reader: object,
    trace: TraceLogger,
    stage: str,
    fingerprint: str = "",
) -> dict[str, Any]:
    """Classify the WeCom page from a trusted CapturedFrame (no internal screen captures)."""
    region_texts: dict[str, str] = {}
    region_ocr_results: dict[str, list[str]] = {}

    # OCR each region from the trusted frame — single pass per region.
    # main_body uses multi-engine (RapidOCR + EasyOCR); others use EasyOCR only.
    # Diagnostics are saved during the same OCR pass (no separate save call).
    for rname in ["app_sidebar", "main_header", "main_body", "bottom_action_bar", "summary_history_list"]:
        if rname in frame.regions:
            texts = _ocr_region_once(frame.regions[rname], rname, reader, trace, stage, fingerprint=fingerprint)
            region_texts[rname] = " ".join(texts)
            region_ocr_results[rname] = texts

    # Build all_text from region OCRs (no separate full-image OCR pass).

    # Cross-content sanity check: if OCR clearly shows non-WeCom content, refuse
    all_text = " ".join(region_texts.values())
    if _ocr_contains_non_wecom(all_text):
        trace.log(event="classification_rejected", stage=stage, reason="non_wecom_content_detected",
                  matched_keywords=[kw for kw in NON_WECOM_KEYWORDS if kw in all_text])
        return {
            "state": "summary_unknown_page",
            "confidence": 0.0,
            "signals": ["non_wecom_content_detected"],
            "missing": ["valid_wecom_content"],
            "region_evidence": {k: v[:120] for k, v in region_texts.items()},
            "in_smart_summary": False,
            "tainted": True,
        }

    # ---- MEMBER SELECTION DIALOG DETECTION ----
    # If a member selection dialog appeared (e.g. because _action_click_plus
    # accidentally clicked "添加成员"), stop ALL further actions immediately.
    _MEMBER_DIALOG_STRONG = ["选择成员", "从群聊中选择"]
    if any(kw in all_text for kw in _MEMBER_DIALOG_STRONG):
        matched = [kw for kw in _MEMBER_DIALOG_STRONG if kw in all_text]
        trace.log(event="classification_rejected", stage=stage, reason="member_selection_dialog_detected",
                  matched_keywords=matched)
        return {
            "state": "terminal_failure",
            "confidence": 1.0,
            "signals": ["member_selection_dialog_detected"] + matched,
            "missing": [],
            "region_evidence": {k: v[:120] for k, v in region_texts.items()},
            "in_smart_summary": True,
            "tainted": False,
        }

    # Check if we are in Smart Summary.
    # UIA / child-window "智能总结" is only a sidebar-entry hint — it does NOT
    # prove the current visible main content is a Smart Summary page.  Only OCR
    # evidence from the main content area can confirm we are inside Smart Summary.
    uia_smart_summary_entry = False
    child_smart_summary_entry = False

    # UIA check
    try:
        import uiautomation as auto
        root = auto.GetRootControl()
        for win in root.GetChildren():
            try:
                name = (win.Name or "")
                cls = (win.ClassName or "")
                if "智能总结" in name or "智能总结" in cls:
                    uia_smart_summary_entry = True
                    break
            except Exception:
                continue
    except Exception:
        pass

    # Fallback: check window children (hint only — does not set in_smart_summary)
    for _hwnd, _rect, _title, children in _enum_wecom_windows():
        for _ch, cn, title, _cr, _sz in children:
            if "智能总结" in cn or "智能总结" in title:
                child_smart_summary_entry = True
                break

    # OCR-based Smart Summary content-page check.
    # "智能总结" in app_sidebar alone is NOT sufficient — it's just the sidebar
    # navigation entry visible on any WeCom page.  Require it in main_header, or
    # in sidebar PLUS smart-summary-specific body/history-list signals.
    main_text = region_texts.get("main_header", "")
    sidebar_text = region_texts.get("app_sidebar", "")
    body_text_early = region_texts.get("main_body", "")
    history_list_text = region_texts.get("summary_history_list", "")

    smart_summary_body_signals = [
        "开始总结", "输入你想总结", "暂无历史总结",
        "新建文档", "发送邮件", "总结团队周报", "总结聊天内容",
        "+添加成员", "PRAS-",
    ]

    # Smart Summary header signals: fingerprint or prompt-instruction text in
    # main_header is definitive for a Smart Summary content page (current or
    # old result).  "采集标识" and "请在总结结果" are from the fingerprint
    # instruction; "PRAS-" is the fingerprint prefix.
    smart_summary_header_signals = [
        "采集标识", "请在总结结果", "PRAS-",
    ]

    # Structured history list with multiple "总结" entries is strong evidence
    # of being inside the smart summary page (vs. a chat contact list).
    history_list_structured = history_list_text.count("总结") >= 2

    in_smart_summary = False
    header_has_ss_signal = any(s in main_text for s in smart_summary_header_signals)
    body_or_history_ok = any(s in body_text_early for s in smart_summary_body_signals) or history_list_structured
    if "智能总结" in main_text:
        in_smart_summary = True
    elif "智能总结" in sidebar_text:
        if body_or_history_ok or header_has_ss_signal:
            in_smart_summary = True
    elif body_or_history_ok or header_has_ss_signal:
        # Smart-summary body/header signals are strong enough even without
        # "智能总结" text — corroborated by UIA / child window entry evidence.
        if uia_smart_summary_entry or child_smart_summary_entry:
            in_smart_summary = True

    if not in_smart_summary:
        return {
            "state": "main_page",
            "confidence": 0.9,
            "signals": ["no_smart_summary_indicator"],
            "missing": ["smart_summary_child_window", "smart_summary_text"],
            "region_evidence": {k: v[:120] for k, v in region_texts.items()},
            "in_smart_summary": False,
        }

    # ---- MAIN PAGE OVERRIDE ----
    # Even if a smart summary window/control was detected, the visible content may
    # still be an ordinary chat page. Check for strong chat page indicators in
    # main_body and app_sidebar before proceeding to sub-page classification.
    body_text = region_texts.get("main_body", "")
    sidebar_text = region_texts.get("app_sidebar", "")
    bottom_text = region_texts.get("bottom_action_bar", "")
    all_text = " ".join(region_texts.values())

    main_page_signals_found: list[str] = []
    for kw in MAIN_PAGE_STRONG_INDICATORS:
        if kw in body_text:
            main_page_signals_found.append(kw)
    for kw in MAIN_PAGE_WEAK_INDICATORS:
        if kw in body_text:
            main_page_signals_found.append(kw)

    # Sidebar chat-list patterns: timestamps like "分汁前" (OCR for 分钟前),
    # unread badges like "[185条]", contact names — indicate the sidebar is
    # showing a chat list, not a Smart Summary history list.
    sidebar_chat_list = 0
    if "分汁前" in sidebar_text:
        sidebar_chat_list += 1
    if "条]" in sidebar_text:
        sidebar_chat_list += 1
    if sidebar_chat_list >= 2:
        main_page_signals_found.append("sidebar_chat_list")

    strong_count = sum(1 for s in main_page_signals_found if s in MAIN_PAGE_STRONG_INDICATORS)
    weak_count = sum(1 for s in main_page_signals_found if s in MAIN_PAGE_WEAK_INDICATORS)
    sidebar_override = (sidebar_chat_list >= 2)

    if strong_count >= 2 or (strong_count >= 1 and weak_count >= 1) or sidebar_override:
        return {
            "state": "main_page",
            "confidence": 0.85,
            "signals": ["ordinary_chat_page_indicators"] + main_page_signals_found,
            "missing": ["smart_summary_content"],
            "region_evidence": {k: v[:120] for k, v in region_texts.items()},
            "in_smart_summary": False,
        }

    # ---- We are in Smart Summary. Classify sub-page (history-first). ----
    history_text = region_texts.get("summary_history_list", "")

    # === HISTORY PAGE CHECK (MUST RUN FIRST) ===
    import re
    history_signals: list[str] = []
    history_missing: list[str] = []

    history_items = bool(re.search(r"(?:^|\s)\d{1,2}[\.\s、]", history_text))
    has_dates = bool(re.search(r"\d{4}[-/]\d{2}[-/]\d{2}", history_text))
    has_times = bool(re.search(r"\d{1,2}:\d{2}", history_text))
    # Multiple "总结"-prefixed entries (e.g. "总结本周 (6月228至6月26曰")
    # is the dominant pattern in real OCR output and was missed by the
    # numbered-item / date / time regexes above.
    multi_summary_entries = history_text.count("总结") >= 2
    if history_items or has_dates or has_times or multi_summary_entries:
        history_signals.append("sidebar_history_items")
    else:
        history_missing.append("sidebar_history_items")

    body_len = len(body_text)
    has_body_content = body_len > 80
    if has_body_content:
        history_signals.append(f"long_body_text_{body_len}chars")
    else:
        history_missing.append("long_body_text")

    has_result_actions = any(kw in all_text for kw in ["新建文档", "发送邮件", "复制"])
    if has_result_actions:
        history_signals.append("result_action_buttons")
        if "复制" in all_text:
            history_signals.append("copy_button_present")

    # Header fingerprint/prompt text (PRAS-..., 采集标识, 请在总结结果) is
    # definitive evidence of a Smart Summary content page — the old fingerprint
    # in the header means we are looking at a historical result, not a chat page.
    if header_has_ss_signal:
        history_signals.append("header_fingerprint_evidence")

    has_start_button = "开始总结" in all_text
    has_input_hints = any(kw in all_text for kw in ["输入你想总结", "暂无历史总结", "总结团队周报", "总结聊天内容"])
    if not has_start_button:
        history_signals.append("no_start_button")
    else:
        history_missing.append("no_start_button")
    if not has_input_hints:
        history_signals.append("no_input_hints")
    else:
        history_missing.append("no_input_hints")

    history_score = len(history_signals)
    history_conf = history_score / max(history_score + len(history_missing), 1)

    # History page requires at least one of: sidebar_history_items (dated list
    # entries), result_action_buttons ("新建文档/发送邮件/复制"), or
    # header_fingerprint_evidence (PRAS-/采集标识/请在总结结果 in main_header).
    # Long body text alone is NOT sufficient — ordinary chat pages also have long text.
    has_history_structure = bool(history_signals) and any(
        s in history_signals for s in ["sidebar_history_items", "result_action_buttons", "header_fingerprint_evidence"]
    )
    if history_score >= 3 and has_history_structure and not (has_start_button and has_input_hints):
        return {
            "state": "summary_history_page",
            "confidence": round(history_conf, 2),
            "signals": history_signals,
            "missing": history_missing,
            "region_evidence": {k: v[:120] for k, v in region_texts.items()},
            "in_smart_summary": True,
        }

    # === INPUT PAGE CHECK ===
    input_signals: list[str] = []
    input_missing: list[str] = []

    if has_start_button:
        input_signals.append("start_button")
    else:
        input_missing.append("start_button")

    if has_input_hints:
        input_signals.append("input_hints")
    else:
        input_missing.append("input_hints")

    if not has_result_actions:
        input_signals.append("no_result_actions")
    else:
        input_missing.append("no_result_actions")

    if body_len < 80:
        input_signals.append("short_body_text")
    else:
        input_missing.append("short_body_text")

    tm_x, tm_y, tm_conf = template_match(frame.full_image, "start_summary_1080p_light.png")
    if tm_x is not None:
        input_signals.append(f"template_start_button_{tm_conf:.2f}")
    else:
        input_missing.append("template_start_button")

    input_score = len(input_signals)
    input_conf = input_score / max(input_score + len(input_missing), 1)

    has_strong_input_hints = has_input_hints and not has_body_content and not has_result_actions
    history_or_result = history_score >= 3 or (has_body_content and has_result_actions)

    if has_start_button and not history_or_result:
        return {
            "state": "summary_input_page",
            "confidence": round(input_conf, 2),
            "signals": input_signals,
            "missing": input_missing,
            "region_evidence": {k: v[:120] for k, v in region_texts.items()},
            "in_smart_summary": True,
        }

    if has_strong_input_hints and not has_start_button and not history_or_result:
        return {
            "state": "summary_input_page",
            "confidence": min(round(input_conf, 2), 0.6),
            "signals": input_signals + ["no_start_button_but_strong_hints"],
            "missing": input_missing,
            "region_evidence": {k: v[:120] for k, v in region_texts.items()},
            "in_smart_summary": True,
        }

    # === RESULT PAGE CHECK ===
    # Result page MUST have either result action buttons (复制/新建文档/发送邮件)
    # or the current-run fingerprint.  Long body text + no start button alone is
    # NOT sufficient — ordinary chat pages also match that pattern.
    result_signals: list[str] = []
    result_missing: list[str] = []

    if has_body_content:
        result_signals.append(f"body_text_{body_len}chars")
    if has_result_actions:
        result_signals.append("result_action_buttons")
    if not has_start_button:
        result_signals.append("no_start_button")
    else:
        result_missing.append("no_start_button")

    if fingerprint and fingerprint in all_text:
        result_signals.append("fingerprint_present")
    elif fingerprint:
        result_missing.append("fingerprint_present")

    result_score = len(result_signals)
    result_conf = result_score / max(result_score + len(result_missing), 1)

    has_result_mandatory = has_result_actions or (fingerprint and fingerprint in all_text)
    if result_score >= 2 and has_result_mandatory:
        return {
            "state": "summary_result_page",
            "confidence": round(result_conf, 2),
            "signals": result_signals,
            "missing": result_missing,
            "region_evidence": {k: v[:120] for k, v in region_texts.items()},
            "in_smart_summary": True,
        }

    # === GENERATING PAGE CHECK ===
    # Only classify as generating when we have body text, no start button, no
    # result actions, AND no ordinary chat page indicators.  Ordinary chat pages
    # also have body text without start/result buttons.
    any_main_page_signals = bool(main_page_signals_found)
    if body_len > 20 and not has_start_button and not has_result_actions and not any_main_page_signals:
        return {
            "state": "summary_generating_page",
            "confidence": 0.5,
            "signals": ["some_body_text", "no_start_button", "no_result_actions"],
            "missing": ["result_content", "action_buttons"],
            "region_evidence": {k: v[:120] for k, v in region_texts.items()},
            "in_smart_summary": True,
        }

    return {
        "state": "summary_unknown_page",
        "confidence": 0.3,
        "signals": ["in_smart_summary"],
        "missing": ["clear_page_classification"],
        "region_evidence": {k: v[:120] for k, v in region_texts.items()},
        "in_smart_summary": True,
    }


# ---------------------------------------------------------------------------
# Automation Actions (foreground-verified captures)
# ---------------------------------------------------------------------------


def _action_open_smart_summary_entry(
    main_hwnd: int,
    window_rect: wintypes.RECT,
    reader: object,
    trace: TraceLogger,
) -> str:
    import interception

    width = window_rect.right - window_rect.left
    height = window_rect.bottom - window_rect.top

    # Strategy A: UI Automation
    try:
        import uiautomation as auto
        root = auto.GetRootControl()
        for win in root.GetChildren():
            try:
                if win.NativeWindowHandle == main_hwnd:
                    for control, _depth in auto.WalkTree(win, lambda c, d: d < 6):
                        try:
                            name = (control.Name or "").strip()
                            auto_id = (control.AutomationId or "").strip()
                            if "智能总结" in name or "智能总结" in auto_id:
                                rect = control.BoundingRectangle
                                cx = rect.left + rect.width() // 2
                                cy = rect.top + rect.height() // 2
                                if cx > 0 and cy > 0:
                                    print(f"企微：UIA 找到智能总结入口 @ ({cx},{cy})，点击。")
                                    ensure_wecom_foreground(main_hwnd)
                                    interception.move_to(cx, cy)
                                    time.sleep(0.1)
                                    interception.click(button="left")
                                    time.sleep(1.5)
                                    trace.log(stage="open_entry", method="uia", coords=(cx, cy))
                                    return "reclassify"
                        except Exception:
                            continue
            except Exception:
                continue
    except ImportError:
        pass

    # Strategy B: OCR in left sidebar area (verified foreground)
    _verify_foreground_or_fail(main_hwnd, "WeWorkWindow", "open_entry_ocr", trace)
    img = capture_rect(window_rect, trace.stage_screenshot("entry_ocr_scan"))
    for bbox, text, _conf in ocr_all(img, reader, 0.15):
        cx = int((bbox[0][0] + bbox[2][0]) / 2)
        cy = int((bbox[0][1] + bbox[2][1]) / 2)
        if cx < width * 0.35 and "智能总结" in text:
            sx = window_rect.left + cx
            sy = window_rect.top + cy
            print(f"企微：OCR 找到智能总结入口 '{text}' @ ({sx},{sy})，点击。")
            ensure_wecom_foreground(main_hwnd)
            interception.move_to(sx, sy)
            time.sleep(0.1)
            interception.click(button="left")
            time.sleep(1.5)
            trace.log(stage="open_entry", method="ocr", text=text, coords=(sx, sy))
            return "reclassify"

    # Strategy C: Single calibrated probe (not a scan)
    probe_x = window_rect.left + 31
    probe_y = window_rect.top + int(height * 499 / 1080)
    print(f"企微：UIA 和 OCR 均未找到入口，使用单点探针 ({probe_x},{probe_y})。")
    ensure_wecom_foreground(main_hwnd)
    interception.move_to(probe_x, probe_y)
    time.sleep(0.1)
    interception.click(button="left")
    time.sleep(1.5)
    trace.log(stage="open_entry", method="probe", coords=(probe_x, probe_y))
    return "reclassify"


def _action_click_plus(
    main_hwnd: int,
    window_rect: wintypes.RECT,
    reader: object,
    trace: TraceLogger,
) -> str:
    import interception

    width = window_rect.right - window_rect.left
    height = window_rect.bottom - window_rect.top

    ensure_wecom_foreground(main_hwnd)
    _verify_foreground_or_fail(main_hwnd, "WeWorkWindow", "click_plus", trace)
    img = capture_rect(window_rect, trace.stage_screenshot("before_plus"))
    save_ocr(trace.ocr_path("before_plus"), img, reader, 0.1)

    # Crop the summary_sidebar_header region — the real + lives here.
    regions = compute_regions(window_rect)
    sx1, sy1, sx2, sy2 = regions["summary_sidebar_header"]
    header_crop = img.crop((
        sx1 - window_rect.left, sy1 - window_rect.top,
        sx2 - window_rect.left, sy2 - window_rect.top,
    ))
    header_crop.save(str(trace.region_screenshot("before_plus", "summary_sidebar_header")))

    # ---- Strategy 1: template matching on header crop only ----
    if template_available("plus_1080p_light.png"):
        tm_x, tm_y, tm_conf = template_match(header_crop, "plus_1080p_light.png")
        if tm_x is not None:
            sx = sx1 + tm_x
            sy = sy1 + tm_y
            # Safety: verify match is inside summary_sidebar_header
            if sx1 <= sx <= sx2 and sy1 <= sy <= sy2:
                print(f"企微：模板匹配找到 + 按钮 conf={tm_conf:.2f} @ ({sx},{sy})，点击。")
                trace.log(stage="click_plus", method="template",
                          template="plus_1080p_light", confidence=tm_conf,
                          coords=(sx, sy), region="summary_sidebar_header")
                ensure_wecom_foreground(main_hwnd)
                interception.move_to(sx, sy)
                time.sleep(0.1)
                interception.click(button="left")
                time.sleep(1.2)

                # Post-click safety check
                _verify_foreground_or_fail(main_hwnd, "WeWorkWindow", "post_plus_check", trace)
                check_img = capture_rect(window_rect, trace.stage_screenshot("post_plus_check"))
                check_text = ocr_joined(check_img, reader, 0.1)
                if any(kw in check_text for kw in ["选择成员", "从群聊中选择"]):
                    print("企微安全失败 [+点击后]：检测到成员选择弹窗"
                          "（OCR 出现「选择成员」/「从群聊中选择」），"
                          "可能误触了「添加成员」控件，已停止。")
                    trace.log(stage="click_plus", method="template", coords=(sx, sy),
                              error="member_dialog_detected_after_click")
                    return "terminal_failure"
                return "reclassify"
            else:
                trace.log(stage="click_plus", method="template_rejected",
                          template="plus_1080p_light", confidence=tm_conf,
                          coords=(sx, sy),
                          reason="outside_summary_sidebar_header",
                          header_bounds=(sx1, sy1, sx2, sy2))
        else:
            trace.log(stage="click_plus", method="template",
                      template="plus_1080p_light", confidence=tm_conf,
                      error="below_threshold")

    # ---- Strategy 2: OCR in summary_sidebar_header ----
    # Only search the sidebar header crop to avoid false matches on
    # "添加成员" / "+添加成员" in the main content area.
    _PLUS_BLOCKLIST = ["添加成员", "添加咸员", "选择成员", "从群聊中选择"]

    candidates: list[tuple[int, int, str]] = []
    for bbox, text, _conf in ocr_all(header_crop, reader, 0.1):
        if "+" not in text and "＋" not in text:
            continue
        if any(blocked in text for blocked in _PLUS_BLOCKLIST):
            trace.log(stage="click_plus", method="ocr_rejected", text=text,
                      reason="blocklisted_member_term")
            continue
        cx = int((bbox[0][0] + bbox[2][0]) / 2)
        cy = int((bbox[0][1] + bbox[2][1]) / 2)
        candidates.append((sx1 + cx, sy1 + cy, f"OCR '{text}'"))

    for sx, sy, label in candidates[:3]:
        print(f"企微：OCR + 候选 {label} @ ({sx},{sy})，点击。")
        ensure_wecom_foreground(main_hwnd)
        interception.move_to(sx, sy)
        time.sleep(0.1)
        interception.click(button="left")
        time.sleep(1.2)
        trace.log(stage="click_plus", method="ocr", label=label, coords=(sx, sy))

        _verify_foreground_or_fail(main_hwnd, "WeWorkWindow", "post_plus_check", trace)
        check_img = capture_rect(window_rect, trace.stage_screenshot("post_plus_check"))
        check_text = ocr_joined(check_img, reader, 0.1)
        if any(kw in check_text for kw in ["选择成员", "从群聊中选择"]):
            print("企微安全失败 [+点击后]：检测到成员选择弹窗"
                  "（OCR 出现「选择成员」/「从群聊中选择」），"
                  "可能误触了「添加成员」控件，已停止。")
            trace.log(stage="click_plus", method="ocr", label=label, coords=(sx, sy),
                      error="member_dialog_detected_after_click")
            return "terminal_failure"
        return "reclassify"

    # ---- Strategy 3: layout-based estimate ----
    # If OCR detected "智能总结" in the header, the + button is at the right
    # edge of the sidebar header near the title's row.  Use a constrained
    # estimate derived from the observed layout (v4: + at ~87% x, ~35% y within
    # the sidebar header).
    header_text = ocr_joined(header_crop, reader, 0.1)
    if "智能总结" in header_text:
        est_x = sx1 + int((sx2 - sx1) * 0.87)
        est_y = sy1 + int((sy2 - sy1) * 0.35)
        if sx1 <= est_x <= sx2 and sy1 <= est_y <= sy2:
            print(f"企微：布局估计 + 按钮 @ ({est_x},{est_y})，点击。")
            trace.log(stage="click_plus", method="layout_estimate",
                      coords=(est_x, est_y), region="summary_sidebar_header",
                      header_text_sample=header_text[:80])
            ensure_wecom_foreground(main_hwnd)
            interception.move_to(est_x, est_y)
            time.sleep(0.1)
            interception.click(button="left")
            time.sleep(1.2)

            _verify_foreground_or_fail(main_hwnd, "WeWorkWindow", "post_plus_check", trace)
            check_img = capture_rect(window_rect, trace.stage_screenshot("post_plus_check"))
            check_text = ocr_joined(check_img, reader, 0.1)
            if any(kw in check_text for kw in ["选择成员", "从群聊中选择"]):
                print("企微安全失败 [+点击后]：检测到成员选择弹窗"
                      "（OCR 出现「选择成员」/「从群聊中选择」），"
                      "可能误触了「添加成员」控件，已停止。")
                trace.log(stage="click_plus", method="layout_estimate",
                          coords=(est_x, est_y),
                          error="member_dialog_detected_after_click")
                return "terminal_failure"
            return "reclassify"

    print("企微：未找到可信 + 按钮（模板、OCR 和布局估计均失败）。")
    trace.log(stage="click_plus", method="none", error="no_plus_candidates")
    return "terminal_failure"


def _action_paste_prompt(
    main_hwnd: int,
    window_rect: wintypes.RECT,
    prompt: str,
    reader: object,
    trace: TraceLogger,
) -> bool:
    """Paste prompt into input area. Returns True if fingerprint is visible after paste.

    Uses OCR to locate the input area (looking for input hints like 你想总结的主题
    or 输入你想总结) before clicking and pasting.  After paste, re-captures and
    verifies the fingerprint is visible in the on-screen text.
    """
    import interception
    import pyperclip

    width = window_rect.right - window_rect.left
    height = window_rect.bottom - window_rect.top

    # Copy prompt to clipboard
    ensure_wecom_foreground(main_hwnd)
    pyperclip.copy(prompt)

    # Try to locate the input area via OCR in main_body region (avoid full-window OCR).
    _verify_foreground_or_fail(main_hwnd, "WeWorkWindow", "paste_locate", trace)
    pre_img = capture_rect(window_rect, trace.stage_screenshot("paste_locate"))
    input_cx = window_rect.left + int(width * 0.5)
    input_cy = window_rect.top + int(height * 0.45)
    input_located = False

    mb_left = int(width * 0.17)
    mb_top = int(height * 0.10)
    mb_right = int(width * 0.83)
    mb_bottom = int(height * 0.88)
    mb_crop = pre_img.crop((mb_left, mb_top, mb_right, mb_bottom))

    for bbox, text, _conf in ocr_all(mb_crop, reader, 0.1):
        if any(hint in text for hint in ["你想总结", "输入你想总结", "输入你想"]):
            cx = int((bbox[0][0] + bbox[2][0]) / 2)
            cy = int((bbox[0][1] + bbox[2][1]) / 2)
            input_cx = window_rect.left + mb_left + cx
            input_cy = window_rect.top + mb_top + cy + 20  # click slightly below the hint text
            input_located = True
            print(f"企微：OCR 定位输入区提示 '{text}' @ ({input_cx},{input_cy})。")
            trace.log(stage="paste_locate", method="ocr_hint", text=text, coords=(input_cx, input_cy))
            break

    if not input_located:
        print(f"企微：未找到输入区提示文字，使用固定比例点 ({input_cx},{input_cy})。")
        trace.log(stage="paste_locate", method="fallback", coords=(input_cx, input_cy))

    # Click input area and paste
    ensure_wecom_foreground(main_hwnd)
    interception.move_to(input_cx, input_cy)
    time.sleep(0.2)
    interception.click(button="left")
    time.sleep(0.3)

    ensure_wecom_foreground(main_hwnd)
    with interception.hold_key("ctrl"):
        interception.press("v")
    time.sleep(0.5)
    trace.log(stage="paste_prompt", prompt_len=len(prompt), input_located=input_located,
              paste_coords=(input_cx, input_cy))

    # Verify fingerprint visible after paste
    _verify_foreground_or_fail(main_hwnd, "WeWorkWindow", "after_paste", trace)
    img_pasted = capture_rect(window_rect, trace.stage_screenshot("after_paste"))
    # Crop to main_body for OCR — fingerprint and paste text live here, avoids
    # expensive full-image multi-engine OCR.
    mb_pasted = img_pasted.crop((int(width * 0.17), int(height * 0.10),
                                  int(width * 0.83), int(height * 0.88)))
    # Extract fingerprint from prompt — it's the PRAS-... pattern
    import re
    fp_match = re.search(r"PRAS-\d{8}-\d{6}-\d{4}", prompt)
    fingerprint = fp_match.group(0) if fp_match else ""
    save_ocr(trace.ocr_path("after_paste"), mb_pasted, reader)
    pasted_text = " ".join(ocr_texts_multi(mb_pasted, reader, 0.1, fingerprint=fingerprint))
    fp_visible = fingerprint in pasted_text if fingerprint else False
    trace.log(event="paste_verify", visible_fingerprint=fp_visible, fingerprint=fingerprint,
              pasted_text_preview=pasted_text[:200])

    if not fp_visible:
        print(f"企微：粘贴后未在屏幕 OCR 中检测到采集指纹 {fingerprint}。")
        print(f"  可能原因：输入框未获得焦点、粘贴未成功、或 OCR 未能识别。")
    else:
        print(f"企微：粘贴校验通过，指纹 {fingerprint} 在屏幕可见。")

    return fp_visible


def _action_click_start(
    main_hwnd: int,
    window_rect: wintypes.RECT,
    reader: object,
    trace: TraceLogger,
) -> bool:
    import interception

    _verify_foreground_or_fail(main_hwnd, "WeWorkWindow", "click_start", trace)
    img = capture_rect(window_rect, trace.stage_screenshot("before_start"))
    save_ocr(trace.ocr_path("before_start"), img, reader)

    width = window_rect.right - window_rect.left
    height = window_rect.bottom - window_rect.top

    # Strategy A: template match
    tm_x, tm_y, tm_conf = template_match(img, "start_summary_1080p_light.png")
    if tm_x is not None:
        sx = window_rect.left + tm_x
        sy = window_rect.top + tm_y
        print(f"企微：模板匹配找到开始总结 conf={tm_conf:.2f} @ ({sx},{sy})，点击。")
        trace.log(stage="click_start", method="template", confidence=tm_conf, coords=(sx, sy))
        ensure_wecom_foreground(main_hwnd)
        interception.move_to(window_rect.left + width // 2, window_rect.top + 15)
        time.sleep(0.1)
        interception.click(button="left")
        time.sleep(0.2)
        interception.move_to(sx, sy)
        time.sleep(0.1)
        interception.click(button="left")
        return True

    # Strategy B: OCR exact match for "开始总结" — use low confidence threshold
    # because the button text may be rendered at low contrast.
    best_match: tuple[int, int, float, str] | None = None
    for bbox, text, conf in ocr_all_multi(img, reader, 0.08):
        if "开始总结" in text:
            # Exclude suggestion cards that happen to contain these characters
            if any(blocked in text for blocked in START_BUTTON_BLOCKLIST):
                continue
            cx = int((bbox[0][0] + bbox[2][0]) / 2)
            cy = int((bbox[0][1] + bbox[2][1]) / 2)
            if best_match is None or conf > best_match[2]:
                best_match = (cx, cy, conf, text)

    if best_match is not None:
        bx, by, conf, text = best_match
        sx = window_rect.left + bx
        sy = window_rect.top + by
        print(f"企微：OCR 找到 '{text}' conf={conf:.2f} @ ({sx},{sy})，点击。")
        trace.log(stage="click_start", method="ocr_exact", text=text, confidence=conf, coords=(sx, sy))
        ensure_wecom_foreground(main_hwnd)
        interception.move_to(window_rect.left + width // 2, window_rect.top + 15)
        time.sleep(0.1)
        interception.click(button="left")
        time.sleep(0.2)
        interception.move_to(sx, sy)
        time.sleep(0.1)
        interception.click(button="left")
        return True

    # Strategy C: constrained OCR search in bottom-right button area.
    # Only accept texts that are SHORT button-like labels (≤6 chars) containing
    # "开始" or exactly "开始总结".  Exclude long suggestion card texts.
    button_left = int(width * 0.55)
    button_top = int(height * 0.40)
    for bbox, text, conf in ocr_all_multi(img, reader, 0.15):
        cx = int((bbox[0][0] + bbox[2][0]) / 2)
        cy = int((bbox[0][1] + bbox[2][1]) / 2)
        text_stripped = text.strip()
        # Must be in the button area
        if not (cx > button_left and cy > button_top):
            continue
        # Must be a short button label, not a long suggestion card
        if len(text_stripped) > 6:
            continue
        # Must explicitly contain "开始总结" or "开始"
        if "开始总结" not in text_stripped and "开始" not in text_stripped:
            continue
        # Must NOT be a suggestion card
        if any(blocked in text_stripped for blocked in START_BUTTON_BLOCKLIST):
            continue
        sx = window_rect.left + cx
        sy = window_rect.top + cy
        print(f"企微：按钮区域候选 '{text}' conf={conf:.2f} @ ({sx},{sy})，点击。")
        trace.log(stage="click_start", method="ocr_constrained", text=text, confidence=conf, coords=(sx, sy))
        ensure_wecom_foreground(main_hwnd)
        interception.move_to(window_rect.left + width // 2, window_rect.top + 15)
        time.sleep(0.1)
        interception.click(button="left")
        time.sleep(0.2)
        interception.move_to(sx, sy)
        time.sleep(0.1)
        interception.click(button="left")
        return True

    print("企微：未找到开始总结按钮（模板匹配和 OCR 均失败），已停止。")
    trace.log(stage="click_start", method="none", error="no_start_button_found")
    return False


def _fuzzy_fingerprint_match(ocr_text: str, fingerprint: str, max_diff: int = 1) -> tuple[bool, bool, str]:
    """Check if fingerprint appears in OCR text with fuzzy allowance.

    OCR may misread or drop 1-2 characters of the fingerprint (e.g. PV10 → P10).
    Returns (exact_match, fuzzy_match, matched_text).

    Fuzzy matching: finds candidate substrings starting with 'PRAS-' in the OCR
    text, extracts a segment of the same length as the fingerprint, and compares
    character-by-character.  Up to max_diff characters may differ.
    """
    if not fingerprint or not fingerprint.startswith("PRAS-"):
        return fingerprint in ocr_text if fingerprint else True, False, ""

    # Exact match first
    if fingerprint in ocr_text:
        return True, True, fingerprint

    # Extract prefix: PRAS-YYYYMMDD-HHMMSS-
    # The fingerprint format is PRAS-YYYYMMDD-HHMMSS-XXXX
    prefix_end = fingerprint.rfind("-")
    if prefix_end < 10:
        return False, False, ""
    prefix = fingerprint[:prefix_end + 1]  # "PRAS-YYYYMMDD-HHMMSS-"
    suffix = fingerprint[prefix_end + 1:]    # "XXXX"

    # Search for PRAS- prefix in OCR text
    import re
    fp_len = len(fingerprint)
    for m in re.finditer(r"PRAS-\d{8}-\d{6}-[\dA-Za-z]", ocr_text):
        start = m.start()
        # Extract a segment of approximately the fingerprint length
        segment_end = min(start + fp_len + 4, len(ocr_text))
        candidate = ocr_text[start:segment_end]
        candidate = candidate[:fp_len + max_diff + 1]
        # Trim trailing non-fingerprint chars so OCR noise after FP doesn't inflate diff count
        while candidate and not (candidate[-1].isalnum() or candidate[-1] == '-'):
            candidate = candidate[:-1]

        # Compare character-by-character
        diff_count = 0
        fi, ci = 0, 0
        fp_chars = list(fingerprint)
        cand_chars = list(candidate)

        while fi < len(fp_chars) and ci < len(cand_chars):
            if cand_chars[ci] == fp_chars[fi]:
                fi += 1
                ci += 1
            elif ci + 1 < len(cand_chars) and cand_chars[ci + 1] == fp_chars[fi]:
                # Extra char in candidate (OCR misread)
                diff_count += 1
                ci += 1
            elif fi + 1 < len(fp_chars) and fp_chars[fi + 1] == cand_chars[ci]:
                # Missing char in candidate (OCR dropped)
                diff_count += 1
                fi += 1
            else:
                # Substitution
                diff_count += 1
                fi += 1
                ci += 1

            if diff_count > max_diff:
                break

        # Count remaining chars as differences
        # Only count unmatched fingerprint chars as differences.
        # Trailing candidate chars after full FP match are OCR noise.
        diff_count += abs(len(fp_chars) - fi)

        if diff_count <= max_diff:
            matched = ocr_text[start:start + fp_len + 2].strip()
            # Clean up: extract just the fingerprint portion (no trailing OCR noise)
            clean_end = min(fp_len + 2, len(matched))
            for ch in " ~，。、；：！？\n\r\t":
                idx = matched.find(ch)
                if 0 <= idx < clean_end:
                    clean_end = idx
            matched = matched[:clean_end].strip()
            return False, True, matched

    return False, False, ""


def _fingerprint_prefix_match(
    ocr_text: str, fingerprint: str, max_date_diff: int = 1, max_time_diff: int = 2,
) -> tuple[bool, str]:
    """Check if OCR text contains a PRAS- prefix matching this run's date + timestamp.

    The fingerprint suffix (4 digits) may be mangled by OCR, but the PRAS + date +
    timestamp portion is longer and more distinctive.  Combined with paste+start
    confirmation and privacy notice, this provides a reliable weak signal that the
    current-run result page is visible — even when the full fingerprint is illegible.

    Returns (match_found, matched_prefix).
    """
    import re
    prefix_match = re.search(r"PRAS-(\d{8})-(\d{6})", ocr_text)
    if not prefix_match:
        return False, ""
    ocr_date = prefix_match.group(1)
    ocr_time = prefix_match.group(2)
    # fingerprint format: PRAS-YYYYMMDD-HHMMSS-DDDD
    fp_date = fingerprint[5:13]   # YYYYMMDD
    fp_time = fingerprint[14:20]  # HHMMSS

    date_diff = sum(1 for a, b in zip(ocr_date, fp_date) if a != b)
    time_diff = sum(1 for a, b in zip(ocr_time, fp_time) if a != b)

    if date_diff <= max_date_diff and time_diff <= max_time_diff:
        return True, prefix_match.group(0)
    return False, ""


def _action_wait_result(
    main_hwnd: int,
    window_rect: wintypes.RECT,
    reader: object,
    trace: TraceLogger,
    fingerprint: str,
    max_wait: int = 180,
    stable_seconds: int = 15,
    poll_interval: int = 3,
    paste_verified: bool = True,
    start_clicked: bool = True,
) -> str:
    """Wait for generation using region OCR. Verifies foreground on each poll.

    Returns one of: 'copy_available', 'result_detected', 'generating',
    'generation_not_triggered', 'generation_timeout'.

    Uses wall-clock time for the hard upper limit.  Detects "generation never
    triggered" early: if input page indicators (开始总结 button, suggestion
    cards, 添加成员) persist for multiple consecutive polls with no result
    actions, the start button was likely not clicked or a suggestion card was
    misclicked.

    paste_verified and start_clicked provide context: by the time this function
    is called, we already know paste succeeded and the start button was clicked.
    These are used as additional constraints for the prefix-based weak fingerprint
    confirmation path, so that an OCR-mangled fingerprint suffix can still form a
    trusted result_detected signal when combined with privacy notice, body
    stability, and the PRAS + date + timestamp prefix match.
    """
    wall_start = time.time()
    state = "submitted"
    last_body_text = ""
    stable_since: float = 0.0
    input_page_streak = 0  # consecutive polls showing input page structure
    result_signals_seen = False  # flip to True once body/fp/privacy/actions appear
    current_run_result_confirmed = False  # persists: this run's result was once confirmed

    while True:
        wall_elapsed = time.time() - wall_start
        if wall_elapsed >= max_wait:
            break

        # Layered polling: use longer interval during early generation when no
        # result signals are visible yet; shorten once the result starts appearing.
        interval = poll_interval if result_signals_seen else min(poll_interval * 2, 6)
        poll_start = time.time()
        time.sleep(interval)

        clear_ocr_cache()

        # Verify foreground before region captures
        _verify_foreground_or_fail(main_hwnd, "WeWorkWindow", f"wait_{int(wall_elapsed)}", trace)

        # Capture ONE trusted frame and crop regions from it
        frame = capture_trusted_frame(main_hwnd, window_rect, trace, f"wait_{int(wall_elapsed)}",
                                       region_names=["main_body", "bottom_action_bar"])
        save_frame_artifacts(frame, trace, f"wait_{int(wall_elapsed)}")

        body_img = frame.regions.get("main_body")
        action_img = frame.regions.get("bottom_action_bar")
        if body_img is None or action_img is None:
            continue

        # --- Single-pass OCR on body (merge text extraction + diagnostic save) ---
        body_texts = _ocr_region_once(body_img, "main_body", reader, trace, f"wait_{int(wall_elapsed)}", fingerprint=fingerprint)
        body_joined = " ".join(body_texts)
        body_len = len(body_joined)

        # Action bar: small region, single EasyOCR pass
        action_results = ocr_all(action_img, reader, 0.1)
        action_texts = [text for _bbox, text, _conf in action_results]
        action_joined = " ".join(action_texts)
        # Save action bar diagnostics from the same OCR results
        _save_ocr_lines(
            trace.ocr_path(f"wait_{int(wall_elapsed)}_action"),
            [(bbox, text, conf) for bbox, text, conf in action_results],
            "E",
        )

        # "开始总结" may be in main_body (next to input box) or bottom_action_bar
        start_visible = "开始总结" in action_joined or "开始总结" in body_joined
        has_result_actions = any(kw in action_joined or kw in body_joined
                                 for kw in ["复制", "新建文档", "新建智能文档", "发送邮件"])
        fp_exact, fp_fuzzy, fp_candidate = _fuzzy_fingerprint_match(body_joined, fingerprint, max_diff=1) if fingerprint else (True, True, "")
        fp_visible = fp_exact
        has_soft_fp = fp_fuzzy
        # "结果仅你个人可见" is a strong result-page signal from WeCom
        has_privacy_notice = "结果仅你个人可见" in body_joined or "仅你个人可见" in body_joined
        # Prefix match: PRAS + date + timestamp (suffix may be OCR-mangled)
        has_fp_prefix, fp_prefix_candidate = _fingerprint_prefix_match(body_joined, fingerprint) if fingerprint else (True, "")

        # Check for persistent input page indicators (generation never triggered)
        input_page_indicators = sum(
            1 for kw in INPUT_PAGE_PERSISTENT_INDICATORS if kw in body_joined
        )
        has_suggestion_cards = any(
            blocked in body_joined for blocked in START_BUTTON_BLOCKLIST
        )

        # Once any result signal appears, switch to normal polling cadence
        if not result_signals_seen:
            if body_len >= 80 or fp_visible or has_soft_fp or has_fp_prefix or has_privacy_notice or has_result_actions:
                result_signals_seen = True

        # Persist: once this run's result was trusted, keep that knowledge.
        # Guards against long-result scenarios where signals scroll out of view.
        if not current_run_result_confirmed:
            _fp_prefix_ok = (paste_verified and start_clicked
                             and has_fp_prefix
                             and (has_privacy_notice or has_result_actions))
            if (fp_visible or has_result_actions
                    or (has_soft_fp and has_privacy_notice)
                    or _fp_prefix_ok):
                current_run_result_confirmed = True

        trace.log(
            stage="wait_result", state=state,
            wall_elapsed=round(wall_elapsed, 1),
            body_len=body_len, start_visible=start_visible,
            has_result_actions=has_result_actions, fp_visible=fp_visible,
            fp_fuzzy=has_soft_fp, fp_candidate=fp_candidate[:30] if fp_candidate else "",
            fp_prefix=has_fp_prefix, fp_prefix_candidate=fp_prefix_candidate,
            privacy_notice=has_privacy_notice,
            input_page_indicators=input_page_indicators,
            has_suggestion_cards=has_suggestion_cards,
            current_run_result_confirmed=current_run_result_confirmed,
            action_bar_preview=action_joined[:120],
        )

        # ---- Early-stop: generation never triggered ----
        # If we still see input page structure (开始总结 visible + suggestion cards
        # or 添加成员) for 3+ consecutive polls and no result actions, the click
        # likely didn't trigger generation (e.g. misclicked a suggestion card).
        if start_visible and not has_result_actions:
            if input_page_indicators >= 2 or has_suggestion_cards or fp_visible:
                input_page_streak += 1
            else:
                input_page_streak = max(0, input_page_streak - 1)

            if input_page_streak >= 3:
                print(f"企微：连续 {input_page_streak} 轮检测到输入页结构（开始总结可见、建议卡片/添加成员存在），"
                      f"判定未触发生成。")
                trace.log(event="generation_not_triggered", input_page_streak=input_page_streak,
                          body_preview=body_joined[:200])
                return "generation_not_triggered"
        else:
            input_page_streak = max(0, input_page_streak - 1)

        # ---- State machine ----
        if state == "submitted":
            if not start_visible:
                state = "generating"
                print(f"企微：开始总结按钮消失（主内容区 {body_len} 字符），"
                      f"进入生成状态（{wall_elapsed:.0f}s）。")
                continue
            # Still seeing start button — log heartbeat
            if int(wall_elapsed) % 12 < poll_interval:
                print(f"企微：等待开始总结按钮消失（{wall_elapsed:.0f}s），"
                      f"按钮区：{action_joined[:60]}，body区开始总结：{'是' if '开始总结' in body_joined else '否'}")
            continue

        if state == "generating":
            if has_result_actions:
                state = "result_detected"
                print(f"企微：检测到结果操作区（{wall_elapsed:.0f}s），监控稳定性。")
                continue
            # Multi-tier fingerprint evidence for result detection.
            # Tier 1 (fp_strong): exact full fingerprint → strongest signal.
            # Tier 2 (fp_weak):   fuzzy full fingerprint + privacy/actions.
            # Tier 3 (fp_prefix_ok): PRAS+date+timestamp prefix + privacy/actions
            #        + paste verified + start clicked.  Guards against OCR-mangled
            #        suffix characters (e.g. 3ZRK→3队 in EasyOCR, now also covered
            #        by RapidOCR primary engine).
            if body_len > 80 and not start_visible:
                fp_strong = fp_visible
                fp_weak = has_soft_fp and (has_privacy_notice or has_result_actions)
                fp_prefix_ok = (paste_verified and start_clicked
                                and has_fp_prefix
                                and (has_privacy_notice or has_result_actions))
                if fp_strong or fp_weak or fp_prefix_ok:
                    still_looks_like_input = (input_page_indicators >= 2 or has_suggestion_cards)
                    if not still_looks_like_input:
                        state = "result_detected"
                        if fp_visible:
                            method = "exact_fp"
                        elif has_soft_fp:
                            method = "fuzzy_fp_with_context"
                        else:
                            method = "prefix_fp_with_context"
                        print(f"企微：主内容区文本增长到 {body_len} 字符、判定{method}"
                              f"且无开始按钮（{wall_elapsed:.0f}s），监控稳定性。")
                        continue
                if int(wall_elapsed) % 12 < poll_interval and not fp_visible:
                    if has_soft_fp:
                        print(f"企微：生成中（{wall_elapsed:.0f}s），主内容区 {body_len} 字符，"
                              f"指纹近似匹配={fp_candidate}，等待结果页信号确认。")
                    elif has_fp_prefix:
                        print(f"企微：生成中（{wall_elapsed:.0f}s），主内容区 {body_len} 字符，"
                              f"检测到PRAS前缀={fp_prefix_candidate}，等待结果页隐私提示或操作区。")
                    else:
                        print(f"企微：生成中（{wall_elapsed:.0f}s），主内容区 {body_len} 字符，指纹不可见。")
                continue

        if state == "result_detected":
            if has_result_actions and not start_visible:
                state = "copy_available"
                print(f"企微：复制/结果操作区可见（{wall_elapsed:.0f}s），进入复制阶段。")
                return state

            if body_joined == last_body_text:
                stable_since += time.time() - poll_start
                if stable_since >= stable_seconds:
                    still_looks_like_input = (input_page_indicators >= 2 or has_suggestion_cards)
                    # Text stability alone is not enough — require fingerprint
                    # evidence or result actions to guard against stale history pages.
                    fp_prefix_ok = (paste_verified and start_clicked
                                    and has_fp_prefix
                                    and (has_privacy_notice or has_result_actions))
                    # current_run_result_confirmed persists across polls — handles
                    # long-result scenarios where signals scrolled out of view.
                    if not still_looks_like_input and (fp_visible or has_result_actions or (has_soft_fp and has_privacy_notice) or fp_prefix_ok or current_run_result_confirmed):
                        state = "copy_available"
                        if current_run_result_confirmed and not (fp_visible or has_result_actions):
                            print(f"企微：本次结果已确认且正文稳定 {stable_seconds}s（{wall_elapsed:.0f}s），"
                                  f"但操作区未在当前视图可见，进入复制阶段滚动查找。")
                        else:
                            print(f"企微：主内容区文本稳定 {stable_seconds}s（{wall_elapsed:.0f}s），进入复制阶段。")
                        return state
            else:
                stable_since = 0.0
                last_body_text = body_joined
            continue

        if state == "copy_available":
            return state

        if int(wall_elapsed) % 12 < poll_interval:
            print(f"企微：状态={state}，{wall_elapsed:.0f}/{max_wait}s。")

    wall_elapsed = time.time() - wall_start
    print(f"企微：等待达到硬上限 {max_wait}s（墙钟 {wall_elapsed:.0f}s），状态={state}。")
    if state in ("result_detected", "copy_available"):
        return state
    if state == "submitted":
        return "generation_not_triggered"
    return "generation_timeout"


def _estimate_copy_from_action_row(
    ocr_results: list[tuple],
    region_left: int,
    region_top: int,
    region_width: int,
    region_height: int,
    trace: TraceLogger,
) -> tuple[int | None, int | None, str, dict[str, Any]]:
    """Estimate copy button position from action-row OCR results.

    Handles three cases:
    A) Pure "复制" detected → use its center directly.
    B) Merged text "新建智能文档 发送邮件 复制" → estimate 3rd action position
       by splitting the merged bbox proportionally.
    C) Only "新建智能文档 发送邮件" (missing "复制") → estimate copy button
       to the right of the rightmost detected action.

    All estimates are constrained to the provided region (main_body or lower crop).
    Returns (screen_x, screen_y, method, trace_info) or (None, None, "", {}).
    """
    _COPY_KEYWORDS = ["复制", "拷贝"]
    _NON_COPY_ACTIONS = ["新建智能文档", "发送邮件"]
    _ACTION_SIGNALS = _COPY_KEYWORDS + _NON_COPY_ACTIONS

    # Collect candidates that contain action signals
    candidates: list[dict[str, Any]] = []
    for bbox, text, conf in ocr_results:
        if not any(kw in text for kw in _ACTION_SIGNALS):
            continue
        bx1 = int(bbox[0][0])
        by1 = int(bbox[0][1])
        bx2 = int(bbox[2][0])
        by2 = int(bbox[2][1])
        cx = (bx1 + bx2) // 2
        cy = (by1 + by2) // 2
        has_copy = any(kw in text for kw in _COPY_KEYWORDS)
        has_other = any(kw in text for kw in _NON_COPY_ACTIONS)
        candidates.append(dict(
            bbox=bbox, text=text, conf=conf, cx=cx, cy=cy,
            bx1=bx1, by1=by1, bx2=bx2, by2=by2,
            has_copy=has_copy, has_other=has_other,
        ))

    if not candidates:
        return None, None, "", {}

    trace_info: dict[str, Any] = {
        "candidates_count": len(candidates),
        "candidates": [{"text": c["text"], "conf": c["conf"],
                        "cx": c["cx"], "cy": c["cy"],
                        "bx1": c["bx1"], "bx2": c["bx2"]} for c in candidates],
    }

    # Group candidates into action rows by vertical proximity (within 40px)
    candidates.sort(key=lambda c: c["cy"])
    rows: list[list[dict]] = []
    for c in candidates:
        placed = False
        for row in rows:
            avg_y = sum(rc["cy"] for rc in row) / len(row)
            if abs(c["cy"] - avg_y) < 40:
                row.append(c)
                placed = True
                break
        if not placed:
            rows.append([c])

    trace_info["rows_count"] = len(rows)

    # Process rows from bottom to top — action bar is always at the bottom
    # of the result page, so lower rows (higher y) are preferred.
    for row_idx, row in enumerate(reversed(rows)):
        # Sort by x within row
        row.sort(key=lambda c: c["bx1"])
        trace_info[f"row_{row_idx}"] = [c["text"] for c in row]

        # Case A: pure "复制" found separately → use directly
        pure_copies = [c for c in row if c["has_copy"] and not c["has_other"]]
        if pure_copies:
            c = pure_copies[0]
            sx = region_left + c["cx"]
            sy = region_top + c["cy"]
            trace_info["method"] = "ocr_direct"
            trace_info["selected"] = c["text"]
            trace_info["screen_coords"] = (sx, sy)
            return sx, sy, "ocr_direct", trace_info

        # Case B: merged text containing "复制" + other actions
        merged_with_copy = [c for c in row if c["has_copy"] and c["has_other"]]
        if merged_with_copy:
            c = merged_with_copy[0]
            bbox_w = c["bx2"] - c["bx1"]
            # "复制" (2 chars) is the rightmost item among ~12 total chars
            # "新建智能文档" (6) + "发送邮件" (4) + "复制" (2) = 12 chars with spacing
            # Estimate "复制" center at ~88% from left edge of the merged bbox
            frac = 0.88
            est_cx = c["bx1"] + int(bbox_w * frac)
            est_cy = c["cy"]
            # Clamp to region
            est_cx = max(0, min(region_width - 1, est_cx))
            sx = region_left + est_cx
            sy = region_top + est_cy
            trace_info["method"] = "geometry_merged_split"
            trace_info["selected"] = c["text"]
            trace_info["merged_bbox"] = (c["bx1"], c["by1"], c["bx2"], c["by2"])
            trace_info["estimated_fraction"] = frac
            trace_info["screen_coords"] = (sx, sy)
            return sx, sy, "geometry_merged_split", trace_info

        # Case C: only non-copy actions visible → estimate copy to the right
        non_copy_only = [c for c in row if c["has_other"] and not c["has_copy"]]
        if non_copy_only:
            # Use the rightmost detected action
            rightmost = max(non_copy_only, key=lambda c: c["bx2"])
            gap = 16  # spacing between action buttons
            est_copy_half_width = 24  # half of estimated "复制" button width
            est_cx = rightmost["bx2"] + gap + est_copy_half_width
            est_cy = rightmost["cy"]
            # Safety: clamp to region, and limit how far right we estimate
            max_est_x = rightmost["bx2"] + 120  # don't estimate unreasonably far
            est_cx = min(est_cx, max_est_x)
            est_cx = max(0, min(region_width - 1, est_cx))
            sx = region_left + est_cx
            sy = region_top + est_cy
            trace_info["method"] = "geometry_right_estimate"
            trace_info["selected"] = rightmost["text"]
            trace_info["rightmost_bbox"] = (rightmost["bx1"], rightmost["by1"],
                                            rightmost["bx2"], rightmost["by2"])
            trace_info["gap"] = gap
            trace_info["est_copy_half_width"] = est_copy_half_width
            trace_info["screen_coords"] = (sx, sy)
            return sx, sy, "geometry_right_estimate", trace_info

    trace_info["method"] = "no_viable_candidate"
    return None, None, "", trace_info


def _action_copy_result(
    main_hwnd: int,
    window_rect: wintypes.RECT,
    reader: object,
    trace: TraceLogger,
    fingerprint: str,
    max_scrolls: int = 6,
) -> str | None:
    import interception
    import pyperclip
    import time as _time

    width = window_rect.right - window_rect.left
    height = window_rect.bottom - window_rect.top

    t_start = _time.time()

    def _elapsed(since: float | None = None) -> int:
        """Milliseconds elapsed since *since* (or t_start)."""
        return int((_time.time() - (since if since is not None else t_start)) * 1000)

    # Phase 1: Confirm result-page context before copy.
    # Exact on-screen fingerprint match is NOT a hard gate here — OCR may
    # misread 1-2 chars (e.g. PV10 → P10).  Fuzzy fingerprint, privacy
    # notice, and result-action keywords are accepted as context signals.
    # The final clipboard check after copy still requires the EXACT full
    # fingerprint; that is the safety net, not the pre-copy screen OCR.
    def _copy_context_signals(ocr_text: str) -> dict:
        fp_exact = fingerprint in ocr_text if fingerprint else False
        fp_fuzzy, fp_candidate = False, ""
        if not fp_exact and fingerprint:
            _, fp_fuzzy, fp_candidate = _fuzzy_fingerprint_match(ocr_text, fingerprint, max_diff=1)
        return dict(
            fp_exact=fp_exact,
            fp_fuzzy=fp_fuzzy,
            fp_candidate=fp_candidate,
            privacy_notice="结果仅你个人可见" in ocr_text or "仅你个人可见" in ocr_text,
            has_result_actions=any(kw in ocr_text for kw in ["新建智能文档", "发送邮件", "复制"]),
        )

    _verify_foreground_or_fail(main_hwnd, "WeWorkWindow", "copy_fp_check", trace)
    frame = capture_trusted_frame(main_hwnd, window_rect, trace, "before_copy",
                                   region_names=["main_body", "bottom_action_bar"])
    save_frame_artifacts(frame, trace, "before_copy")
    # Use main_body region for OCR (fingerprint, privacy, result actions all live here);
    # avoids expensive full-image dual-engine OCR.
    mb_img = frame.regions.get("main_body", frame.full_image)
    all_text = " ".join(ocr_texts_multi(mb_img, reader, 0.05, fingerprint=fingerprint))
    save_ocr_multi(trace.ocr_path("before_copy"), mb_img, reader, 0.1)
    ctx = _copy_context_signals(all_text)
    result_context_confirmed = ctx["fp_exact"] or ctx["fp_fuzzy"] or ctx["privacy_notice"] or ctx["has_result_actions"]
    trace.log(stage="copy_result", phase="fingerprint_check", **ctx,
              result_context_confirmed=result_context_confirmed)
    trace.log(stage="copy_result", phase="copy_timing",
              step="fingerprint_check", elapsed_ms=_elapsed())

    copy_frame = frame
    copy_frame_source = "before_copy"
    fp_scroll_all_text: str | None = None  # saved from Phase 1 OCR for Phase 2 reuse

    if not result_context_confirmed and fingerprint:
        print("企微：当前视图未检测到本次结果页信号，先在结果区域滚动寻找。")
        for scroll_pass in range(1, max_scrolls + 1):
            ensure_wecom_foreground(main_hwnd)
            # Wheel-only scroll: move to safe area (right side, away from
            # center text/URLs) without clicking to avoid triggering links.
            safe_x = window_rect.left + int(width * 0.85)
            safe_y = window_rect.top + int(height * 0.55)
            interception.move_to(safe_x, safe_y)
            time.sleep(0.1)
            for _ in range(8):
                interception.scroll('down')
            time.sleep(0.5)

            _verify_foreground_or_fail(main_hwnd, "WeWorkWindow", f"fp_scroll_{scroll_pass}", trace)
            scroll_frame = capture_trusted_frame(main_hwnd, window_rect, trace, f"fp_scroll_{scroll_pass}",
                                                  region_names=["main_body", "bottom_action_bar"])
            save_frame_artifacts(scroll_frame, trace, f"fp_scroll_{scroll_pass}")
            scroll_texts = " ".join(ocr_texts_multi(scroll_frame.full_image, reader, 0.05, fingerprint=fingerprint))
            sctx = _copy_context_signals(scroll_texts)
            sctx["pass_num"] = scroll_pass
            sctx["elapsed_ms"] = _elapsed()

            if "智能总结" not in scroll_texts:
                trace.log(stage="copy_result", phase="fp_scroll", **sctx)
                print(f"企微：滚动 {scroll_pass} 次后离开智能总结页，停止搜索。")
                break

            if sctx["fp_exact"] or sctx["fp_fuzzy"] or sctx["privacy_notice"] or sctx["has_result_actions"]:
                result_context_confirmed = True
                copy_frame = scroll_frame
                copy_frame_source = f"fp_scroll_{scroll_pass}"
                fp_scroll_all_text = scroll_texts  # reuse in Phase 2, avoid re-OCR
                trace.log(stage="copy_result", phase="fp_scroll",
                          context_confirmed=True,
                          use_frame=copy_frame_source,
                          **sctx)
                print(f"企微：滚动 {scroll_pass} 次后检测到本次结果页信号"
                      f"（use_frame={copy_frame_source}）。")
                break
            else:
                trace.log(stage="copy_result", phase="fp_scroll", **sctx)

            if scroll_pass > 1:
                try:
                    prev_path = trace.ocr_path(f"fp_scroll_{scroll_pass - 1}")
                    cur_path = trace.ocr_path(f"fp_scroll_{scroll_pass}")
                    if prev_path.exists() and cur_path.exists():
                        if prev_path.read_text(encoding="utf-8") == cur_path.read_text(encoding="utf-8"):
                            print(f"企微：滚动 {scroll_pass} 次后文本无变化，已到底部。")
                            break
                except Exception:
                    pass

        if not result_context_confirmed:
            print(f"企微：在 {max_scrolls} 次滚动后仍未找到本次结果页信号，拒绝点击复制。")
            trace.log(stage="copy_result", phase="context_search_failed", scrolls=max_scrolls)
            return None

    # Phase 2: Result-page context confirmed — locate and click copy.
    # copy_frame is set to the best available frame: fp_scroll_n if Phase 1
    # confirmed context during scroll, otherwise before_copy.
    _verify_foreground_or_fail(main_hwnd, "WeWorkWindow", "copy_ready", trace)
    trace.log(stage="copy_result", phase="copy_search",
              source_frame=copy_frame_source)
    save_frame_artifacts(copy_frame, trace, "copy_ready")

    # Recompute all_text from the current copy_frame for action-row
    # visibility check — copy_frame may be fp_scroll_n if Phase 1
    # updated it, and the original all_text came from before_copy.
    if copy_frame_source != "before_copy":
        if fp_scroll_all_text is not None:
            # Reuse Phase 1 full-image OCR result — same frame, same image.
            all_text = fp_scroll_all_text
            trace.log(stage="copy_result", phase="copy_timing",
                      step="all_text_reuse", elapsed_ms=_elapsed(t_start),
                      source="fp_scroll_ocr")
        else:
            all_text = " ".join(ocr_texts_multi(copy_frame.full_image, reader, 0.05, fingerprint=fingerprint))
            trace.log(stage="copy_result", phase="copy_timing",
                      step="all_text_recompute", elapsed_ms=_elapsed(t_start))

    tm_x, tm_y, tm_conf = template_match(copy_frame.full_image, "copy_1080p_light.png")
    if tm_x is not None:
        sx = window_rect.left + tm_x
        sy = window_rect.top + tm_y
        print(f"企微：模板匹配找到复制按钮 conf={tm_conf:.2f} @ ({sx},{sy})，点击。")
        pyperclip.copy("")
        ensure_wecom_foreground(main_hwnd)
        interception.move_to(sx, sy)
        time.sleep(0.1)
        interception.click(button="left")
        time.sleep(0.6)
        result = pyperclip.paste()
        if result and len(result.strip()) >= 10:
            if fingerprint and fingerprint not in result:
                print(f"企微：警告 — 复制结果中未找到采集指纹 {fingerprint}，可能是旧结果。")
                trace.log(stage="copy_result", method="template", fingerprint_match=False)
                return None
            trace.log(stage="copy_result", method="template", result_len=len(result), fingerprint_match=True)
            return result.strip()
        print("企微：模板复制后剪贴板为空或过短，继续尝试 OCR。")

    trace.log(stage="copy_result", phase="copy_timing",
              step="template_match", elapsed_ms=_elapsed())

    # ---- Combined main_body lower search + action-row geometry ----
    # Single OCR pass on the lower 70% of main_body, reused for:
    #   1) Pure "复制" detection (main_body_ocr legacy path)
    #   2) Action-row geometry estimation (merged-text / adjacent-estimate)
    _COPY_KEYWORDS = ["复制", "拷贝"]
    _NON_COPY_ACTIONS = ["新建智能文档", "发送邮件"]
    _ACTION_SIGNALS = _COPY_KEYWORDS + _NON_COPY_ACTIONS

    mb_left = window_rect.left + int(width * 0.17)
    mb_top = window_rect.top + int(height * 0.10)
    mb_right = window_rect.left + int(width * 0.98)
    mb_bottom = window_rect.top + int(height * 0.85)

    _action_row_visible = any(kw in all_text for kw in _ACTION_SIGNALS)
    lower_results: list[tuple] = []  # reused across strategies

    if "main_body" in copy_frame.regions:
        mb = copy_frame.regions["main_body"]
        mb_h = mb.height
        # Start at 30% — action bar seen as high as 45% in live data
        lower_mb = mb.crop((0, int(mb_h * 0.30), mb.width, mb_h))

        t_mb_ocr = _time.time()
        lower_results = ocr_all_multi(lower_mb, reader, 0.03)
        lower_joined = " ".join([t for _, t, _ in lower_results])
        trace.log(stage="copy_result", phase="main_body_lower_search",
                  lower_texts_preview=lower_joined[:200])
        trace.log(stage="copy_result", phase="copy_timing",
                  step="main_body_lower_ocr", elapsed_ms=_elapsed(t_mb_ocr))

        # Strategy 1: Pure "复制" detection (main_body_ocr legacy path)
        for bbox, text, conf in lower_results:
            has_copy = any(kw in text for kw in _COPY_KEYWORDS)
            has_other = any(kw in text for kw in _NON_COPY_ACTIONS)
            if has_copy and not has_other:
                cx = int((bbox[0][0] + bbox[2][0]) / 2)
                cy = int((bbox[0][1] + bbox[2][1]) / 2)
                sx = mb_left + cx
                sy = mb_top + int(mb_h * 0.30) + cy
                print(f"企微：主内容区 OCR 找到 '{text}' conf={conf:.2f} @ ({sx},{sy})，点击。")
                pyperclip.copy("")
                ensure_wecom_foreground(main_hwnd)
                interception.move_to(sx, sy)
                time.sleep(0.1)
                interception.click(button="left")
                time.sleep(0.6)
                result = pyperclip.paste()
                if result and len(result.strip()) >= 10:
                    if fingerprint and fingerprint not in result:
                        print(f"企微：警告 — 复制结果中未找到采集指纹 {fingerprint}，可能是旧结果。")
                        trace.log(stage="copy_result", method="main_body_ocr", fingerprint_match=False)
                        return None
                    trace.log(stage="copy_result", method="main_body_ocr", result_len=len(result),
                              fingerprint_match=True)
                    return result.strip()

        # Strategy 2: Action-row geometry estimation (reuses lower_results)
        if _action_row_visible:
            est_x, est_y, est_method, est_info = _estimate_copy_from_action_row(
                lower_results, mb_left, mb_top + int(mb_h * 0.30),
                mb.width, mb_h - int(mb_h * 0.30), trace,
            )
            trace.log(stage="copy_result", phase="action_row_geometry",
                      action_row_visible=True, **est_info)
            trace.log(stage="copy_result", phase="copy_timing",
                      step="action_row_geometry", elapsed_ms=_elapsed())
            if est_x is not None and est_y is not None:
                print(f"企微：操作行几何定位 ({est_method}) @ ({est_x},{est_y})，点击。")
                pyperclip.copy("")
                ensure_wecom_foreground(main_hwnd)
                interception.move_to(est_x, est_y)
                time.sleep(0.1)
                interception.click(button="left")
                time.sleep(0.6)
                result = pyperclip.paste()
                if result and len(result.strip()) >= 10:
                    if fingerprint and fingerprint not in result:
                        print(f"企微：警告 — 复制结果中未找到采集指纹 {fingerprint}，可能是旧结果。")
                        trace.log(stage="copy_result", method=est_method, fingerprint_match=False)
                        return None
                    trace.log(stage="copy_result", method=est_method, result_len=len(result),
                              fingerprint_match=True)
                    return result.strip()
                print("企微：几何定位点击后剪贴板为空或过短，继续尝试。")
            else:
                print("企微：操作行信号存在但几何定位未产生有效候选，尝试底部合并区。")
    elif not _action_row_visible:
        trace.log(stage="copy_result", phase="action_row_geometry",
                  action_row_visible=False,
                  reason="no_action_signals_in_current_view")
        print("企微：当前视图未检测到操作区信号，将在滚动中搜索。")
    # ---- Lower combined: bottom 30% of full image ----
    # Action-row may straddle the main_body / bottom_action_bar boundary.
    # Crop the bottom 30% of the full image as a single search area.
    if _action_row_visible:
        from PIL import Image
        t_lc = _time.time()
        combined = copy_frame.full_image.crop((
            0,
            int(copy_frame.full_image.height * 0.70),
            copy_frame.full_image.width,
            copy_frame.full_image.height,
        ))
        combined_results = ocr_all_multi(combined, reader, 0.03)
        combined_text = " ".join([t for _, t, _ in combined_results])
        trace.log(stage="copy_result", phase="copy_timing",
                  step="lower_combined_ocr", elapsed_ms=_elapsed(t_lc))
        if any(kw in combined_text for kw in _ACTION_SIGNALS):
            combined_left = window_rect.left
            combined_top = window_rect.top + int(height * 0.70)
            est_x3, est_y3, est_method3, est_info3 = _estimate_copy_from_action_row(
                combined_results, combined_left, combined_top,
                combined.width, combined.height, trace,
            )
            trace.log(stage="copy_result", phase="action_row_geometry",
                      action_row_visible=True, region="lower_combined", **est_info3)
            if est_x3 is not None and est_y3 is not None:
                print(f"企微：底部合并区几何定位 ({est_method3}) @ ({est_x3},{est_y3})，点击。")
                pyperclip.copy("")
                ensure_wecom_foreground(main_hwnd)
                interception.move_to(est_x3, est_y3)
                time.sleep(0.1)
                interception.click(button="left")
                time.sleep(0.6)
                result = pyperclip.paste()
                if result and len(result.strip()) >= 10:
                    if fingerprint and fingerprint not in result:
                        print(f"企微：警告 — 复制结果中未找到采集指纹 {fingerprint}，可能是旧结果。")
                        trace.log(stage="copy_result", method=est_method3, fingerprint_match=False)
                        return None
                    trace.log(stage="copy_result", method=est_method3, result_len=len(result),
                              fingerprint_match=True)
                    return result.strip()
                print("企微：底部合并区定位点击后剪贴板为空或过短，继续尝试滚动搜索。")

    # ---- Scroll-assisted search ----
    # Each scroll pass saves OCR diagnostics and tries both direct "复制"
    # detection and action-row geometry estimation.  Search is always
    # constrained to the main_body region.
    for scroll_pass in range(max_scrolls + 1):
        if scroll_pass > 0:
            ensure_wecom_foreground(main_hwnd)
            # Wheel-only scroll: move to safe area without clicking.
            safe_x = window_rect.left + int(width * 0.85)
            safe_y = window_rect.top + int(height * 0.55)
            interception.move_to(safe_x, safe_y)
            time.sleep(0.1)
            for _ in range(8):
                interception.scroll('down')
            time.sleep(0.5)
            trace.log(stage="copy_result", phase="scroll",
                      method="wheel_without_click",
                      scroll_pass=scroll_pass,
                      elapsed_ms=_elapsed())

            _verify_foreground_or_fail(main_hwnd, "WeWorkWindow", f"copy_scroll_{scroll_pass}", trace)
            scroll_frame = capture_trusted_frame(main_hwnd, window_rect, trace, f"copy_scroll_{scroll_pass}",
                                                  region_names=["main_body", "bottom_action_bar"])
            save_frame_artifacts(scroll_frame, trace, f"copy_scroll_{scroll_pass}")

        # Always search within main_body region (constrained, not full-window)
        if scroll_pass == 0:
            search_img = copy_frame.regions.get("main_body", copy_frame.full_image)
        else:
            search_img = scroll_frame.regions.get("main_body", scroll_frame.full_image)
        offset_x = int(width * 0.17)
        offset_y = int(height * 0.10)

        # Save OCR diagnostics for this scroll pass
        _verify_foreground_or_fail(main_hwnd, "WeWorkWindow", f"copy_scroll_ocr_{scroll_pass}", trace)
        save_ocr_multi(trace.ocr_path(f"copy_scroll_{scroll_pass}"), search_img, reader, 0.05)

        # Run OCR once per pass and reuse results
        scroll_results = ocr_all_multi(search_img, reader, 0.05)
        scroll_texts = " ".join([t for _, t, _ in scroll_results])
        trace.log(stage="copy_result", phase=f"copy_scroll_{scroll_pass}_ocr",
                  scroll_pass=scroll_pass,
                  ocr_preview=scroll_texts[:200])
        trace.log(stage="copy_result", phase="copy_timing",
                  step=f"copy_scroll_{scroll_pass}_ocr", elapsed_ms=_elapsed())

        # Safety: still in smart summary?
        if scroll_pass > 0 and "智能总结" not in scroll_texts:
            print(f"企微：滚动 {scroll_pass} 次后离开智能总结页，停止。")
            break

        # --- Strategy A: direct "复制" detection (pure, not merged with other actions) ---
        for bbox, text, conf in scroll_results:
            cx = int((bbox[0][0] + bbox[2][0]) / 2)
            cy = int((bbox[0][1] + bbox[2][1]) / 2)
            has_copy = any(kw in text for kw in _COPY_KEYWORDS)
            has_other = any(kw in text for kw in _NON_COPY_ACTIONS)
            if has_copy and not has_other and cy > search_img.height * 0.3:
                sx = window_rect.left + offset_x + cx
                sy = window_rect.top + offset_y + cy
                print(f"企微：OCR 找到 '{text}' conf={conf:.2f} @ ({sx},{sy})，点击。")
                pyperclip.copy("")
                ensure_wecom_foreground(main_hwnd)
                interception.move_to(sx, sy)
                time.sleep(0.1)
                interception.click(button="left")
                time.sleep(0.6)
                result = pyperclip.paste()
                if result and len(result.strip()) >= 10:
                    if fingerprint and fingerprint not in result:
                        print(f"企微：警告 — 复制结果中未找到采集指纹 {fingerprint}，可能是旧结果。")
                        trace.log(stage="copy_result", method="ocr_scroll", scroll_pass=scroll_pass,
                                  fingerprint_match=False)
                        return None
                    trace.log(stage="copy_result", method="ocr_scroll", scroll_pass=scroll_pass,
                              result_len=len(result), fingerprint_match=True)
                    return result.strip()

        # --- Strategy B: action-row geometry estimation ---
        action_visible = any(kw in scroll_texts for kw in _ACTION_SIGNALS)
        if action_visible:
            est_x2, est_y2, est_method2, est_info2 = _estimate_copy_from_action_row(
                scroll_results, window_rect.left + offset_x, window_rect.top + offset_y,
                search_img.width, search_img.height, trace,
            )
            trace.log(stage="copy_result", phase=f"copy_scroll_{scroll_pass}_geometry",
                      **est_info2)
            if est_x2 is not None and est_y2 is not None:
                print(f"企微：滚动 {scroll_pass} 操作行几何定位 ({est_method2}) @ ({est_x2},{est_y2})，点击。")
                pyperclip.copy("")
                ensure_wecom_foreground(main_hwnd)
                interception.move_to(est_x2, est_y2)
                time.sleep(0.1)
                interception.click(button="left")
                time.sleep(0.6)
                result = pyperclip.paste()
                if result and len(result.strip()) >= 10:
                    if fingerprint and fingerprint not in result:
                        print(f"企微：警告 — 复制结果中未找到采集指纹 {fingerprint}，可能是旧结果。")
                        trace.log(stage="copy_result", method=est_method2, scroll_pass=scroll_pass,
                                  fingerprint_match=False)
                        return None
                    trace.log(stage="copy_result", method=est_method2, scroll_pass=scroll_pass,
                              result_len=len(result), fingerprint_match=True)
                    return result.strip()

        # ---- No-change detection: compare OCR between consecutive scrolls ----
        if scroll_pass >= 1:
            try:
                prev_path = trace.ocr_path(f"copy_scroll_{scroll_pass - 1}")
                cur_path = trace.ocr_path(f"copy_scroll_{scroll_pass}")
                if prev_path.exists() and cur_path.exists():
                    prev_text = prev_path.read_text(encoding="utf-8")
                    cur_text = cur_path.read_text(encoding="utf-8")
                    if prev_text == cur_text:
                        print(f"企微：滚动 {scroll_pass} 次后截图/OCR 无变化，"
                              f"判定已到底部或滚动无效，安全停止。")
                        trace.log(stage="copy_result", phase="scroll_no_change",
                                  scroll_pass=scroll_pass, reason="ocr_identical")
                        break
            except Exception:
                pass

    trace.log(stage="copy_result", method="none", error="all_strategies_failed",
              total_elapsed_ms=_elapsed())
    return None


# ---------------------------------------------------------------------------
# Probe-Only Mode
# ---------------------------------------------------------------------------


def _clean_old_artifacts(run_dir: Path) -> None:
    """Remove old screenshots/OCR/trace from an explicit --screenshot-dir before a new run."""
    for sub in ["regions", "ocr"]:
        subdir = run_dir / sub
        if subdir.exists():
            shutil.rmtree(subdir, ignore_errors=True)
    for pattern in ["*.png", "trace.jsonl"]:
        for f in run_dir.glob(pattern):
            f.unlink(missing_ok=True)


def _print_countdown(seconds: int = 3) -> None:
    """Print a short countdown advising the user not to touch mouse/keyboard."""
    print()
    print("=" * 60)
    print("采集期间请不要操作鼠标键盘。")
    print("若需要接管，请等待本轮结束或按 Ctrl+C 中断。")
    print("=" * 60)
    for i in range(seconds, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    print()


def run_probe_only(args: argparse.Namespace) -> int:
    """Read-only diagnostic mode: find window, capture, OCR, classify — no clicks/pastes/copies.

    All screenshots (full + regions) come from a single trusted ImageGrab.grab() call.
    Foreground is verified before AND after the capture.
    """
    require_windows()
    check_automation_dependencies()

    import easyocr

    run_id = generate_run_id()
    run_dir = Path(args.screenshot_dir or f"outputs/wecom_runs/{run_id}")

    # Clean old artifacts when using explicit --screenshot-dir
    if args.screenshot_dir and run_dir.exists():
        _clean_old_artifacts(run_dir)

    run_dir.mkdir(parents=True, exist_ok=True)
    trace = TraceLogger(run_dir)
    fingerprint = generate_fingerprint()
    trace.log(event="probe_start", run_id=run_id, fingerprint=fingerprint,
              screenshot_dir=str(run_dir))

    print(f"企微探针模式：只读诊断，不点击、不粘贴、不复制。")
    print(f"运行 ID：{run_id}")
    print(f"诊断目录：{run_dir}")

    # Init
    print("企微：初始化 OCR（首次加载可能需要几十秒）...")
    reader = easyocr.Reader(["ch_sim", "en"])

    # Find window
    main_hwnd, window_rect, children = find_best_wecom_window()
    if main_hwnd is None or window_rect is None:
        print("企微探针失败：未找到企业微信窗口。")
        trace.log(event="probe_end", error="no_wecom_window")
        return 1

    width = window_rect.right - window_rect.left
    height = window_rect.bottom - window_rect.top
    print(f"企微：找到窗口 0x{main_hwnd:x}，尺寸 {width}x{height}。")
    trace.log(event="window_found", hwnd=f"0x{main_hwnd:x}", width=width, height=height)

    # Initial foreground check
    fg_ok = _foreground_is_wecom(main_hwnd)
    fg_snap = _foreground_snapshot()
    trace.log(event="foreground_check_initial", is_foreground=fg_ok,
              target_hwnd=f"0x{main_hwnd:x}", **fg_snap)
    print(f"企微：{'已是' if fg_ok else '不是'}前台窗口。")

    if not fg_ok:
        print(f"企微探针：企业微信不是前台窗口，当前前台为 class={fg_snap['class']} "
              f"title={fg_snap['title'][:80]}。")
        print("企微探针：自动尝试恢复企业微信前台...")
        trace.log(event="probe_foreground_recovery_start", target_hwnd=f"0x{main_hwnd:x}",
                  attempts=max(4, 1), **fg_snap)

        recovered = ensure_wecom_foreground(main_hwnd, max_attempts=4)
        fg_after = _foreground_snapshot()
        trace.log(event="probe_foreground_recovery_end", recovered=recovered, **fg_after)

        if not recovered:
            print(f"企微探针失败：多次尝试后仍无法将企业微信置于前台。")
            print(f"  当前前台窗口：class={fg_after['class']} title={fg_after['title'][:80]}")
            print(f"  目标企微窗口：0x{main_hwnd:x}")
            print("请关闭可能抢占前台的窗口后重试 --probe-only。")
            print(f"诊断目录：{run_dir}")
            trace.log(event="probe_end", error="foreground_recovery_failed", **fg_after)
            return 1

        print("企微探针：企业微信已成功置前，继续只读诊断。")
        # Re-verify after recovery before proceeding
        if not _foreground_is_wecom(main_hwnd):
            fg_final = _foreground_snapshot()
            print(f"企微探针失败：置前后再次校验失败，前台可能已被其它窗口抢占。")
            print(f"  当前前台：class={fg_final['class']} title={fg_final['title'][:80]}")
            trace.log(event="probe_end", error="foreground_lost_after_recovery", **fg_final)
            return 1

    # Countdown warning
    _print_countdown(3)

    # ---- Single trusted capture: foreground verified before AND after ----
    print("企微：采集可信截图（验证前台 → 截图 → 再次验证前台）...")
    try:
        frame = capture_trusted_frame(main_hwnd, window_rect, trace, "probe")
    except SystemExit:
        # capture_trusted_frame already printed diagnostics
        return 1

    # Save all artifacts from the same frame
    save_frame_artifacts(frame, trace, "probe")

    # Build region OCR summary (from the trusted frame, no new captures)
    region_ocr: dict[str, str] = {}
    for rname in REGION_FRACTIONS:
        if rname in frame.regions:
            try:
                texts = ocr_texts(frame.regions[rname], reader, 0.1)
                region_ocr[rname] = " ".join(texts)
                save_ocr(trace.ocr_path(f"probe-{rname}"), frame.regions[rname], reader, 0.1)
            except Exception as e:
                region_ocr[rname] = f"ERROR: {e}"

    # Classify from the trusted frame (no internal captures in classify_page_structured)
    state = classify_page_structured(frame, reader, trace, "probe", fingerprint)
    trace.log(event="classification", **state)

    # Check for tainted (non-WeCom content detected in OCR)
    if state.get("tainted"):
        print()
        print("=" * 60)
        print("企微探针安全失败：检测到非企业微信内容")
        print("=" * 60)
        print(f"页面状态：{state['state']}（置信度 {state['confidence']}）")
        print(f"拒绝原因：OCR 检测到非企微内容，截图可能被其它窗口遮挡。")
        print("请确保企业微信窗口在最前且无遮挡后重试。")
        print(f"诊断目录：{run_dir}")
        trace.log(event="probe_end", error="tainted_content_detected")
        return 1

    # Check template availability
    tm_status = {}
    for tm_name in ["plus_1080p_light.png", "start_summary_1080p_light.png", "copy_1080p_light.png"]:
        available = template_available(tm_name)
        tm_status[tm_name] = available
        if available:
            tm_x, tm_y, tm_conf = template_match(frame.full_image, tm_name)
            tm_status[f"{tm_name}_match"] = f"({tm_x},{tm_y}) conf={tm_conf:.2f}" if tm_x else f"no_match conf={tm_conf:.2f}"

    trace.log(event="template_status", **tm_status)

    # Summary
    print()
    print("=" * 60)
    print("探针诊断结果")
    print("=" * 60)
    print(f"运行 ID：{run_id}")
    print(f"窗口：0x{main_hwnd:x} ({width}x{height})")
    print(f"采集方式：单次可信截屏 → 裁剪区域（全窗与区域来自同一图像）")
    print(f"页面状态：{state['state']}（置信度 {state['confidence']}）")
    print(f"存在信号：{', '.join(state['signals'])}")
    print(f"缺失信号：{', '.join(state['missing'])}")
    print()
    print("区域 OCR 摘要：")
    for rname, text in region_ocr.items():
        print(f"  [{rname}]: {text[:100]}")
    print()
    print("模板资产状态：")
    for tm_name, available in tm_status.items():
        if tm_name.endswith("_match"):
            continue
        print(f"  {tm_name}: {'可用' if available else '缺失'}")
        match_key = f"{tm_name}_match"
        if match_key in tm_status:
            print(f"    匹配结果: {tm_status[match_key]}")
    print()
    print(f"完整诊断：{run_dir}")
    print(f"  trace.jsonl      — 结构化事件日志（含前后台校验记录）")
    print(f"  probe.png   — 全窗截图（与区域截图同源）")
    print(f"  regions/         — 区域截图（从全窗裁剪）")
    print(f"  ocr/             — OCR 文本")
    print()
    print("提示：如需提取模板资产，请检查 regions/ 目录下的区域截图，")
    print("裁剪目标控件后保存到：")
    print(f"  {TEMPLATE_DIR}")
    print()
    print("probe.png 与 regions/*.png 来自同一次屏幕采集，内容一致。")
    trace.log(event="probe_end", status="success", state=state["state"])
    return 0


# ---------------------------------------------------------------------------
# Full Automation Mode
# ---------------------------------------------------------------------------


def _stage(msg: str) -> None:
    """Print a stage banner for supervised collection progress visibility."""
    print()
    print("-" * 40)
    print(f"  {msg}")
    print("-" * 40)


def run_automation(args: argparse.Namespace) -> str:
    require_windows()
    check_automation_dependencies()

    import easyocr
    import interception

    run_id = generate_run_id()
    fingerprint = generate_fingerprint()
    run_dir = Path(args.screenshot_dir or f"outputs/wecom_runs/{run_id}")

    if args.screenshot_dir and run_dir.exists():
        _clean_old_artifacts(run_dir)

    run_dir.mkdir(parents=True, exist_ok=True)
    trace = TraceLogger(run_dir)

    global_start = time.time()
    global_budget = args.global_budget_seconds

    def _global_ok(stage: str) -> bool:
        elapsed = time.time() - global_start
        if elapsed > global_budget:
            print(f"企微失败 [{stage}]：全局耗时 {elapsed:.0f}s 超过上限 {global_budget}s。")
            trace.log(event="global_timeout", stage=stage, elapsed=elapsed, budget=global_budget)
            return False
        return True

    trace.log(event="automation_start", run_id=run_id, fingerprint=fingerprint,
              period=args.period, global_budget=global_budget)

    # Countdown warning
    _print_countdown(3)

    _stage("阶段 1/6：初始化")

    print(f"运行 ID：{run_id}")
    print(f"采集指纹：{fingerprint}")
    print(f"诊断目录：{run_dir}")

    prompt = load_prompt(args)
    fp_instruction = make_fingerprint_instruction(fingerprint)
    if fingerprint not in prompt:
        prompt = fp_instruction + "\n" + prompt
    trace.log(event="prompt_prepared", prompt_len=len(prompt), has_fingerprint=True)

    print("企微：初始化 Interception 设备。")
    interception.auto_capture_devices()
    print("企微：初始化 OCR（首次加载可能需要几十秒）...")
    reader = easyocr.Reader(["ch_sim", "en"])
    trace.log(event="init_complete")

    # ---- Keep-awake guard ----
    _kw_enabled = False
    if sys.platform == "win32" and kernel32 is not None:
        try:
            _kw_prev = kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
            )
            if _kw_prev == 0:
                trace.log(event="keep_awake", state="enable_failed",
                          reason="SetThreadExecutionState returned 0")
                print("企微：请求保持唤醒失败（SetThreadExecutionState 返回 0），继续采集但不保证防息屏。")
            else:
                _kw_enabled = True
                trace.log(event="keep_awake", state="enabled",
                          flags="ES_CONTINUOUS|ES_SYSTEM_REQUIRED|ES_DISPLAY_REQUIRED",
                          previous_state=f"0x{_kw_prev:x}")
                print("企微：已请求 Windows 保持系统/显示器唤醒（SetThreadExecutionState）。")
        except Exception as _kw_exc:
            trace.log(event="keep_awake", state="enable_failed", error=str(_kw_exc))
            print(f"企微：请求保持唤醒失败（{_kw_exc}），继续采集但不保证防息屏。")

    def _release_keep_awake():
        if _kw_enabled:
            try:
                kernel32.SetThreadExecutionState(ES_CONTINUOUS)
                trace.log(event="keep_awake", state="disabled", flags="ES_CONTINUOUS")
                print("企微：已释放保持唤醒请求，恢复原有电源行为。")
            except Exception as _kw_exc:
                trace.log(event="keep_awake", state="disable_failed", error=str(_kw_exc))
                print(f"企微：释放保持唤醒请求失败（{_kw_exc}），电源行为可能未恢复。")

    atexit.register(_release_keep_awake)

    _stage("阶段 2/6：窗口定位与归一化")

    # ---- Stage 1: Find and normalize window ----
    if not _global_ok("find_window"):
        _save_diagnostics_and_exit("全局超时", "find_window", str(run_dir))

    main_hwnd, window_rect, children = find_best_wecom_window()
    if main_hwnd is None or window_rect is None:
        _save_diagnostics_and_exit("未找到企业微信窗口。", "find_window", str(run_dir))
    trace.log(event="window_found", hwnd=f"0x{main_hwnd:x}")

    if not _global_ok("normalize"):
        _save_diagnostics_and_exit("全局超时", "normalize", str(run_dir))

    print("企微：归一化企业微信窗口...")
    new_rect = normalize_window(main_hwnd)
    if new_rect is not None:
        window_rect = new_rect
    else:
        print("企微：窗口归一化失败，使用当前尺寸继续。")

    trace.log(event="window_normalized",
              width=window_rect.right - window_rect.left,
              height=window_rect.bottom - window_rect.top)

    _, _, children = find_best_wecom_window()
    child_hwnd, child_rect = find_smart_summary_child(children)

    _stage("阶段 3/6：页面状态恢复")

    # ---- Stage 2: State machine loop ----
    if not _global_ok("state_machine"):
        _save_diagnostics_and_exit("全局超时", "state_machine", str(run_dir))

    recovery_cycles = 0
    state_history: list[str] = []

    while True:
        if not _global_ok("state_machine"):
            _save_diagnostics_and_exit("全局超时", "state_machine", str(run_dir))

        # Classify from trusted capture
        _verify_foreground_or_fail(main_hwnd, "WeWorkWindow", f"classify_{recovery_cycles}", trace)
        frame = capture_trusted_frame(main_hwnd, window_rect, trace, f"cycle{recovery_cycles}")
        save_frame_artifacts(frame, trace, f"cycle{recovery_cycles}")

        st = classify_page_structured(frame, reader, trace, f"cycle{recovery_cycles}", fingerprint)
        page_state = st["state"]
        trace.log(event="state_machine_cycle", cycle=recovery_cycles, page_state=page_state, **st)
        print(f"企微：状态机 (循环 {recovery_cycles}) → {page_state} (conf={st['confidence']})")

        if st.get("tainted"):
            _save_diagnostics_and_exit(
                "可信截图检测到非企业微信内容（OCR 出现编辑器/终端文本），可能被其它窗口遮挡。",
                "state_machine",
                str(run_dir),
            )

        if page_state == "summary_input_page":
            print("企微：已确认进入智能总结输入页。")
            break

        if page_state == "summary_unknown_page":
            _save_diagnostics_and_exit(
                f"页面状态为未知智能总结页（置信度 {st['confidence']}），已停止。"
                f"存在信号：{', '.join(st['signals'])}；缺失：{', '.join(st['missing'])}",
                "open_smart_summary",
                str(run_dir),
            )
        if page_state == "terminal_failure":
            _save_diagnostics_and_exit("状态机进入终止失败状态。", "state_machine", str(run_dir))

        state_history.append(page_state)
        if len(state_history) >= CYCLE_MAX_REPEATS:
            recent = state_history[-CYCLE_MAX_REPEATS:]
            if len(set(recent)) == 1:
                _save_diagnostics_and_exit(
                    f"页面状态 {page_state} 连续重复 {CYCLE_MAX_REPEATS} 次，检测到循环。"
                    f"状态序列：{' → '.join(state_history[-6:])}",
                    "state_machine",
                    str(run_dir),
                )

        recovery_cycles += 1
        if recovery_cycles > MAX_RECOVERY_CYCLES:
            _save_diagnostics_and_exit(
                f"恢复循环已执行 {recovery_cycles} 次仍未到达输入页。"
                f"最后状态序列：{' → '.join(state_history[-6:])}",
                "state_machine",
                str(run_dir),
            )

        if page_state == "main_page":
            print(f"企微：当前为主聊天页（恢复第 {recovery_cycles} 次），尝试打开智能总结入口。")
            clear_ocr_cache()
            _action_open_smart_summary_entry(main_hwnd, window_rect, reader, trace)
            main_hwnd, window_rect, children = find_best_wecom_window()
            if main_hwnd is None:
                _save_diagnostics_and_exit("打开入口后未找到企业微信窗口。", "open_entry", str(run_dir))
            child_hwnd, child_rect = find_smart_summary_child(children)
            ensure_wecom_foreground(main_hwnd)
            continue

        elif page_state == "summary_history_page":
            print(f"企微：检测到历史结果页（恢复第 {recovery_cycles} 次），点击 + 新建。")
            clear_ocr_cache()
            result = _action_click_plus(main_hwnd, window_rect, reader, trace)
            if result == "terminal_failure":
                _save_diagnostics_and_exit("历史结果页 + 新建失败，已停止。", "history_to_input", str(run_dir))
            main_hwnd, window_rect, children = find_best_wecom_window()
            if main_hwnd is None:
                _save_diagnostics_and_exit("+ 新建后未找到企业微信窗口。", "history_to_input", str(run_dir))
            child_hwnd, child_rect = find_smart_summary_child(children)
            ensure_wecom_foreground(main_hwnd)
            continue

        elif page_state == "summary_result_page":
            fingerprint_present = "fingerprint_present" in st.get("signals", [])
            if not fingerprint_present:
                print(f"企微：检测到结果页但无本次指纹（恢复第 {recovery_cycles} 次），尝试 + 新建。")
                clear_ocr_cache()
                result = _action_click_plus(main_hwnd, window_rect, reader, trace)
                if result == "terminal_failure":
                    _save_diagnostics_and_exit("结果页 + 新建失败，已停止。", "history_to_input", str(run_dir))
                main_hwnd, window_rect, children = find_best_wecom_window()
                if main_hwnd is None:
                    _save_diagnostics_and_exit("+ 新建后未找到企业微信窗口。", "history_to_input", str(run_dir))
                child_hwnd, child_rect = find_smart_summary_child(children)
                ensure_wecom_foreground(main_hwnd)
                continue
            else:
                print("企微：检测到含本次指纹的结果页，直接进入复制阶段。")
                break

        elif page_state == "summary_generating_page":
            # Without paste+start precondition the "generating" classification
            # is likely a misclassified old history result page.  Do NOT enter
            # the wait loop — try + to reach the real input page instead.
            print(f"企微：检测到疑似生成中页面（恢复第 {recovery_cycles} 次），"
                  f"缺少粘贴/开始点击前置条件，尝试 + 新建。")
            clear_ocr_cache()
            result = _action_click_plus(main_hwnd, window_rect, reader, trace)
            if result == "terminal_failure":
                _save_diagnostics_and_exit(
                    "疑似生成中页面 + 新建失败，已停止。",
                    "generating_to_input",
                    str(run_dir),
                )
            main_hwnd, window_rect, children = find_best_wecom_window()
            if main_hwnd is None:
                _save_diagnostics_and_exit(
                    "+ 新建后未找到企业微信窗口。",
                    "generating_to_input",
                    str(run_dir),
                )
            child_hwnd, child_rect = find_smart_summary_child(children)
            ensure_wecom_foreground(main_hwnd)
            continue

        else:
            _save_diagnostics_and_exit(f"意外页面状态：{page_state}", "state_machine", str(run_dir))

    _stage("阶段 4/6：粘贴提示词与开始总结")

    # ---- Stage 3: Verify and paste ----
    if not _global_ok("paste"):
        _save_diagnostics_and_exit("全局超时", "paste", str(run_dir))

    _verify_foreground_or_fail(main_hwnd, "WeWorkWindow", "pre_paste", trace)
    pre_frame = capture_trusted_frame(main_hwnd, window_rect, trace, "pre_paste")
    save_frame_artifacts(pre_frame, trace, "pre_paste")
    st = classify_page_structured(pre_frame, reader, trace, "pre_paste", fingerprint)

    if st["state"] == "summary_history_page":
        _save_diagnostics_and_exit("当前仍是历史结果页，拒绝粘贴提示词。", "paste_and_start", str(run_dir))

    if st["state"] == "summary_result_page":
        print("企微：检测到含本次指纹的结果页，跳过粘贴，直接复制。")
    elif st["state"] != "summary_input_page":
        _save_diagnostics_and_exit(
            f"粘贴前页面状态为 {st['state']}，非输入页，已停止。",
            "paste_and_start",
            str(run_dir),
        )
    else:
        print(f"企微：粘贴提示词（{len(prompt)} 字符）...")
        clear_ocr_cache()
        fp_visible = _action_paste_prompt(main_hwnd, window_rect, prompt, reader, trace)

        if not fp_visible:
            _save_diagnostics_and_exit(
                f"粘贴后未能在屏幕OCR中检测到采集指纹。"
                f"输入框可能未获得焦点或粘贴未成功。"
                f"请检查企业微信智能总结输入页是否正常显示。",
                "paste_verify_failed",
                str(run_dir),
            )

        if not _global_ok("click_start"):
            _save_diagnostics_and_exit("全局超时", "click_start", str(run_dir))

        print("企微：点击开始总结...")
        clear_ocr_cache()
        clicked = _action_click_start(main_hwnd, window_rect, reader, trace)
        if not clicked:
            _save_diagnostics_and_exit(
                "未找到「开始总结」按钮（模板匹配和OCR均失败）。"
                "可能原因：页面不是智能总结输入页、按钮被遮挡、或OCR未能识别。",
                "start_button_not_found",
                str(run_dir),
            )

    _stage("阶段 5/6：等待智能总结生成")

    # ---- Stage 4: Wait ----
    if not _global_ok("wait"):
        _save_diagnostics_and_exit("全局超时", "wait_generation", str(run_dir))

    print("企微：等待智能总结生成...")
    clear_ocr_cache()
    wait_state = _action_wait_result(
        main_hwnd, window_rect, reader, trace, fingerprint,
        args.max_wait_seconds, args.stable_seconds, args.poll_interval,
        paste_verified=True, start_clicked=True,
    )
    if wait_state not in ("result_detected", "copy_available"):
        if wait_state == "generation_not_triggered":
            extra = (
                "点击后未检测到生成流程启动（输入页结构持续存在、开始总结按钮仍可见）。"
                "可能原因：误点了建议模板卡片（总结团队周报/汇总项目进展/跟踪任务进度/总结聊天内容）"
                "而非「开始总结」按钮，或点击未生效。"
            )
        elif wait_state == "generation_timeout":
            extra = (
                f"等待达到硬上限 {args.max_wait_seconds}s（墙钟时间），"
                f"生成流程已启动但未在时限内完成。"
            )
        else:
            extra = f"等待结束后状态为 {wait_state}。"
        _save_diagnostics_and_exit(
            f"智能总结生成失败：{extra}",
            "wait_generation",
            str(run_dir),
        )

    _stage("阶段 6/6：复制结果与指纹校验")

    # ---- Stage 5: Copy ----
    if not _global_ok("copy"):
        _save_diagnostics_and_exit("全局超时", "copy_result", str(run_dir))

    print("企微：定位并点击复制按钮...")
    clear_ocr_cache()
    result = _action_copy_result(main_hwnd, window_rect, reader, trace, fingerprint)
    if result is None:
        _save_diagnostics_and_exit(
            f"所有复制策略均失败，未能复制本次智能总结结果。采集指纹：{fingerprint}",
            "copy_result",
            str(run_dir),
        )

    if fingerprint not in result:
        print(f"企微：严重警告 — 复制结果中未找到采集指纹 {fingerprint}！可能是旧结果。")
        trace.log(event="fingerprint_verify_failed", fingerprint=fingerprint, result_preview=result[:200])
        _save_diagnostics_and_exit(
            f"复制结果未包含本次采集指纹 {fingerprint}，拒绝保存。",
            "fingerprint_verify",
            str(run_dir),
        )

    print(f"企微：指纹校验通过，结果 {len(result)} 字符。")
    trace.log(event="automation_complete", result_len=len(result), fingerprint_match=True)

    return result


# ---------------------------------------------------------------------------
# Fallback / Support Functions
# ---------------------------------------------------------------------------


def _save_diagnostics_and_exit(reason: str, stage: str, run_dir: str, exit_code: int = 1) -> None:
    print(f"\n企微采集失败 [{stage}]：{reason}")
    print(f"诊断目录：{run_dir}")
    print("建议：改用手动模式（--manual-input）、半自动模式（--semi-manual）或只生成提示词（--prompt-only）。")
    sys.exit(exit_code)


def require_windows() -> None:
    if sys.platform != "win32":
        print("Error: Desktop automation requires Windows.")
        print("Use --manual-input on other platforms.")
        sys.exit(1)


def check_automation_dependencies() -> None:
    missing = []
    for mod in ["interception", "easyocr", "PIL", "pyperclip", "numpy"]:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        print(f"Error: Missing dependencies: {', '.join(missing)}")
        print("Install: pip install -r performance-report-assistant/scripts/requirements-wecom.txt")
        print("The 'interception' module and driver require separate installation.")
        sys.exit(1)


def format_period_for_prompt(period: str) -> str:
    normalized = " ".join((period or "").strip().split())
    if not normalized:
        return ""
    if ".." in normalized:
        start, end = normalized.split("..", 1)
        if start.strip() and end.strip():
            return f"{start.strip()} 至 {end.strip()}"
    return normalized


def load_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        return Path(args.prompt_file).read_text(encoding="utf-8").strip()
    period = format_period_for_prompt(args.period)
    if period:
        return f"总结 {period} 期间{DEFAULT_PROMPT_BODY}"
    return f"总结目标周期内{DEFAULT_PROMPT_BODY}"


def run_prompt_only(args: argparse.Namespace) -> int:
    prompt = load_prompt(args)
    fingerprint = generate_fingerprint()
    fp_instruction = make_fingerprint_instruction(fingerprint)
    full_prompt = fp_instruction + "\n" + prompt

    print("=" * 60)
    print("企业微信智能总结提示词（请复制到企微智能总结输入框）：")
    print("=" * 60)
    print(full_prompt)
    print("=" * 60)
    print()
    print("操作步骤：")
    print("1. 复制上方提示词。")
    print("2. 打开企业微信，进入智能总结界面。")
    print("3. 如果看到历史结果页，先点击左上 + 新建本次总结。")
    print('4. 粘贴提示词，点击"开始总结"。')
    print('5. 等待生成完成后，点击"复制"按钮。')
    print("6. 运行以下命令保存结果：")
    print()
    scenario = args.scenario
    period = args.period
    output = args.output or "outputs/wecom_summary_manual.md"
    output_json = args.output_json or "outputs/wecom_summary_manual.json"
    print(
        f'  "粘贴智能总结结果" | python '
        f'collect_wecom_smart_summary.py --manual-input '
        f'--scenario {scenario} --period "{period}" '
        f'--output {output} --output-json {output_json}'
    )
    print()
    print("或者直接使用半自动模式：")
    print(
        f'  python collect_wecom_smart_summary.py --semi-manual '
        f'--scenario {scenario} --period "{period}" '
        f'--output {output} --output-json {output_json}'
    )
    print()
    return 0


def run_semi_manual(args: argparse.Namespace) -> int:
    prompt = load_prompt(args)
    fingerprint = generate_fingerprint()
    fp_instruction = make_fingerprint_instruction(fingerprint)
    full_prompt = fp_instruction + "\n" + prompt

    print("=" * 60)
    print("【半自动模式】企业微信智能总结采集")
    print("=" * 60)
    print(f"采集指纹：{fingerprint}")
    print()
    print("步骤 1/2：请将以下提示词粘贴到企业微信智能总结输入框：")
    print("-" * 40)
    print(full_prompt)
    print("-" * 40)
    print()
    print("然后在企微中：")
    print("  - 如果看到历史结果页，先点击左上 + 新建本次总结。")
    print('  - 粘贴提示词，点击"开始总结"。')
    print('  - 等待生成完成后，点击"复制"按钮。')
    print()
    print("步骤 2/2：将复制的结果粘贴到下方（按 Ctrl+Z 然后回车结束）：")
    print("-" * 40)

    if not sys.stdin.isatty():
        raw_bytes = sys.stdin.buffer.read()
        if not raw_bytes:
            print()
            print("错误：当前终端不支持交互输入且未提供管道数据。")
            print("请在 cmd.exe 或 PowerShell 中运行此命令，或使用管道传入结果。")
            print("示例：")
            print('  "粘贴结果" | python collect_wecom_smart_summary.py --semi-manual --output outputs/wecom.md')
            return 1
        raw_summary = raw_bytes.decode("utf-8", errors="replace").strip()
    else:
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        raw_summary = "\n".join(lines).strip()

    if not raw_summary:
        print("错误：未提供任何内容，已退出。")
        return 1

    if fingerprint not in raw_summary:
        print(f"警告：粘贴结果中未找到采集指纹 {fingerprint}，请确认是本次生成的结果。")

    collection_method = "semi_manual"
    if args.output:
        write_markdown(args.output, args.scenario, args.period, collection_method, raw_summary, fingerprint)
        print(f"Markdown 已保存：{args.output}")
    else:
        print(raw_summary)

    if args.output_json:
        write_json(args.output_json, args.scenario, args.period, collection_method, raw_summary, fingerprint)
        print(f"JSON 已保存：{args.output_json}")

    print()
    print("半自动采集完成。请人工核实企微智能总结内容是否准确。")
    return 0


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
    output_path: str, scenario: str, period: str,
    collection_method: str, raw_summary: str, fingerprint: str = "",
) -> None:
    collected_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fp_block = f"\n- Fingerprint: {fingerprint}" if fingerprint else ""
    content = f"""# Enterprise WeChat Smart Summary Evidence

- Source: wecom_smart_summary
- Collection method: {collection_method}
- Scenario: {scenario}
- Period: {period}
- Status: needs_user_confirmation
- Collected at: {collected_at}{fp_block}

## Raw Smart Summary

{raw_summary}
"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(content, encoding="utf-8", errors="replace")


def write_json(
    output_path: str, scenario: str, period: str,
    collection_method: str, raw_summary: str, fingerprint: str = "",
) -> None:
    data: dict[str, Any] = {
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
        },
    }
    if fingerprint:
        data["fingerprint"] = fingerprint
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect Enterprise WeChat Smart Summary evidence on Windows.")
    parser.add_argument("--scenario", default="weekly-summary", help="Report scenario tag.")
    parser.add_argument("--period", default="", help="Report period, e.g. '2026-06-22..2026-06-26'.")
    parser.add_argument("--prompt-file", help="Read smart summary prompt from file instead of default.")
    parser.add_argument("--output", help="Output Markdown file path.")
    parser.add_argument("--output-json", help="Output JSON file path.")
    parser.add_argument("--manual-input", action="store_true", help="Manual mode: read from stdin or clipboard.")
    parser.add_argument("--semi-manual", action="store_true",
                        help="Semi-auto mode: print prompt, wait for user to paste result, save output.")
    parser.add_argument("--prompt-only", action="store_true",
                        help="Generate and print the WeCom Smart Summary prompt, then exit (no desktop automation).")
    parser.add_argument("--probe-only", action="store_true",
                        help="Read-only diagnostic mode: capture, OCR, classify; no clicks, pastes, or copies.")
    parser.add_argument("--from-clipboard", action="store_true", help="With --manual-input: read text from clipboard.")
    parser.add_argument("--screenshot-dir", default="",
                        help="Override run directory (default: outputs/wecom_runs/<run-id>).")
    parser.add_argument("--max-wait-seconds", type=int, default=180,
                        help="Hard upper limit for summary generation wait (default 180).")
    parser.add_argument("--stable-seconds", type=int, default=15,
                        help="Seconds of stable result text before attempting copy (default 15).")
    parser.add_argument("--timeout", type=int, default=120,
                        help="Deprecated. Use --max-wait-seconds instead.")
    parser.add_argument("--poll-interval", type=int, default=3,
                        help="Seconds between OCR poll checks (default 3).")
    parser.add_argument("--global-budget-seconds", type=int, default=GLOBAL_BUDGET_SECONDS_DEFAULT,
                        help="Global time budget for the entire automation run (default 300).")
    args = parser.parse_args()

    if args.prompt_only:
        return run_prompt_only(args)

    if args.semi_manual:
        return run_semi_manual(args)

    if args.probe_only:
        return run_probe_only(args)

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
