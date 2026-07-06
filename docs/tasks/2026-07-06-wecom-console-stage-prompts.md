# Task: Improve Console Stage Prompts for Supervised WeCom Collection

## Background

The user considered adding a visual breathing-light overlay during WeCom Smart Summary collection, but an overlay can enter the real screen capture used by OCR/template matching and may interfere with page classification, result waiting, or copy-button detection.

The chosen safer direction is to improve console-stage prompts only. Console output does not enter the WeCom screenshot region and therefore does not affect OCR or template matching.

## User Need

During supervised WeCom collection, the user wants clearer feedback about what the collector is currently doing, without adding any visual overlay on the WeCom window.

## Goal

Improve the CLI/console experience for the supervised `desktop_automation` path by adding clear, consistent stage prompts.

The prompts should help the supervising user understand progress such as:

- pre-run warning / supervision reminder;
- keep-awake status;
- initialization;
- window discovery and normalization;
- page-state recovery;
- prompt paste and fingerprint verification;
- start-summary click;
- waiting for generation;
- copy-result phase;
- final success / failure / manual fallback guidance.

## Scope

In scope:

- Add a small console-stage helper if it fits the current script style.
- Make the supervised automation path easier to follow from the terminal.
- Keep messages concise and human-readable.
- Include stage numbers or clear labels if useful, for example `阶段 3/6`.
- Preserve existing safety warnings and detailed failure messages.
- Keep trace logging behavior unchanged unless adding harmless matching trace events is clearly local and useful.
- Remove or tidy the now-unused `keep_awake()` context manager if it remains unused, since the accepted keep-awake logic now lives inside `run_automation()`.

Out of scope:

- Do not add breathing lights, overlays, GUI windows, tray icons, toasts, or any visible element that may overlap WeCom.
- Do not change OCR, screenshots, template matching, page-state classification, copy strategy, wait-result logic, fingerprint verification, foreground checks, or desktop input behavior.
- Do not change the accepted keep-awake behavior beyond minor console wording or removing dead unused code.
- Do not run full-auto live WeCom tests unless the user is supervising and explicitly authorizes it in the current conversation.

## UX Guidelines

- Prefer stable stage announcements over noisy repeated lines.
- Repeated polling output in the wait phase should remain bounded and useful.
- Avoid printing anything that implies unattended operation.
- Continue to remind the user not to operate mouse/keyboard during supervised collection.
- Failure output should still include stage, reason, run directory, and safe fallback suggestion.

## Suggested Execution Steps

1. Read `AGENTS.md`.
2. Read `docs/status.md` Current Handoff Snapshot.
3. Read `performance-report-assistant/references/wecom-smart-summary-collector.md`.
4. Inspect current console output in `performance-report-assistant/scripts/collect_wecom_smart_summary.py`.
5. Design a small stage-prompt style consistent with the existing Chinese terminal messages.
6. Apply it only to supervised `run_automation()` and nearby failure/success messages.
7. Optionally remove the unused `keep_awake()` context manager if it is still unused.
8. Validate with non-live commands only.

## Verification Requirements

Minimum:

```powershell
python -m py_compile performance-report-assistant/scripts/collect_wecom_smart_summary.py
```

Recommended non-live:

```powershell
python performance-report-assistant/scripts/collect_wecom_smart_summary.py --prompt-only --period "2026-07-01..2026-07-05"
```

If practical, perform a mocked non-live smoke run for the supervised path without interacting with WeCom, but do not run live full-auto automation.

## Acceptance Criteria

- Console output clearly communicates the supervised collection stage.
- No visible overlay or GUI element is introduced.
- No screenshot/OCR/template/copy/fingerprint/page-safety behavior changes are made.
- Existing failure diagnostics remain at least as informative as before.
- Prompt-only, semi-manual, manual-input, and probe-only modes are not made noisier or changed outside their current purpose.
- `py_compile` passes.

## Acceptance Round 1 (2026-07-06)

Result: accepted.

Validated:

- `python -m py_compile performance-report-assistant/scripts/collect_wecom_smart_summary.py` passed.
- `python performance-report-assistant/scripts/collect_wecom_smart_summary.py --prompt-only --period '2026-07-01..2026-07-05'` passed and did not print supervised automation stage banners.
- Mocked non-live supervised failure path printed stage banners for `阶段 1/6：初始化` and `阶段 2/6：窗口定位与归一化`, then stopped at the mocked `find_window` failure without live WeCom interaction.
- Diff review confirmed no overlay, GUI, screenshot, OCR, template matching, page classification, copy strategy, fingerprint verification, or foreground-check logic was changed for this UX task.

Acceptance notes:

- No live full-auto WeCom test was run.
- Existing failure output still includes stage, reason, diagnostic directory, and fallback suggestion.
- The unused `keep_awake()` context manager and `contextlib` import from the earlier keep-awake iteration are no longer present.

## Risk Notes

This is intentionally lower risk than a visual overlay. A console-only change should not affect screen capture, OCR, or template matching, provided it does not add any desktop UI.
