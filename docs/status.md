# Project Status

## Current Handoff Snapshot (2026-06-30)

This is the first section to read after switching Codex / Claude windows.

Current project entry file:

```text
AGENTS.md
```

Do not recreate these files:

```text
CLAUDE.md
AGENT.md
```

User deleted them intentionally because prior usage blurred file responsibilities. Keep `AGENTS.md` as the single root project entry.

Current active execution task for Claude:

```text
none
```

Latest completed Claude/Codex acceptance task:

```text
docs/tasks/fix-wecom-acceptance-regressions.zh-CN.md
```

Codex third-round acceptance passed for the documented follow-up.

Previous acceptance baseline task:

```text
docs/tasks/fix-wecom-safety-copy-timeout-and-doc-cleanup.zh-CN.md
```

Superseded WeCom task documents have been archived under:

```text
docs/archive/tasks/
```

They are historical context only. Do not use archived WeCom tasks as implementation instructions unless the user explicitly asks for history.

Current WeCom automation posture:

- The collector is unstable and must not be described as stable, unattended, cross-platform, or generally compatible with all Enterprise WeChat UI variants.
- Do not add more automation breadth until unsafe fallback behavior is removed.
- Remove any left-side vertical menu scanning or multi-coordinate trial clicking.
- Do not rely on fixed absolute coordinates for Smart Summary entry discovery. Enterprise WeChat windows can be resized freely.
- Smart Summary generation time is variable. Use observable UI/result-state signals plus a hard safety cap, not timeout alone.
- Copying must handle long results, scrollbars, bottom action buttons, and partially visible windows. If the copy button/result page cannot be verified, stop and offer manual input.
- Do not use right-click menu copying, multi-coordinate copy guesses, or unknown-region `Ctrl+A/Ctrl+C` as default fallbacks.

Current Excel open item:

- `fill_excel_template.py` now explicitly handles or rejects `.xlsx`, `.xlsm`, `.xltx`, `.xltm`, and `.xls`.
- Real macro preservation for genuine `.xlsm` / `.xltm` files still requires a real macro workbook check before claiming strong macro-preservation guarantees.

Recommended recovery sequence:

1. Read `AGENTS.md`.
2. Read this `Current Handoff Snapshot`.
3. Read the latest completed acceptance note near the bottom: `Codex Acceptance Review Round 3: Passed for Documented Follow-up`.
4. Use `docs/tasks/fix-wecom-acceptance-regressions.zh-CN.md` and `docs/tasks/fix-wecom-safety-copy-timeout-and-doc-cleanup.zh-CN.md` as history/baseline unless the user explicitly asks for new implementation.
5. If implementing, update code only after confirming with the user or after the user explicitly assigns implementation to Codex. By default, Codex writes/maintains task documents and validates Claude output.

## Current Understanding

This repository contains the `performance-report-assistant` Claude Code / Codex skill. The skill helps Chinese workplace users turn weekly reports, git commits, work notes, and fixed templates into polished work reports while preserving the user's original template format whenever possible.

The core workflow is:

1. Interview the user step by step.
2. Confirm report type, audience, date range, template situation, output location, and evidence sources.
3. Inspect fixed templates before editing.
4. Show exact planned changes and wait for explicit user confirmation.
5. Fill a copied template, not the original file.
6. Summarize inputs, assumptions, repository metrics, filled fields, output path, and remaining evidence gaps.

## Files Reviewed

- `README.md`
- `README.zh-CN.md`
- `claude-code-skill-build-plan.md`
- `performance-report-assistant/SKILL.md`
- `performance-report-assistant/agents/openai.yaml`
- `performance-report-assistant/references/intake-questions.md`
- `performance-report-assistant/references/report-patterns.md`
- `performance-report-assistant/references/template-workflow.md`
- `performance-report-assistant/references/excel-template-workflow.md`
- `performance-report-assistant/scripts/collect_git_commits.py`
- `performance-report-assistant/scripts/fill_excel_template.py`
- `performance-report-assistant/scripts/resolve_report_period.py`

## Validation Results (2026-06-29)

- `python scripts/collect_git_commits.py --help` — passed.
- `python scripts/fill_excel_template.py --help` — passed.
- `python scripts/resolve_report_period.py --help` — passed.

## Documentation Sync Completed

- `README.md` and `README.zh-CN.md`: repository structure block updated to include `template-workflow.md` and `resolve_report_period.py`; script description section added for `resolve_report_period.py`.
- `claude-code-skill-build-plan.md`: "Current Status Notes" section added, preserving original plan as historical context.

## Earlier Open Items From Initial Sync

- Excel sample fill validation has not yet been recorded. Should be run before publishing or handoff.
- At that time, no skill behavior, reference workflow, script code, or agent config had been changed. Later sections record subsequent behavior and script updates.

