# Task: Fix WeCom Smart Summary History Page Classification After Entry

## Background

A supervised WeCom Smart Summary collection run failed on 2026-07-06 after the recent keep-awake and console-stage-prompt changes.

Failure run directory:

```text
E:\work\asi-station-mini\outputs\wecom_runs\20260706-152126-MW1F
```

Related probe directory:

```text
E:\work\asi-station-mini\outputs\wecom_runs\20260706-152005-19SA
```

The failure is not caused by the keep-awake guard or console-stage prompts. The trace shows the collector successfully foregrounded and normalized WeCom, then entered the Smart Summary surface, but classified the visible Smart Summary history/result page as `main_page`.

## Evidence

Key trace facts from `20260706-152126-MW1F`:

- `automation_start` fingerprint: `PRAS-20260706-152126-8890`
- keep-awake enabled and later disabled correctly.
- `cycle0` was a normal chat page: `page_state="main_page"`.
- `open_entry method="probe" coords=[31,499]` clicked the Smart Summary rail entry.
- `cycle1.png` visually shows the Smart Summary page:
  - left rail selected `智能总结`;
  - Smart Summary sidebar title `智能总结 AI+`;
  - left history list of old summaries;
  - main pane showing an old retained summary headed by fingerprint `PRAS-20260706-102206-5678`;
  - bottom actions include `新建智能文档`, `发送邮件`, `复制`.
- `cycle1` was still classified as `main_page` with `signals=["no_smart_summary_indicator"]`.
- `cycle2` repeated the same misclassification and the state machine failed after repeated `main_page`.

Likely root cause:

- The current `in_smart_summary` gate treats `"智能总结"` in `app_sidebar` as insufficient unless corroborated by strict body/history signals.
- In this real screenshot, OCR captured `智能总结 AIt` in `app_sidebar`, but sidebar history text was OCR-degraded (`行原样保罂采...`) and did not satisfy `history_list_text.count("总结") >= 2`.
- The body had Smart Summary-specific evidence such as `+添加成员`, old prompt/fingerprint text, and bottom action buttons visually present, but current OCR/region logic did not treat this combination as sufficient to enter Smart Summary classification.
- The old fingerprint is not current evidence; correct behavior is to classify this as `summary_history_page` or old-result page, then click trusted `+` to create a new current summary.

## Goal

Make the collector robustly recognize this real Smart Summary history/result page as a Smart Summary page, without weakening protections against ordinary chat pages.

Expected behavior for the saved `cycle1.png` / `cycle2.png` artifact:

- It must not classify as `main_page`.
- Preferred classification: `summary_history_page`, so the existing flow clicks trusted `+` and creates a new current summary.
- It must not treat the old fingerprint `PRAS-20260706-102206-5678` as current-run evidence.

## Scope

In scope:

- Improve the Smart Summary `in_smart_summary` gate and/or history-page classifier using bounded, corroborated signals.
- Use saved run artifacts for offline/non-live regression validation.
- Add trace signals that explain why a page was classified as Smart Summary history, if locally useful.
- Keep the fix narrow and evidence-driven.

Out of scope:

- Do not change keep-awake behavior.
- Do not change console-stage prompts except if a wording line is directly affected by this fix.
- Do not change OCR engines, screenshot capture mechanics, region capture model, copy strategy, wait-result logic, fingerprint verification, or foreground/page-state safety checks unless strictly necessary for this classifier bug.
- Do not relax final clipboard fingerprint verification.
- Do not run full-auto live WeCom testing unless the user is supervising and explicitly authorizes it in the current conversation.

## Suggested Fix Direction

Consider adding additional corroborated Smart Summary history/result-page signals, such as:

- `智能总结` in `app_sidebar` plus `添加成员` / `+添加成员` in `main_body`;
- old prompt header text such as `请在总结结果...采集标识` or `PRAS-` in `main_header` / `main_body`, treated only as old-result/history evidence, not current result evidence;
- bottom/result action evidence from `新建智能文档`, `发送邮件`, `复制`, when captured in any trusted Smart Summary content/action region;
- visual/OCR evidence from the selected Smart Summary rail entry plus old-summary history list layout, without allowing ordinary chat pages to pass.

Be conservative:

- ordinary chat pages may contain long text and pasted reports, so long body text alone must remain insufficient;
- `智能总结` in the left rail alone must remain insufficient;
- old fingerprints must not bypass current-run fingerprint checks.

## Verification Requirements

Minimum:

```powershell
python -m py_compile performance-report-assistant/scripts/collect_wecom_smart_summary.py
```

Required non-live artifact validation:

- Use saved artifacts from:

```text
E:\work\asi-station-mini\outputs\wecom_runs\20260706-152126-MW1F
```

- Confirm `cycle1.png` or its saved OCR evidence is no longer classified as `main_page`.
- Confirm expected result is `summary_history_page` or an equivalent state that triggers trusted `+` new-summary creation.
- Confirm the old fingerprint `PRAS-20260706-102206-5678` is not treated as current-run evidence for `PRAS-20260706-152126-8890`.

Optional:

- Add a small offline regression helper/test if it fits the project style.

## Acceptance Criteria

- The failed saved Smart Summary history/result screenshot is no longer misclassified as `main_page`.
- Ordinary chat pages like `cycle0.png` remain classified as `main_page`.
- The state machine can proceed from old Smart Summary result/history page toward trusted `+` creation.
- Existing WeCom safety boundaries remain unchanged.
- No live full-auto WeCom test is run without explicit supervised authorization.

## Acceptance Round 1 (2026-07-06)

Result: accepted.

Validated:

- `python -m py_compile performance-report-assistant/scripts/collect_wecom_smart_summary.py` passed.
- `python performance-report-assistant/scripts/collect_wecom_smart_summary.py --prompt-only --period '2026-07-01..2026-07-05'` passed and remained non-live.
- Offline artifact classification against `E:\work\asi-station-mini\outputs\wecom_runs\20260706-152126-MW1F` passed:
  - `cycle0` remains `main_page`.
  - `cycle1` is now `summary_history_page`.
  - `cycle2` is now `summary_history_page`.
- The old fingerprint `PRAS-20260706-102206-5678` is treated as history/header evidence, not current-run result evidence for `PRAS-20260706-152126-8890`.
- A synthetic negative check with ordinary chat text containing `PRAS-...` did not classify as Smart Summary.

Acceptance notes:

- No live full-auto WeCom test was run.
- The code change is scoped to `classify_page_structured()`.
- No keep-awake, console-stage prompt, screenshot capture, OCR engine, copy strategy, wait-result, final fingerprint verification, or foreground safety logic was changed for this task.

## Risk Notes

This bug demonstrates why the collector must not be described as generally stable across all WeCom UI states. The fix should improve this observed UI state without broadly weakening classifier gates.
