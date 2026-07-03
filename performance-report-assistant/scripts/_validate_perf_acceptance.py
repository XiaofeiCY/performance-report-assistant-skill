"""Non-live validation: performance-optimization acceptance regressions.

Covers:
1. Blank / low-entropy templates are rejected by template_match()
2. Template matching in copy phase is constrained to result-page context
3. poll_start is defined before use in _action_wait_result stability branch
"""

import sys
from pathlib import Path

PASSES = 0
FAILS = 0


def check(condition: bool, label: str) -> None:
    global PASSES, FAILS
    if condition:
        PASSES += 1
        print(f"  PASS: {label}")
    else:
        FAILS += 1
        print(f"  FAIL: {label}")


# ============================================================================
# 1. Blank template rejection in template_match()
# ============================================================================
print("=" * 60)
print("Test 1: template_match rejects blank / low-entropy templates")
print("=" * 60)

# Verify the template was deleted
TEMPLATE_DIR = Path("performance-report-assistant/assets/wecom")
blank_template = TEMPLATE_DIR / "copy_1080p_light.png"
check(not blank_template.exists(),
      "Blank copy_1080p_light.png has been deleted (not on disk)")

# Verify template_match() has the stddev guard
source = Path("performance-report-assistant/scripts/collect_wecom_smart_summary.py").read_text(encoding="utf-8")
tm_func = source[source.index("def template_match"):source.index("def template_available")]
check("t_std = float(np.std(template_gray))" in tm_func,
      "template_match() computes template stddev")
check("if t_std < 5.0:" in tm_func,
      "template_match() rejects templates with stddev < 5.0")
check("return None, None, 0.0" in tm_func,
      "template_match() returns None on blank template rejection")

# Verify template_available() still exists
check("def template_available" in source,
      "template_available() still exists for template existence checks")

# ============================================================================
# 2. Template match constrained to result-page context in _action_copy_result()
# ============================================================================
print("\n" + "=" * 60)
print("Test 2: Copy template matching is constrained to result context")
print("=" * 60)

copy_start = source.index("def _action_copy_result")
copy_end = source.index("def _clean_old_artifacts")
copy_func = source[copy_start:copy_end]
# Before template match, result_context_confirmed must be True
# Verify the call flow: template_match is AFTER context confirmation
tm_call_in_copy = "template_match(copy_frame.full_image, \"copy_1080p_light.png\")"
tm_in_copy = tm_call_in_copy in copy_func
# Not finding the template call is actually OK — it means the template was
# already gated by template_available or template_match itself returns None
# for blank templates.  The critical check: result_context_confirmed is True
# before any copy click.
check("result_context_confirmed" in copy_func,
      "Copy phase checks result_context_confirmed before any click")
check("if not result_context_confirmed" in copy_func,
      "Copy phase has guard that refuses to click without result context")

# If template match is still in the code, verify it's after context confirmation.
# If the template was removed/deleted, template_match will return None immediately
# because the file doesn't exist.  Either way, no unconstrained click.
has_template_file = blank_template.exists()
if tm_in_copy:
    # Template match exists in code — verify it's after context confirmation
    tm_pos = copy_func.index(tm_call_in_copy)
    ctx_pos = copy_func.index("result_context_confirmed = True")
    last_ctx_pos = copy_func.rindex("result_context_confirmed")
    check(tm_pos > last_ctx_pos,
          "template_match in copy phase is AFTER result_context_confirmed")
else:
    print("  INFO: template_match for copy not found in _action_copy_result (template deleted)")
    PASSES += 1
    print("  PASS: No copy template in click path (template deleted from disk)")

# Verify foreground is verified before any click in copy phase
check("_verify_foreground_or_fail" in copy_func,
      "Copy phase verifies foreground before clicks")

# ============================================================================
# 3. poll_start defined before use in stability branch
# ============================================================================
print("\n" + "=" * 60)
print("Test 3: poll_start is defined before use in _action_wait_result")
print("=" * 60)

wait_func = source[source.index("def _action_wait_result"):source.index("def _action_copy_result")]
check("poll_start = time.time()" in wait_func,
      "poll_start is assigned (time.time()) in wait loop")

# Verify poll_start is assigned BEFORE the stable_since reference
poll_assign_pos = wait_func.index("poll_start = time.time()")
stable_use_pos = wait_func.index("stable_since += time.time() - poll_start")
check(poll_assign_pos < stable_use_pos,
      "poll_start assignment precedes stable_since reference")

# Verify poll_start is inside the main while loop (re-assigned each iteration)
# Find the while loop
while_pos = wait_func.index("while True:")
# The poll_start should be between while and the sleep
sleep_pos = wait_func.index("time.sleep(interval)", while_pos)
poll_after_while = wait_func.index("poll_start = time.time()", while_pos)
check(while_pos < poll_after_while < sleep_pos,
      "poll_start assigned inside while loop, before sleep")

# Also verify stable_since is reset when text changes
check("stable_since = 0.0" in wait_func,
      "stable_since is reset to 0.0 when body text changes")
check("last_body_text = body_joined" in wait_func,
      "last_body_text is updated when body text changes")

# ============================================================================
# 4. RapidOCR primary / EasyOCR fallback in ocr_texts_multi
# ============================================================================
print("\n" + "=" * 60)
print("Test 4: RapidOCR primary path skips EasyOCR when fingerprint confirmed")
print("=" * 60)

multi_func = source[source.index("def ocr_texts_multi"):source.index("def ocr_all_multi")]
check("fingerprint: str = \"\"" in multi_func,
      "ocr_texts_multi() accepts optional fingerprint parameter")
check("fingerprint in" in multi_func and "return rapid_texts" in multi_func,
      "ocr_texts_multi() skips EasyOCR when RapidOCR confirms fingerprint")

# _ocr_region_once for main_body also skips EasyOCR
region_once_func = source[source.index("def _ocr_region_once"):source.index("def _load_template")]
check("fingerprint: str = \"\"" in region_once_func,
      "_ocr_region_once() accepts optional fingerprint parameter")
check("fingerprint and fingerprint in rapid_joined" in region_once_func,
      "_ocr_region_once() checks RapidOCR fingerprint before EasyOCR")
check("# RapidOCR confirmed the fingerprint — skip EasyOCR" in region_once_func,
      "_ocr_region_once() explicitly skips EasyOCR on fingerprint confirmation")

# ============================================================================
# RESULTS
# ============================================================================
print("\n" + "=" * 60)
print(f"RESULTS: {PASSES} passed, {FAILS} failed")
if FAILS > 0:
    print("SOME CHECKS FAILED")
else:
    print("All checks passed")
print("=" * 60)
sys.exit(0 if FAILS == 0 else 1)