## Date Boundary Fix Validation (2026-06-29)

- Claude updated `performance-report-assistant/scripts/collect_git_commits.py` to normalize date-only `--since` and `--until` values.
- `YYYY-MM-DD` `--since` values are now expanded to `YYYY-MM-DD 00:00:00`.
- `YYYY-MM-DD` `--until` values are now expanded to `YYYY-MM-DD 23:59:59`.
- Explicit datetime inputs are preserved.
- Codex validated with a temporary git repository:
  - Workweek range `2026-06-29` to `2026-07-03` included Monday morning, Wednesday noon, and Friday evening commits.
  - The same workweek range excluded a Saturday commit.
  - Monthly range `2026-07-01` to `2026-07-31` included a `2026-07-31` evening commit.
  - Explicit datetime range `2026-06-29 10:00:00` to `2026-07-03 17:00:00` preserved the narrower boundary and excluded commits outside that time window.
  - Repository metrics, file touch frequency, author distribution, and daily distribution used the corrected range.

## Reference Report and Repository Intake Fix (2026-06-29)

Claude updated the skill instructions after user testing found workflow issues around old weekly-report references and repository evidence collection.

Completed changes:

- `performance-report-assistant/SKILL.md` now says that when a user explicitly provides an old report as structure/format reference only, the agent must not reuse old work items, repository names, module names, commit counts, or statistics.
- The agent must not ask whether explicitly structure-only old content is current-period work.
- The agent must not infer missing current repositories or modules from old reference content.
- Before running `collect_git_commits.py`, the agent must confirm branch scope with the user: current branch, specified branch, or all branches.
- For personal weekly/performance reports or "my commits", the agent must confirm git author name/email before filtering.
- Before any code-data review or repository scan, the agent must present a confirmation checklist covering date range, repositories, branch scope, author filter, statistics scope, and old-report usage, then wait for an explicit affirmative reply.
- `performance-report-assistant/references/intake-questions.md` now includes guardrail prompts for structure-only old reports, branch confirmation, author confirmation, and pre-execution confirmation.
- `performance-report-assistant/references/report-patterns.md` now states that old weekly reports may provide structure/format only, not old tasks, repository names, module names, or statistics.

User retested this flow and reported no obvious issues.

## Current Open Items

- Excel sample fill validation has not yet been recorded. Should be run before publishing or handoff.
- WeCom Smart Summary automation is currently unstable and must not be presented as a stable/unattended capability.
- Current WeCom collector implementation still contains unsafe or insufficiently verified fallback behavior and should not be live-tested as acceptable until the current task removes/rewrites it.
- The current WeCom repair task is `docs/tasks/fix-wecom-safety-copy-timeout-and-doc-cleanup.zh-CN.md`.
- Archived WeCom handoff tasks under `docs/archive/tasks/` are historical records only. Do not treat older "user must pre-enter Smart Summary", "debug-only screenshots", vertical scanning, or broad fallback copy wording as current behavior.
- `performance-report-assistant/references/wecom-smart-summary-collector.md` is the current operational reference, but it must stay aligned with the new safety task as implementation changes land.
- Excel suffix compatibility remains open: `.xlsx`, `.xlsm`, `.xltx`, `.xltm`, and `.xls` handling must be made explicit.

## New WeCom Foreground Recovery Requirement (2026-06-29)

User clarified the expected foreground behavior after another failed WeCom collection test:

- If the foreground window is not Enterprise WeChat, the collector must not immediately stop.
- It should attempt to bring Enterprise WeChat to the foreground several times.
- Only after repeated foreground recovery attempts fail should it stop.
- If Enterprise WeChat is in the foreground but still on the main chat/list page, this is a recoverable state and should trigger Smart Summary entry scanning, not immediate failure.
- The implementation must distinguish dangerous states from recoverable states:
  - Dangerous: WeCom cannot be found or cannot be foregrounded after retries.
  - Recoverable: WeCom is foregrounded but the Smart Summary input page is not visible yet.
- Historical task document at that time: `docs/tasks/fix-wecom-foreground-recovery-state-machine.zh-CN.md`. This has since been superseded and archived.

## WeCom History Result Page Finding (2026-06-29)

Latest user retest showed progress but still failed:

- Foreground recovery and chat-main-page recovery now appear to be partially effective.
- The collector can enter the Enterprise WeChat Smart Summary application.
- The visible page may default to the most recent historical Smart Summary result if the feature has been used before.
- In that state, the page shows historical summary content and bottom actions such as document/email/copy, not the prompt input page.
- This is not the same as the first-use initialization/template page.
- The collector must classify this as a recoverable `smart_summary_history_result_page`.
- Recovery should click the `+` new-summary button near the top of the Smart Summary conversation list, then wait for and verify a new input page before pasting the prompt.
- The then-current task document `docs/tasks/fix-wecom-foreground-recovery-state-machine.zh-CN.md` was updated with this state and acceptance criteria. This has since been superseded and archived.

