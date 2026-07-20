# WeCom Smart Summary Collector

Enterprise WeChat Windows client Smart Summary collector.

This collector is a user-supervised desktop automation path. Do not describe it as unattended, generally stable across environments, cross-platform, or compatible with all WeCom UI variants.

## Operational Baseline

The collector has completed supervised end-to-end validation, but every future live run still requires fresh user
authorization and active supervision. Preserve these implemented safeguards:

- temporarily request system/display awake during supervised automation and release it on exit;
- print stage progress to the terminal with unbuffered Python (`python -u`); never display an overlay that could enter
  screenshots or affect OCR;
- treat old Smart Summary results and old fingerprints as history only, then use the trusted `+` path to create a new
  current-period summary;
- after current result-page context is confirmed, search the lower combined bottom-of-window action area even when
  `main_body` OCR misses action signals;
- retain `lower_combined_search`, `combined_text_preview`, and `action_signals_found` diagnostics;
- require the exact current fingerprint in the final clipboard text.

## Supported Modes

Primary path:

- `desktop_automation`: supervised full-auto collection. User authorizes and supervises; script performs window
  recovery, Smart Summary entry, new summary creation, prompt paste, start click, result wait, copy, and fingerprint
  verification. The verified result prints to stdout by default; Markdown/JSON files are optional explicit exports.

Diagnostic / fallback:

- `--probe-only`: read-only diagnostic. It may find, foreground, and normalize the WeCom window, then capture screenshots, OCR regions, classify page state, and write trace output. It must not click business controls, paste, or copy. Requires explicit `--screenshot-dir`.
- `--prompt-only`: generate prompt and exit. File-free.
- `--semi-manual`: user handles WeCom manually.
- `--manual-input`: user provides summary text; script only wraps Markdown/JSON.

Manual, prompt-only, and semi-manual modes are fallback/debug paths, not the recommended main path when the user asks for supervised full-auto collection.

## Preview-First Collection (Preferred Evidence Flow)

The preferred flow for collecting WeCom Smart Summary as evidence within a report session does not create persistent Markdown/JSON files:

```bash
python -u scripts/collect_wecom_smart_summary.py --period "YYYY-MM-DD..YYYY-MM-DD"
```

This invocation:

1. Auto-creates a run-specific diagnostic directory under the OS temporary directory (`%TEMP%\wecom_runs\<run-id>\`).
2. Runs the full supervised automation (all safety gates active).
3. Prints the verified result to stdout (no Markdown/JSON file created).
4. On success, cleans the temporary diagnostics directory under the existing guarded cleanup logic.
5. On failure, retains exactly one run-specific diagnostic bundle with `failure_summary.md` under the temp directory and reports its path.

To save persistent Markdown/JSON result files, pass explicit `--output` and `--output-json` with absolute paths:

```bash
python -u scripts/collect_wecom_smart_summary.py --period "YYYY-MM-DD..YYYY-MM-DD" \
  --output E:\confirmed-output\wecom.md \
  --output-json E:\confirmed-output\wecom.json \
  --screenshot-dir E:\confirmed-output\wecom_runs\<run-id>
```

To retain diagnostics on success, pass `--diagnostics-policy keep` with an explicit `--screenshot-dir`:

```bash
python -u scripts/collect_wecom_smart_summary.py --period "YYYY-MM-DD..YYYY-MM-DD" \
  --screenshot-dir E:\confirmed-output\wecom_runs\<run-id> \
  --diagnostics-policy keep
```

Agents must use `python -u` so stage output is visible to the supervising user.

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
-> save Markdown/JSON (only when --output/--output-json provided)
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
- lower combined bottom-of-window OCR and action-row geometry for fixed bottom action bars;
- bounded result-area scrolling;
- action-row geometry fallback for merged or partially missed result actions.

Forbidden copy strategies:

- right-click copy;
- unknown-area `Ctrl+A/Ctrl+C`;
- fixed-coordinate multi-point probing;
- whole-window arbitrary OCR click;
- continuing after foreground leaves WeCom.

Current real `copy_1080p_light.png` template is not required for the accepted path. If future repeated runs show copy instability, first inspect the failed run-specific diagnostics before creating a narrow task for a real copy template or additional result-action-row hardening.

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

## Diagnostics Lifecycle

### Full-Auto Without Explicit --screenshot-dir (Preview/Evidence Flow)

When `--screenshot-dir` is not provided, the script auto-creates a run-specific directory under the OS temporary directory (`%TEMP%\wecom_runs\<run-id>\`).

- **Success**: diagnostics are cleaned automatically under the guarded `_cleanup_run_diagnostics` logic. The empty parent `wecom_runs` directory is also removed if it contains no other runs.
- **Failure**: exactly one run-specific diagnostic directory is retained under `%TEMP%\wecom_runs\<run-id>\` with `trace.jsonl`, screenshots, OCR, region crops, and `failure_summary.md`. The path is printed to stdout.
- No Markdown/JSON result files are created unless `--output`/`--output-json` are explicitly passed.

### Full-Auto With Explicit --screenshot-dir

When an explicit absolute `--screenshot-dir` is provided:

- **`--diagnostics-policy on-failure` (default)**: cleans the run-specific diagnostic directory after successful output save and fingerprint verification. Cleanup is guarded by run-directory identity checks and final-output-file checks; it must not delete final outputs or user files.
- **`--diagnostics-policy keep`**: always retains diagnostics.
- Failed runs always keep diagnostics and write `failure_summary.md` in the run directory.

### Probe-Only

`--probe-only` is diagnostic by nature. It requires an explicit absolute `--screenshot-dir`. Diagnostics may be retained for inspection.

### Cleanup Safety Gates

`_cleanup_run_diagnostics` enforces:

1. Rejects system/root/home/Desktop/Downloads/drive-root paths.
2. Requires directory name matching `YYYYMMDD-HHMMSS-XXXX` run-id pattern, or parent named `wecom_runs` with `trace.jsonl` present.
3. Rejects directories containing final output files (`.md`, `.json`, `.docx`, `.xlsx`, `.pptx`) except allowed diagnostics (`trace.jsonl`, `failure_summary.md`).

Failure diagnostics must not be silently deleted before analysis. Cleanup after failure is a separate, explicitly authorized action.

### Failure Reporting

On failure, report:

- current stage;
- page state and confidence;
- present and missing signals;
- run directory path;
- whether retry is safe;
- whether manual input is recommended.

## Live Test Rule

Do not run full-auto WeCom live automation unless the user is supervising and explicitly authorizes it in the current conversation.
