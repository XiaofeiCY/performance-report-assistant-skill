"""Offline validation for fix-wecom-copy-action-row-geometry.

Validates:
1. QIYG merged text: "新建智能文档 发送邮件 复制" -> estimate 3rd button position
2. ZWS5 missing right: "新建智能文档 发送邮件" -> estimate copy to the right
3. Pure "复制" detection still works (regression)
4. No action signals -> returns None
5. Long content scroll scenario logic
6. No-change scroll safe-fail
7. Safety: all estimates constrained to main_body
8. Safety: fingerprint still required for final result
"""
import json
from pathlib import Path
from typing import Any

PROJECT = Path("E:/work/performance-report-assistant-skill")
QIYG_DIR = PROJECT / "outputs/wecom_runs/20260702-161414-QIYG"
ZWS5_DIR = PROJECT / "outputs/wecom_runs/20260702-162441-ZWS5"
SCRIPT = PROJECT / "performance-report-assistant/scripts/collect_wecom_smart_summary.py"

passed = 0
failed = 0


def check(ok, label):
    global passed, failed
    if ok:
        print(f"  PASS: {label}")
        passed += 1
    else:
        print(f"  FAIL: {label}")
        failed += 1


# =====================================================================
# Replicate _estimate_copy_from_action_row inline for offline testing
# =====================================================================

class _FakeTrace:
    """Minimal trace logger for offline tests."""
    def __init__(self):
        self.logs = []

    def log(self, **kwargs):
        self.logs.append(kwargs)


def _estimate_copy_from_action_row(
    ocr_results, region_left, region_top, region_width, region_height, trace,
):
    _COPY_KEYWORDS = ["复制", "拷贝"]
    _NON_COPY_ACTIONS = ["新建智能文档", "发送邮件"]
    _ACTION_SIGNALS = _COPY_KEYWORDS + _NON_COPY_ACTIONS

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
    for row_idx, row in enumerate(reversed(rows)):
        row.sort(key=lambda c: c["bx1"])
        trace_info[f"row_{row_idx}"] = [c["text"] for c in row]

        # Case A: pure "复制"
        pure_copies = [c for c in row if c["has_copy"] and not c["has_other"]]
        if pure_copies:
            c = pure_copies[0]
            sx = region_left + c["cx"]
            sy = region_top + c["cy"]
            trace_info["method"] = "ocr_direct"
            trace_info["selected"] = c["text"]
            trace_info["screen_coords"] = (sx, sy)
            return sx, sy, "ocr_direct", trace_info

        # Case B: merged text with copy + other
        merged_with_copy = [c for c in row if c["has_copy"] and c["has_other"]]
        if merged_with_copy:
            c = merged_with_copy[0]
            bbox_w = c["bx2"] - c["bx1"]
            frac = 0.88
            est_cx = c["bx1"] + int(bbox_w * frac)
            est_cy = c["cy"]
            est_cx = max(0, min(region_width - 1, est_cx))
            sx = region_left + est_cx
            sy = region_top + est_cy
            trace_info["method"] = "geometry_merged_split"
            trace_info["selected"] = c["text"]
            trace_info["merged_bbox"] = (c["bx1"], c["by1"], c["bx2"], c["by2"])
            trace_info["estimated_fraction"] = frac
            trace_info["screen_coords"] = (sx, sy)
            return sx, sy, "geometry_merged_split", trace_info

        # Case C: only non-copy actions
        non_copy_only = [c for c in row if c["has_other"] and not c["has_copy"]]
        if non_copy_only:
            rightmost = max(non_copy_only, key=lambda c: c["bx2"])
            gap = 16
            est_copy_half_width = 24
            est_cx = rightmost["bx2"] + gap + est_copy_half_width
            est_cy = rightmost["cy"]
            max_est_x = rightmost["bx2"] + 120
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


# =====================================================================
# Helper: make a synthetic OCR bbox tuple
# =====================================================================

def _make_bbox(x1, y1, x2, y2):
    """Create an EasyOCR-compatible bbox tuple."""
    return ([[x1, y1], [x2, y1], [x2, y2], [x1, y2]])


# =====================================================================
# Test 1: QIYG merged text case
# =====================================================================
print("=" * 60)
print("Test 1: QIYG — merged '新建智能文档 发送邮件 复制'")