## Current WeCom Stability Notice (2026-06-29)

The WeCom Smart Summary collector is not stable yet.

Current agreed posture:

- Do not claim the collector can reliably operate all Enterprise WeChat Smart Summary interfaces.
- Do not claim unattended, cross-platform, or enterprise-grade stability.
- The only supported automated path is the `wecom_uia_probe`-validated template-page flow: Smart Summary template page -> paste prompt -> click "开始总结" -> wait -> copy.
- The safest recovery point is for the user to have Enterprise WeChat open at the target chat/range, preferably already on the Smart Summary template page.
- If automation fails, preserve the failure state, continue other material sources, and offer `--manual-input` or manual paste.
- Any future fix must start from the staged screenshots/OCR saved by the collector, not from speculative UI assumptions.

## WeCom Focus Safety Direct Fix (2026-06-29)

Codex directly updated `performance-report-assistant/scripts/collect_wecom_smart_summary.py` after the user asked not to re-delegate the fix.

Completed changes:

- Strengthened foreground detection so WeCom checks include root windows and process IDs, not only the immediate foreground handle.
- Added stronger focus recovery: standard foreground calls, cross-thread focus fallback, temporary topmost nudge, title-bar click fallback, and a short manual-focus recovery window before failing.
- Added recovery-aware foreground assertions before dangerous actions.
- Re-checked WeCom foreground and Smart Summary visibility before prompt paste.
- Re-checked WeCom foreground before clicking input area, clicking "开始总结", clicking copy, and sending Ctrl+A/Ctrl+C fallback.
- Kept failure behavior conservative: if WeCom cannot be verified as foreground, the script exits instead of sending input to Codex or another window.

Validation run:

- `python -m py_compile performance-report-assistant/scripts/collect_wecom_smart_summary.py` passed.
- `python performance-report-assistant/scripts/collect_wecom_smart_summary.py --help` passed.
- `--manual-input` Markdown/JSON output path test passed, then temporary ignored outputs were removed.

Still requires supervised live WeCom automation retest by the user.

## Superseded WeCom Chat-Style Attempt (2026-06-29)

User retest still failed. Codex inspected the live Enterprise WeChat window and incorrectly generalized the current UI into a chat-style Smart Summary mode.

- The active top-level process was real `WXWork.exe`, not Codex.
- The active child window title/class was `企业微信-智能总结`, meaning the user was already inside the Smart Summary app.
- The visible UI was not the older Smart Summary template page with a "开始总结" button. It was a chat-style Smart Summary interface with a bottom input box and a lower-right send/stop button.
- The previous automation was therefore looking for the wrong UI: it tried to locate a left-side entry or a "开始总结" button even though the current Smart Summary mode required chat-style prompt input.

This direction is now superseded by the probe-baseline reset below:

- Do not treat the chat-style branch as the current behavior.
- Do not keep expanding unverified UI modes inside the main collector.
- The current collector must follow the validated `E:/work/AgentsShare/wecom_uia_probe/stage3_v2.py` path.

Validation run:

- `python -m py_compile performance-report-assistant/scripts/collect_wecom_smart_summary.py` passed.
- `python performance-report-assistant/scripts/collect_wecom_smart_summary.py --help` passed.
- `--manual-input` Markdown/JSON output path test passed, then temporary ignored outputs and `__pycache__` were removed.

This section is historical context only.

## WeCom Probe-Baseline Reset (2026-06-29)

After user feedback, Codex re-read the existing `E:/work/AgentsShare/wecom_uia_probe` project and compared it with the collector implementation.

Confirmed baseline:

- `README.md` states that the validated chain is: open target chat -> locate Smart Summary in the left sidebar -> click Smart Summary -> paste prompt -> click Start Summary -> wait -> copy -> read clipboard.
- `stage3_v2.py` is the successful implementation for the Smart Summary page. It finds the Smart Summary child window, captures the WeCom window, OCRs "开始总结", clicks it, polls for "复制", clicks copy, and reads the clipboard.
- `interception_test.py` validates that Interception is required for reliable paste into WeCom because normal injected input is ignored.
- `stage3_copy.py` contains copy fallbacks.

Root gap in the previous collector:

- Codex over-generalized the implementation instead of migrating the validated probe flow.
- The collector attempted unverified UI modes and broad entry strategies, which made failures harder to diagnose.
- The correct current boundary is not "support every Smart Summary UI"; it is "faithfully execute the already validated probe flow and fail with screenshots/OCR when the visible UI is outside that boundary."

Codex replaced `performance-report-assistant/scripts/collect_wecom_smart_summary.py` automation logic with a probe-aligned staged implementation:

