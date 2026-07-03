"""One-shot helper: extract the + button template from a v4 before_plus screenshot.

Reads before_plus.png, crops the summary_sidebar_header region, and tries to
locate the new-summary + button via multiple image-processing strategies.
Saves the best candidate as plus_1080p_light.png.
"""

import sys
from pathlib import Path
from PIL import Image
import json

USAGE = "python _extract_plus_template.py <before_plus.png> <output_template.png>"

# Region fractions matching collect_wecom_smart_summary.py
REGION_FRACTIONS = {
    "summary_sidebar_header": (0.00, 0.00, 0.17, 0.10),
}


def compute_regions(window_width, window_height):
    regions = {}
    for name, (lx, ly, rx, ry) in REGION_FRACTIONS.items():
        regions[name] = (
            int(window_width * lx),
            int(window_height * ly),
            int(window_width * rx),
            int(window_height * ry),
        )
    return regions


def find_plus_candidates(header_crop_rgb, header_crop_gray):
    """Return list of (x, y, w, h, method, confidence) candidates for the + button."""
    candidates = []

    import numpy as np
    import cv2

    hh, hw = header_crop_gray.shape

    # ---- Strategy 1: binary-threshold + contour hunt for small rect/circle ----
    # The header background is typically dark; the + button is lighter.
    _, thresh = cv2.threshold(header_crop_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Also try inverse in case button is dark-on-light
    for th, label in [(thresh, "otsu"), (255 - thresh, "otsu_inv")]:
        contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            # + button is small: 15–45 px per side, roughly square
            if not (12 <= w <= 50 and 12 <= h <= 50):
                continue
            aspect = w / h if h > 0 else 0
            if not (0.5 <= aspect <= 2.0):
                continue
            # Must be in the right half of the header (left half has title text)
            if x < hw * 0.35:
                continue
            # Prefer square-ish (0.7–1.4)
            sq_score = 1.0 - abs(aspect - 1.0)
            candidates.append((x, y, w, h, f"contour_{label}", sq_score))

    # ---- Strategy 2: Canny edge detection + contour on edges ----
    edges = cv2.Canny(header_crop_gray, 50, 150)
    contours_e, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours_e:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        if not (12 <= w <= 50 and 12 <= h <= 50):
            continue
        aspect = w / h if h > 0 else 0
        if not (0.5 <= aspect <= 2.0):
            continue
        if x < hw * 0.35:
            continue
        sq_score = 1.0 - abs(aspect - 1.0)
        candidates.append((x, y, w, h, "canny_contour", sq_score * 0.8))

    # ---- Strategy 3: Laplacian variance (sharpness) sliding window for icon-like regions ----
    win_size = 36
    best_sharp = 0
    best_sx, best_sy = 0, 0
    for sy in range(0, hh - win_size, 8):
        for sx in range(int(hw * 0.35), hw - win_size, 8):
            patch = header_crop_gray[sy:sy + win_size, sx:sx + win_size]
            lap_var = cv2.Laplacian(patch, cv2.CV_64F).var()
            if lap_var > best_sharp:
                best_sharp = lap_var
                best_sx, best_sy = sx, sy
    if best_sharp > 10:  # reasonable sharpness threshold
        candidates.append((best_sx, best_sy, win_size, win_size, "sharpness", min(best_sharp / 500, 1.0)))

    return candidates


def main():
    if len(sys.argv) != 3:
        print(USAGE)
        sys.exit(1)

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])

    if not src.exists():
        print(f"ERROR: {src} not found")
        sys.exit(1)

    import cv2
    import numpy as np

    img = cv2.imread(str(src))
    if img is None:
        print(f"ERROR: cannot read {src}")
        sys.exit(1)

    h, w = img.shape[:2]
    print(f"Image: {w}x{h}")

    regions = compute_regions(w, h)
    sx1, sy1, sx2, sy2 = regions["summary_sidebar_header"]
    print(f"summary_sidebar_header: ({sx1},{sy1})-({sx2},{sy2})  [{sx2-sx1}x{sy2-sy1}]")

    header = img[sy1:sy2, sx1:sx2]
    header_gray = cv2.cvtColor(header, cv2.COLOR_BGR2GRAY)
    header_rgb = cv2.cvtColor(header, cv2.COLOR_BGR2RGB)

    candidates = find_plus_candidates(header_rgb, header_gray)

    if not candidates:
        print("No + candidates found via image processing.")
        # Save header crop so user can manually inspect
        header_pil = Image.fromarray(header_rgb)
        header_dst = dst.parent / "summary_sidebar_header_v4_crop.png"
        header_pil.save(str(header_dst))
        print(f"Saved header crop for manual inspection: {header_dst}")
        sys.exit(1)

    # Sort by confidence desc and pick best
    candidates.sort(key=lambda c: c[5], reverse=True)
    print(f"\nFound {len(candidates)} candidate(s):")
    for x, y, cw, ch, method, conf in candidates[:10]:
        print(f"  ({x},{y}) {cw}x{ch}  method={method}  conf={conf:.3f}")

    best = candidates[0]
    bx, by, bw, bh, method, conf = best
    cx = bx + bw // 2
    cy = by + bh // 2
    print(f"\nBest: ({bx},{by}) {bw}x{bh} center=({cx},{cy}) method={method}")

    # Extract with some padding
    pad = 4
    x1 = max(bx - pad, 0)
    y1 = max(by - pad, 0)
    x2 = min(bx + bw + pad, header.shape[1])
    y2 = min(by + bh + pad, header.shape[0])

    template = header[y1:y2, x1:x2]
    cv2.imwrite(str(dst), template)
    print(f"\nTemplate saved: {dst}  [{template.shape[1]}x{template.shape[0]}]")

    # Also save header crop for reference
    header_pil = Image.fromarray(header_rgb)
    header_dst = dst.parent / "summary_sidebar_header_v4_crop.png"
    header_pil.save(str(header_dst))
    print(f"Header crop saved: {header_dst}")

    # Print template pixel center relative to header
    print(f"\nTemplate center in header coords: ({cx}, {cy})")
    print(f"Template center in window coords: ({sx1 + cx}, {sy1 + cy})")


if __name__ == "__main__":
    main()