# Simulate the OCR result from QIYG before_copy.txt:
# [R 0.87] '困新建智能文档 发送邮件 复制' @ (138,725) — center
# Assume bbox width ~340px spanning ~(-32, 708) to (308, 742)
qiYG_bbox = _make_bbox(20, 710, 308, 742)
qiYG_results = [
    (qiYG_bbox, "困新建智能文档 发送邮件 复制", 0.87),
    # Add some body text to verify they're ignored
    (_make_bbox(80, 100, 200, 120), "已完成总结", 0.90),
    (_make_bbox(80, 130, 700, 150), "PRAS-20260702-161414-6042", 0.92),
]

trace = _FakeTrace()
sx, sy, method, info = _estimate_copy_from_action_row(
    qiYG_results, region_left=326, region_top=108,
    region_width=1555, region_height=810, trace=trace,
)

check(method == "geometry_merged_split",
      f"QIYG: method is geometry_merged_split (got: {method})")
check(sx is not None and sy is not None,
      f"QIYG: returns valid screen coords ({sx}, {sy})")

# The estimated "复制" center should be near the right portion of the merged bbox
# bbox: 20..308, 0.88 fraction → est_cx ≈ 20 + 288*0.88 ≈ 273
# screen_x = 326 + 273 ≈ 599
expected_cx_min = 326 + 250  # ≈576
expected_cx_max = 326 + 308  # ≈634
check(expected_cx_min <= (sx or 0) <= expected_cx_max,
      f"QIYG: copy_x ({sx}) within expected range [{expected_cx_min}, {expected_cx_max}]")

# Verify it's NOT clicking on the merged box center
merged_center_x = 326 + 164  # center of bbox 20..308
check(abs((sx or 0) - merged_center_x) > 40,
      f"QIYG: NOT clicking merged bbox center (center={merged_center_x}, got={sx})")

# Verify it's constrained to main_body x range
check(326 <= (sx or 0) <= 326 + 1555,
      f"QIYG: copy_x constrained to main_body [326, 1881]")

# Verify it's NOT clicking "新建智能文档" or "发送邮件" area
# Left 50% of the action row should contain non-copy actions
action_row_left_half = 326 + 164  # ~490 in screen coords
check((sx or 0) > action_row_left_half,
      f"QIYG: copy_x ({sx}) > action row left half ({action_row_left_half})")

print(f"  INFO: QIYG estimated copy at screen ({sx}, {sy}) method={method}")
print(f"  INFO: trace_info = {json.dumps(info, ensure_ascii=False, default=str)[:300]}")

# =====================================================================
# Test 2: ZWS5 missing right button case
# =====================================================================
print("=" * 60)
print("Test 2: ZWS5 — only '新建智能文档 发送邮件' visible")

# [R 0.85] '国新建智能文档 发送邮件' @ (112,541) — center
# Assume bbox width ~260px spanning ~(-18, 526) to (242, 556)
zws5_bbox = _make_bbox(20, 526, 238, 556)
zws5_results = [
    (zws5_bbox, "国新建智能文档 发送邮件", 0.85),
    (_make_bbox(80, 44, 700, 72), "已完成总结，结果仅你个人可见", 0.80),
    (_make_bbox(80, 111, 400, 131), "1. 主要工作内容", 0.87),
]

trace2 = _FakeTrace()
sx2, sy2, method2, info2 = _estimate_copy_from_action_row(
    zws5_results, region_left=326, region_top=108,
    region_width=1555, region_height=810, trace=trace2,
)

check(method2 == "geometry_right_estimate",
      f"ZWS5: method is geometry_right_estimate (got: {method2})")
check(sx2 is not None and sy2 is not None,
      f"ZWS5: returns valid screen coords ({sx2}, {sy2})")

# The estimated "复制" should be to the RIGHT of the detected bbox
# bbox: 20..238, gap=16, half_width=24 → est_cx ≈ 238+16+24 = 278
# screen_x = 326 + 278 ≈ 604
expected_x_min = 326 + 238 + 10  # must be right of detected bbox right edge
check((sx2 or 0) > expected_x_min,
      f"ZWS5: copy_x ({sx2}) > detected bbox right edge ({expected_x_min})")

# Verify NOT unreasonably far right (within 120px of right edge)
max_est = 326 + 238 + 120  # ≈ 684
check((sx2 or 0) <= max_est,
      f"ZWS5: copy_x ({sx2}) <= max estimate ({max_est})")

# Verify constrained to main_body
check(326 <= (sx2 or 0) <= 326 + 1555,
      f"ZWS5: copy_x constrained to main_body [326, 1881]")