- Keeps manual-input mode and Markdown/JSON outputs.
- Finds an existing Smart Summary child window and resumes from the input/start/copy stages.
- If no Smart Summary child exists, attempts only the validated left-entry OCR/coordinate path around `(31, 499)` scaled to the current window height.
- Verifies the Smart Summary template page before pasting. Required indicators include "智能总结" plus template-page hints such as "开始总结", "输入你想总结", "暂无历史总结", "总结团队周报", or "总结聊天内容".
- Uses Interception to paste the prompt and click.
- Uses OCR to find "开始总结"; falls back to the `stage3_v2.py` bottom-right button estimate.
- Polls for "复制" or "开始总结" disappearing.
- Copies via OCR-located "复制"; falls back to the probe-style select/copy approach.
- Always saves staged screenshots and OCR text under `outputs/wecom_screenshots` for diagnosis.
- Stops instead of guessing if a Smart Summary child exists but the page is not the validated template page.

Validation run:

- `python -m py_compile performance-report-assistant/scripts/collect_wecom_smart_summary.py` passed.
- `python performance-report-assistant/scripts/collect_wecom_smart_summary.py --help` passed.
- `--manual-input` Markdown/JSON output path test passed, then temporary ignored outputs and `__pycache__` were removed.

Still requires supervised live WeCom automation retest by the user.

## WeCom Smart Summary Entry Fix (2026-06-29)

User retest showed WeCom can now be brought to the foreground, but the collector still failed to open the Smart Summary entry by itself.

Codex directly updated `performance-report-assistant/scripts/collect_wecom_smart_summary.py` again:

- Tightened Smart Summary visibility detection so generic "总结" text in chat content no longer counts as being in the Smart Summary UI.
- Added optional UI Automation search for visible controls named/classed "智能总结".
- Kept OCR text matching as the second strategy.
- Added calibrated left-sidebar entry candidates based on earlier successful local probe data around relative coordinate `(31, 499)` in a 1080px-tall WeCom window.
- Every calibrated click is guarded by WeCom foreground checks and followed by Smart Summary UI verification.
- If entry opening is confirmed by OCR but not by a child window title, the script now continues instead of falsely failing.

Validation run:

- `python -m py_compile performance-report-assistant/scripts/collect_wecom_smart_summary.py` passed.
- `python performance-report-assistant/scripts/collect_wecom_smart_summary.py --help` passed.
- `--manual-input` Markdown/JSON output path test passed, then temporary ignored outputs were removed.

Still requires supervised live WeCom automation retest by the user.

## WeCom Collector Documentation Sync (2026-06-29)

Codex updated `performance-report-assistant/references/wecom-smart-summary-collector.md` to match the current implementation:

- The collector is documented as Win32 foreground control + Interception + UI Automation + OCR, not OCR-only.
- The user is no longer required to pre-enter the Smart Summary page; the script tries UIA, OCR, and calibrated left-sidebar candidates before failing safely.
- The document now records the focus-safety rules: no click, paste, copy, or shortcut fallback unless the foreground window is verified as Enterprise WeChat.
- The document now records the Smart Summary visibility gate before prompt paste.
- Debug behavior now states that entry-location and verification screenshots are kept only in `--debug` mode.

## WeCom Entry Retest Failure and Direct Fix (2026-06-29)

User retest still failed after WeCom was successfully foregrounded. The script did not autonomously find the Smart Summary entry and again suggested manual entry selection.

Root cause:

- Entry opening still depended too much on OCR recognizing the exact Smart Summary label or page title.
- The calibrated coordinate fallback was too narrow for different WeCom layouts/scaling.
- Failure diagnostics were weak because non-debug runs removed temporary screenshots, leaving little evidence for the next correction.
- The user-facing failure message still implied the user should manually solve an automation step that the script is supposed to handle.

Codex directly updated `performance-report-assistant/scripts/collect_wecom_smart_summary.py`:

- Added fuzzy OCR matching for Smart Summary entry labels, constrained to the left navigation/sidebar area.
- Strengthened Smart Summary page detection with multiple secondary page-specific indicators instead of requiring one exact OCR phrase.
- Strengthened UI Automation entry search so it can search controls overlapping the WeCom window, not only a single exact native window handle.
- Added deterministic left-rail scanning after UIA/OCR/calibrated coordinates fail. This was later found unsafe in live testing and is superseded by the "WeCom History Page Safety Fix" below.
- Added forced failure artifacts: entry-location failures now save screenshots and OCR text to `outputs/wecom_screenshots` even when `--debug` is not enabled.
- Replaced the old "please manually click Smart Summary" failure wording with a diagnostic message that lists attempted strategies and points to saved artifacts.
- Updated `performance-report-assistant/references/wecom-smart-summary-collector.md` to document the four-layer entry strategy and automatic failure artifacts.

Validation run:

