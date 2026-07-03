# WeCom Smart Summary Collector

Enterprise WeChat Windows client Smart Summary collector.

This collector is a user-supervised desktop automation path. Do not describe it as unattended, generally stable across environments, cross-platform, or compatible with all WeCom UI variants.

## Current Status

Latest retained successful current-period run:

```text
outputs/wecom_runs/20260703-110152-77IJ/
```

Fingerprint:

```text
PRAS-20260703-110152-4089
```

Outputs:

```text
outputs/wecom_summary_live_2026-06-29_2026-07-03.md
outputs/wecom_summary_live_2026-06-29_2026-07-03.json
```

Trace result:

```text
automation_complete
fingerprint_match=true
copy method=main_body_ocr
```

The current collector path has completed supervised end-to-end live runs. Geometry fallback for copy action-row positioning is covered by non-live validation, but the latest retained run copied through independent `main_body_ocr`; do not claim that geometry fallback was triggered live in that run.

## Supported Modes

Primary path:

- `desktop_automation`: supervised full-auto collection. User authorizes and supervises; script performs window recovery, Smart Summary entry, new summary creation, prompt paste, start click, result wait, copy, fingerprint verification, and Markdown/JSON save.

Diagnostic / fallback:

- `--probe-only`: read-only diagnostic. It may find, foreground, and normalize the WeCom window, then capture screenshots, OCR regions, classify page state, and write trace output. It must not click business controls, paste, or copy.
- `--prompt-only`: generate prompt and exit.
- `--semi-manual`: user handles WeCom manually.
- `--manual-input`: user provides summary text; script only wraps Markdown/JSON.

Manual, prompt-only, and semi-manual modes are fallback/debug paths, not the recommended main path when the user asks for supervised full-auto collection.

## State Machine

Implemented page states:

- `main_page`: ordinary WeCom chat/workbench/contact page.
- `summary_unknown_page`: Smart Summary context exists but page type is unclear.
- `summary_history_page`: old Smart Summary result is visible.
- `summary_input_page`: new summary input page.
- `summary_generating_page`: generation in progress.
- `summary_result_page`: current generated result page.
- `terminal_failure`: unsafe or unrecoverable state.

Expected flow:

```text
ensure_wecom_foreground
-> capture_and_classify_page
-> main_page: open Smart Summary entry
-> summary_history_page: click trusted + to create current summary
-> summary_input_page: paste prompt and verify fingerprint on screen
-> click start
-> wait until current result evidence appears
-> copy result from verified result page
-> verify clipboard contains exact current fingerprint
-> save Markdown/JSON
```

History result pages are not current evidence. If Smart Summary opens to an old result, the collector must create a new summary with the trusted `+` path before pasting the current prompt.

## Region Model

The collector uses normalized window-relative regions instead of full-window OCR as the main loop:

- `app_sidebar`: Smart Summary entry evidence.
- `summary_sidebar_header`: trusted `+` new-summary button.
- `summary_history_list`: history list evidence.
- `main_header`: content title/header evidence.
- `main_body`: input area, generated result body, and result actions.
- `bottom_action_bar`: supplemental action area.
- `right_scrollbar`: scroll state evidence.

## Fingerprint Rules

Each automatic run generates a unique OCR-friendly fingerprint:

```text
PRAS-YYYYMMDD-HHMMSS-1234
```

Prompt must instruct WeCom to preserve the fingerprint as the first line of the summary. The collector must:

- verify the fingerprint is visible on screen after paste before clicking start;
- use exact/fuzzy/prefix fingerprint evidence plus result context while waiting;
- require the final clipboard text to contain the exact fingerprint before saving.

Do not relax final clipboard verification.

## Copy Rules

Allowed copy strategies after current result context is confirmed:

- real template match if a valid copy template exists;
- constrained OCR inside `main_body` / result action area;
- bounded result-area scrolling;
- action-row geometry fallback for merged or partially missed result actions.

Forbidden copy strategies:

- right-click copy;
- unknown-area `Ctrl+A/Ctrl+C`;
- fixed-coordinate multi-point probing;
- whole-window arbitrary OCR click;
- continuing after foreground leaves WeCom.

Current real `copy_1080p_light.png` template is not required for the retained successful run. If future repeated runs show copy instability, create a narrow task for a real copy template or additional result-action-row hardening.

## Safety Boundaries

Allowed:

- find, foreground, and normalize WeCom window;
- take screenshots and write diagnostics;
- regional OCR;
- OpenCV template matching;
- verified target clicks;
- prompt paste;
- start-summary click;
- bounded result-region scroll;
- verified copy-button click;
- clipboard read and fingerprint verification.

Forbidden:

- read local WeCom databases;
- call or spoof WeCom APIs;
- send, delete, edit, or forward messages;
- handle login, verification codes, or security dialogs;
- continue when WeCom is not foreground;
- click/paste/copy on unknown page state;
- interact with member-selection dialogs;
- left-menu vertical scanning;
- multi-fixed-coordinate probing;
- unknown-area `Ctrl+A/Ctrl+C`;
- right-click copy.

## Diagnostics

Each run writes:

```text
outputs/wecom_runs/<run-id>/
  trace.jsonl
  *.png
  regions/*.png
  ocr/*.txt
```

On failure, report:

- current stage;
- page state and confidence;
- present and missing signals;
- run directory;
- whether retry is safe;
- whether manual input is recommended.

## Live Test Rule

Do not run full-auto WeCom live automation unless the user is supervising and explicitly authorizes it in the current conversation.
