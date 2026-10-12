# Project Status

## Current Collaboration Update (2026-10-12)

- The user explicitly assigned this WeCom Smart Summary iteration to Codex for direct implementation; the user will perform acceptance. This overrides the default Claude handoff for this iteration only.
- Current phase: navigation entry implementation and supervised entry-only test accepted by the user on 2026-10-12. The user authorized committing and pushing this iteration to the remote. No full summary collection was performed.
- Per-run live WeCom collection still requires fresh explicit authorization and active user supervision. Implementation authorization alone does not authorize a live collection run.
- Initial code inspection found review candidates: a calibrated fixed entry probe after UIA/OCR failure; proportional input targeting when OCR hints are missing; old diagnostic cleanup when reusing an explicit run directory; stage-boundary rather than continuously enforced global timeout checks.
- Approved scope: replace fixed entry probe with exact visible UIA/OCR label localization, recheck before clicking, verify the destination content page, and stop on missing/ambiguous/changed targets. No changes to generation, copying, input targeting, diagnostic cleanup, or timeout policy.
- Implementation: UIA searches only the selected window and navigation envelope; OCR uses a dedicated navigation crop rather than summary history. OCR labels are re-read before clicking. Destination checks are bounded to three attempts without repeated clicks. Entry failures are propagated to the main state machine.
- Offline navigation validation: 9 tests passed, covering reordered positions, missing/partial/ambiguous labels, foreground changes, label changes, wrong destination, tainted screenshot, and UIA success. Existing copy regression: 43 passed, 0 failed. Python syntax compilation passed.
- Broader preview-first contract validation was attempted but aborted with Windows PermissionError in its sandbox temporary directory; it did not complete and is not counted as passed. Diff whitespace check passed.
- The user subsequently requested direct execution for acceptance of the entry feature. Added `--entry-only` to execute the shared entry action without prompt paste, summary generation, clipboard access, or diagnostic cleanup. No full collection is authorized by this request.
- Live findings and fixes: sandbox execution could not foreground WeCom; execution outside the sandbox could. Corrected the UIA traversal call to `WalkControl(maxDepth=6)` after inspecting the installed API. EasyOCR missed small navigation labels; a saved-image check confirmed RapidOCR recognition, so navigation OCR now enlarges labels 3x, prioritizes RapidOCR, and converts coordinates back to original pixels.
- Updated navigation regression after live fixes: 10 tests passed, including enlarged-image coordinate conversion. Diff whitespace check passed.
- Successful run: `C:\Users\Lenovo\AppData\Local\Temp\wecom_runs\20261012-104343-0JQK`. Shared entry action used OCR, clicked the detected label, and classified the destination as `summary_input_page`. Final state: Smart Summary input page; no prompt pasted, generation started, or results copied. Failed diagnostics were retained without cleanup.
- Remaining limitation: navigation search still uses the left 17% envelope; hidden/renamed entries or large structural redesigns stop safely and require manual entry. Offline mocks do not establish live UI compatibility.
- Next step: commit and push the accepted iteration. Actual hidden/ambiguous-entry live scenarios have not been exercised; their fail-safe behavior is covered by offline mocks. The installed Claude skill has not been synchronized by this iteration. Full collection regression and installed-skill synchronization remain follow-ups outside this commit/push request. The July baseline below remains historical.

## Current Handoff Snapshot (2026-07-20)

Project entry: `AGENTS.md`

Do not recreate `CLAUDE.md` or `AGENT.md`.

Current state:

- No pending Claude task.
- The interview/template-isolation/preview-first/output-lifecycle refactor was accepted on 2026-07-20.
- The source skill and installed Claude skill are synchronized: 24 files on each side, with no missing, extra, or
  SHA256-mismatched files.
- Project reduction was completed on 2026-07-20: the completed task handoff and six installed-only historical test
  files were removed; multi-round acceptance history was consolidated into this snapshot.
- No WeCom diagnostic run, Python cache, or acceptance-test directory is retained.
- No live WeCom automation was run during acceptance or reduction.

## Current Product Contract

### Interview and evidence isolation

- Initialize a new task-local state for every report request.
- Confirm, in order and only when missing: report type, audience, exact period, template role, evidence sources, special
  requirements, then draft.
- Conversation memory may suggest stable style preferences but is never current evidence by default.
- Old reports, outputs, traces, WeCom results, and git statistics enter current evidence only when their period matches
  or the user explicitly opts in.

### Templates and references