- `python -m py_compile performance-report-assistant/scripts/collect_wecom_smart_summary.py` passed.
- `python performance-report-assistant/scripts/collect_wecom_smart_summary.py --help` passed.
- `--manual-input` Markdown/JSON output path test passed, then temporary ignored outputs and `__pycache__` were removed.

Still requires supervised live WeCom automation retest by the user.

## WeCom History Page Safety Fix (2026-06-29)

User reported that Claude's latest fix was unsafe in live testing:

- When Enterprise WeChat Smart Summary was already on a historical result page, the collector failed to find the `+` new-summary button.
- It then repeatedly switched items in the Enterprise WeChat left-side menu.
- This exposed private information and even navigated into contacts/organization views.

Codex directly fixed the safety boundary in `performance-report-assistant/scripts/collect_wecom_smart_summary.py`:

- Added explicit page classification: `smart_summary_input_page`, `smart_summary_history_result_page`, `smart_summary_unknown_page`, and `main_or_unknown_page`.
- Added `click_new_summary_plus(...)` for the history-result page. It only clicks candidates inside the Smart Summary page header/session pane near the top-left `+`.
- Removed the dangerous left-rail vertical scan that clicked many Enterprise WeChat menu positions.
- Tightened UIA/OCR entry search to exact "智能总结" matches instead of generic "总结".
- Kept only one bounded probe coordinate fallback for opening Smart Summary from the main WeCom page.
- If the current page is a Smart Summary history result, the collector no longer falls back to scanning Enterprise WeChat's left menu.
- If clicking the page-local `+` does not produce a verified input page, the collector stops and saves screenshots/OCR instead of continuing to click.
- Final verification now refuses to paste prompts or copy old results when the page is still a history-result page.

Validation run:

- `python -m py_compile performance-report-assistant/scripts/collect_wecom_smart_summary.py` passed.
- `python performance-report-assistant/scripts/collect_wecom_smart_summary.py --help` passed.
- `--manual-input` Markdown/JSON output path test passed.

Still requires supervised live WeCom automation retest by the user. The critical acceptance point is that no live run should scan or switch through the Enterprise WeChat left-side menu when already inside Smart Summary history results.

## WeCom Prompt Period Wording Fix (2026-06-29)

User caught a wording bug in the WeCom collection flow:

- The report period was correctly resolved from "上周" to `2026-06-22` through `2026-06-26`.
- The subsequent suggested WeCom prompt still used a current-week wording, which contradicted the user's requested period even though the absolute dates were correct.

Codex directly fixed the prompt wording:

- `collect_wecom_smart_summary.py` no longer hardcodes "本周" in the default prompt.
- When `--period` is provided, the default prompt now says `总结 [period] 期间...`.
- `YYYY-MM-DD..YYYY-MM-DD` period strings are normalized to `YYYY-MM-DD 至 YYYY-MM-DD` for Chinese prompt readability.
- Without a known period, the default prompt says "目标周期内" instead of "本周".
- `performance-report-assistant/SKILL.md` now explicitly says WeCom prompts must use absolute dates or neutral "目标周期内" wording after period resolution.
- `performance-report-assistant/references/intake-questions.md` now carries the same guardrail for interview prompts.

Validation run:

- `python -m py_compile performance-report-assistant/scripts/collect_wecom_smart_summary.py` passed.
- Direct `load_prompt(...)` check with `2026-06-22..2026-06-26` produced a prompt using `2026-06-22 至 2026-06-26` and no "本周".
- `--manual-input` Markdown/JSON output path test passed.

## WeCom Prompt Label Consistency Fix (2026-06-29)

User caught a second prompt wording issue:

- The prompt no longer used the old script-level hardcoded phrase, but the agent's conversational suggestion could still combine a current-week label with the resolved previous-week date range.
- Example class of bug: user says "上周", date resolves to `2026-06-22` through `2026-06-26`, but the suggested prompt labels that date range as the current week.

Codex tightened the instructions:

- `performance-report-assistant/SKILL.md` now requires the WeCom prompt's period label to stay semantically consistent with the user's original period request.
- `performance-report-assistant/references/intake-questions.md` now says that if the user said "上周", the suggested prompt should either say `上周（YYYY-MM-DD 至 YYYY-MM-DD）` or only use absolute dates.
- Negative examples containing the wrong wording were removed from active instructions to avoid re-priming the model.
- The historical Claude task document was updated so it no longer presents a fixed current-week default prompt as the implementation target.

## Root Agent Entry File Decision (2026-06-29, updated 2026-06-30)

User retested in another terminal/agent session and still saw the old prompt wording. Root cause:

- The repository only had `AGENT.md`.
- Many tools look for `AGENTS.md` or `CLAUDE.md`, so the other agent session may not have loaded the updated project rules at all.
- Existing agent sessions may also keep old instructions in context and will not hot-reload edited skill files.