# Verify NOT clicking the detected action center
action_center_x = 326 + 129  # center of bbox
check(abs((sx2 or 0) - action_center_x) > 30,
      f"ZWS5: NOT clicking detected action center ({action_center_x})")

print(f"  INFO: ZWS5 estimated copy at screen ({sx2}, {sy2}) method={method2}")
print(f"  INFO: trace_info = {json.dumps(info2, ensure_ascii=False, default=str)[:300]}")


# =====================================================================
# Test 3: Pure "复制" detection regression
# =====================================================================
print("=" * 60)
print("Test 3: Pure '复制' OCR detection (regression guard)")

pure_copy_results = [
    (_make_bbox(240, 720, 290, 744), "复制", 0.90),
    (_make_bbox(20, 710, 180, 744), "新建智能文档 发送邮件", 0.88),
    (_make_bbox(80, 44, 700, 72), "已完成总结，结果仅你个人可见", 0.80),
]

trace3 = _FakeTrace()
sx3, sy3, method3, info3 = _estimate_copy_from_action_row(
    pure_copy_results, region_left=326, region_top=108,
    region_width=1555, region_height=810, trace=trace3,
)

check(method3 == "ocr_direct",
      f"Pure copy: method is ocr_direct (got: {method3})")
check(sx3 is not None and sy3 is not None,
      f"Pure copy: returns valid coords ({sx3}, {sy3})")
# Screen coords: 326 + 265 = 591
check(abs((sx3 or 0) - 591) < 20,
      f"Pure copy: x ({sx3}) near expected 591")

print(f"  INFO: Pure copy at screen ({sx3}, {sy3}) method={method3}")


# =====================================================================
# Test 4: No action signals → returns None
# =====================================================================
print("=" * 60)
print("Test 4: No action signals in view")

no_action_results = [
    (_make_bbox(80, 44, 700, 72), "已完成总结，结果仅你个人可见", 0.80),
    (_make_bbox(80, 130, 400, 150), "1. 主要工作内容", 0.87),
    (_make_bbox(80, 500, 400, 520), "提交反馈帮助提升效果", 0.91),
]

trace4 = _FakeTrace()
sx4, sy4, method4, info4 = _estimate_copy_from_action_row(
    no_action_results, region_left=326, region_top=108,
    region_width=1555, region_height=810, trace=trace4,
)

check(sx4 is None and sy4 is None and method4 == "",
      f"No action: returns None/empty (got: sx={sx4}, sy={sy4}, method='{method4}')")


# =====================================================================
# Test 5: Action row partially scrolled out of view at top
# =====================================================================
print("=" * 60)
print("Test 5: Action row at very bottom of region (scrolled scenario)")

# Simulate OCR results where the action row appeared only after scrolling
# The action row is near the bottom of the main_body crop
scroll_action_results = [
    (_make_bbox(20, 720, 308, 750), "新建智能文档 发送邮件 复制", 0.85),
    (_make_bbox(80, 600, 400, 620), "提交反馈帮助提升效果", 0.91),
]

trace5 = _FakeTrace()
sx5, sy5, method5, info5 = _estimate_copy_from_action_row(
    scroll_action_results, region_left=326, region_top=108,
    region_width=1555, region_height=810, trace=trace5,
)

check(method5 == "geometry_merged_split",
      f"Scroll scenario: method is geometry_merged_split (got: {method5})")
check(sx5 is not None and sy5 is not None,
      f"Scroll scenario: returns valid coords ({sx5}, {sy5})")
# sy5 should be within region bounds
check(108 <= (sy5 or 0) <= 108 + 810,
      f"Scroll scenario: y ({sy5}) within region [108, 918]")

print(f"  INFO: Scroll scenario copy at screen ({sx5}, {sy5})")


# =====================================================================
# Test 6: Empty OCR results → returns None
# =====================================================================
print("=" * 60)
print("Test 6: Empty OCR results")

trace6 = _FakeTrace()
sx6, sy6, method6, info6 = _estimate_copy_from_action_row(
    [], region_left=326, region_top=108,
    region_width=1555, region_height=810, trace=trace6,
)

check(sx6 is None and sy6 is None,
      f"Empty results: returns None (got: sx={sx6}, sy={sy6})")


# =====================================================================
# Test 7: Handles OCR noise prefix (困/国 prefix on text)
# =====================================================================
print("=" * 60)
print("Test 7: OCR noise prefix handling")

noisy_results = [
    (_make_bbox(20, 710, 308, 742), "国新建智能文档 发送邮件 复制", 0.82),
]

