"""One-shot helper: extract copy button template from v5 main_body screenshot.

The "新建智能文档 / 发送邮件 / 复制" action bar appears at the bottom of
the result content within main_body.  This script tries to locate it.
"""
import sys
from pathlib import Path
import cv2
import numpy as np

SRC = Path("E:/work/performance-report-assistant-skill/outputs/wecom_runs/test_20260701_v5/regions/wait_177-main_body.png")
DST = Path("E:/work/performance-report-assistant-skill/performance-report-assistant/assets/wecom/copy_1080p_light.png")

if not SRC.exists():
    print(f"ERROR: {SRC} not found")
    sys.exit(1)

img = cv2.imread(str(SRC))
h, w = img.shape[:2]
print(f"main_body: {w}x{h}")

# The action bar is typically at the bottom of the result content.
# For v5, we know the result text ends around y~306 (414 - 108 header offset),
# and main_body is 810px tall.  The action bar should be below the result text,
# near the bottom.

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Strategy: look for horizontal rectangular UI elements in the lower portion
# that could be button bars (action bar with multiple buttons side by side)

# Try to find "复制" via OCR analysis is unlikely to work based on v5 evidence,
# so instead use visual features: the action bar has distinct button shapes.

# Approach: scan the lower half for distinct UI button clusters
# Action buttons are typically light-colored rounded rectangles on a slightly
# darker background bar.

# Look at bottom 40% of main_body
bottom_start = int(h * 0.5)
bottom = gray[bottom_start:, :]
bh, bw = bottom.shape

# Try to find horizontal edges that span significant width (divider line)
edges = cv2.Canny(bottom, 50, 150)
# Sum horizontally to find rows with many edge pixels
row_sums = edges.sum(axis=1)
# Normalize
if row_sums.max() > 0:
    row_sums = row_sums / row_sums.max()

# Find rows with high edge density (potential separator lines)
candidates = []
for y in range(1, len(row_sums) - 1):
    if row_sums[y] > 0.15 and row_sums[y] > row_sums[y-1] * 1.5:
        candidates.append((bottom_start + y, row_sums[y]))

if candidates:
    print("Separator candidates (screen_y, density):")
    for sy, d in candidates[:10]:
        print(f"  y={sy}, density={d:.2f}")

# Also try: find horizontal rectangular contours in bottom portion
_, thresh = cv2.threshold(bottom, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

button_candidates = []
for cnt in contours:
    x, y, cw, ch = cv2.boundingRect(cnt)
    # Buttons are typically wider than tall, moderate size
    if ch < 15 or ch > 80:
        continue
    if cw < 30 or cw > 300:
        continue
    aspect = cw / ch if ch > 0 else 0
    if aspect < 0.8 or aspect > 8:
        continue
    button_candidates.append((x, bottom_start + y, cw, ch, aspect))

# Sort by y (bottom-most first) and group nearby buttons
button_candidates.sort(key=lambda c: c[1], reverse=True)

# Try to find clusters of buttons at similar y (action bar)
if button_candidates:
    # Group by y within 15px
    groups = []
    current_group = [button_candidates[0]]
    for btn in button_candidates[1:]:
        if abs(btn[1] - current_group[-1][1]) < 15:
            current_group.append(btn)
        else:
            if len(current_group) >= 2:
                groups.append(current_group)
            current_group = [btn]
    if len(current_group) >= 2:
        groups.append(current_group)

    if groups:
        print(f"\nFound {len(groups)} button group(s):")
        for gi, group in enumerate(groups[:3]):
            print(f"  Group {gi}: {len(group)} buttons")
            for x, y, cw, ch, aspect in group:
                print(f"    ({x},{y}) {cw}x{ch} aspect={aspect:.1f}")

        # Extract the best group's region as potential action bar
        best_group = groups[0]
        min_x = min(b[0] for b in best_group)
        min_y = min(b[1] for b in best_group)
        max_x = max(b[0] + b[2] for b in best_group)
        max_y = max(b[1] + b[3] for b in best_group)
        pad = 8
        x1 = max(0, min_x - pad)
        y1 = max(0, min_y - pad)
        x2 = min(w, max_x + pad)
        y2 = min(h, max_y + pad)

        # Try to find the "复制" button specifically — usually the rightmost
        # or look for the word in individual button crops
        action_bar = img[y1:y2, x1:x2]
        cv2.imwrite(str(DST.parent / "action_bar_v5_crop.png"), action_bar)
        print(f"\nAction bar crop saved: action_bar_v5_crop.png [{x2-x1}x{y2-y1}]")

        # Also save each individual button as potential copy template
        for i, (bx, by, bw_, bh_, _) in enumerate(best_group):
            btn_crop = img[by-2:by+bh_+2, bx-2:bx+bw_+2]
            name = f"button_{i}_v5.png"
            cv2.imwrite(str(DST.parent / name), btn_crop)
            print(f"  Button {i} saved: {name} [{bw_}x{bh_}]")

# Also save a diagnostic of the bottom 200px where action bar should be
diag = img[max(0, h-200):, :, :]
cv2.imwrite(str(DST.parent / "main_body_bottom_200px.png"), diag)
print(f"\nBottom 200px diagnostic saved: main_body_bottom_200px.png")

# Try to locate text-like regions in the bottom area
# Use MSER or simple thresholding to find text regions
mser = cv2.MSER_create()
regions, _ = mser.detectRegions(bottom)
text_like = []
for region in regions:
    rx, ry, rw, rh = cv2.boundingRect(region)
    if 10 < rh < 50 and 15 < rw < 200 and ry > bh * 0.5:
        text_like.append((rx, bottom_start + ry, rw, rh))
text_like.sort(key=lambda t: t[1])
print(f"\nText-like regions in bottom half: {len(text_like)}")
for rx, ry, rw, rh in text_like[:20]:
    print(f"  ({rx},{ry}) {rw}x{rh}")