Codex previously added or planned multiple root entry files, but user later deleted `CLAUDE.md` and `AGENT.md` because those files were being overused beyond their intended purpose.

Current decision:

- Keep `AGENTS.md` as the single root project entry file.
- Do not recreate `CLAUDE.md`.
- Do not recreate `AGENT.md`.
- New sessions should be explicitly told to read `AGENTS.md` if their tool/runtime does not auto-load it.

Validation:

- Repository search found no active `总结本周` or `本周（` prompt templates after the change.
- Existing sessions must be restarted or explicitly told to read `AGENTS.md` again.

## WeCom Safety Boundary Reset and Documentation Cleanup (2026-06-30)

User clarified several first-principles constraints after the adversarial review:

- Left-side vertical scanning is the wrong approach. Enterprise WeChat windows can be resized freely, so absolute coordinate scanning has high drift risk and can expose or switch to unrelated private content.
- Smart Summary generation duration is not reliably fixed. The collector should use observable UI/result signals plus a hard maximum wait, not a simple timeout-as-completion model.
- Copying is currently under-specified. The copy button may be below the visible area when the window is not fully visible, or below long generated content behind a scrollbar.
- The collector needs cross-validation for basic behavior: CLI, manual mode, period prompt formatting, page classification, and safety boundaries.
- Excel suffix compatibility must be handled explicitly for `.xlsx`, `.xlsm`, `.xltx`, `.xltm`, and `.xls`.
- README and active project docs must describe WeCom as Windows-only, supervised, unstable, and not a general unattended automation capability.

Cleanup performed by Codex:

- Archived superseded WeCom task documents into `docs/archive/tasks/`.
- Added the current execution task:
  - `docs/tasks/fix-wecom-safety-copy-timeout-and-doc-cleanup.zh-CN.md`
- Updated `AGENTS.md` so the current task points to the new task document.
- Kept `CLAUDE.md` and `AGENT.md` absent per user decision.

Current execution priority:

```text
docs/tasks/fix-wecom-safety-copy-timeout-and-doc-cleanup.zh-CN.md
```

Current acceptance posture:

- Do not continue expanding WeCom automation until unsafe fallback behavior is removed.
- Remove left-rail vertical scanning.
- Replace timeout handling with UI/result-state-based waiting plus hard maximum wait.
- Redesign copying around UIA/OCR result-page verification and bounded in-page scrolling.
- Stop safely when copy cannot be verified; offer manual input instead of right-click/fixed-coordinate/Ctrl+A fallback.
- Add Excel suffix compatibility or explicit rejection behavior.

## WeCom Safety Boundary Fix Implementation (2026-06-30)

Claude implemented the full scope of `docs/tasks/fix-wecom-safety-copy-timeout-and-doc-cleanup.zh-CN.md`:

### Code Changes

**`collect_wecom_smart_summary.py`:**
- Removed left-rail vertical scanning (Strategy C in `click_smart_summary_entry`). The probe coordinate (31, 499 scaled) is now only used as a single unstable fallback when UIA and OCR both fail, not as a scan range.
- Replaced fixed-timeout polling with a UI-observable state machine: `submitted → generating → result_detected → copy_available`. Completion is determined by start-button disappearance, result content detection, text stability, and copy-button presence. Added `--max-wait-seconds` (default 180) and `--stable-seconds` (default 15) CLI args. Heartbeat messages during wait.
- Removed unsafe copy strategies: right-click context menu (Strategy C), calibrated coordinate candidates (Strategy D), Ctrl+A/Ctrl+C on unknown regions (Strategy E). Copy now uses only UIA exact match or OCR with bounded in-page scrolling (max 6 scroll passes, each scroll verified to stay on Smart Summary page). Unsafe to copy when page cannot be verified as result page.
- Removed "使用 Ctrl+A / Ctrl+C fallback" from dangerous-action safety list.

**`fill_excel_template.py`:**
- Added `validate_suffixes()` to enforce suffix rules: `.xlsm` template → `.xlsm` output only; `.xltm` template → `.xlsm` output; `.xltx` template → `.xlsx` output.
- Added `load_workbook_safe()` with `keep_vba=True` for macro files.
- `.xls` input and output both rejected with clear user-facing messages.
- Template-only formats (`.xltx`/`.xltm`) copied to target output format with warnings.

### Documentation Changes

- **`README.md` / `README.zh-CN.md`**: Repository structure updated to include `wecom-smart-summary-collector.md`, `collect_wecom_smart_summary.py`, `requirements-wecom.txt`. Limitations expanded with explicit WeCom safety boundaries: Windows-only, supervised, not unattended, no left-menu scanning, no right-click/Ctrl+A fallback. Excel format support matrix added.
- **`wecom-smart-summary-collector.md`**: Removed Ctrl+A/Ctrl+C from dangerous-action safety list. Updated timeout error row in failure table.
- **`docs/archive/tasks/`**: Moved expired tasks `fix-date-range-boundaries.md` and `update-documentation-status-sync.md` out of `docs/tasks/`.
- **`AGENTS.md`**: Already correct; no changes needed.