- An old report explicitly described as a template/reference is `reference_only` immediately.
- Extract structure, formatting, tone, and granularity only. Never reuse its work items, names, dates, metrics, risks,
  conclusions, or plans.
- Do not ask whether template data is current after the user already classified it as a template/reference.
- Templates and accepted drafts remain current-task references unless the user explicitly approves broader persistence.

### Evidence menu

Present the complete multi-select menu after report type, audience, period, and template role are known:

- direct description or pasted text;
- uploaded/local files;
- git repositories;
- user-supervised WeCom Smart Summary collection;
- other user-specified sources;
- no additional evidence.

### Preview and export

- Default to a full in-conversation preview and revise there.
- Do not ask for an output location before the user explicitly requests save/export/fill-copy.
- Git collection is stdout-only without `--output`.
- WeCom collection is stdout-first without `--output`/`--output-json`.
- When export is requested, confirm the absolute output path immediately before writing. Never overwrite a supplied
  template; write a copy and preserve protected structure.

### Git evidence

- Full clone is the default; shallow clone requires explicit opt-in.
- Confirm repositories, period, branch scope, and author scope before collection.
- Local fallback requires matching origin and explicit disclosure.
- Never infer repositories or work facts from `reference_only` materials.

### WeCom automation

- Full-auto is Windows-only, user-supervised, and explicitly authorized per run. Do not advertise it as unattended,
  cross-environment stable, or compatible with every WeCom UI.
- Use `python -u` so stage progress is visible.
- Without an explicit diagnostics directory, use `%TEMP%\wecom_runs\<run-id>`.
- Success cleans only the current owned diagnostics path; failure retains one run bundle with `failure_summary.md`.
- Never silently delete failure diagnostics. Cleanup after failure requires separate authorization.
- Preserve foreground/page-state/click/scroll guards and exact final clipboard fingerprint verification.
- If copying becomes unstable, first obtain the failed run's `--screenshot-dir` and inspect `trace.jsonl`, `ocr/`, and
  `regions/`; do not start with live retry or coordinate guessing.

## Accepted Verification Baseline

- Output-location safety accepted.
- Git stdout-only behavior accepted.
- WeCom prompt-only file-free behavior accepted.
- WeCom progress flush/`python -u`, diagnostics policies, success cleanup, and failure retention accepted.
- Bottom action-bar copy search and exact fingerprint verification accepted.
- Preview-first contract validator accepted after reduction: 127 PASS, 0 FAIL, 0 SKIP, 3 dependency BLOCKED in the
  bundled environment used by Codex.
- Collision testing confirmed pre-existing sibling failure bundles survived byte-for-byte while only validator-owned
  paths were cleaned.

The 3 BLOCKED checks required unavailable `cv2`/`yaml`; they were reported honestly rather than counted as PASS.

## Retained Outputs

These four user-accepted deliverables remain intentionally:

```text
outputs/weekly_report_2026-06-29_2026-07-03.md
outputs/weekly_git_stats_2026-06-29_2026-07-03.md
outputs/wecom_summary_live_2026-06-29_2026-07-03.md
outputs/wecom_summary_live_2026-06-29_2026-07-03.json
```

They are historical deliverables, not automatic evidence for a new period.

## Reduction Record (2026-07-20)

Removed after consolidation:

- `docs/tasks/2026-07-17-interview-preview-output-lifecycle-refactor.md`;
- empty `docs/tasks/` directory;
- installed-only `mini_commits.md` and `pc_commits.md`;
- four installed-only `outputs/wecom_summary_test*` Markdown/JSON test files;
- `_validate_ocr_fingerprint_success.py`, which required deleted historical run data and wrote a report into project
  `outputs/`;
- `_validate_plus_fix.py`, whose cases all depended on deleted historical run directories and only produced SKIP;
- the hard-coded external A7K2 diagnostic-path assertions from `_validate_copy_fix.py`; its self-contained bottom-action
  regression remains and passes 43/43;
- obsolete multi-round acceptance narratives from the former `docs/status.md`.

Retained intentionally:

- runtime scripts and focused maintenance validators;
- WeCom templates and extraction/trace-analysis utilities;
- current references and bilingual README files;
- four accepted report outputs listed above.

## Next Step

- For a new report period, reconfirm report type, audience, exact period, template role, and evidence sources. Preview in
  conversation before discussing export.
- For WeCom collector maintenance, read `performance-report-assistant/references/wecom-smart-summary-collector.md` and
  do not run live automation without fresh supervision and authorization.