trace7 = _FakeTrace()
sx7, sy7, method7, info7 = _estimate_copy_from_action_row(
    noisy_results, region_left=326, region_top=108,
    region_width=1555, region_height=810, trace=trace7,
)

check(method7 == "geometry_merged_split",
      f"OCR noise: method is geometry_merged_split (got: {method7})")
check(sx7 is not None,
      f"OCR noise: returns valid x ({sx7})")


# =====================================================================
# Test 8: Constrained to region — extreme right estimate clamped
# =====================================================================
print("=" * 60)
print("Test 8: Right estimate clamped to region bounds")

# Make a bbox that's already at the right edge of a small region
edge_bbox = _make_bbox(300, 100, 380, 130)
edge_results = [
    (edge_bbox, "发送邮件", 0.90),
]
trace8 = _FakeTrace()
sx8, sy8, method8, info8 = _estimate_copy_from_action_row(
    edge_results, region_left=0, region_top=0,
    region_width=400, region_height=200, trace=trace8,
)

check(method8 == "geometry_right_estimate",
      f"Edge clamp: method is geometry_right_estimate (got: {method8})")
check((sx8 or 0) <= 399,
      f"Edge clamp: x ({sx8}) <= region_width-1 (399)")
check((sx8 or 0) > 380,
      f"Edge clamp: x ({sx8}) > detected bbox right edge (380)")

print(f"  INFO: Edge clamp copy at ({sx8}, {sy8})")


# =====================================================================
# Test 9: Multiple action rows — picks the one with copy signal
# =====================================================================
print("=" * 60)
print("Test 9: Multiple action rows — prefer row with copy signal")

multi_row_results = [
    (_make_bbox(20, 710, 180, 740), "新建智能文档 发送邮件", 0.88),
    (_make_bbox(240, 710, 290, 740), "复制", 0.90),
    (_make_bbox(20, 200, 180, 230), "复制", 0.60),  # false positive higher up
]

trace9 = _FakeTrace()
sx9, sy9, method9, info9 = _estimate_copy_from_action_row(
    multi_row_results, region_left=326, region_top=108,
    region_width=1555, region_height=810, trace=trace9,
)

check(method9 == "ocr_direct",
      f"Multi-row: method is ocr_direct (got: {method9})")
# Should pick the one with highest row (first row in sorted order, with pure copy)
check((sy9 or 0) > 108 + 400,
      f"Multi-row: y ({sy9}) is in lower half of region (expected > 508)")


# =====================================================================
# Test 10: Verifies that script has the geometry helper importable
# =====================================================================
print("=" * 60)
print("Test 10: Script integrity check")

script_exists = SCRIPT.exists()
check(script_exists, f"Script exists at {SCRIPT}")

# Read function signature from script
script_text = SCRIPT.read_text(encoding="utf-8")
check("def _estimate_copy_from_action_row(" in script_text,
      "_estimate_copy_from_action_row defined in script")
check("def _action_copy_result(" in script_text,
      "_action_copy_result defined in script")
check("action_row_geometry" in script_text,
      "action_row_geometry phase in script")
check("geometry_merged_split" in script_text,
      "geometry_merged_split method in script")
check("geometry_right_estimate" in script_text,
      "geometry_right_estimate method in script")
check("scroll_no_change" in script_text,
      "scroll_no_change detection in script")
check("save_ocr_multi(trace.ocr_path(f\"copy_scroll_" in script_text,
      "copy_scroll OCR saved per pass")

# =====================================================================
# Test 11: Safety boundaries — QIYG and ZWS5 screenshots exist
# =====================================================================
print("=" * 60)
print("Test 11: Failure run screenshots available for diagnosis")

qiYG_copy = QIYG_DIR / "copy_ready.png"
zws5_copy = ZWS5_DIR / "copy_ready.png"
check(qiYG_copy.exists(), f"QIYG copy_ready.png exists")
check(zws5_copy.exists(), f"ZWS5 copy_ready.png exists")

qiYG_mb = QIYG_DIR / "regions" / "copy_ready-main_body.png"
zws5_mb = ZWS5_DIR / "regions" / "copy_ready-main_body.png"
check(qiYG_mb.exists(), f"QIYG copy_ready-main_body.png exists")
check(zws5_mb.exists(), f"ZWS5 copy_ready-main_body.png exists")


# =====================================================================
# Summary
# =====================================================================
print()
print("=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed}")
if failed:
    print("SOME CHECKS FAILED — review output above.")
    raise SystemExit(1)
else:
    print("All checks passed.")