### Validation

- `python -m py_compile` on both scripts passed.
- `--help` output verified for both scripts.
- `--manual-input` mode verified with piped input.
- `format_period_for_prompt("2026-06-22..2026-06-26")` → "2026-06-22 至 2026-06-26".

### Remaining

- Live WeCom automation retest under user supervision still required.
- Excel `.xlsm` keep_vba behavior requires live test with a real macro file.
- `docs/tasks/fix-wecom-safety-copy-timeout-and-doc-cleanup.zh-CN.md` task document serves as acceptance checklist.

## Codex Acceptance Review: Not Passed (2026-06-30)

Codex reviewed Claude's implementation against `docs/tasks/fix-wecom-safety-copy-timeout-and-doc-cleanup.zh-CN.md`.

Acceptance result: **not passed; follow-up repair required**.

New active follow-up task:

```text
docs/tasks/fix-wecom-acceptance-regressions.zh-CN.md
```

Main findings:

- `copy_result()` can still proceed when the page is classified as `smart_summary_history_result_page`. This violates the hard rule that historical Smart Summary results must not be copied as the current run's evidence.
- `_try_click_plus_loose()` still accepts `smart_summary_unknown_page` and tries multiple calibrated `+` coordinates. Unknown Smart Summary pages should save diagnostics and stop, or continue only after reclassification as a known page state.
- `performance-report-assistant/references/wecom-smart-summary-collector.md` still lists "快捷键复制" as an allowed behavior, which conflicts with the current copy safety boundary.
- Excel suffix validation still allows `.xltx -> .xltx` and `.xltm -> .xltm`, while the task requires template files to output workbook formats (`.xlsx` / `.xlsm`).
- Minimal Excel verification found `.xlsm` / `.xltm` runs returning code 0 while emitting `ValueError: I/O operation on closed file` to stderr. Macro-capable paths need either clean execution or clear rejection.

Validation already run by Codex:

- `python -m py_compile performance-report-assistant\scripts\collect_wecom_smart_summary.py performance-report-assistant\scripts\fill_excel_template.py` passed.
- `python performance-report-assistant\scripts\collect_wecom_smart_summary.py --help` passed.
- `python performance-report-assistant\scripts\fill_excel_template.py --help` passed.
- Manual mode with piped input passed and generated Markdown/JSON output.
- `format_period_for_prompt("2026-06-22..2026-06-26")` returns a string containing Unicode `\u81f3` (`至`).
- `CLAUDE.md` and `AGENT.md` remain absent; `AGENTS.md` exists.
- `docs/tasks/` contains only the active task file before this follow-up was added; archived tasks remain under `docs/archive/tasks/`.

Current execution priority:

```text
docs/tasks/fix-wecom-acceptance-regressions.zh-CN.md
```

Do not run live Enterprise WeChat automation without user supervision.

## Codex Acceptance Review Round 2: Not Passed (2026-06-30)

Codex reviewed Claude's follow-up implementation for:

```text
docs/tasks/fix-wecom-acceptance-regressions.zh-CN.md
```

Acceptance result: **not passed; smaller follow-up required**.

What improved:

- `_try_click_plus_loose()` now refuses `smart_summary_unknown_page` and no longer uses calibrated `+` coordinates.
- `copy_result()` now receives `wait_state` from the generation state machine and rejects copy when the wait state is not `result_detected` or `copy_available`.
- `copy_result()` rejects `smart_summary_unknown_page`, `smart_summary_input_page`, and `main_or_unknown_page` before copying.
- `wecom-smart-summary-collector.md` no longer lists "快捷键复制" as an allowed behavior; it now says only verified "复制" button clicks are allowed.
- Excel suffix rules were tightened: `.xltx -> .xltx` and `.xltm -> .xltm` now reject; `.xltx -> .xlsx` and `.xltm -> .xlsm` are the intended paths.
- Excel macro-capable success paths no longer emit the previous `ValueError: I/O operation on closed file` stderr from the script subprocess.

Remaining findings:

- `click_new_summary_plus()` still allows `smart_summary_unknown_page` in its own guard. Although current callers usually call it after an earlier history-page check, the function can reclassify the page as unknown immediately before clicking and still proceed to OCR `+` clicking. This violates the follow-up task rule that unknown Smart Summary pages must fail safely and must not continue with `+` clicks.
- `fill_excel_template.py` rejection paths still print Python tracebacks before the Chinese user-facing error. The return code is correct and the error text is readable, but the original task requires unsupported formats to produce a readable error rather than a stack trace.

Validation run by Codex:

- `python -m py_compile performance-report-assistant\scripts\collect_wecom_smart_summary.py performance-report-assistant\scripts\fill_excel_template.py` passed.
- `python performance-report-assistant\scripts\collect_wecom_smart_summary.py --help` passed.
- `python performance-report-assistant\scripts\fill_excel_template.py --help` passed.
- Manual mode with piped input passed and generated Markdown/JSON output.
- `format_period_for_prompt("2026-06-22..2026-06-26")` returned `2026-06-22 \u81f3 2026-06-26`.
- Excel matrix:
  - `.xlsx -> .xlsx` passed.
  - `.xlsm -> .xlsm` passed with no subprocess stderr.
  - `.xlsm -> .xlsx` rejected.
  - `.xltx -> .xlsx` passed.
  - `.xltx -> .xltx` rejected.
  - `.xltm -> .xlsm` passed with no subprocess stderr.
  - `.xltm -> .xltm` rejected.
  - `.xls` input/output rejected, but with Python traceback noise.

Required next fixes:

- Change `click_new_summary_plus()` so it accepts only `smart_summary_history_result_page`; if the immediate pre-click classification is `smart_summary_unknown_page`, save diagnostics and stop.
- Wrap `fill_excel_template.py` CLI errors so expected validation failures print concise user-facing messages and exit nonzero without a traceback.

Live Enterprise WeChat automation remains untested and must only be run under user supervision.

## Global Collaboration Rule Update (2026-06-30)

User clarified a global requirement for all future projects:

- Whenever the next step requires Claude execution, Codex must first persist the task, handoff,返工说明, or acceptance result into project documentation.
- After documentation is updated, Codex must generate a directly copyable Claude execution prompt for the user.
- The prompt must instruct Claude to read the project entry file, the current `docs/status.md` snapshot, and the relevant task document.
- The prompt must include the task document path, scope, explicit non-goals, and required validation commands.
- For acceptance failures or follow-up repairs, the prompt must tell Claude to fix only the documented remaining issues and not expand scope.
- For supervised or high-risk actions such as desktop automation, production changes, publishing, deletion, migration, or other user-authorized operations, the prompt must explicitly forbid Claude from running them unsupervised.

This rule has been written to the global Codex instructions at:

```text
C:\Users\Lenovo\.codex\AGENTS.md
```

The same rule has also been added to this project's `AGENTS.md`.

## Codex Acceptance Review Round 3: Passed for Documented Follow-up (2026-06-30)

Codex reviewed Claude's latest follow-up for:

```text
docs/tasks/fix-wecom-acceptance-regressions.zh-CN.md
```

Acceptance result: **passed for the two documented remaining repair points**.

Verified fixes:

- `click_new_summary_plus()` now accepts only `smart_summary_history_result_page` before attempting any `+` click.
- If the immediate pre-click classification is `smart_summary_unknown_page`, `click_new_summary_plus()` saves diagnostics and exits instead of continuing to OCR-find or click `+`.
- `fill_excel_template.py` now handles expected suffix validation failures with concise Chinese user-facing errors and nonzero exit status, without Python traceback output.

Validation run by Codex:

- `python -m py_compile performance-report-assistant\scripts\collect_wecom_smart_summary.py performance-report-assistant\scripts\fill_excel_template.py` passed.
- `python performance-report-assistant\scripts\collect_wecom_smart_summary.py --help` passed.
- `python performance-report-assistant\scripts\fill_excel_template.py --help` passed.
- Manual mode passed:

```powershell
"测试智能总结内容" | python performance-report-assistant\scripts\collect_wecom_smart_summary.py --manual-input --output outputs\wecom_summary_manual_test.md --output-json outputs\wecom_summary_manual_test.json
```

Excel rejection validation passed with no traceback:

- `.xlsm -> .xlsx` rejected with concise Chinese error.
- `.xltx -> .xltx` rejected with concise Chinese error.
- `.xltm -> .xltm` rejected with concise Chinese error.
- `.xls` input rejected with concise Chinese error.
- `.xls` output rejected with concise Chinese error.

Excel success validation passed:

- `.xlsx -> .xlsx`
- `.xlsm -> .xlsm`
- `.xltx -> .xlsx`
- `.xltm -> .xlsm`

Note: the external Codex validation harness emitted a local openpyxl `ZipFile.__del__` gc warning after loading generated `.xlsm` files for inspection. The tested `fill_excel_template.py` subprocesses themselves returned code 0 with no stderr for success paths.

Remaining outside this follow-up:

- Live Enterprise WeChat automation is still untested and must only be run under user supervision.
- Real macro preservation for genuine `.xlsm` / `.xltm` files still requires a real macro workbook check before claiming strong macro-preservation guarantees.
